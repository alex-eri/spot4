import logging
import asyncio
import aiohttp

logger = logging.getLogger('zte')
debug = logger.debug
import time

class Client:
    def __init__(self,*a,**kw):
        self.base_url = kw.pop('url')
        self.sms_unread_num = 0

        headers = {
            'Referer':self.base_url+"/index.html",
            'X-Requested-With':'XMLHttpRequest'
        }

#        connector = aiohttp.TCPConnector(force_close=True, conn_timeout=10)

#        super().__init__(
#            headers = headers,
#            version=aiohttp.HttpVersion11,
#            connector=connector,
#            *a,**kw)

    async def get_count(self,*a,**kw):

        uri = "{base}/goform/goform_get_cmd_process?"\
            "multi_data=1&isTest=false&sms_received_flag_flag=0&sts_received_flag_flag=0&"\
            "cmd=sms_received_flag,sms_unread_num,sms_read_num&_={date}".format(
                base=self.base_url,
                date=int(time.time()*1000)
            )

        return self.get(uri,*a,**kw)

    async def get_messages(self,*a,**kw):
        uri = "{base}/goform/goform_get_cmd_process?"\
            "isTest=false&cmd=sms_data_total&page=0&data_per_page=100&mem_store=1&tags=1&"\
            "order_by=order+by+id+desc&_={date}".format(
                base=self.base_url,
                date=int(time.time()*1000)
            )
        return self.get(uri,*a,**kw)

    async def set_msg_read(self,msg_id,*a,**kw):
        to_mark = '%3B'.join(msg_id)
        uri = "{base}/goform/goform_set_cmd_process"
        post = dict(isTest="false",
                    goformId="SET_MSG_READ",
                    msg_id=to_mark,
                    notCallback="true"
            )
        return self.post(uri,data=post)

    async def get(self,url):



async def simple():
    client = Client(url='http://192.168.8.1')

    uri = "{base}/goform/goform_get_cmd_process?"\
            "multi_data=1&isTest=false&"\
            "cmd=sms_received_flag,sms_unread_num,sms_read_num&_={date}".format(
                base=client.base_url,
                date=int(time.time()*1000)
            )

   # async with await client.get(uri) as c:
   #     assert c.status == 200
   #     resp = await c.read()
   #     print(resp[:30])
   # with aiohttp.Timeout(10):
        async with await client.get_count() as c:
            assert c.status == 200
            resp = await c.read()
            print(resp[:30])

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(simple())
    finally:
        loop.close()

    
