from . import _httpclient

import logging
import time
from utils.codecs import trydecodeHexUcs2,encodeUcs2

from lxml.etree import Element, SubElement, Comment, tostring

from datetime import datetime

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
        inbox =  int(cap.find('LocalInbox').text)
        sent =  int(cap.find('LocalOutbox').text)
        capacity = int(cap.find('LocalMax').text)

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

    """
    http://192.168.8.1/api/sms/sms-list

<?xml version="1.0" encoding="UTF-8"?><request><PageIndex>1</PageIndex><ReadCount>50</ReadCount><BoxType>1</BoxType><SortType>0</SortType><Ascending>0</Ascending><UnreadPreferred>0</UnreadPreferred></request>

    <?xml version="1.0" encoding="utf-8"?>
<response>
	<Count>6</Count>
	<Messages>
		<Message>
			<Smstat>0</Smstat>
			<Index>40005</Index>
			<Phone>+79624118643</Phone>
			<Content>1342</Content>
			<Date>2018-11-08 12:09:59</Date>
			<Sca></Sca>
			<SaveType>4</SaveType>
			<Priority>0</Priority>
			<SmsType>1</SmsType>
		</Message>
		<Message>
			<Smstat>1</Smstat> <-- read
			<Index>40004</Index>
			<Phone>+79624118643</Phone>
			<Content>Анд </Content>
			<Date>2018-11-08 08:51:41</Date>
			<Sca></Sca>
			<SaveType>4</SaveType>
			<Priority>0</Priority>
			<SmsType>1</SmsType>
		</Message>
		<Message>
			<Smstat>0</Smstat>
			<Index>40003</Index>
			<Phone>+79624118643</Phone>
			<Content>So </Content>
			<Date>2018-11-07 09:29:45</Date>
			<Sca></Sca>
			<SaveType>4</SaveType>
			<Priority>0</Priority>
			<SmsType>1</SmsType>
		</Message>
		<Message>
			<Smstat>0</Smstat>
			<Index>40002</Index>
			<Phone>+79624118643</Phone>
			<Content>Do </Content>
			<Date>2018-11-07 09:14:15</Date>
			<Sca></Sca>
			<SaveType>4</SaveType>
			<Priority>0</Priority>
			<SmsType>1</SmsType>
		</Message>
		<Message>
			<Smstat>0</Smstat>
			<Index>40001</Index>
			<Phone>+79624118643</Phone>
			<Content>Dj </Content>
			<Date>2018-11-07 09:11:06</Date>
			<Sca></Sca>
			<SaveType>4</SaveType>
			<Priority>0</Priority>
			<SmsType>1</SmsType>
		</Message>
		<Message>
			<Smstat>0</Smstat>
			<Index>40000</Index>
			<Phone>+79624118643</Phone>
			<Content>Dj </Content>
			<Date>2018-11-07 08:58:23</Date>
			<Sca></Sca>
			<SaveType>4</SaveType>
			<Priority>0</Priority>
			<SmsType>1</SmsType>
		</Message>
	</Messages>
</response>

    """


    async def messages(self):
        return []

    async def clean(self):
        pass


    def unread(self):
        '''
           returns async
        '''
        return self.messages()

    async def send(self,phone,text,*a,**kw):
        try:
            res = await self._send_sms(phone,text)
            assert res.get("result") == "success", 'Modem cant send message'
        except Exception as e:
            self.logger.error(e)
            return False
        else:
            return True

    @_httpclient.get_xml
    def _send_sms(self,phone,text,**kw):
        uri = "{base}/goform/api/sms/send-sms".format(
                base=self.base_url
            )

        """
        <?xml version="1.0" encoding="UTF-8"?>
        <request><Index>-1</Index><Phones><Phone>+7123456789</Phone></Phones><Sca></Sca>
        <Content>Прив!</Content><Length>5</Length><Reserved>0</Reserved><Date>2016-06-12 22:56:44</Date>
        </request>
        """

        top=Element('request')
        child = SubElement(top, 'Index')
        child.text = '-1'
        phones = SubElement(top, 'Phones')
        child = SubElement(phones, 'Phone')
        child.text = phone
        child = SubElement(top, 'Sca')
        child = SubElement(top, 'Content')
        child.text = text
        child = SubElement(top, 'Length')
        child.text = str(len(text))
        child = SubElement(top, 'Reserved')
        child.text = str(0)
        child = SubElement(top, 'Date')
        child.text = "{:%Y-%m-%d %H:%M:%S}".format(datetime.now())

        postdata = tostring(top,encoding="UTF-8",method="xml",xml_declaration=True)

        self.logger.debug(uri)
        self.logger.debug(postdata)

        return self.post(uri,data=postdata)
