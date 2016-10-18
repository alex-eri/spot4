import struct
from .decoders import decoders
from collections import defaultdict
from .constants import *

from mschap import mschap

import random
#random_generator = random.SystemRandom()
import hashlib
import threading
import logging
logger = logging.getLogger('packet')
debug = logger.debug

class Packet(defaultdict):
    def __init__(self,data=b'', secret=b'',code=AccessAccept, id=None, authenticator=None):
        super().__init__(bytes)

        self.lock = threading.Lock()
        self.header = bytearray()
        self.body = bytearray()
        self.secret = secret

        if data:
            self.header = bytearray(data[:20])
            self.body = data[20:]
            self.parse()
        elif secret:

            self.header = bytearray(struct.pack('!BBH', code, id, 0))
            if id is None: id = random.randrange(0, 256)
            authenticator = authenticator or bytearray(random.getrandbits(8) for _ in range(16))
            self.header = bytearray(struct.pack('!BBH16s', code, id, 20,authenticator))

    def reply(self,code):
        return Packet(
            secret=self.secret,
            id=self.id,
            code=code,
            authenticator=self.authenticator)


    @property
    def code(self):
        return self.header[0]

    @code.setter
    def code(self,value):
        self.header[0] = value

    @property
    def id(self):
        return self.header[1]

    @property
    def size(self):
        return struct.unpack_from('!H', self.header,2)[0]

    @property
    def authenticator(self):
        return self.header[4:20]

    def parse(self):
        cursor = 0

        while cursor < len(self.body):

            k,l = struct.unpack_from('!BB', self.body, cursor)
            cursor += 2

            if k == 26:
                v, t, l = struct.unpack_from('!LBB', self.body, cursor)
                k = (v,t)
                cursor += 6

            l2 = l-2

            v = self.body[cursor:cursor+l2]
            self[k] = v
            cursor += l2

    def decode(self,k):
        return decoders[k](self[k])

    def encode(self,v):
        if isinstance(v, bytes):
            return v
        elif isinstance(v, int):
            return struct.pack("!L",v)
        elif isinstance(v, str):
            return v.encode('utf8')

    @property
    def data(self):
        with self.lock:
            resp = self.header.copy()

            for k,v in self.items():
                v = self.encode(v)
                l = len(v)+2
                if isinstance(k,int):
                    key = [k,l]
                elif isinstance(k, tuple):
                    key = struct.pack("!BBLBB",26,l+6,k[0],k[1],l)
                resp.extend(key)
                resp.extend(v)

            struct.pack_into("!H",resp,2,len(resp))
            authenticator = hashlib.md5(resp+self.secret).digest()
            struct.pack_into("!16s",resp,4,authenticator)
            return resp

    def pw_decrypt(self,v):
        last = self.authenticator.copy()
        buf = v
        pw = b''
        while buf:
            hash = hashlib.md5(self.secret + last).digest()
            for i in range(16):
                pw += bytes((hash[i] ^ buf[i],))

            (last, buf) = (buf[:16], buf[16:])

        pw=pw.rstrip(b'\x00')
        debug(pw)
        return pw.decode('utf-8')

    def check_password(self, cleartext=""):
        debug(cleartext)

        if self[UserPassword]:
            try:
                return (self.pw_decrypt(self[UserPassword]) == cleartext)
            except UnicodeDecodeError:
                return

        chap_challenge = self[CHAPChallenge]
        chap_password  = self[CHAPPassword]

        if chap_password:

            chap_id = bytes([chap_password[0]])
            chap_password = chap_password[1:]

            m = hashlib.md5()
            m.update(chap_id)
            m.update(cleartext.encode(encoding='utf-8', errors='strict'))
            m.update(chap_challenge)
            res = m.digest()
            debug(res)
            debug(chap_password)
            return chap_password == m.digest()

        if self[MSCHAPResponse] and self[MSCHAPChallenge]:
            return mschap.generate_nt_response_mschap(
                self[MSCHAPChallenge],cleartext
            ) == self[MSCHAPResponse][26:]

        if self[MSCHAP2Response] and self[MSCHAPChallenge]:
            raise NotImplementedError

        #TODO: MSCHAP2 EAP

