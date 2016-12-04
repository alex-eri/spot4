from .message import *
import ssl
import logging
logger = logging.getLogger('eap.session')
debug = logger.debug

path = '/home/eri/Projects/CA/eap/'

ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLSv1)
ssl_context.load_cert_chain(path+'radius-chain.crt',path+'radius.key')

class peap_session():
    id = 0
    handshaked = False
    start = True

    def __init__(self):
        self.i = ssl.MemoryBIO()
        self.o = ssl.MemoryBIO()
        self.ssl = ssl_context.wrap_bio(self.i,self.o,True)

    def read(self):
        try:
            data = self.ssl.read()
        except ssl.SSLWantReadError:
            pass
        else:
            debug(data)
            return eap_message(data)

    def s2challenge(self,mes):
        i = mes.id + 1
        data = mschapv2_challenge(i,name)
        self.ssl.write(data)

    def s2identity(self):
        #data = struct.pack('!BBHB', Request, self.id+1, 5, Identity)
        data = bytes([Identity])
        self.ssl.write(data)


    def next(self):
        self.id += 1
        self.id &= 0xff
        data = self.o.read(994)
        return peap_request(self.id,data,self.o.pending,self.start)

    def feed(self,data):
        mes = eap_message(data)
        self.id = mes.id
        tls = mes.get('TLS')
        if tls:
            self.start = False
            self.i.write(tls)

    def do_handshake(self):
        try:
            self.ssl.do_handshake()
        except ssl.SSLWantReadError:
            pass
        else:
            self.handshaked = True
