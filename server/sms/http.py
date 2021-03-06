import logging
from . import _httpclient
import urllib.parse

import traceback

class Client(_httpclient.Client):

    def __init__(self,*a,**kw):
        print(a)
        print(kw)
        self.logger = logging.getLogger('http')
        self.base_url = kw.pop('url')
        method = kw.pop('method','get').lower()
        assert method in ['get','post'], 'wrong http method'
        self.request = getattr(self,method)
        self.query =  kw.pop('query')
        self.reciever = kw.get('reciever', False) and False
        self.callie = kw.get('number', 'http')
        self.strip =  kw.get('strip', False)
        self.quote =  kw.get('quote', True)
        super(Client,self).__init__( *a, **kw)

    def _send_sms(self,phone,text):
        if self.strip:
            phone=phone.strip('+')
        data = self.query.format(phone=phone,text=text)

        return self.request(self.base_url,data)

    async def send(self,phone,text,*a,**kw):
        #text = urllib.parse.quote(text)
        if self.quote:
            text = urllib.parse.quote(text, safe='/%', encoding=self.encoding)
        try:
            ret = await self._send_sms(phone, text)
            self.logger.info(ret.read())
            #assert res.get("result") == "success", 'Modem cant send message'
        except Exception as e:
            self.logger.error(e)
            self.logger.error(traceback.format_exc())
            return False
        else:
            return True
