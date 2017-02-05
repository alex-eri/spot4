from . import _httpclient

import logging
import time
from utils.codecs import trydecodeHexUcs2,encodeUcs2


class Client(_httpclient.Client):

    def __init__(self,*a,**kw):
        self.logger = logging.getLogger('huawei')
        self.base_url = kw.pop('url')
        self.max = 100
        self.callie = kw.get('number','')
        super(Client,self).__init__( *a, **kw)


    @_httpclient.get_xml
    def _capacity_info(self,*a,**kw):

        """
        Request URL:http://192.168.8.1/api/sms/sms-count

<?xml version="1.0" encoding="utf-8"?>
<response>
	<LocalUnread>0</LocalUnread>
	<LocalInbox>0</LocalInbox>
	<LocalOutbox>0</LocalOutbox>
	<LocalDraft>0</LocalDraft>
	<LocalDeleted>0</LocalDeleted>
	<SimUnread>0</SimUnread>
	<SimInbox>0</SimInbox>
	<SimOutbox>0</SimOutbox>
	<SimDraft>0</SimDraft>
	<LocalMax>500</LocalMax>
	<SimMax>5</SimMax>
	<SimUsed>0</SimUsed>
	<NewMsg>0</NewMsg>
</response>

        """
        uri = "{base}/api/sms/sms-count".format(base=self.base_url)
        return self.get(uri,*a,**kw)

    async def capacity(self):
        cap = await self._capacity_info()
        inbox =  int(cap.find('LocalInbox'))
        sent =  int(cap.find('LocalOutbox'))
        capacity = int(cap.find('LocalMax'))

        ret = {
            'inbox': inbox,
            'sent': sent,
            'total': inbox + sent,
            'capacity': capacity or 100
        }

        self.total_count = inbox + sent
        self.max = capacity or 100
        self.logger.debug(ret)
        return ret

    async def messages(self):
        return []

    def unread(self):
        '''
           returns async
        '''
        return self.messages()
