from multiprocessing import Process
import logging
import db
import asyncio
import aiohttp
import json
logger = logging.getLogger('zte')
debug = logger.debug
logger.error
import sys, traceback

import time
import re
from datetime import datetime
from utils.codecs import decodeHexUcs2

class Client(aiohttp.ClientSession):
    def __init__(self,*a,**kw):
        self.base_url = kw.pop('url')
        self.sms_unread_num = 0

        headers = {
            'Referer':self.base_url+"/index.html",
            'X-Requested-With':'XMLHttpRequest'
        }
        super(Client,self).__init__(
            headers = headers,
            *a,**kw)

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



async def get_json(fu):
    async with await fu() as c:
        #c = await fu()
        debug(c)
        assert c.status == 200
        resp = await c.read()
        debug(resp)
        data = json.loads(resp.decode('ascii'))
#        debug(data)
        return data

retoken = re.compile('([0-9]{6})')


def handle_cb(*a,**kw):
    debug(*a)
    debug(**kw)


async def handle_messages(messages):
    read = []
    delete = []
    for m in messages:
        phone = m.get('number')
        text = decodeHexUcs2(m.get('content'))
        d = [int(i) for i in m.get('date').split(',')]
        d[0] = d[0]+2000
        tz = d.pop(-1)
        date = datetime(*d)
        t = retoken.match(text)
        if t:
            q = dict(
                login=phone,
                sms_waited=t.group()
            )
            db.db.devices.update(q, {'checked':True, 'check_date':date}, callback = handle_cb)
            delete.append(m.get('id',0))
        else:
            read.append(m.get('id',0))
            logger.info("Непонятная SMS от {}: {}".format(phone,text))
        debug(phone)
        debug(date)
        debug(text)

    return read,delete


async def worker(client):
    read = []
    try:
        data = await get_json(client.get_count)
        num = int(data.get('sms_unread_num'))
        if num:
            data = await get_json(client.get_messages)
            assert data.get("messages")
            read,delete = await handle_messages(data.get("messages"))
        debug('readed {}'.format(read))
        pass

    except aiohttp.errors.ClientError as e:
        logger.error(e.__repr__())
        traceback.print_exc(file=sys.stdout)

    except AssertionError as e:
        logger.warning(e.__repr__())

    except Exception as e:
        logger.error(e.__repr__())




async def main_loop(clients):
    while True:
        loop = asyncio.get_event_loop()
        tasks = [ asyncio.ensure_future(worker(client)) for client in clients ]
        await asyncio.wait(tasks)
        await asyncio.sleep(5)


def setup_loop(ztes):
    clients = []
    for url in ztes:
        clients.append( Client(url=url))

    loop = asyncio.get_event_loop()

    try:
        loop.run_until_complete(main_loop(clients))
    except Exception as e:
        logger.critical(e.__repr__())
        raise e
    finally:
        loop.close()


def setup(ztes):
    proc = Process(target=setup_loop, args=(ztes,))
    return [proc]


def main():
    import json
    config = json.load(open('config.json','r'))
    logging.basicConfig(level=logging.DEBUG)
    setup_loop(config['SMS_POLLING'].get('ZTE',[]))


if __name__ == '__main__':

    main()
