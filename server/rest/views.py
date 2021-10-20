from .phone import *
from .device import *
from .decorators import json
import aiohttp.web
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


async def filter_for_admin(administrator,collection,data,db):

    filters = administrator.get('filters',None)

    field = False

    if collection in ["tarif","users","collector"] and filters:
        raise web.HTTPForbidden()

    if not filters: return

    command = next(iter(data[0].keys()))

    if not command: return

    if collection in ["accounting",'devices','sms_sent','sms_received']:
        field = 'callee'

    elif collection in ['limit','uamconfig']:
        field = '_id'
        if command == 'find':
            filters.append('default')

    elif collection == "administrator":
        if administrator.get('superadmin',None):
            return
        else:
            field = '_id'
            filters = [administrator.get('_id')]
            if command == 'find':
                pass
            elif command == 'find_one_and_update':
                if data[0][command].get('update'):
                    if data[0][command]['update'].get('$set'):
                        data[0][command]['update']['$set'].pop('filters',None)
                        data[0][command]['update']['$set'].pop('_id',None)
                        data[0][command]['update']['$set'].pop('superadmin',None)
                    else:
                        upd = data[0][command]['update']
                        upd.pop('filters',None)
                        upd.pop('superadmin',None)
                        upd.pop('_id',None)
                        data[0][command]['update'] = {'$set': upd }
                else:
                    raise web.HTTPForbidden()
            else:
                raise web.HTTPForbidden()

    if not field: return

    if command in ['find','find_one_and_update','remove']:
        opts = data[0][command]
        try:
            if not opts:
                data[0][command] = [{}]
                data[0][command][0][field] = {'$in':filters}

            elif type(opts) == dict:
                if not data[0][command]['filter'].get(field, None) in filters:
                    data[0][command]['filter'][field] = {'$in':filters}

            elif type(opts) == list:
                if not data[0][command][0].get(field, None) in filters:
                    data[0][command][0][field] = {'$in':filters}

        except KeyError:
            web.HTTPForbidden()


    elif command == 'distinct':
        data.insert(0,{'find': [{field: {'$in':filters} }]})

    elif command == 'aggregate':
        data[0][command][0].insert(0, {'$match': {field: {'$in':filters}} })

    elif command == 'insert':
        raise web.HTTPForbidden()
    else:
        raise web.HTTPForbidden()

    """
    find
    find_one_and_update
    distinct
    aggregate
    """




@json
async def db_handler(request):
    collection = request.match_info.get('collection')
    skip = int(request.match_info.get('skip',0))
    limit = int(request.match_info.get('limit',500))

    data = await request.json(loads=loads)
    debug(data)

    cursor = request.app['db'][collection]

    await filter_for_admin(request.administrator, collection, data, request.app['db'])
    logger.debug(data)

    for cmd in data:
        for c,a in cmd.items():
            cursor = add_cmd(cursor,c,a)

    if hasattr(cursor,'find'):
        cursor = cursor.find()

    c = None

    if hasattr(cursor,'estimated_document_count'):
        c = await cursor.estimated_document_count()
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
