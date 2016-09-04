SALT = b'441dbf23b4d344f19b89c76fd65cc75c'
SMSSENT = 1
SMSWAIT = 2

import base64, pyotp

def getsms(phone,mac):
    base = base64.b32encode("{phone}:{mac}:{salt}".format(phone,mac, SALT).encode('ascii'))
    otp =  pyotp.HOTP(base)
    return (otp.at(SMSSENT), otp.at(SMSWAIT))

def getpassw(username, mac, n=None):
    base = base64.b32encode("{username}:{mac}:{salt}".format(username, mac, SALT).encode('ascii'))
    otp = pyotp.TOTP(base)
    if n:
        return otp.at(time.time(),n)
    else:
        return otp.now()
