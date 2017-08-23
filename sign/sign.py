from ctypescrypto.pkey import PKey
from base64 import b64encode


key = open('/home/eri/Projects/CA/my/spot4.key','rb')
verifier = PKey(privkey=key.read())

subj = "Вансевич"
digest = subj.encode('utf-8')
sign = verifier.sign(digest)
sign = b64encode(sign)

LIC = subj + "::" + sign.decode('ascii')

print('"LIC": "%s",' % LIC)
