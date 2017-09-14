from ctypescrypto.pkey import PKey
from base64 import b64encode


key = open('/home/eri/Projects/CA/my/spot4.key','rb')
verifier = PKey(privkey=key.read())


""""LIC": "Леонид (‎‎+7 978 843-56-46, mail.leonid@gmail.com, 
Крым)::YkfoZTFpvxMPHhnmZeSIpTRynHPstc4T/JO8Nap5MyFdB988SazXZv8sQc/qyhqqU65spEI7otU/P9tG6PbEV2tygEUiEZteo3Nz3+bKiJEBozzPRYOe2H5CgUE9O5hmDVLORk66Yf7J4ru/B0o0A3V3ZEZQfInbparn/vpBRgvqCWQonb0PWkPqT2d8t2jpGpiqPIPMBCT/VzJ0qbBTeh2tBx6u1bYCCqVEy94mer6yo+rXIdshldEQC3gtya4mA+apWJ0hgEyLxkU6qxt6DMLu5k604hH7qHKZx/1A2zCsjqyAw89r+X+w9nERuEdB/ZiAgg3N9TZxp12mb7Tk5w==","""

subj = "ГК Октябрьский, ИП Черникова (Марк Бузоверов)"
digest = subj.encode('utf-8')
sign = verifier.sign(digest)
sign = b64encode(sign)

LIC = subj + "::" + sign.decode('ascii')

print('"LIC": "%s",' % LIC)
