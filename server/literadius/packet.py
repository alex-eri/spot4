import struct
from .decoders import decoders
from collections import defaultdict
from .constants import *

from mschap import mschap
import hmac

import random
#random_generator = random.SystemRandom()
import hashlib
import threading
import logging
logger = logging.getLogger('packet')
debug = logger.debug

import os

class Packet(defaultdict):
    _reply = None
    def __init__(self,data=b'', secret=b'',code=AccessAccept, id=None, authenticator=None):
        super().__init__(bytes)

        self.lock = threading.Lock()
        self.header = bytearray()
        self.body = bytearray()
        self.secret = secret
        self.ma = None

        if data:
            self.header = bytearray(data[:20])
            self.body = data[20:]
            self.parse()
        elif secret:
            #self.header = bytearray(struct.pack('!BBH', code, id, 0))
            if id is None: id = random.randrange(0, 256)
            authenticator = authenticator or os.urandom(16)
            self.header = bytearray(struct.pack('!BBH16s', code, id, 20,authenticator))

    def reply(self,code=AccessReject):
        if not self._reply:
            self._reply = Packet(
                secret=self.secret,
                id=self.id,
                code=code,
                authenticator=self.authenticator)
        return self._reply


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

    def get_message_authenticator(self,cursor):
        m = hmac.HMAC(key=self.secret)
        m.update(self.header)
        m.update(self.body[:cursor])
        m.update(bytes(16))
        m.update(self.body[cursor+16:])
        return m.digest()

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

            if k == MessageAuthenticator:
                d = self.get_message_authenticator(cursor)
                assert d == v, 'MessageAuthenticator not valid'

            self[k] = v
            cursor += l2

    def decode(self,k):
        v = self.get(k)
        if isinstance(v, bytes):
            return decoders[k](v)
        return v

    def encode(self,v):
        if isinstance(v, bytes):
            return v
        elif isinstance(v, bytearray):
            return bytes(v)
        elif isinstance(v, int):
            return struct.pack("!L",v)
        elif isinstance(v, str):
            return v.encode('utf8')

    def data(self):
        with self.lock:
            resp = self.header.copy()
            body = bytearray()
            for k,v in self.items():
                if k == MessageAuthenticator:
                    continue
                v = self.encode(v)
                length = len(v)

                while length > 0:
                    if isinstance(k,int):
                        if length > 253: cut = 253
                        else: cut = length
                        key = (k,cut+2)
                    elif isinstance(k, tuple):
                        if length > 249: cut = 249
                        else: cut = length
                        key = struct.pack("!BBLBB",26,cut+8,k[0],k[1],cut+2)

                    body.extend(key)
                    body.extend(v[:cut])
                    v=v[cut:]
                    length -= cut


            ma_cursor = 0
            if MessageAuthenticator in self.keys():
                ma_cursor = len(body)+2
                body.extend((MessageAuthenticator,18))
                body.extend(bytes(16))

            struct.pack_into("!H",resp,2,20+len(body))

            if ma_cursor \
                  and self.code in (AccessRequest,AccessAccept,AccessReject,AccessChallenge):

                self.header = resp
                self.body = body

                self[MessageAuthenticator] = message_authenticator = self.get_message_authenticator(ma_cursor)
                body[ma_cursor:ma_cursor+16] = message_authenticator
                #struct.pack_into("!16s",resp,ma_cursor+20,message_authenticator)

                #self.body = body
                #debug(self.body)
                #debug(message_authenticator)
                #debug(self.get_message_authenticator(ma_cursor))

            resp.extend(body)

            authenticator = hashlib.md5(resp+self.secret).digest()
            struct.pack_into("!16s",resp,4,authenticator)

            return bytes(resp)

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

        if UserPassword in self.keys():
            try:
                return (self.pw_decrypt(self[UserPassword]) == cleartext)
            except UnicodeDecodeError:
                return

        if CHAPPassword in self.keys():

            chap_challenge = self[CHAPChallenge]
            chap_password  = self[CHAPPassword]

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

        if MSCHAPChallenge in self.keys():

            if MSCHAPResponse in self.keys():
                return mschap.generate_nt_response_mschap(
                    self[MSCHAPChallenge],cleartext
                ) == self[MSCHAPResponse][26:]

            if MSCHAP2Response in self.keys():
                ms_chap_response = self[MSCHAP2Response]
                if 50 == len(ms_chap_response):
                    nt_response = ms_chap_response[26:50]
                    peer_challenge = ms_chap_response[2:18]
                    authenticator_challenge = self[MSCHAPChallenge]
                    user = self[UserName]

                    success = mschap.generate_nt_response_mschap2(
                        authenticator_challenge,
                        peer_challenge,
                        user,
                        cleartext) == nt_response
                    if success:
                        auth_resp = mschap.generate_authenticator_response(
                            cleartext,
                            nt_response,
                            peer_challenge,
                            authenticator_challenge,
                            user)
                        return auth_resp

#                    reply = self.reply()
#                    with reply.lock:
#                        reply[MSCHAP2Success] = auth_resp
#                    return success


