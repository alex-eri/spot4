import db
from aiohttp import web
import aiohttp
import procutil
from multiprocessing import Process, current_process
from bson.json_util import dumps

import base64, pyotp

SMSSEND = 1
SMSGET = 2

async def device_handler(request):
    q = dict(
        login = request.match_info.get('login'),
        mac = request.match_info.get('mac')
        )
    #request.app.logger.debug(type(request.match_info.get('mac')))

    device = await request.app['db'].devices.find_one(q)
    if device:
        return {'response': device}
    else:
        base = "{login}#{mac}".format(**q).encode('ascii')
        otp =  pyotp.HOTP(base64.b32encode(base))
        q['otp'] = otp.at(SMSGET)
        request.app.logger.debug(q['otp'])
        device_id = await request.app['db'].devices.insert(q)
        q['_id'] = device_id
        return {'response': q}


async def sms_handler(request):
    POST = await request.post()
    q = dict(
        login = POST.get('login'),
        otp = POST.get('otp')
        )
    device = await request.app['db'].devices.update(q, {'checked':'true'})
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

def setup_web(config):
    name = current_process().name
    procutil.set_proc_name(name)

    db.db.devices.ensure_index( [ ("login",1), ("mac",1) ], unique=True, dropDups=True ,callback=db.index_cb)

    app = web.Application(middlewares=[json_middleware])
    app['db'] = db.db

    app.router.add_route('GET', '/device/{login}/{mac}', device_handler)
    app.router.add_route('POST', '/sms_callback', sms_handler, expect_handler=check_auth)

    web.run_app(app)

def setup(config):
    web = Process(target=setup_web, args=(config,))
    web.name = 'web'
    return [web]
