from .decorators import json
from .logger import *
import uuid
import hashlib
import random
import bson

@json
async def voucher(request,series):
    now = datetime.utcnow()
    coll = request.app['db'].voucher
    
    if 'json' in request.headers.get('Content-Type',''):
        DATA = await request.json()
    else:
        DATA = await request.post()

    q = {
        'voucher' : DATA.get('voucher'),
        'callee': DATA.get('callee'),
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
        tarif = request.app['db'].tarif.find_one({'_id':voucher['tarif']})
        invoices = request.app['db'].invoice

        q = {   'username': voucher['username'],
                'paid':True,
                'start': now ,
                'stop':{'$gt':now},
                'voucher': voucher['_id'],
                'tarif': tarif['_id'],
                'limit': tarif.get('limit',{})
             }

        debug(type(voucher['_id']))
        invoice = await invoices.insert(q)

        invoice['voucher'] = voucher
        invoice['tarif'] = tarif
        return invoice


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

    for i in range(500):
        r = random.randrange(10000_0000)
        a = {
            'voucher': str(r).zfill(8)
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
