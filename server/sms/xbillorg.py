import logging
from . import _httpclient
import urllib.parse
import time
import json
import sys, traceback
import hashlib

class Client(_httpclient.Client):
    def __init__(self,*a,**kw):
        self.logger = logging.getLogger('x-bill.org')
        self.pay_url = "https://api2.x-bill.org/?payment"
        self.request = self.post
        self.sid = kw.pop('sid')
        self.secret =  kw.pop('secret')
        self.cost = kw.pop('cost')
        self.test = kw.pop('test')
        super(Client,self).__init__( *a, **kw)

    async def _send_sms(self, phone, text, device):
        phone = phone.strip('+')
        data = json.dumps({
            'sid': self.sid,
            'phone': phone,
            'cost': self.cost,
            'hash': hashlib.md5((str(self.sid)+phone+str(self.cost)+self.secret).encode()).hexdigest(),
            'order_id': device
        })
        if self.test:
            data['test']='test'
        self.logger.info(data)
        return await self.request(self.base_url,data)

    async def send(self, phone, text, device, *a, **kw):
        #text = urllib.parse.quote(text)
        #text = urllib.parse.quote(text, safe='/%',encoding=self.encoding)
        try:
            res = await self._send_sms(phone, text, device)
            #assert res.get("result") == "success", 'Modem cant send message'
            self.logger.info(res.status)
            self.logger.info(res.read())
        except Exception as e:
            self.logger.error(e)
            traceback.print_exc(limit=5, file=sys.stderr)
            return False
        else:
            return True
