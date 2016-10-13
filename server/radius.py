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
import socket
logger = logging.getLogger('radius')
debug = logger.debug
from datetime import datetime
from utils.password import getsms, getpassw
import pytz




class RadiusProtocol(asyncio.DatagramProtocol):
    radsecret = None
    db = None
    ttl = 56

    def __getitem__(self,y):
        r = self.pkt.decode(y)
        return r

    def connection_made(self, transport):
        self.transport = transport
        sock = self.transport.get_extra_info('socket')
        sock.setsockopt(socket.SOL_IP, socket.IP_TTL, self.ttl)


    def datagram_received(self, data, addr):
        debug('From {} data received: '.format(addr))
        self.caller = addr
        self.pkt = rad.Packet(data, self.radsecret)

        debug(self.pkt.authenticator)
        debug(self.pkt.secret)

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
        self.reply = self.pkt.reply(rad.AccessReject)
        self.reply[rad.Class]=uuid4().bytes

        self.db.users.find_one({'_id':self[rad.UserName]},callback=self.got_user)
        debug('user was {}'.format(self[rad.UserName]))

    def got_user(self,response,error):
        if error:
            logger.error(error.__repr__())
        if response:
            q = {
                'username':response['_id'],
                'mac':self[rad.CallingStationId]
                 }
            if response.get('password') and self.check_password(response.get('password')):
                self.db.devices.find_and_modify(q,
                    {'$currentDate':{'seen':True},'$set':{'checked':True}},
                    upsert=True, new=True,
                    callback=self.got_device
                    )
                self.reply.code = rad.AccessAccept
            else:
                for n in [0,-1]:
                    psw = getpassw(n=n, **q)
                    if self.check_password(psw):
                        q['checked']=True
                        self.db.devices.find_one(q,callback=self.got_device)
                        return
                    else:
                        debug('otp was {}'.format(psw))
        #reject
        self.respond( self.reply )


    def got_device(self,response,error):
        if error:
            logger.error(error.__repr__())
        if response:
            self.reply.code = rad.AccessAccept
        self.respond( self.reply )

    def check_password(self, cleartext=""):
        return self.pkt.check_password(cleartext)


    def handle_acct(self):
        q = {
                'auth_class': self[rad.Class],
                'session_id': self[rad.AcctSessionId],
                #'sensor': self.caller[0]
            }

        upd = {}

        if self[rad.AcctStatusType] == rad.AccountingStart:
            upd['$set']={
                    'ip': self[rad.FramedIPAddress],
                    'nas': self[rad.NASIdentifier],
                    'callee': self[rad.CalledStationId],
                    'caller': self[rad.CallingStationId],
                    'username': self[rad.UserName],
                    'start_time': self[rad.EventTimestamp]
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
#            if self[rad.AcctStatusType] == rad.AccountingUpdate:
#                pass #update always

            if self[rad.AcctStatusType] == rad.AccountingStop:
                account['termination_cause'] =  self[rad.AcctTerminateCause]

            upd['$set']= account

        elif self[rad.AcctStatusType] in [rad.AccountingOn, rad.AccountingOff]:
            self.db.accounting.find_and_modify(
                {'nas': self[rad.NASIdentifier],'termination_cause':{'$exists': False}},
                {'$set':{'termination_cause': rad.TCNASReboot}},
                callback=self.accounting_cb
            )
            #TODO accountin on/off

        if upd :
            upd.update({
            '$setOnInsert':{'start_date':datetime.now(pytz.utc)},
            '$currentDate':{'stop_date':True},
            '$set':{'sensor':{
                'ip':self.caller[0],
                'port':self.caller[1]
              }}
            })

            self.db.accounting.find_and_modify(q,upd,upsert=True,new=True,callback=self.accounting_cb)

        self.respond( self.pkt.reply(rad.AccountingResponse) )

    def accounting_cb(self,r,e,*a,**kw):
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

    #db.accounting.ensure_index(
    #    [ ("auth_class",1), ("session_id",1) ],
    #    unique=True, dropDups=True ,callback=storage.index_cb)

    db.accounting.ensure_index([ ("username",1) ], unique=False, callback=storage.index_cb)

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
