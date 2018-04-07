from .decorators import json
from aiohttp import web
from utils.password import getsms, getpassw
from utils.phonenumbers import check as phcheck
import random
from .logger import *
#from .device import FIELDS
from datetime import datetime, timedelta
from .front import get_uam_config


REREG_DAYS = 3
REREG = timedelta(days=REREG_DAYS)
DEVMAX = 4

async def nextuser(db):
    n = await db.counters.find_and_modify({'_id':'userid'},{ '$inc': { 'seq': 1 } }, new=True)
    return str(n.get('seq')).zfill(6)


async def setuser(db,reg):

    user = \
        await db.users.find_one({'with':reg})
    if user:
        return user['_id']

    return await db.users.insert({'with':reg,'_id': await nextuser(db)})


@json
async def phone_handler(request):
    now = datetime.utcnow()

    coll = request.app['db'].devices
    if 'json' in request.headers.get('Content-Type',''):
        DATA = await request.json()
    else:
        DATA = await request.post()
    phone = DATA.get('phone')

    call = DATA.get('call','sms')

    try:
        phcheck(phone)
    except:
        raise web.HTTPForbidden()

    uam = await get_uam_config(request.app['db'], DATA.get('profile','default'))
    debug(uam)
    uam = uam or {}

    q = dict(
        phone = phone,
        mac = DATA.get('mac').upper().replace('-',':')
        )

    updq = {
        '$set':{
            'seen':now,
            'ua': request.headers.get('User-Agent',''),
            'seen_callee': DATA.get('profile','default')
            },
        '$setOnInsert':{'registred': now, 'callee': DATA.get('profile','default') },
        #, "$set" {'sensor': request.ip }
        }

    device = await coll.find_and_modify(q, updq, upsert=True, new=True)#,fields=FIELDS)
    debug(device.__repr__())

    upd = {'try': 0 }

    if uam.get('rereg'):
        rereg = timedelta(days=uam.get('rereg'))
    else:
        rereg = REREG

    count = await coll.find( {'mac':q['mac'],'seen': {'$lt': (now-rereg)}} ).count()

    if count >= uam.get('devmax', DEVMAX):
        uam['smssend'] = False

    if device.get('username'):
        reg = False
        if device.get('checked'):
            pass
        elif (now - device.get('registred',now)) > rereg:
            reg = True
        elif uam.get('smssend',False) and not device.get('sms_sent'):
            reg = True
    else:
        reg = True
        upd['username'] = (await setuser(request.app['db'],phone))


    if reg:
        if uam.get('nosms',False):
            upd['checked'] = True
        elif call=="out":
            pass
        elif call=="in":
            pass
        else:
            numbers = request.app['config'].get('numbers')
            if uam.get('smsrecieve',False) and numbers:
                code = getsms(**q)
                upd['sms_waited'] = code
                upd['sms_callie'] = random.choice(numbers)

            if uam.get('smssend',False):
                code = getsms(**q)
                upd['sms_sent'] = code

                tmpl = uam.get('smstmpl',"Код подтверждения {code}.")
                text = tmpl.format(code=code)

                #request.app['config']['smsq'].put((phone,text))
                request.app['db'].sms_sent.insert(
                    {
                        'phone':phone,
                        'text':text,
                        'sent':now,
                        'callee': uam.get('_id','default')
                    })

        updq = {
            '$set': upd,
        }

        debug(upd)
        device = await coll.find_and_modify({'_id':device['_id']}, updq, new=True)#,fields=FIELDS)
        debug(device.__repr__())

    if device:
        device['sms_sent'] = device.get('sms_sent') and True
        if device.get('checked'):
            device['password'] = getpassw(device.get('username'), device.get('mac'))
        return device
    else:
        raise web.HTTPNotFound()

@json
async def sms_handler(request):
    POST = await request.post()

    q = dict(
        phone = POST.get('from'),
        sms_waited = POST.get('sms')
        )
    device = await request.app['db'].devices.update(q, {'$set':{'checked':True}})
    debug(device)
    return {'response': 'OK'}


