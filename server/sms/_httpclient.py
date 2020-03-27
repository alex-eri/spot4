import asyncio
import json
import urllib.request
import urllib.parse
from . import _sms
import ssl

import http.cookiejar
import http.cookies

def get_json(fu):
    async def inner(*a,**kw):
        c = await fu(*a,**kw)
        assert c.status == 200, 'status %d' % c.status
        resp = c.read()
        data = json.loads(resp.decode('utf-8'))
        return data
    return inner


def get_xml(fu):
    import xml.etree.ElementTree as ET
    async def inner(*a,**kw):
        c = await fu(*a,**kw)
        assert c.status == 200, 'status %d' % c.status
        resp = c.read()
        data = ET.fromstring(resp)
        return data
    return inner


class Client(_sms.Client):
    def __init__(self, *a, **kw):

        headers = kw.pop('headers', {})
        self.get_headers = kw.pop('get_headers', headers)
        self.post_headers = kw.pop('post_headers', headers)
        self.encoding = kw.pop('encoding', 'utf-8')
        self.sema = asyncio.Lock()

        self.cookie = http.cookiejar.MozillaCookieJar()
        cookiehandler = urllib.request.HTTPCookieProcessor(self.cookie)
        sslhandler = urllib.request.HTTPSHandler(context=ssl._create_unverified_context())
        self.opener = urllib.request.build_opener(sslhandler, cookiehandler)

        super(Client, self).__init__(*a, **kw)

    def set_cookie(self, url, **kw):

        url = url.split('//')[1]
        domain = url.split('/')[0]
        port = 80
        if ":" in domain:
            domain, port = domain.split(':')

        for k, v in kw.items():
            # Cookie(version, name, value, port, port_specified, domain,
            # domain_specified, domain_initial_dot, path, path_specified,
            # secure, discard, comment, comment_url, rest)
            c = http.cookiejar.Cookie(1, k, v, '*', None, '*',
                   None, None, '/', None, False, False, None, None, None, None)
            self.cookie.set_cookie(c)

    def get(self, uri, data=None):
        if isinstance(data, (dict,list,tuple)):
            data = urllib.parse.urlencode(data)
        if isinstance(data, str):
            uri = '?'.join((uri, data))
        self.logger.debug(uri)
        req = urllib.request.Request(uri, headers=self.get_headers, method="GET")
        return self.urlopen(req)

    def post(self, uri, data):
        if isinstance(data, (dict, list, tuple)):
            data = urllib.parse.urlencode(data,)
        if isinstance(data, str):
            data = data.encode(self.encoding)

        req = urllib.request.Request(uri, data=data,
                                     headers=self.post_headers, method='POST')

        return self.urlopen(req)

    async def urlopen(self, req):
        await self.sema.acquire()
        try:
            ret = self.opener.open(req, timeout=5)
            self.logger.debug('http request')
            self.logger.debug(req.headers)
            self.logger.debug(req.data)
            self.logger.debug('http response')
            self.logger.debug(ret.headers)

        except Exception as e: error=e
        else:
            return ret
        finally: self.sema.release()
        raise error

