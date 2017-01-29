import logging
from . import _httpclient
import urllib.parse

class Client(_httpclient.Client):

    def __init__(self,*a,**kw):
        self.logger = logging.getLogger('http')
        self.base_url = kw.pop('url')
        method = kw.pop('method','get').lower()
        assert method in ['get','post'], 'wrong http method'
        self.request = getattr(self,method)
        self.query =  kw.pop('query')
        self.callie = kw.get('number','http')
        super(Client,self).__init__( *a, **kw)

    def _send_sms(self,phone,text):
        data = self.query.format(phone=phone,text=text)

        return self.request(self.base_url,data)

    async def send(self,phone,text,*a,**kw):
        text = urllib.parse.quote(text)
        try:
            res = await self._send_sms(phone,text)
            #assert res.get("result") == "success", 'Modem cant send message'
        except Exception as e:
            self.logger.error(e)
            return False
        else:
            return True
