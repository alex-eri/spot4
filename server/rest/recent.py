from .decorators import json
from aiohttp import web
from utils.password import getsms, getpassw
from utils.phonenumbers import check as phcheck
import random
from .logger import *
#from .device import FIELDS
from datetime import datetime, timedelta
from .front import get_uam_config
from monthdelta import monthdelta
from .billing import addinvoice


@json
async def recent_handler(request):
    now = datetime.utcnow()

    coll = request.app['db'].devices
    if 'json' in request.headers.get('Content-Type',''):
        DATA = await request.json()
    else:
        DATA = await request.post()

    uam = await get_uam_config(request.app['db'], DATA.get('profile','default'))
    uam = uam or {}

    q = {
        'seen': {"$gt": now - timedelta(seconds=uam.get('fastlogin', 1200))},
        'seen_callee': uam.get('id', 'default'),
        "phone": phone,
        "mac": DATA.get('mac').upper().replace('-', ':'),
        }

    updq = {
        '$set': {
            'seen': now,
            'ua': request.headers.get('User-Agent', ''),
            },
        }

    device = await coll.find_one_and_update(q, updq, return_document=True)

    if device:
        device['sms_sent'] = device.get('sms_sent') and True
        if device.get('checked'):
            device['password'] = getpassw(device.get('username'), device.get('mac'))
            if uam.get('tarif'):
                await addinvoice(request.app['db'], device, uam) #
        return device
    else:
        raise web.HTTPNotFound()
