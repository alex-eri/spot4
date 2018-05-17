import re
from asterisk.ami import AMIClient, AutoReconnect


class Client():
    def __init__(self,username, secret, address="127.0.0.1", port=5038, *a, **kw):
        self._client = AMIClient(address=address,port=port)
        AutoReconnect(self._client)
        self._client.login(username=username,secret=secret)
        self._client.add_event_listener(
            on_Newstate=self.event_listener,
            white_list='Newstate',
            ChannelStateDesc=re.compile('^Ring.*')
            )

    def event_listener(self, event):
        print(event)

    def stop(self):
        self._client.logoff()