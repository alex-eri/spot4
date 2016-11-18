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
from utils.codecs import trydecodeHexUcs2,encodeUcs2
from utils.password import SMSLEN
import hashlib
logger = logging.getLogger('zte')
debug = logger.debug

retoken = re.compile('([0-9]{%d})' % SMSLEN)

from itertools import cycle

TZ = format(-time.timezone//3600,"+d")

INTERVAL = 4

async def get_json(fu,*a,**kw):
    c = await fu(*a,**kw)
    assert c.status == 200
    resp = c.read()
    data = json.loads(resp.decode('ascii'))
    debug(data)
    return data

class Client(object):

    def __init__(self,db,url,callie,sender,config,*a,**kw):
        self.db = db
        self.base_url = url
        self.callie =  callie
        self.sender =  sender
        config['numbers'].append(callie)
        self.numbers = config['numbers']
        self.headers = {
            'Referer':self.base_url+"/index.html",
            'X-Requested-With':'XMLHttpRequest'
        }

        self.logger = logging.getLogger('zte')
        self.sema = Semaphore()
        debug(self.numbers)
        self.max=100

    def set_max(self):
        loop = asyncio.get_event_loop()
        c = get_json(self.sms_capacity_info)
        f = loop.create_task(c)
        try:
            capacity = loop.run_until_complete(f)
        except Exception as e:
            logger.warning('sms_capacity_info: %s',e)
        else:
            self.max= capacity.get('sms_nv_total')

    #def __del__(self):
    #    self.numbers.remove(self.callie)

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

    def sms_capacity_info(self,*a,**kw):

        """
        Request URL:http://192.168.0.1/goform/goform_get_cmd_process?isTest=false&cmd=sms_capacity_info&_=1477750277341
        {"sms_nv_total":"100","sms_sim_total":"5","sms_nv_rev_total":"0",
        "sms_nv_send_total":"1","sms_nv_draftbox_total":"0",
        "sms_sim_rev_total":"0","sms_sim_send_total":"0","sms_sim_draftbox_total":"0"}
        """
        uri = "{base}/goform/goform_get_cmd_process?"\
            "isTest=false&cmd=sms_capacity_info&_={date}".format(
                base=self.base_url,
                date=int(time.time()*1000))
        return self.get(uri,*a,**kw)

    def get_count(self,*a,**kw):
        uri = "{base}/goform/goform_get_cmd_process?"\
            "multi_data=1&isTest=false&sms_received_flag_flag=0&sts_received_flag_flag=0&"\
            "cmd=sms_received_flag,sms_unread_num,sms_read_num&_={date}".format(
                base=self.base_url,
                date=int(time.time()*1000)
            )
        return self.get(uri,*a,**kw)

    def get_messages(self,tags=1,*a,**kw):
        uri = "{base}/goform/goform_get_cmd_process?"\
            "isTest=false&cmd=sms_data_total&page=0&data_per_page={max}&mem_store=1&tags={tags}&"\
            "order_by=order+by+id+desc&_={date}".format(
                max= self.max,
                base=self.base_url,
                date=int(time.time()*1000),
                tags=tags
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
        for m in messages:
            phone = trydecodeHexUcs2(m.get('number'))
            text = trydecodeHexUcs2(m.get('content'))
            logger.info('SMS: %s >>> %s', phone,text)
            t = retoken.match(text)
            if t:
                q = dict(
                    phone=phone, sms_waited=t.group()
                )
                r = await self.db.devices.update(q, {
                      '$set':{ 'checked': True },
                      '$currentDate':{'check_date':True}
                    })
                delete.append(m.get('id',0))
            else:
                read.append(m.get('id',0))

        return read,delete

    async def clean(self):
        data = await get_json(self.get_messages,tags=10)
        delete = [ m['id'] for m in data.get("messages",[]) ]
        if delete: await self.delete_sms(delete)

    async def worker(self):
        try:
            data = await get_json(self.get_messages)
            if data.get("messages"):
                read, delete = await self.handle_messages(data["messages"])
                if delete: await self.delete_sms(delete)
                if read: await self.set_msg_read(read)

            data = await get_json(self.sms_capacity_info)
            if data.get('sms_nv_total'):
                self.max = int(data.get('sms_nv_total',100))
                total = \
                    int(data.get("sms_nv_rev_total",0)) + \
                    int(data.get("sms_nv_send_total",0)) + \
                    int(data.get("sms_nv_draftbox_total",0))
                top = self.max * 0.8
                if total > top:
                     await self.clean()

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
        finally:
            pass
            #debug('worker_done')




    def send_sms(self,phone,text,**kw):
        uri = "{base}/goform/goform_set_cmd_process".format(
                base=self.base_url
            )

        postdata = dict(isTest="false",
                goformId="SEND_SMS",
                Number=phone,
                notCallback="true",
                sms_time=time.strftime("%y;%m;%d;%H;%M;%S;")+TZ,
                MessageBody=encodeUcs2(text),
                encode_type="UNICODE",
                ID=-1
            )
        debug(uri)
        debug(postdata)
        return self.post(uri,data=postdata)


async def recieve_loop(clients):
    name = current_process().name
    procutil.set_proc_name(name)

    while clients:

        try:
            tasks = [ asyncio.ensure_future(client.worker()) for client in clients ]
            await asyncio.wait(tasks)

        except Exception as e:
            debug(e)
        await asyncio.sleep(INTERVAL)

async def send_loop(clients,db):
    clients = list(filter(lambda x: x.sender, clients))
    if not clients: return

    from pymongo.cursor import CursorType
    while True:
        skip = await db.sms_sent.count()
        cursor = db.sms_sent.find(cursor_type=CursorType.TAILABLE_AWAIT,skip=skip)
        while cursor.alive:
            for client in clients:
                if (await cursor.fetch_next):
                        sms = cursor.next_object()
                        try:
                            await client.send_sms(**sms)
                        except Exception as e:
                            self.logger.error(e)
                debug('next')
            await asyncio.sleep(INTERVAL)


def setup_clients(db, config):

    ztes = config['SMS'].get('ZTE',[])

    clients = []
    for modem in ztes:
        clients.append( Client(
            url=modem['url'],
            db=db,
            callie=modem['number'],
            sender=modem['sender'],
            config=config
            ))

    return clients

def setup_loop(config):
    executor = None
    name = current_process().name
    procutil.set_proc_name(name)

    loop = asyncio.get_event_loop()
    import storage

    db = storage.setup(
        config['DB']['SERVER'],
        config['DB']['NAME']
    )

    debug(id(db))


    t = asyncio.Task(storage.create_capped(db,"sms_sent",2<<10))
    loop.run_until_complete(t)
    t = asyncio.Task(storage.create_capped(db,"sms_received",2<<10))
    loop.run_until_complete(t)

    clients = setup_clients(db, config)



    try:
        loop.create_task(recieve_loop(clients))
        loop.create_task(send_loop(clients,db))

        loop.run_forever()
    except Exception as e:
        logger.critical(e.__repr__())
        raise e
    finally:
        loop.close()


def setup(config):
    smsd = Process(target=setup_loop,args=(config,))
    smsd.name = 'smser'
    return [smsd]


def main():
    import json
    import multiprocessing as mp
    config = json.load(open('config.json','r'))
    logging.basicConfig(level=logging.DEBUG)
    #config['smsq'] = mp.Queue()
    setup_loop(config)


if __name__ == '__main__':
    main()
