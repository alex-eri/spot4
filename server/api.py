from aiohttp import web
import aiohttp
from utils import procutil
from multiprocessing import Process, current_process
from bson.json_util import dumps, loads
import random

import logging
import motor.core
import hashlib

logger = logging.getLogger('http')
debug = logger.debug

def setup_web(config):
    global logger
    name = current_process().name
    procutil.set_proc_name(name)

    import storage
    import asyncio
    import rest.urls

    db = storage.setup(
        config['DB']['SERVER'],
        config['DB']['NAME']
    )

    loop = asyncio.get_event_loop()

    loop.run_until_complete(
        db.counters.find_and_modify(
        {'_id':'userid'},
        { '$setOnInsert': {'seq':0}},
        upsert=True,new=True)
        )

    debug('starting webapp')


    app = web.Application()
    app['db'] = db
    app['config'] = config
    app.logger = logger

    rest.urls.routers(app)

    port = config.get('API_PORT',8080)

    web.run_app(app,port=port)

def setup(config):
    web = Process(target=setup_web, args=(config,))
    web.name = 'web'
    return [web]
