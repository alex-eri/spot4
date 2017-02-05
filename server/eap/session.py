from .message import eap_body, eap_message, mschapv2_challenge, peap_request
from .constants import *

import ssl
import logging
logger = logging.getLogger('eap.session')
debug = logger.debug

ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLSv1)
ssl_context.load_cert_chain('radius.pem')
#ssl_context.load_dh_params('dhparam.pem')

class peap_session():
    id = 0
    handshaked = False
    start = True
    MSCHAPChallenge = None

    def __init__(self):
        self.i = ssl.MemoryBIO()
        self.o = ssl.MemoryBIO()
        self.ssl = ssl_context.wrap_bio(self.i,self.o,True)

    def read(self):
        try:
            data = self.ssl.read()
        except ssl.SSLWantReadError:
            return {'needmore':True}
        else:
            debug(data)
            return eap_body(data)

    def s2challenge(self,mes):
        debug('s2challenge')
        debug(self.o.pending)
        i = mes.get('id')  or self.id
        challenge, data = mschapv2_challenge(i+1,b'spot4')
        self.challenge = challenge
        self.ssl.write(data)

    def s2identity(self):
        #data = struct.pack('!BBHB', Request, self.id+1, 5, Identity)
        data = bytes([Identity])
        self.ssl.write(data)

    def s2success(self,mes,success):
        i = mes.get('id') or self.id
        data = mschapv2_success(i+1,success)
        self.ssl.write(data)

    def next(self):
        self.id += 1
        self.id &= 0xff
        data = self.o.read(994)
        return peap_request(self.id,data,self.o.pending,self.start)

    def feed(self,data):
        debug('feed')
        mes = eap_message(data)
        self.id = mes['id']
        tls = mes.get('TLS')
        debug(tls)
        if tls:
            self.start = False
            self.i.write(tls)

    def do_handshake(self):
        debug('hs')
        try:
            self.ssl.do_handshake()
        except ssl.SSLWantReadError:
            pass
        else:
            self.handshaked = True
