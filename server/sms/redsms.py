import logging
from . import _httpclient
import urllib.parse
import time

import sys, traceback
import hashlib

class Client(_httpclient.Client):
    def __init__(self,*a,**kw):
        self.logger = logging.getLogger('http')
        self.base_url = "https://lk.redsms.ru/get/send.php"
        self.request = self.get
        self.apikey =  kw.pop('apikey')
        self.login =  kw.pop('login')
        self.callie = kw.get('number','http')
        super(Client,self).__init__( *a, **kw)

    async def _send_sms(self,phone,text):
        req = await self.get('https://lk.redsms.ru/get/timestamp.php')
        try:
            timestamp = int(req.read()) or int(time.time())
        except Exception as e:
            timestamp = int(time.time())

        timestamp = str(timestamp)

        phone = phone[1:]

        data = {
            'login': self.login,
            'phone':phone,
            'text':text,
            'sender':self.callie,
            'timestamp': timestamp,
        }

        sigstr = b""
        for i in sorted(data.keys()):
            sigstr += data[i].encode(self.encoding)
        sigstr += self.apikey.encode(self.encoding)

        data['signature'] = hashlib.md5(sigstr).hexdigest()

        return await self.request(self.base_url,data)

    async def send(self,phone,text,*a,**kw):
        #text = urllib.parse.quote(text)
        #text = urllib.parse.quote(text, safe='/%',encoding=self.encoding)
        try:
            res = await self._send_sms(phone,text)
            #assert res.get("result") == "success", 'Modem cant send message'
        except Exception as e:
            self.logger.error(e)
            traceback.print_exc(limit=5, file=sys.stderr)
            return False
        else:
            return True
