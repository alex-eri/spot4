import codecs
import socket
import struct
import logging

logger=logging.getLogger('codecs')

def ip2int(addr):
    return struct.unpack("!I", socket.inet_aton(addr))[0]

def int2ip(addr):
    return socket.inet_ntoa(struct.pack("!I", addr))


def trydecodeHexUcs2(a):
    try:
        a = codecs.decode(a, "hex")
        return a.decode('utf-16be')
        #return decodeUcs2(iter(a),len(a))
    except Exception as e:
        logger.error('Decode UCS2 failed')
        logger.error(e)
        logger.error(repr(a))
    return a


def decodeUcs2(byteIter, numBytes=256):
    """ Decodes UCS2-encoded text from the specified byte iterator, up to a maximum of numBytes """
    userData = []
    i = 0
    try:
        while i < numBytes:
            userData.append(chr((next(byteIter) << 8) | next(byteIter)))
            i += 2
    except StopIteration:
        # Not enough bytes in iterator to reach numBytes; return what we have
        pass
    return ''.join(userData)

def encodeUcs2byte(text):
    """ UCS2 text encoding algorithm

    Encodes the specified text string into UCS2-encoded bytes.

    :param text: the text string to encode

    :return: A bytearray containing the string encoded in UCS2 encoding
    :rtype: bytearray
    """
    result = bytearray()
    for b in map(ord, text):
        result.append(b >> 8)
        result.append(b & 0xFF)
    return result

def encodeUcs2(text):
    return str(codecs.encode(text.encode('utf-16be'), 'hex_codec'), 'ascii').upper()
