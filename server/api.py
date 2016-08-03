from aiohttp import web
import aiohttp
from utils import procutil
from multiprocessing import Process, current_process
from bson.json_util import dumps, loads
import random
import base64, pyotp
import logging

import hashlib

logger = logging.getLogger('http')
debug = logger.debug

SMSSEND = 1
SMSWAIT = 2

async def salt_handler(request):
    resp = {
        'salt': request.app['config'].get('SALT_ASCII','')
    }
    return resp

async def device_handler(request):
    q = dict(
        phonehash = request.match_info.get('phonehash'),
        mac = request.match_info.get('mac')
        )
    #request.app.logger.debug(type(request.match_info.get('mac')))

    base = base64.b32encode("{phonehash}#{mac}".format(**q).encode('ascii'))
    device = await request.app['db'].devices.find_one(q)
    request.app.logger.debug(device.__repr__())
    if device:
        if device.get('checked'):
            otp = pyotp.TOTP(base)
            device['password'] = otp.now()
        else:
            numbers = request.app['config']['SMS_POLLING'].get('CALLIE')
            if device.get('sms_callie') in numbers:
                pass
            else:
                device['sms_callie'] = callie = random.choice(numbers)
                request.app.logger.debug(q)
                r = await request.app['db'].devices.update(q, {'$set':{'sms_callie': callie}})
                request.app.logger.debug(r)
        return {'response': device}

    else:
        otp =  pyotp.HOTP(base)
        q['username'] = q['phonehash']
        q['sms_waited'] = otp.at(SMSWAIT)
        q['sms_callie'] = random.choice(request.app['config']['SMS_POLLING'].get('CALLIE'))
        debug(q)
        device_id = await request.app['db'].devices.insert(q)
        q['_id'] = device_id
        return {'response': q}


async def sms_handler(request):
    POST = await request.post()

    m = hashlib.md5()
    m.update(request.app['config'].get("SALT",b""))
    m.update(POST.get('phone').encode('ascii'))

    q = dict(
        phonehash = m.hexdigest(),
        sms_waited = POST.get('sms_waited')
        )
    device = await request.app['db'].devices.update(q, {'$set':{'checked':True}})
    return {'response': 'OK'}



def add_cmd(pipe,command,args):
    if type(args) == dict:
        kw = args
        a = []
    elif type(args) == list:
        a = args
        kw = dict()
    try:
        r = getattr(pipe, command)
    except AttributeError as e:
        logger.error(e)
    return r(*a,**kw)


async def db_handler(request):
    collection = request.match_info.get('collection')
    skip = int(request.match_info.get('skip',0))
    limit = int(request.match_info.get('limit',500))

    data = await request.json(loads=loads)
    debug(data)

    cursor = request.app['db'][collection]

    for cmd in data:
        for c,a in cmd.items():
            cursor = add_cmd(cursor,c,a)

    if type(cursor) == storage.motor_asyncio.MotorCollection:
        cursor = cursor.find()

    c = await cursor.count()
    r = await cursor.skip(skip).limit(limit).to_list(limit)
    return {'response': r, 'total':c}


def check_auth(fu):
    async def handler(request):
        if request.headers.get('AUTHORIZATION') is None:
            raise web.HTTPUnauthorized(headers={'WWW-Authenticate':'Basic realm="Spot4 API"'})
        else:
            method, secret = request.headers.get('AUTHORIZATION').split()
            login, password = base64.b64decode(secret).decode('ascii').split(':')
            if request.app['config']['API_SECRET'].get(login) != password:
                raise web.HTTPForbidden()
        return await fu(request)
    return handler


async def json_middleware(app, handler):
    async def middleware_handler(request):
        resp = await handler(request)
        return web.json_response(resp, dumps=dumps)
    return middleware_handler

async def cors(app, handler):
    "Access-Control-Allow-Origin"
    async def middleware_handler(request):
        resp = await handler(request)
        resp.headers['Access-Control-Allow-Origin'] = request.headers.get('Origin','')
        return resp
    return middleware_handler



def setup_web(config):
    global logger
    name = current_process().name
    procutil.set_proc_name(name)

    import storage
    db = storage.setup(
        config['DB']['SERVER'],
        config['DB']['NAME']
    )

    debug(id(db))

    db.devices.ensure_index( [ ("username",1), ("mac",1) ], unique=True, dropDups=True ,callback=storage.index_cb)
    db.devices.ensure_index( [ ("phonehash",1), ("mac",1) ], unique=True, dropDups=True ,callback=storage.index_cb)
    db.devices.ensure_index( [ ("username",1) ], unique=False, callback=storage.index_cb)

    app = web.Application(middlewares=[cors, json_middleware])
    app['db'] = db
    app['config'] = config
    app.logger = logger

    if config.get('SMS_POLLING'):
        app.router.add_route('GET', '/device/{phonehash}/{mac}', device_handler)
        app.router.add_route('POST', '/sms_callback', check_auth(sms_handler))

    app.router.add_route('GET', '/salt', salt_handler)
    app.router.add_route('POST', '/db/{collection}/{skip}::{limit}', check_auth(db_handler))
    app.router.add_route('POST', '/db/{collection}', check_auth(db_handler))

    port = config.get('API_PORT',8080)

    web.run_app(app,port=port)

def setup(config):
    web = Process(target=setup_web, args=(config,))
    web.name = 'web'
    return [web]
