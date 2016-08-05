import literadius as rad
from multiprocessing import Process, current_process
from uuid import uuid4
import hashlib
import logging
import os
from utils import procutil
import asyncio
import time, base64, pyotp
import netflow

logger = logging.getLogger('radius')
debug = logger.debug



class RadiusProtocol:
    radsecret = None
    db = None

    def __getitem__(self,y):
        r = self.pkt[y]
	if r:
            return r[-1]

    def connection_made(self, transport):
        debug('start'+ transport.__repr__())
        self.transport = transport

    def datagram_received(self, data, addr):
        debug('From {} data received: '.format(addr))

        self.caller = addr

        self.pkt = rad.Packet(data, self.radsecret)

        if self.pkt.code == rad.AccessRequest:
            self.handle_auth()
        elif self.pkt.code == rad.AccountingRequest:
            self.handle_acct()
        else:
            raise Exception('Packet is not request')

        if logger.isEnabledFor(logging.DEBUG):
            for attr in self.pkt.keys():
                debug('{} :\t{}'.format(attr,self.pkt.decode(attr))



    def respond(self,resp):
        self.transport.sendto(resp, self.caller)

    def error_received(self, exc):
        debug('Error received:', exc)

    def connection_lost(self, exc):
        debug('stop', exc)


    def handle_auth(self):

        reply_attributes=dict(Class=uuid4().hex.encode('ascii'))
        self.reply = self.pkt.CreateReply(**reply_attributes)

        q = {
            'login':self['User-Name'],
            'mac':self['Calling-Station-Id'],
            'checked':True
             }

        base = base64.b32encode("{login}#{mac}".format(**q).encode('ascii'))
        otp = pyotp.TOTP(base)

        if self.check_password(otp.now()) or self.check_password(otp.at(time.time(),-1)):
            self.get_user(q)
        else:
            debug("otp is {}".format(otp.now()))
            self.reply.code = packet.AccessReject
        self.respond( self.reply.ReplyPacket() )

    def get_user(self,creds):
        self.db.devices.find_one(creds,callback=self.got_user)

    def got_user(self,response,error):
        if error:
            logger.error(error.__repr__())
        if response:
            debug(response)
            self.reply.code = packet.AccessAccept
            self.respond( self.reply.ReplyPacket())
        else:
            self.reply.code = packet.AccessReject
            self.respond( self.reply.ReplyPacket() )

    def check_password(self, cleartext=""):
        pkt = self.pkt

        if self['User-Password']:
            #debug(pkt.PwDecrypt(self['User-Password']))
            return (pkt.PwDecrypt(self['User-Password']) == cleartext)

        if self['CHAP-Password'] and self['CHAP-Challenge']:

            chap_challenge = self['CHAP-Challenge']
            chap_password  = self['CHAP-Password']

            chap_id = bytes([chap_password[0]])
            chap_password = chap_password[1:]

            m = hashlib.md5()
            m.update(chap_id)
            m.update(cleartext.encode(encoding='utf_8', errors='strict'))
            m.update(chap_challenge)

            return chap_password == m.digest()

        if self['MS-CHAP-Response'] and self['MS-CHAP-Challenge']:
            #https://github.com/mehulsbhatt/freeIBS/blob/master/radius_server/pyrad/packet.py
            raise NotImplementedError

        if self['MS-CHAP2-Response'] and self['MS-CHAP-Challenge']:
            raise NotImplementedError

    def handle_acct(self):
        q = {
                'auth_class': self['Class'],
                'session_id': self['Acct-Session-Id'],
            }

        if self['Acct-Status-Type'] == STATUS_TYPE_START:
            upd = {
                '$currentDate':{'start_date':True},
                '$set':{
                    'ip': self['Framed-IP-Address'],
                    'nas': self['NAS-Identifier'],
                    'called': self['Called-Station-Id'],
                    'mac': self['Calling-Station-Id'],
                    'login': self['User-Name'],
                    'start_time': self['Event-Timestamp']
                }
            }

        elif self['Acct-Status-Type'] == STATUS_TYPE_UPDATE or \
             self['Acct-Status-Type'] == STATUS_TYPE_STOP:

            debug(self['Acct-Input-Octets'])
            debug(self['Acct-Input-Gigawords'])

            account = {
                'session_time': self['Acct-Session-Time'],
                'input_bytes': self['Acct-Input-Gigawords'] or 0 << 32 | self['Acct-Input-Octets'],
                'input_packets': self['Acct-Input-Packets'],
                'output_bytes': self['Acct-Output-Gigawords'] or 0 << 32 | self['Acct-Output-Octets'],
                'output_packets': self['Acct-Output-Packets'],
                'delay':self['Acct-Delay-Time'],
                'event_time': self['Event-Timestamp']
            }
            if self['Acct-Status-Type'] == STATUS_TYPE_UPDATE:
                upd={ '$set': account }

            elif self['Acct-Status-Type'] == STATUS_TYPE_STOP:
                account['termination_cause'] =  self['Acct-Terminate-Cause']
                upd = {
                        '$set': account,
                        '$currentDate':{'stop_date':True}
                    }

        self.db.accounting.find_and_modify(q,upd,upsert=True,new=True,callback=self.accounting_cb)
        debug('accounting respond')
        self.respond( self.pkt.CreateReply().ReplyPacket() )

    def accounting_cb(self,r,e,*a,**kw):
        debug(r)
        if r and r.get('termination_cause'):
            loop = asyncio.get_event_loop()
            asyncio.run_coroutine_threadsafe(
                netflow.aggregate(self.db, self.caller[0], r),
                loop)

        if e:
            logger.error('accounting callback')
            logger.error(e.__repr__())


def setup_radius(config,PORT):

    name = current_process().name
    procutil.set_proc_name(name)
    debug("{}`s pid is {}".format(name, os.getpid()))

    loop = asyncio.get_event_loop()

    import storage
    db = storage.setup(
        config['DB']['SERVER'],
        config['DB']['NAME']
    )

    db.accounting.ensure_index(
        [ ("auth_class",1), ("session_id",1) ],
        unique=True, dropDups=True ,callback=storage.index_cb)

    HOST = config.get('RADIUS_IP','0.0.0.0')

    RadiusProtocol.radsecret = config.get('RADIUS_SECRET','testing123').encode('ascii')
    RadiusProtocol.db = db

    t = asyncio.Task(loop.create_datagram_endpoint(
        RadiusProtocol, local_addr=(HOST,PORT)))

    transport, server = loop.run_until_complete(t)
    try:
        loop.run_forever()
    finally:
        transport.close()
        loop.close()


def setup(config):
    acct = Process(target=setup_radius, args=(config, config.get('ACCT_PORT', 1813)))
    acct.name = 'radius.acct'

    auth = Process(target=setup_radius, args=(config, config.get('AUTH_PORT', 1812)))
    auth.name = 'radius.auth'

    return [acct,auth]



def main():
    import json
    config = json.load(open('config.json','r'))

    servers = setup(config)

    for proc in servers:
        proc.start()

    for proc in servers:
        proc.join()


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    main()
