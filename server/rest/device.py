from .decorators import json
from utils.password import getsms, getpassw
from .logger import debug
from aiohttp import web
import random
from bson.objectid import ObjectId
import asyncio
from .billing import addinvoice
from .front import get_uam_config

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
            device = await coll.find_and_modify(q, {'$inc': {'try': 1}}, new=True) # ,fields=FIELDS)
            n = device.get('try')
            if n > 7: raise web.HTTPForbidden()
            if n > 3: n*=5
            await asyncio.sleep(n)
    else:
        device = await coll.find_one(q)#,fields=FIELDS)
    if device:
        if device.get('checked'):
            #username = device.get('username')
            #user = await request.app['db'].users.find_one({'_id':username})
            #user.get('password') or
            debug('checked')
            device['password'] = getpassw(device['username'], device['mac'])

            uam = await get_uam_config(request.app['db'], device.get('seen_callee', 'default'))
            uam = uam or {}

            if uam.get('tarif'):
                await addinvoice(request.app['db'], device, uam)
        else:
            numbers = request.app['config'].get('numbers', [])
            if device.get('sms_callie', None) and device.get('sms_callie', None) in numbers:
                debug("%s in %s" % (device.get('sms_callie'), numbers))
            elif numbers:
                device['sms_callie'] = callie = random.choice(numbers)
                request.app.logger.debug(q)
                r = await coll.update(q, {'$set': {'sms_callie': callie}})
                request.app.logger.debug(r)
        device['sms_sent'] = device.get('sms_sent') and True
        device['phone'] = 'saved'

        debug(device.__repr__())
        return device

    else:
        raise web.HTTPNotFound()

