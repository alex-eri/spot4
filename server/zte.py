from multiprocessing import Process, current_process, Semaphore
import logging
import asyncio
import aiohttp
import json

from utils import procutil
import sys, traceback
import urllib.request
import urllib.parse
import time
import re
from datetime import datetime
from utils.codecs import decodeHexUcs2
import hashlib
logger = logging.getLogger('zte')
debug = logger.debug

retoken = re.compile('([0-9]{6})')

from itertools import cycle

async def get_json(fu,*a,**kw):
    c = await fu(*a,**kw)
    debug(c)
    assert c.status == 200
    resp = c.read()
    debug(resp)
    data = json.loads(resp.decode('ascii'))
    debug(data)
    return data

class Client(object):
    def __init__(self,db,url,callie,sender,smsq,config,*a,**kw):
        self.db = db
        self.base_url = url
        self.callie =  callie
        self.sender =  sender
        self.smsq = smsq
        self.numbers = config['numbers']

        self.sema = Semaphore()

        self.headers = {
            'Referer':self.base_url+"/index.html",
            'X-Requested-With':'XMLHttpRequest'
        }

    def get(self,uri):
        req = urllib.request.Request(uri, headers=self.headers, method="GET")
        return self.urlopen(req)

    def post(self,uri,data):
        data = urllib.parse.urlencode(data)
        data = data.encode('ascii')
        req = urllib.request.Request(uri, data=data, headers=self.headers, method='POST')
        return self.urlopen(req)

    async def urlopen(self,req):
        self.sema.acquire()
        try: ret = urllib.request.urlopen(req,timeout=5)
        except Exception as e: error=e
        else: return ret
        finally: self.sema.release()
        raise error

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

    async def handle_messages(self,messages):
        read = []
        delete = []
        debug(messages)
        for m in messages:
            phone = decodeHexUcs2(m.get('number'))
            logger.info(phone)
            text = decodeHexUcs2(m.get('content'))
            logger.info(text)
            t = retoken.match(text)
            if t:
                debug(t.group())

                q = dict(
                    phone=phone, sms_waited=t.group()
                )
                debug(q)
                r = await self.db.devices.update(q, {
                      '$set':{ 'checked': True },
                      '$currentDate':{'check_date':True}
                    })
                debug(r)
                delete.append(m.get('id',0))
            else:
                read.append(m.get('id',0))

        return read,delete

    async def worker(self):
        debug("worker")

        try:
            data = await get_json(self.get_messages)
            if data.get("messages"):
                read, delete = await self.handle_messages(data["messages"])
                if delete: await self.delete_sms(delete)
                if read: await self.set_msg_read(read)

        except json.decoder.JSONDecodeError as e:
            logger.error(self.base_url)
            logger.error(e.__repr__())

        except urllib.error.URLError as e:
            logger.error(self.base_url)
            logger.error(e.__repr__())

        except AssertionError as e:
            logger.warning(e.__repr__())

        except Exception as e:
            logger.error(self.base_url)
            logger.error(e.__repr__())
            raise e

        debug('worker_done')




    def send(self,phone,text):
        pass

    async def send_from_queue(self):
        debug('sender')
        sms = self.smsq.get()
        self.send(*sms)
        self.smsq.task_done()
        pass


async def recieve_loop(clients):
    name = current_process().name
    procutil.set_proc_name(name)

    while clients:
        try:
            tasks = [ asyncio.ensure_future(client.worker()) for client in clients ]
            await asyncio.wait(tasks)

        except Exception as e:
            debug(e)
        debug('sleep')
        await asyncio.sleep(3)

async def send_loop(clients):
    name = current_process().name
    procutil.set_proc_name(name)

    clients = list(filter(lambda x: x.sender, clients))
    while clients:
        tasks = [ asyncio.ensure_future(
            client.send_from_queue()
            ) for client in clients ]
        await asyncio.wait(tasks)
        await asyncio.sleep(3)


def setup_clients(config, smsq=None):

    ztes = config['SMS'].get('ZTE',[])

    import storage

    db = storage.setup(
        config['DB']['SERVER'],
        config['DB']['NAME']
    )

    debug(id(db))

    clients = []
    for modem in ztes:
        clients.append( Client(
            url=modem['url'],
            db=db,
            callie=modem['number'],
            sender=modem['sender'],
            smsq=smsq,
            config=config
            ))

    return clients

def setup_loop(clients, forever):
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(forever(clients))
    except Exception as e:
        logger.critical(e.__repr__())
        raise e
    finally:
        loop.close()


def setup(config,smsq):

    clients = setup_clients(config,smsq)

    reciever = Process(target=setup_loop, args=(clients,recieve_loop))
    reciever.name = 'zte_reciever'

    sender = Process(target=setup_loop, args=(clients,send_loop))
    sender.name = 'zte_sender'

    return [reciever, sender]


def main():
    import json
    config = json.load(open('config.json','r'))
    logging.basicConfig(level=logging.DEBUG)
    setup_loop(config)


if __name__ == '__main__':
    main()
