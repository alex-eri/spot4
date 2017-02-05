from .phone import *
from .device import *
from .decorators import json
import aiohttp.web
from aiohttp.file_sender import FileSender
import logging
logger = logging.getLogger('http')
debug = logger.debug
from bson.json_util import dumps, loads
import asyncio
import motor
import motor.core

def add_cmd(pipe,command,args):
    if type(args) == dict:
        kw = args
        a = []
    elif type(args) == list:
        a = args
        kw = dict()
    else:
        a = []
        kw = dict()
    try:
        r = getattr(pipe, command)
    except AttributeError as e:
        logger.error(e)
    else:
        ret = r(*a,**kw)
        return ret

@json
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

    if hasattr(cursor,'find'):
        cursor = cursor.find()

    c = None

    if hasattr(cursor,'count'):
        c = await cursor.count()
    if hasattr(cursor,'skip'):
        cursor = cursor.skip(skip).limit(limit)

    if hasattr(cursor,'to_list'):
        r = await cursor.to_list(limit)
    else:
        r = await cursor

    return {'response': r, 'total':c}

async def db_options(request):
    resp = web.Response()
    resp.headers['ALLOW']='POST, GET'
    resp.headers['WWW-Authenticate'] = 'Basic realm="Spot4 API"'
    return resp


async def generate_204(request):
    raise web.HTTPNoContent()

async def hotspot_detect(request):
    return web.Response(
        body=b"<HTML><HEAD><TITLE>Success</TITLE></HEAD><BODY>Success</BODY></HTML>",
        content_type='text/html')
