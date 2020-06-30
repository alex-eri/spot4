import asyncio
import csv
import logging
import datetime
from multiprocessing import Process, current_process
# from collections import namedtuple
# import ftplib
import os
import ipaddress
import concurrent.futures

logger = logging.getLogger('sheduler')
debug = logger.debug


pool = concurrent.futures.ThreadPoolExecutor()


def pathtree(cfg, now):
    paths = []
    if cfg.get('year', True):
        paths.append(str(now.year))
    if cfg.get('month', True):
        paths.append(str(now.month).rjust(2,'0'))
    if cfg.get('day', True):
        paths.append(str(now.day).rjust(2,'0'))
    return paths


def makepath(cfg, now):
    paths = [cfg.get('dir', '../data/exports')]
    paths += pathtree(cfg, now)
    path = os.path.join(*paths)
    os.makedirs(path, exist_ok=True)
    return path


async def runcurl(cmd):
    proc = await asyncio.create_subprocess_shell(cmd,
                                                 stderr=asyncio.subprocess.PIPE)

    stderr = await proc.communicate()
    debug(stderr)
    debug(proc.returncode)


def upload(name, cfg, loop, now):
    paths = [cfg.get('ftp')]
    paths += pathtree(cfg, now)
    path = os.path.join(*paths)

    debug('upload started')
    username, password = cfg.get('username', 'anonymous'), cfg.get('password', ''),

    cmd = "curl --ftp-create-dirs -T {name} -u {username}:{password} {path}/".format(
        name=name,
        username=username,
        password=password,
        path=path
    )
    loop.create_task(runcurl(cmd))


async def sheduler_callback_async(db, loop):
    while True:
        cfg = await db.sheduler.find_one({'_id': 'exporter'})

        if not(cfg and cfg.get('enabled', False)):
            loop.call_later(60, sheduler_callback, db, loop, 'waiting')
            return

        now = datetime.datetime.utcnow()
        step = datetime.timedelta(seconds=cfg.get('step', 36000))

        cfg = await db.sheduler.find_and_modify(
                 {'_id': 'exporter'},
                 {'$set': {'date': now}},
                 new=False
                 )

        then = cfg.get('date', now - step)

        debug(f'export from {then} to {now}')

        ACCOUNTINGfieldnames = ['_id', 'username', 'caller', 'ip', 'callee', 'start_date', 'stop_date']

        accs = db.accounting.find({'$and': [
            {'start_date': {'$lte': now}},
            {'stop_date': {'$gte': then}}
             ]},
             ACCOUNTINGfieldnames)

        path = makepath(cfg, now)
        ACCOUNTINGname = os.path.join(path,('ACCOUNTING{now:%Y%m%d_%H%M%S}.csv'.format(now=now)))
        REGname = os.path.join(path,('REG{now:%Y%m%d_%H%M%S}.csv'.format(now=now)))
        debug(f'open {ACCOUNTINGname}')
        with open(ACCOUNTINGname, 'w', newline='') as f:
            writer = csv.DictWriter(f, ACCOUNTINGfieldnames)
            async for line in accs:
                line['ip'] = ipaddress.IPv4Address(line['ip'])
                writer.writerow(line)

        if cfg.get('ftp', False):
            loop.call_soon(
                upload, ACCOUNTINGname, cfg, loop, now
            )

        REGfieldnames = ['_id', 'username', 'checked', 'phone', 'mac', 'registred', 'callee', 'seen', 'seen_callee']
        regs = db.devices.find( { '$or': [
            {'$and': [
                { 'registred' : {'$gte': then} },
                { 'registred' : {'$lte': now} }
            ]},{'$and': [
                { 'seen' : {'$gte': then} },
                { 'seen' : {'$lte': now} }
            ]}
             ]},
             REGfieldnames)
        debug(f'open {REGname}')
        with open(REGname, 'w', newline='') as f:
            writer = csv.DictWriter(f, REGfieldnames)
            async for line in regs:
                writer.writerow(line)

        if cfg.get('ftp', False):
            loop.call_soon(
                upload, REGname, cfg, loop, now
            )
        await asyncio.sleep(step.total_seconds())

    # name = 'export at '+(now+step).isoformat()
    # debug('call next at '+(now+step).isoformat())
    # timer = loop.call_at(
    #     (now+step).timestamp(),
    #     sheduler_callback,
    #     db,
    #     loop,
    #     name)
    # debug(timer)


def done_callback(name):
    def noop(*a, **kw):
        debug('done ' + name)
    return noop


def sheduler_callback(db, loop, name):
    debug('starting '+name)
    t = loop.create_task(sheduler_callback_async(db, loop))
    t.add_done_callback(done_callback(name))


def run(config):
    import storage
    db = storage.setup(
        config['DB']['SERVER'],
        config['DB']['NAME']
    )
    loop = asyncio.get_event_loop()

    loop.call_soon(sheduler_callback, db, loop, 'export on start')

    try:
        loop.run_forever()
    except Exception as e:
        logger.error(repr(e))
    finally:
        loop.close()

def setup(config):
    proc = Process(target=run, args=(config,))
    proc.name = 'exporter'
    return [proc]


def main():
    import json
    config = json.load(open('../config/config.json','r'))
    run(config)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    main()
