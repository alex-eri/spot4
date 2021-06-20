from multiprocessing import Process, current_process, Semaphore
import logging
import asyncio
import aiohttp
import json

from utils import procutil
import sys, traceback
import time
import re
from datetime import datetime

from utils.password import SMSLEN
import hashlib
logger = logging.getLogger('sms')
debug = logger.debug

retoken = re.compile('([0-9]{%d})' % SMSLEN)

from itertools import cycle
from collections import defaultdict

TZ = format(-time.timezone//3600, "+d")

INTERVAL = 5


async def handle(m, db, client):
    t = retoken.search(m['text'])
    q = None

    if t:
        q = dict(phone=m['phone'], sms_waited=t.group())

    elif client.anytext:
        now = datetime.utcnow()
        delta = timedelta(seconds=client.anytext)
        q = dict(phone=m['phone'], seen={'$gt': now - delta})
        m['text'] += "// принимаем любой текст //"

    if q:
        device = await db.devices.find_and_modify(q, {
              '$set': {'checked': True},
              '$currentDate': {'check_date': True}
            }, upsert=False)
        if device:
            m['callee'] = device.get('callee', 'default')
    logger.info(m)


async def worker(client, db):
    try:
        msgs = []
        #async
        for m in await client.unread():
            await handle(m, db, client)
            msgs.append(m)

        if msgs: db.sms_received.insert(msgs)

        cap = await client.capacity()
        if cap and cap['total'] > (cap['capacity'] * 0.8) :
            await client.clean()
    except Exception as e:
        logger.error(e)
        logger.error(traceback.format_exc())


async def get_numbers(db, config):
    pool =  config['SMS'].get('pool',[])
    numbers = []
    for modem in pool:
        debug(modem)
        if not modem.get('reciever', False):
            debug('not recv')
            continue

        if modem.get('number',False):
            debug(modem['number'])
            numbers.append(modem['number'])
        if modem.get('numbers',False):
            debug(modem['numbers'])
            numbers.extend(modem['numbers'])

    await sms_recv_numbers(db, numbers)


async def recieve_loop(clients,db):
    debug('starting reciever')
    name = current_process().name
    procutil.set_proc_name(name)
    clients = list(filter(lambda x: x.reciever, clients))

    while clients:
        try:
            tasks = [ asyncio.ensure_future(worker(client,db)) for client in clients ]
            await asyncio.wait(tasks)

        except Exception as e:
            logger.error(e)
        await asyncio.sleep(INTERVAL)


def get_gate(sms, count, xclients, roundrobin):
    callee = sms.get('callee', 'default')
    phone = sms.get('phone')

    if callee in xclients.keys():
        client = next(xclients[callee])
    elif roundrobin:
        client = next(roundrobin)
    else:
        logger.warning("No SMS gate for %s", callee)
        return

    if client.filter.match(phone):
        return client
    elif count <= 0:
        logger.warning("No SMS filter for %s", phone)
        return
    else:
        return get_gate(sms, count-1, xclients, roundrobin)


async def send_loop(clients, db):
    debug('starting sender')
    clients = list(filter(lambda x: x.sender, clients))
    if not clients: return

    xclients = defaultdict(list)
    cclients = list()

    for c in clients:
        if c.callee:
            for p in c.callee:
                xclients[p].append(c)
        else:
            cclients.append(c)

    for p in xclients.keys():
        xclients[p] = cycle(xclients[p])

    if cclients:
        roundrobin = cycle(cclients)
    else:
        roundrobin = None

    from pymongo.cursor import CursorType

    last = await db.sms_sent.find().sort([('_id', -1)]).to_list(1)
    if last:
        last = last[0].get('_id')
    q = None

    while True:
        if last:
            q = {"_id": {'$gt': last}}
        cursor = db.sms_sent.find(q, cursor_type=CursorType.TAILABLE_AWAIT)
        while cursor.alive:
            async for sms in cursor:
                redudant = sms.get('redudant', 1)
                for _ in range(redudant):
                    client = get_gate(sms, len(clients), xclients, roundrobin)
                    if client:
                        try:
                            res = await client.send(**sms)
                            logger.info(res)
                        except Exception as e:
                            logger.error(e)
                    else:
                        logger.info('SMS not sended')

                await asyncio.sleep(INTERVAL)
                last = sms.get('_id', last)


async def sms_recv_numbers(db,numbers):
    debug(numbers)
    await db.numbers.remove({'sms_recv':True})
    if numbers:
        r= await db.numbers.insert_many([{'sms_recv': True, 'number': n} for n in numbers])
        debug(r)


def setup_clients(db, config):
    #from sms import zte, at
    #ztes = config['SMS'].get('ZTE',[])

    import sms
    import importlib

    clients = []
    pool =  config['SMS'].get('pool',[])

    for modem in pool:
        driver = modem.get('driver', None)
        if driver:
            try:
                module = importlib.import_module('sms.'+ driver)
            except:
                logger.error('driver load failed')
                logger.error(traceback.format_exc())
                continue
        else:
            logger.error('driver not specified')
            continue

        clients.append( module.Client(**modem ))

    return clients

def setup_loop(config):
    executor = None
    name = current_process().name
    procutil.set_proc_name(name)

    loop = asyncio.get_event_loop()

    from server import lic
    lic(config,"zte")

    import storage

    db = storage.setup(
        config['DB']['SERVER'],
        config['DB']['NAME']
    )

    debug(id(db))


    t = asyncio.Task(storage.create_capped(db,"sms_sent",2<<20))
    loop.run_until_complete(t)
    t = asyncio.Task(storage.create_capped(db,"sms_received",2<<20))
    loop.run_until_complete(t)

    clients = setup_clients(db, config)

    try:
        loop.create_task(get_numbers(db, config))
        loop.create_task(recieve_loop(clients,db))
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
    setup_loop(config)


if __name__ == '__main__':
    main()
