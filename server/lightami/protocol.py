import asyncio
import functools

from asterisk.ami.action import Action, LoginAction, LogoffAction, SimpleAction
from asterisk.ami.client import AMIClient

class TCPClient(asyncio.Protocol):
    def __init__(self, finished):
        self.finished = finished

    def connection_made(self, transport):
        self.transport = transport

    def data_received(self, data):
        self.event_cb(data)


    def connection_lost(self, exc):
        self.transport.close()
        if not self.client_completed.done():
            self.client_completed.set_result(True)
        super().connection_lost(exc)


class asyncAMIClient(AMIClient):

    def __init__(self,*a,**kw):
        super().__init__(*a,**kw)

    async def connect(self):
        loop = asyncio.get_event_loop()
        factory_coroutine = loop.create_connection(lambda: TCPClient(finished=self.finished) , self._address, self._port )
        self._transport, self._protocol = await factory_coroutine

    async def login(self, username, secret, callback=None):
        if self.finished is None or self.finished.is_set():
            await self.connect()
        return await self.send_action(LoginAction(username, secret), callback)






def ClientFactory(*a,**kw):
    return functools.partial(asyncAMIClient,*a,**kw)