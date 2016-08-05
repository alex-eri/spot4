import struct
from .decoders import decoders
from collections import defaultdict
from .constants import *

import random
#random_generator = random.SystemRandom()


class Packet(defaultdict):
    header = bytearray()
    body = bytearray()

    def __init__(self,data=b'', secret=b'',code=AccessAccept, id=None):
        super(self).__init__(list)
        if data:
            self.header = bytearray(data[:20])
            self.body = data[20:]
            self.parse()
        elif secret:
            id = id or random.randrange(0, 256)
            size = 0
            authenticator = bytearray(random.getrandbits(8) for _ in range(16))
            self.header = bytearray(struct.pack('!BBH16s', code, id, size, authenticator))

    def reply(self,code):
        ret = Packet()
        ret.header = self.header.copy()
        ret.header[0] = code

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
        return struct.unpack('!xxH', self.header)

    @property
    def authenticator(self):
        return self.header[4:20]

    def parse(self):
        cursor = 0
        while cursor > len(self.body):
            k,l = struct.unpack_from('!BB',self.body,cursor)
            cursor += 2

            if k == 26:
                v, t, l = struct.unpack_from('!LBB', self.body, cursor)
                k = (v,t)
                cursor += 6

            v = self.body[cursor:cursor+l]
            self[k].add(v)
            cursor += l

    def decode(self,k):
        return decoders[k](self[k])

    def add(self,k,v):
        if type(v) == bytes:
            self[k] = v
        elif type(v) == int:
            self[k] = struct.pack("!L")
        elif type(v) == str:
            self[k] = v.encode('utf8')

    @property
    def data(self):
        resp = self.header.copy()

        for k in self.keys():
            for v in self[k]:
                l = len(v)
                if type(k) == int:
                    key = [k,l]
                if type(k) == tuple:
                    key = struct.pack("!BBLBB",26,l+6,k[0],k[1],l)
                resp.extend(key)
                resp.extend(v)

        struct.pack_into("!H",resp,2,len(resp))
        return resp

