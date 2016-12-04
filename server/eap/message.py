import struct
from .constants import *

def peap_request(i,data,more,start):
    l = len(data) + 6
    flags = 0
    if more:
        flags |= 0x40
    if start:
        flags |= 0x20
    ret = struct.pack('!BBHBB', Request, i, l, PEAP,flags)
    ret += data
    return ret


class eap_message(dict):
    def __init__(self,data):
        self.raw = data
        cursor = 0
        self.code,self.id,self.length,self.type =  struct.unpack_from('!BBHB', self.raw, cursor)
        cursor+=5
        if self.type == Identity:
            self[Identity] = self.raw[cursor:].decode('utf8')
        elif self.type == MD5Challenge:
            l =  self.raw[cursor]
            cursor += 1
            self[MD5Challenge] = self.raw[cursor:cursor+l]
        elif self.type == LegacyNak:
            self[LegacyNak] = self.raw[cursor]

        elif self.type == PEAP:
            self['TLSFlags'] = flags = self.raw[cursor]
            cursor += 1
            if flags & 0x80:
                self['TLSLength'] = struct.unpack_from('!L', self.raw, cursor)[0]
                cursor += 4
            self['TLSMore'] = flags & 0x40

            self['TLS'] = self.raw[cursor:]
