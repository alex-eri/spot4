import struct
from .constants import *
import uuid
import logging
logger = logging.getLogger('eap.message')
debug = logger.debug

def peap_request(i,data,more,start):
    l = len(data)
    flags = 0
    if more:
        flags |= 0x40
    if start:
        flags |= 0x20
    if data:
        flags |= 0x80
        ret = struct.pack('!BBHBBL', Request, i, l+10, PEAP,flags,l)
    else:
        ret = struct.pack('!BBHBB', Request, i, l+6, PEAP,flags)
    ret += data
    return ret

def mschapv2_challenge(i,name):
    challenge = uuid.uuid4().bytes
    l = 21 + len(name)
    #ret = struct.pack('!BBHBBBHB', Request, i, l, MSCHAPV2, Challenge, i,l-5,16)
    ret = struct.pack('!BBBHB', MSCHAPV2, Challenge, i,l,16)
    ret += challenge
    ret += name
    return challenge,ret


def mschapv2_success(i,data):
    l = len(data)
    ret = struct.pack('!BBBHB', MSCHAPV2, Success, i,l+5,l)
    ret += data
    return ret

def eap_body(data):
    r = dict()
    t = r['type'] =  data[0]

    body = data[1:]

    if t == Identity:
        r['Identity'] = body.decode('utf8')
    elif t == LegacyNak:
        r['LegacyNak'] = body[0]

    elif t == MD5Challenge:
        l =  body[0]
        r['MD5Challenge'] = body[1:l+1]

    elif t == PEAP:
        debug('peap')
        r['TLSFlags'] = flags = body[0]
        r['TLSMore'] = flags & 0x40

        if flags & 0x80:
            l = body[1] << 32 | body[2] << 16 | body[3] << 8 | body[4]
            if l:
                r['TLS'] = body[5:l+5]
            else:
                r['TLS'] = body[5:]
        else:
            r['TLS'] = body[1:]

    elif t == MSCHAPV2:
        r['ChapType'] = body[0]
        r['ChapId'] = body[1]
        l =  body[2] << 8 | body[3]
        if Challenge == r['ChapType']:
            cl = body[4]
            r['Challenge'] = body[5:cl+5]
            r['Identity'] = body[cl+5:]
        elif Response == r['ChapType']:
            cl = body[4]
            response = body[5:cl+5]
            r['Identity'] = body[cl+5:]
            #r['Flags'] = response[48]
            r['PeerChallenge'] = response[:16]
            r['NTResponse'] = response[24:48]

    return r


def eap_message(data):
    r = dict()
    r['raw'] = data
    cursor = 0
    r['code'],r['id'],r['length'] = data[0],data[1],data[2] << 8 | data[3]

    body = eap_body(data[4:r['length']])

    r.update(body)
    debug(r)

    return r






    
