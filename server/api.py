import db
from aiohttp import web
import aiohttp
import procutil
from multiprocessing import Process, current_process
from bson.json_util import dumps
import random
import base64, pyotp
import logging
logger = logging.getLogger('http')
debug = logger.debug

SMSSEND = 1
SMSWAIT = 2

async def device_handler(request):
    q = dict(
        login = request.match_info.get('login'),
        mac = request.match_info.get('mac')
        )
    #request.app.logger.debug(type(request.match_info.get('mac')))

    base = base64.b32encode("{login}#{mac}".format(**q).encode('ascii'))
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
        q['sms_waited'] = otp.at(SMSWAIT)
        q['sms_callie'] = random.choice(request.app['config']['SMS_POLLING'].get('CALLIE'))
        debug(q)
        device_id = await request.app['db'].devices.insert(q)
        q['_id'] = device_id
        return {'response': q}


async def sms_handler(request):
    POST = await request.post()
    q = dict(
        login = POST.get('login'),
        sms_waited = POST.get('sms_waited')
        )
    device = await request.app['db'].devices.update(q, {'$set':{'checked':True}})
    return {'response': 'OK'}


async def check_auth(request):
    if request.version != aiohttp.HttpVersion11:
        return
    if request.headers.get('EXPECT') != '100-continue':
        raise web.HTTPExpectationFailed(text="Unknown Expect: %s" % expect)
    if request.headers.get('AUTHORIZATION') is None:
        raise web.HTTPForbidden()
    request.transport.write(b"HTTP/1.1 100 Continue\r\n\r\n")

async def json_middleware(app, handler):
    async def middleware_handler(request):
        resp = await handler(request)
        return web.json_response(resp, dumps=dumps)
    return middleware_handler

async def cors(app, handler):
    "Access-Control-Allow-Origin"
    async def middleware_handler(request):
        resp = await handler(request)
        resp.headers['Access-Control-Allow-Origin'] = request.headers.get('Origin')
        return resp
    return middleware_handler



def setup_web(config):
    global logger
    name = current_process().name
    procutil.set_proc_name(name)

    db.db.devices.ensure_index( [ ("login",1), ("mac",1) ], unique=True, dropDups=True ,callback=db.index_cb)

    app = web.Application(middlewares=[cors, json_middleware])
    app['db'] = db.db
    app['config'] = config

    app.logger = logger

    if config.get('SMS_POLLING'):
        app.router.add_route('GET', '/user/{login}/{mac}', device_handler)
        app.router.add_route('POST', '/sms_callback', sms_handler, expect_handler=check_auth)

    port = config.get('API_PORT',8080)

    web.run_app(app,port=port)

def setup(config):
    web = Process(target=setup_web, args=(config,))
    web.name = 'web'
    return [web]
