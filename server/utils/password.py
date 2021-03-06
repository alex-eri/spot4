SALT = '441dbf23b4d344f19b89c76fd65cc75c'
SMSSENT = 1
SMSWAIT = 2
SMSLEN = 4

import random

import base64, pyotp,time

#def getsms(phone,mac):
#    base = base64.b32encode("{phone}:{mac}:{salt}".format(phone,mac, SALT).encode('ascii'))
#    otp =  pyotp.HOTP(base)
#    return (otp.at(SMSSENT), otp.at(SMSWAIT))

def getsms(phone,mac):
    return str(random.randrange(0,10**SMSLEN-1)).zfill(SMSLEN)

def getpassw(username="", mac="", n=None, *a, **kw):
    base = base64.b32encode(":".join([username, mac, SALT]).encode('ascii'))
    otp = pyotp.TOTP(base)
    if n:
        return otp.at(time.time(),n)
    else:
        return otp.now()
