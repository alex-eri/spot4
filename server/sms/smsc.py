from . import http, _httpclient
import logging
import urllib.parse
import pytz
import time
import datetime

TZ = format(-time.timezone//3600, "+d")

class Client(http.Client):
    def __init__(self, *a, **kw):
        super(Client, self).__init__(*a, **kw)
        self.reciever = kw.pop('reciever', False)
        self.login = kw.pop('login', False)
        self.password = kw.pop('password', False)
        self.query = "login={login}&psw={password}&phones={{phone}}&mes={{text}}&charset={encoding}".format(
            login=self.login,
            password=self.password,
            encoding=self.encoding
            )
        self.url = "http://smsc.ru/sys/send.php"

        self.url2 = "http://smsc.ru/sys/get.php"
        self.query2 = "get_answers=1&login={login}&psw={password}&fmt=3".format(
            login=self.login,
            password=self.password
        )
        self.last_id = None

    def unread(self):
        '''returns async'''
        return self.messages()

    @_httpclient.get_json
    async def _get_messages(self):
        if self.last_id:
            last = "&after_id={}".format(self.last_id)
        else:
            last = "&hour=1"
        return self.request(self.url2, self.query2+last)

    async def messages(self):
        msgs = await self._get_messages()

        for m in msgs:
            self.last_id = max(self.last_id, m['id'])
            m['text'] = m.get('message')
            m['to'] = m.get('to_phone')
            m['date'] = pytz.datetime.datetime.strptime(m['sent'], "%d.%m.%Y %H:%M:%S")
            m['date'] = pytz.datetime.datetime.astimezone(m['date'])

        return msgs
