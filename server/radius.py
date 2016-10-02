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

from utils.password import getsms, getpassw


class RadiusProtocol:
    radsecret = None
    db = None

    def __getitem__(self,y):
        r = self.pkt.decode(y)
        return r

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
                debug('{} :\t{}\t{}'.format(attr,self.pkt[attr],self.pkt.decode(attr)))


    def respond(self,resp):
        self.transport.sendto(resp.data, self.caller)
        print(resp.data)

        if logger.isEnabledFor(logging.DEBUG):
            for attr in resp.keys():
                debug('{} :\t{}'.format(attr,resp.decode(attr)))

    def error_received(self, exc):
        debug('Error received:', exc)

    def connection_lost(self, exc):
        debug('stop', exc)


    def handle_auth(self):

        reply_attributes=dict(Class=uuid4().hex.encode('ascii'))
        self.reply = self.pkt.reply(rad.AccessReject)



        self.db.users.find_one({'_id':self[rad.UserName]},callback=self.got_user)


        debug("otp was {}".format(otp.now()))

        self.respond( self.reply )

    def got_user(self,response,error):
        if error:
            logger.error(error.__repr__())
        if response:
            q = {
                'username':response['username'],
                'mac':self[rad.CallingStationId]
                 }
            if self.check_password(response.get('password')):
                self.db.devices.find_and_modify(q,
                    {'$currentDate':{'seen':True},'$set':{'checked':True}},
                    upsert=True, new=True,
                    callback=self.got_device
                    )
            else:
                for n in [0,-1]:
                    psw = getpassw(n=n, **q)
                    if self.check_password(psw):
                        q['checked']=True
                        self.db.devices.find_one(q,callback=self.got_device)
                        return
        self.respond( self.reply )


    def got_device(self,response,error):
        if error:
            logger.error(error.__repr__())
        if response:
            self.reply.code = rad.AccessAccept
        self.respond( self.reply )

    def check_password(self, cleartext=""):
        if not cleartext: return

        pkt = self.pkt
        debug(type(cleartext))
        debug(type(pkt.pw_decrypt(pkt[rad.UserPassword])))
        debug(pkt.pw_decrypt(pkt[rad.UserPassword]) == cleartext)

        if pkt[rad.UserPassword]:
            return (pkt.pw_decrypt(pkt[rad.UserPassword]) == cleartext)

        chap_challenge = pkt[rad.CHAPChallenge]
        chap_password  = pkt[rad.CHAPPassword]

        if chap_challenge and chap_password:

            chap_id = bytes([chap_password[0]])
            chap_password = chap_password[1:]

            m = hashlib.md5()
            m.update(chap_id)
            m.update(cleartext.encode(encoding='utf_8', errors='strict'))
            m.update(chap_challenge)

            return chap_password == m.digest()
        """
        if self['MS-CHAP-Response'] and self['MS-CHAP-Challenge']:
            #https://github.com/mehulsbhatt/freeIBS/blob/master/radius_server/pyrad/packet.py
            raise NotImplementedError

        if self['MS-CHAP2-Response'] and self['MS-CHAP-Challenge']:
            raise NotImplementedError
        """

    def handle_acct(self):
        q = {
                'auth_class': self[rad.Class],
                'session_id': self[rad.AcctSessionId],
                'sensor': self.caller[0]
            }
        upd = {}

        if self[rad.AcctStatusType] == rad.AccountingStart:
            upd = {
                '$currentDate':{'start_date':True},
                '$set':{
                    'ip': self[rad.FramedIPAddress],
                    'nas': self[rad.NASIdentifier],
                    'callee': self[rad.CalledStationId],
                    'caller': self[rad.CallingStationId],
                    'username': self[rad.UserName],
                    'start_time': self[rad.EventTimestamp]
                }
            }

        elif self[rad.AcctStatusType] in [rad.AccountingUpdate, rad.AccountingStop] :

            account = {
                'session_time': self[rad.AcctSessionTime],
                'input_bytes': self[rad.AcctInputGigawords] or 0 << 32 | self[rad.AcctInputOctets],
                'input_packets': self[rad.AcctInputPackets],
                'output_bytes': self[rad.AcctOutputGigawords] or 0 << 32 | self[rad.AcctOutputOctets],
                'output_packets': self[rad.AcctOutputPackets],
                'delay':self[rad.AcctDelayTime],
                'event_time': self[rad.EventTimestamp]
            }
            if self[rad.AcctStatusType] == rad.AccountingUpdate:
                upd={ '$set': account }

            elif self[rad.AcctStatusType] == rad.AccountingStop:
                account['termination_cause'] =  self[rad.AcctTerminateCause]
                upd = {
                        '$set': account,
                        '$currentDate':{'stop_date':True}
                    }
        if upd :
            self.db.accounting.find_and_modify(q,upd,upsert=True,new=True,callback=self.accounting_cb)
        debug('accounting respond')
        self.respond( self.pkt.reply(rad.AccountingResponse) )

    def accounting_cb(self,r,e,*a,**kw):
        #debug(r)
        #if r and r.get('termination_cause'):
        #    loop = asyncio.get_event_loop()
        #    asyncio.run_coroutine_threadsafe(
        #        netflow.aggregate(self.db, r),
        #        loop)

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
