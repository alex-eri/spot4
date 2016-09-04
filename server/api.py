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


from password import getsms, getpassw


async def device_handler(request):
    q = dict(
        _id = request.match_info.get('oid')
        )

    coll = request.app['db'].devices

    device = await coll.find_one(q,fields=['username','sms_callie','sms_waited'])
    debug(device.__repr__())

    if device:
        if device.get('checked'):
            device['password'] = getpassw(device['username'], mac)
        else:
            numbers = request.app['numbers']
            if device.get('sms_callie') in numbers:
                pass
            else:
                device['sms_callie'] = callie = random.choice(numbers)
                request.app.logger.debug(q)
                r = await coll.update(q, {'$set':{'sms_callie': callie}})
                request.app.logger.debug(r)
        return {'response': device}

    else:
        raise web.HTTPNotFound()


async def phone_handler(request):
    q = dict(
        phone = "+"+request.match_info.get('phone'),
        mac = request.match_info.get('mac')
        )

    coll = request.app['db'].devices

    upd = {
        '$currentDate':{'seen':True}
        #, "$set" {'sensor': request.ip }
        }

    device = await coll.find_and_modify(q, upd, upsert=True, new=True)

    if device.get('username'):
        pass
    else:
        sending, waited = getsms(**q)
        numbers = request.app['config'].get('numbers')

        upd = {
            'username': device['_id'],
            'sms_waited': waited,
            'sms_callie': random.choice(numbers)
        }
        device = await coll.update({'_id':device['_id']}, upd)
    return {'oid': device['_id']}



async def sms_handler(request):
    POST = await request.post()

    q = dict(
        phone = POST.get('phone'),
        sms_waited = POST.get('sms_waited')
        )
    device = await request.app['db'].devices.update(q, {'$set':{'checked':True}})
    debug(device)
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
    #debug(help(cursor))
    #debug(isinstance(cursor, motor.core.AgnosticCollection))
    #if isinstance(cursor, motor.MotorCollection):
    if cursor.__motor_class_name__ == "MotorCollection":
        cursor = cursor.find()

    c = None

    if hasattr(cursor,'count'):
        c = await cursor.count()
    if hasattr(cursor,'skip'):
        cursor = cursor.skip(skip).limit(limit)

    r = await cursor.to_list(limit)

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

        if type(resp) == web.Response:
            return resp

        return web.json_response(resp, dumps=dumps)
    return middleware_handler

async def cors(app, handler):
    "Access-Control-Allow-Origin"
    async def middleware_handler(request):
        try:
            resp = await handler(request)
        except Exception as e:
            logger.warning(e.__repr__())
            resp = e
        resp.headers['Access-Control-Allow-Origin'] = request.headers.get('Origin','')
        resp.headers['Access-Control-Allow-Headers']='Content-Type, Authorization'

        if isinstance(resp, Exception):
            raise resp
        return resp

    return middleware_handler


async def db_options(request):
    resp = web.Response()
    resp.headers['ALLOW']='POST, GET'
    resp.headers['WWW-Authenticate'] = 'Basic realm="Spot4 API"'
    return resp


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
    db.devices.ensure_index( [ ("phone",1), ("mac",1) ], unique=True, dropDups=True ,callback=storage.index_cb)
    db.devices.ensure_index( [ ("username",1) ], unique=False, callback=storage.index_cb)

    app = web.Application(middlewares=[cors, json_middleware])
    app['db'] = db
    app['config'] = config
    app.logger = logger

    if config.get('SMS_POLLING'):

        app.router.add_route('GET', '/register/+{phone:\d+}/{mac}', phone_handler)
        app.router.add_route('GET', '/register/%2B{phone:\d+}/{mac}', phone_handler)

        app.router.add_route('GET', '/device/{oid}', device_handler)

        app.router.add_route('POST', '/sms_callback', check_auth(sms_handler))

    app.router.add_route('POST', '/db/{collection}/{skip}::{limit}', check_auth(db_handler))
    app.router.add_route('POST', '/db/{collection}', check_auth(db_handler))

    app.router.add_route('OPTIONS', '/{path:.*}', db_options)

    port = config.get('API_PORT',8080)

    web.run_app(app,port=port)

def setup(config):
    web = Process(target=setup_web, args=(config,))
    web.name = 'web'
    return [web]
