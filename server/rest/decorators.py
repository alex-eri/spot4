from aiohttp import web
from bson.json_util import dumps, loads

from .logger import logger

import base64

def check_auth(handler):
    async def middleware_handler(request):
        if request.headers.get('AUTHORIZATION') is None:
            raise web.HTTPUnauthorized(headers={'WWW-Authenticate':'Basic realm="Spot4 API"'})
        else:
            method, secret = request.headers.get('AUTHORIZATION').split()
            login, password = base64.b64decode(secret).decode('utf-8').split(':')

            coll = request.app['db'].administrator

            request.administrator = await coll.find_one({'name':login,'password':password})
            logger.debug(request.administrator)
            if not request.administrator:
                raise web.HTTPForbidden()

        return await handler(request)
    return middleware_handler


def json( handler):
    async def middleware_handler(request):
        resp = await handler(request)

        if type(resp) == web.Response:
            return resp

        return web.json_response(resp, dumps=dumps)
    return middleware_handler

def cors( handler):
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


