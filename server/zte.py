from multiprocessing import Process
import logging
import db
import asyncio
import aiohttp
import json
logger = logging.getLogger('zte')
debug = logger.debug

import sys, traceback
import urllib.request
import urllib.parse
import time
import re
from datetime import datetime
from utils.codecs import decodeHexUcs2

class Client(object):
    def __init__(self,*a,**kw):
        self.base_url = kw.pop('url')
        self.sms_unread_num = 0

        self.headers = {
            'Referer':self.base_url+"/index.html",
            'X-Requested-With':'XMLHttpRequest'
        }

    def get(self,uri):
        req = urllib.request.Request(uri, headers=self.headers, method="GET")
        return urllib.request.urlopen(req)

    def post(self,uri,data):
        data = urllib.parse.urlencode(data)
        data = data.encode('ascii')
        req = urllib.request.Request(uri, data=data, headers=self.headers, method='POST')
        return urllib.request.urlopen(req)

    def get_count(self,*a,**kw):

        uri = "{base}/goform/goform_get_cmd_process?"\
            "multi_data=1&isTest=false&sms_received_flag_flag=0&sts_received_flag_flag=0&"\
            "cmd=sms_received_flag,sms_unread_num,sms_read_num&_={date}".format(
                base=self.base_url,
                date=int(time.time()*1000)
            )

        return self.get(uri,*a,**kw)

    def get_messages(self,*a,**kw):
        uri = "{base}/goform/goform_get_cmd_process?"\
            "isTest=false&cmd=sms_data_total&page=0&data_per_page=100&mem_store=1&tags=1&"\
            "order_by=order+by+id+desc&_={date}".format(
                base=self.base_url,
                date=int(time.time()*1000)
            )
        return self.get(uri,*a,**kw)

    def set_msg_read(self,msg_id,*a,**kw):
        to_mark = ';'.join(msg_id)+';'
        uri = "{base}/goform/goform_set_cmd_process".format(
                base=self.base_url
            )
        postdata = dict(isTest="false",
                    goformId="SET_MSG_READ",
                    msg_id=to_mark,
                    notCallback="true",
                    tag=0
            )
        debug(uri)
        debug(postdata)
        return self.post(uri,data=postdata)


    def delete_sms(self,msg_id,*a,**kw):
        to_mark = ';'.join(msg_id)
        uri = "{base}/goform/goform_set_cmd_process".format(
                base=self.base_url
            )
        postdata = dict(isTest="false",
                    goformId="DELETE_SMS",
                    msg_id=to_mark,
                    notCallback="true"
            )
        return self.post(uri,data=postdata)



def get_json(fu):
    with fu() as c:
        #c = await fu()
        debug(c)
        assert c.status == 200
        resp = c.read()
        debug(resp)
        data = json.loads(resp.decode('ascii'))
        debug(data)
        return data

retoken = re.compile('([0-9]{6})')


async def handle_messages(messages):
    read = []
    delete = []
    debug(messages)
    for m in messages:
        phone = decodeHexUcs2(m.get('number'))
        debug(phone)
        text = decodeHexUcs2(m.get('content'))
        debug(text)
        d = [int(i) for i in m.get('date').split(',')]
        d[0] = d[0]+2000
        tz = d.pop(-1)
        date = datetime(*d)
        t = retoken.match(text)

        if t:
            debug(t.group())
            q = dict(
                login=phone,
                sms_waited=t.group()
            )
            r = await db.db.devices.update(q, {
                '$set':{'checked':True},
                '$currentDate':{'check_date':True}
                                          })
            debug(r)
            delete.append(m.get('id',0))
        else:
            read.append(m.get('id',0))
            logger.info("Непонятная SMS от {}: {}".format(phone,text))
        debug(phone)
        debug(date)
        debug(text)

    return read,delete


async def worker(client):
    try:
        data = get_json(client.get_messages)
        if data.get("messages"):
            read,delete = await handle_messages(data.get("messages"))
            if delete: client.delete_sms(delete)
            if read:
                r = client.set_msg_read(read)
                debug(r.read())



    except aiohttp.errors.ClientError as e:
        logger.error(e.__repr__())
        traceback.print_exc(file=sys.stdout)

    except AssertionError as e:
        logger.warning(e.__repr__())

    except Exception as e:
        logger.error(e.__repr__())
        raise e




async def main_loop(clients):
    while True:
        loop = asyncio.get_event_loop()
        tasks = [ asyncio.ensure_future(worker(client)) for client in clients ]
        await asyncio.wait(tasks)
        await asyncio.sleep(3)


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
