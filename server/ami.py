import asyncio
import panoramisk
import motor.motor_asyncio
#import phonenumbers

import logging
import datetime
import functools
from multiprocessing import Process

debug = logging.getLogger('AMI').debug
from pymongo import ReturnDocument



async def call_recv_numbers(db: motor.motor_asyncio.AsyncIOMotorDatabase, numbers):
    await db.get_collection('numbers').delete_many({'call_recv':True})
    if numbers:
        return await db.get_collection('numbers').insert_many([{'call_recv': True, 'number': n} for n in numbers])



async def newchannel_cb(manager, message, db:motor.motor_asyncio.AsyncIOMotorDatabase=None, config=None):
    #cid = phonenumbers.parse(message.CallerIDNum, "RU")
    #phone = "+{}{}".format(cid.country_code, cid.national_number)

    phone = "+{}".format(str(message.CallerIDNum).strip('+'))

    now = datetime.datetime.utcnow()
    delta = datetime.timedelta(seconds=config.get('timeout', 120))
    q = dict(phone=phone, seen={'$gt': now - delta})

    device = await db.get_collection('devices').find_one_and_update(
        q,
        {
            '$set': {'checked': True},
            '$currentDate': {'check_date': True}
        },
        sort={'$natural': -1},
        upsert=False,
        return_document=ReturnDocument.AFTER
    )

    logging.debug(repr(device))

    if device:
        await manager.send_action({"Action": "Hangup", "Channel": message.Channel})


async def init(loop, config):
    import setproctitle
    setproctitle.setproctitle('ami')
    from server import lic
    lic(config, "ami")
    import storage


    db = storage.setup(
        config['DB']['SERVER'],
        config['DB']['NAME']
    )

    managers = []

    numbers = []

    for cfg in config.get('CALL',{}).get('pool',[]):
        if not cfg.get('reciever', False):
            continue
        
        if cfg.get('driver', '~').lower() == 'ami':
            managers.append(
                panoramisk.Manager(
                    loop=loop,
                    host=cfg['host'],
                    username=cfg['username'],
                    secret=cfg['secret'])
            )
        if cfg.get('driver', '~').lower() == 'smsru':
            numbers.append('smsru::{api_id}'.format(**cfg))
            continue

        if cfg.get('number', False):
            debug(cfg['number'])
            numbers.append(cfg['number'])
        if cfg.get('numbers', False):
            debug(cfg['numbers'])
            numbers.extend(cfg['numbers'])


    await call_recv_numbers(db, numbers)

    for m in managers:
        res = await m.connect()
        if res:
            logging.info("Connected: %s", repr(m))
            m.register_event('Newchannel', functools.partial(newchannel_cb, db=db, config=config ))

    return managers


def setup_loop(config):
    loop = asyncio.get_event_loop()
    loop.run_until_complete(init(loop, config))
    loop.run_forever()


def setup(config):
    amid = Process(target=setup_loop,args=(config,))
    amid.name = 'ami'
    return [amid]


def main():
    import json
    config = json.load(open('config.json','r'))
    logging.basicConfig(level=logging.DEBUG)
    setup_loop(config)


if __name__ == '__main__':
    main()
