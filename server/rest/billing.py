from .decorators import json
from .logger import *
import uuid
import hashlib
import random
import bson
from datetime import datetime,timedelta

CHARS = 7
V_COUNT = 200
RANDOM_RANGE = 10 ** CHARS


@json
async def voucher(request):
    now = datetime.utcnow()
    coll = request.app['db'].voucher
    
    if 'json' in request.headers.get('Content-Type',''):
        DATA = await request.json()
    else:
        DATA = await request.post()

    callee = DATA.get('callee')

    q = {
        'voucher' : DATA.get('voucher'),
        'callee': {'$in' :[callee ,'default']},
        'invoiced': { '$exists': False},
        'closed': False
        }

    upd = {
        'invoiced': now,
        'nas': DATA.get('nas'),
        'device' : DATA.get('device'),
        'username': DATA.get('username'),
        'closed':True
        }
    updq = {
        '$set': upd
        }
    voucher = await coll.find_and_modify(q, updq, upsert=False, new=True)
    if voucher:
        tarif = await request.app['db'].tarif.find_one({'_id':voucher['tarif']})
        invoices = request.app['db'].invoice

        if tarif.get('duration') > 0:
            stop = now +timedelta(days=tarif['duration'])
        else:
            stop = 0

        q = {   'username': voucher['username'],
                'paid':True,
                'start': now ,
                'stop': stop,
                'voucher': voucher['_id'],
                'tarif': tarif['_id'],
                'limit': tarif.get('limit',{}),
                'callee' : callee
             }

        debug(type(voucher['_id']))
        invoice = await invoices.insert(q)

        return invoice

    return {'error':'wrongcode'}


async def nextseries(db):
    n = await db.counters.find_and_modify({'_id':'voucher'},{ '$inc': { 'seq': 1 } }, new=True)
    return n.get('seq')

@json
async def generate(request):
    if 'json' in request.headers.get('Content-Type',''):
        DATA = await request.json()
    else:
        DATA = await request.post()

    db = request.app['db']

    series = await nextseries(db)

    q = {
        'tarif' : bson.ObjectId(DATA.get('tarif')),
        'callee': DATA.get('callee'),
        'series': series,
        'closed': False
        }

    datas = []

    for i in range(V_COUNT):
        r = random.randrange(RANDOM_RANGE)
        a = {
            'voucher': str(r).zfill(CHARS)
        }
        a.update(q)
        datas.append(a)

    await db.voucher.insert(datas)

    return q

@json
async def close(request):
    if 'json' in request.headers.get('Content-Type',''):
        DATA = await request.json()
    else:
        DATA = await request.post()

    db = request.app['db']

    q = {
        'series': series
        }

    return await db.voucher.update(
                q,
                {'$set':{'closed': True}},
                multi=True
            )
