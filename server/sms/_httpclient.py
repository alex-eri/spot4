import asyncio
import json
import urllib.request
import urllib.parse
from . import _sms

def get_json(fu):
    async def inner(*a,**kw):
        c = await fu(*a,**kw)
        assert c.status == 200, 'status %d' % c.status
        resp = c.read()
        data = json.loads(resp.decode('utf-8'))
        return data
    return inner

from lxml import objectify


def get_xml(fu):
    async def inner(*a,**kw):
        c = await fu(*a,**kw)
        assert c.status == 200, 'status %d' % c.status
        resp = c.read()
        data = objectify.fromstring(resp)
        return data
    return inner



class Client(_sms.Client):
    def __init__(self,*a,**kw):

        headers = kw.pop('headers',{})
        self.get_headers = kw.pop('get_headers',headers)
        self.post_headers = kw.pop('post_headers',headers)
        self.encoding = kw.pop('encoding','utf-8')
        self.sema = asyncio.Lock()
        super(Client,self).__init__(*a,**kw)

    def get(self,uri,data=None):
        if isinstance(data, (dict,list,tuple)):
            data = urllib.parse.urlencode(data)
        if isinstance(data, str):
            uri = '?'.join((uri,data))
        req = urllib.request.Request(uri, headers=self.get_headers, method="GET")
        return self.urlopen(req)

    def post(self,uri,data):
        if isinstance(data, (dict,list,tuple)):
            data = urllib.parse.urlencode(data,)
        if isinstance(data, str):
            data = data.encode(self.encoding)
        req = urllib.request.Request(uri, data=data,
                                     headers=self.post_headers, method='POST')
        return self.urlopen(req)

    async def urlopen(self,req):
        await self.sema.acquire()
        try: ret = urllib.request.urlopen(req,timeout=5)
        except Exception as e: error=e
        else: return ret
        finally: self.sema.release()
        raise error
