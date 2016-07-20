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
import time, base64, pyotp
import struct

logger = logging.getLogger('radius')
debug = logger.debug


class RadiusProtocol:
    radhost = host.Host(dict=dictionary.Dictionary("dictionary"))
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

        code = data[0]
        debug(code)
        if code == packet.AccessRequest:
            self.pkt = self.radhost.CreateAuthPacket(
                packet=data,
                secret=self.radsecret
                )
            self.handle_auth()
        elif code == packet.AccountingRequest:
            self.pkt = self.radhost.CreateAcctPacket(
                packet=data,
                secret=self.radsecret
            )
            self.handle_acct()
        else:
            raise packet.PacketError('Packet is not request')

        for attr in self.pkt.keys():
            debug('{} :\t{}'.format(attr,self.pkt[attr]))



    def respond(self,resp):
        self.transport.sendto(resp, self.caller)

    def error_received(self, exc):
        debug('Error received:', exc)

    def connection_lost(self, exc):
        debug('stop', exc)


    def handle_auth(self):

        reply_attributes=dict(Class=uuid4().bytes)
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
        db.db.devices.find_one(creds,callback=self.got_user)

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
        if self['Acct-Status-Type'] == 1 : #start
            account = {
                'auth_id': self['Class'],
                'session_id': self['Acct-Session-Id']

            }
            #db.db.accounting.insert(account)

        self.respond( self.pkt.CreateReply().ReplyPacket() )

def setup_radius(config,PORT):

    name = current_process().name
    procutil.set_proc_name(name)
    debug("{}`s pid is {}".format(name, os.getpid()))

    loop = asyncio.get_event_loop()

    HOST = config.get('RADIUS_IP','0.0.0.0')

    RadiusProtocol.radsecret = config.get('RADIUS_SECRET','testing123').encode('ascii')

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

    return acct,auth



def main():
    import json
    config = json.load(open('config.json','r'))

    db.setup(
        config['DB']['SERVER'],
        config['DB']['NAME']
    )

    servers = setup(config)

    for proc in servers:
        proc.start()

    for proc in servers:
        proc.join()


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    main()
