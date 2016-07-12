from pyrad import dictionary, packet, host
import socketserver
from multiprocessing import Process, current_process
from uuid import uuid4
import hashlib
import logging
import db
import os
import procutil
import argparse
import sys
import asyncio
from asyncio import coroutine

logger = logging.getLogger('radius')
debug = logger.debug


class RadiusProtocol:
    radhost = None
    radsecret = None

    def __getitem__(self,y):
        try:
            r = self.pkt[y]
            #debug(r)
            return r[-1]
        except KeyError:
            return None

    def connection_made(self, transport):
        debug('start'+ transport.__repr__())
        self.transport = transport

    def datagram_received(self, data, addr):
        debug('From {} data received: '.format(addr))

        self.caller = addr
        self.pkt = self.radhost.CreateAuthPacket(
            packet=data,
            secret=self.radsecret
            )

        for attr in self.pkt.keys():
            debug('{} :\t{}'.format(attr,self.pkt[attr]))

        self.handle()

    def respond(self,resp):

        self.transport.sendto(resp, self.caller)

    def handle(self,data):
        raise NotImplementedError

    def error_received(self, exc):
        debug('Error received:', exc)

    def connection_lost(self, exc):
        debug('stop', exc)


class AuthProtocol(RadiusProtocol):

    def handle(self):

        reply_attributes=dict(Class=uuid4().bytes)
        self.reply = self.pkt.CreateReply(**reply_attributes)

        if self.check_password(self.defpassw):
            self.get_user()
        else:
            self.reply.code = packet.AccessReject
        self.respond( self.reply.ReplyPacket() )

    def get_user(self):
        creds = {'login':self['User-Name'],'mac':self['Calling-Station-Id']}
        db.db.devices.find_one(creds,callback=self.got_user)

    def got_user(self,response,error):
        if error:
            logger.error(error.__repr__())
        if response:
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


        if self['MS-CHAP2-Response'] and self['MS-CHAP-Challenge']:
            raise NotImplementedError



class AcctProtocol(RadiusProtocol):

    def handle(self):
        if self['Acct-Status-Type'] == 1 : #start
            account = {
                'auth_id': self['Class'],
                'session_id': self['Acct-Session-Id']

            }
            #db.db.accounting.insert(account)

        self.respond( self.pkt.CreateReply().ReplyPacket() )

def setup_acct(config):
    name = current_process().name
    procutil.set_proc_name(name)
    debug("{}`s pid is {}".format(name, os.getpid()))

    loop = asyncio.get_event_loop()

    HOST = config.get('RADIUS_IP','0.0.0.0')
    PORT = config.get('ACCT_PORT', 1813)


    AcctProtocol.radhost = host.Host(dict=dictionary.Dictionary("dictionary"))
    AcctProtocol.radsecret = config.get('RADIUS_SECRET','testing123').encode('ascii')

    t = asyncio.Task(loop.create_datagram_endpoint(
        AcctProtocol, local_addr=(HOST,PORT)))

    transport, server = loop.run_until_complete(t)
    try:
        loop.run_forever()
    finally:
        transport.close()
        loop.close()


def setup_auth(config):

    name = current_process().name
    procutil.set_proc_name(name)
    debug("{}`s pid is {}".format(name, os.getpid()))

    loop = asyncio.get_event_loop()

    HOST = config.get('RADIUS_IP','0.0.0.0')
    PORT = config.get('AUTH_PORT', 1812)


    AuthProtocol.radhost = host.Host(dict=dictionary.Dictionary("dictionary"))
    AuthProtocol.radsecret = config.get('RADIUS_SECRET','testing123').encode('ascii')
    AuthProtocol.defpassw = config.get('DEFAULT_PASSWORD','checksms') #.encode('ascii')

    t = asyncio.Task(loop.create_datagram_endpoint(
        AuthProtocol, local_addr=(HOST,PORT)))

    transport, server = loop.run_until_complete(t)
    try:
        loop.run_forever()
    finally:
        transport.close()
        loop.close()


def setup(config):

    acct = Process(target=setup_acct, args=(config,))
    acct.name = 'radius.acct'

    auth = Process(target=setup_auth, args=(config,))
    auth.name = 'radius.auth'

    return acct,auth



def main():
    config = json.load(open('config.json','r'))

    servers = setup(config)

    for proc in servers:
        proc.start()

    for proc in servers:
        proc.join()


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    main()
