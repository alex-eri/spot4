import asyncio
import panoramisk
import phonenumbers

import logging
import datetime
import functools
from multiprocessing import Process

debug = logging.debug


async def call_recv_numbers(db,numbers):
    await db.numbers.remove({'call_recv':True})
    if numbers:
        return await db.numbers.insert_many([{'call_recv': True, 'number': n} for n in numbers])



async def newchannel_cb(manager, message, db=None, config=None):
    cid = phonenumbers.parse(message.CallerIDNum, "RU")
    phone = "+{}{}".format(cid.country_code, cid.national_number)

    now = datetime.datetime.utcnow()
    delta = datetime.timedelta(seconds=config.get('timeout', 120))
    q = dict(phone=phone, seen={'$gt': now - delta})

    device = await db.devices.find_and_modify(q, {
              '$set': {'checked': True},
              '$currentDate': {'check_date': True}
            }, upsert=False)

    if device:
        await manager.send_action({"Action": "Hangup", "Channel": message.Channel})

    debug(repr(device))


async def init(loop, config):

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
        if cfg.get('driver', '~').lower() == 'ami':
            managers.append(
                panoramisk.Manager(
                    loop=loop,
                    host=cfg['host'],
                    username=cfg['username'],
                    secret=cfg['secret'])
            )

        if cfg.get('number', False):
            debug(cfg['number'])
            numbers.append(cfg['number'])
        if cfg.get('numbers', False):
            debug(cfg['numbers'])
            numbers.extend(cfg['numbers'])


    await call_recv_numbers(numbers)

    for m in managers:
        res = await m.connect()
        if res:
            logging.info("Connected: ", repr(m))
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
