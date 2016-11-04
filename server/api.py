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

    import rest.urls

    db = storage.setup(
        config['DB']['SERVER'],
        config['DB']['NAME']
    )

    db.counters.insert({'_id':'userid', 'seq':0}, callback=storage.ensure_obj)

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
