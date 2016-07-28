from multiprocessing import Process, current_process
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

def get_json(fu):
    c = fu()
    debug(c)
    assert c.status == 200
    resp = c.read()
    debug(resp)
    data = json.loads(resp.decode('ascii'))
    debug(data)
    return data

class Client(object):
    def __init__(self,*a,**kw):
        self.db = kw.pop('db')
        self.config = kw.pop('config')
        self.base_url = kw.pop('url')
        self.sms_unread_num = 0

        self.headers = {
            'Referer':self.base_url+"/index.html",
            'X-Requested-With':'XMLHttpRequest'
        }

    def get(self,uri):
        req = urllib.request.Request(uri, headers=self.headers, method="GET")
        return urllib.request.urlopen(req,timeout=5)

    def post(self,uri,data):
        data = urllib.parse.urlencode(data)
        data = data.encode('ascii')
        req = urllib.request.Request(uri, data=data, headers=self.headers, method='POST')
        return urllib.request.urlopen(req,timeout=5)

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
            #d = [int(i) for i in m.get('date').split(',')]
            #d[0] = d[0]+2000
            #tz = d.pop(-1)
            #date = datetime(*d)

            t = retoken.match(text)

            if t:
                debug(t.group())

                h = hashlib.md5()
                h.update(self.config.get("SALT",b""))
                h.update(phone.encode('ascii'))

                q = dict(
                    phonehash = h.hexdigest(),
                    sms_waited=t.group()
                )
                debug(q)
                r = await self.db.devices.update(q, {
                    '$set':{
                        'checked':True,
                        'phone': phone
                            },
                    '$currentDate':{'check_date':True}
                                              })
                debug(r)
                delete.append(m.get('id',0))
            else:
                read.append(m.get('id',0))

        return read,delete


    async def worker(self):
        try:
            data = get_json(self.get_messages)
            if data.get("messages"):
                read,delete = await self.handle_messages(data.get("messages"))
                if delete: self.delete_sms(delete)
                if read:
                    r = self.set_msg_read(read)
                    debug(r.read())

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



async def main_loop(clients):

    while True:
        tasks = [ asyncio.ensure_future(client.worker()) for client in clients ]
        await asyncio.wait(tasks)
        await asyncio.sleep(3)


def setup_loop(config):
    name = current_process().name
    procutil.set_proc_name(name)

    ztes = config['SMS_POLLING'].get('ZTE',[])

    import storage

    db = storage.setup(
        config['DB']['SERVER'],
        config['DB']['NAME']
    )

    debug(id(db))

    clients = []
    for url in ztes:
        clients.append( Client(url=url,db=db,config=config))

    loop = asyncio.get_event_loop()

    try:
        loop.run_until_complete(main_loop(clients))
    except Exception as e:
        logger.critical(e.__repr__())
        raise e
    finally:
        loop.close()


def setup(config):
    proc = Process(target=setup_loop, args=(config,))
    proc.name = 'zte'
    return [proc]


def main():
    import json
    config = json.load(open('config.json','r'))
    logging.basicConfig(level=logging.DEBUG)
    setup_loop(config['SMS_POLLING'].get('ZTE',[]))


if __name__ == '__main__':
    main()
