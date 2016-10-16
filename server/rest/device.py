from .decorators import json
from utils.password import getsms, getpassw
from .logger import *
from aiohttp import web
import random
from bson.objectid import ObjectId
import asyncio


#FIELDS=['username','sms_callie','sms_waited','checked','sms_sent','mac','try']

@json
async def device_handler(request):
    if 'json' in request.headers.get('Content-Type',''):
        DATA = await request.json()
    else:
        DATA = await request.post()

    q = {
        "_id" : ObjectId(request.match_info.get('oid'))
        }

    coll = request.app['db'].devices

    sms = DATA.get('sms_sent')

    if sms:
        trydevice = await coll.find_and_modify(
                {  'sms_sent':sms, '_id':q['_id'] },
                {'$set':{'checked': True} },
                new=True)#,fields=FIELDS)

        if trydevice:
            debug('check success')
            device = trydevice
        else:
            debug(q)
            device = await coll.find_and_modify(q,{ '$inc': {'try':1} }, new=True)#,fields=FIELDS)
            n = device.get('try')
            if n > 7: raise web.HTTPForbidden()
            if n > 3: n*=5
            await asyncio.sleep(n)
    else:
        device = await coll.find_one(q)#,fields=FIELDS)
    debug(q)
    if device:
        if device.get('checked'):
            #username = device.get('username')
            #user = await request.app['db'].users.find_one({'_id':username})
            #user.get('password') or
            debug('checked')
            device['password'] = getpassw(device['username'], device['mac'])
        else:
            numbers = request.app['config'].get('numbers')
            if device.get('sms_callie') in numbers:
                debug(numbers)
            elif numbers:
                device['sms_callie'] = callie = random.choice(numbers)
                request.app.logger.debug(q)
                r = await coll.update(q, {'$set':{'sms_callie': callie}})
                request.app.logger.debug(r)
        device['sms_sent']=device.get('sms_sent') and True
        device['phone'] = 'saved'

        debug(device.__repr__())
        return device

    else:
        raise web.HTTPNotFound()

