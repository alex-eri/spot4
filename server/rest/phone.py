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
from .smsru import smsru_call


REREG_DAYS = 3
DEVMAX = 10

async def nextuser(db):
    n = await db.counters.find_and_modify({'_id':'userid'},{ '$inc': { 'seq': 1 } }, new=True)
    return str(n.get('seq')).zfill(6)


async def setuser(db, reg):

    user = \
        await db.users.find_one({'with': reg})
    if user:
        return user['_id']

    return await db.users.insert({'with': reg, '_id': await nextuser(db)})




@json
async def phone_handler(request):
    now = datetime.utcnow()

    coll = request.app['db'].devices
    if 'json' in request.headers.get('Content-Type',''):
        DATA = await request.json()
    else:
        DATA = await request.post()
    phone = DATA.get('phone')

    method = DATA.get('method', 'sms')

    debug("method="+method)

    try:
        phcheck(phone)
    except:
        raise web.HTTPForbidden()

    uam = await get_uam_config(request.app['db'], DATA.get('profile','default'))
    uam = uam or {}

    sms_limit = uam.get('sms_limit', -1)

    if uam.get('smssend', False) and sms_limit > 0:
        sms_limit -= await request.app['db'].sms_sent.count(
            {
                'callee': uam.get('_id', 'default'),
                'sent': {'$gt': (now - monthdelta(1))}
             }
             )
    else:
        sms_limit = 1

    q = {
        "phone": phone,
        "mac": DATA.get('mac').upper().replace('-', ':')
        }

    updq = {
        '$set': {
            'seen': now,
            'ua': request.headers.get('User-Agent', ''),
            'seen_callee': DATA.get('profile', 'default')
            },
        '$setOnInsert': {'registred': now, 'callee': DATA.get('profile', 'default') },
        #, "$set" {'sensor': request.ip }
        }

    device = await coll.find_and_modify(q, updq, upsert=True, new=True)#,fields=FIELDS)

    upd = {'try': 0, 'method': method}

    rereg = timedelta(days=uam.get('rereg', REREG_DAYS)) or REREG_DAYS

    count = await coll.find({
            'mac': q['mac'],
            'seen': {'$gt': (now-rereg)},
            'checked': {'$ne': True}
        }).count()

    if count >= uam.get('devmax', DEVMAX):
        uam['smssend'] = False

    debug(uam)
    debug(device)


    sms_timeout = uam.get('sms_timeout', -1)
    if sms_timeout == -1:
        sms_timeout = rereg
    elif sms_timeout == -2:
        sms_timeout = False
    else:
        sms_timeout = timedelta(minutes=sms_timeout)

    if device.get('username'):
        reg = False
        if device.get('checked'):
            debug("checked")
            pass
        elif (now - device.get('registred', now)) > rereg:
            debug(now)
            debug(device.get('registred'))
            debug("rereg")
            reg = True
        elif uam.get('smssend', False):
            debug("smssend")
            if not device.get('sms_sent'):
                debug("reg not sent")
                reg = True
            elif not device.get('sms_time'):
                debug("reg no time")
                reg = True
            else:
                if sms_timeout != False and now - device.get('sms_time') > sms_timeout:
                    reg = True
                    debug("reg timeout")

                debug(now - device.get('sms_time'))
                debug(sms_timeout)

    else:
        reg = True
        upd['username'] = (await setuser(request.app['db'],phone))


    if reg:

        if uam.get('nosms', False):
            upd['checked'] = True
        else:

            if uam.get('callrecieve', False) and method == 'call':
                numberscursor = request.app['db'].numbers.find({'call_recv': True})
                numbers = await numberscursor.to_list(length=1000)
                if numbers:
                    upd['call_waited'] = random.choice(numbers).get('number', '~')
                if upd['call_waited'].startswith('smsru'):
                    try:
                        upd['call_waited'], upd['check_id'] = await smsru_call(upd['call_waited'],phone)
                    except Exception as e:
                        logger.error('failed to register call')
                        logger.error(e)
                    if upd['call_waited']:
                        upd['method'] = 'smsru/call'

            elif uam.get('smsrecieve', False):
                numberscursor = request.app['db'].numbers.find({'sms_recv': True}) #request.app['config'].get('numbers')
                numbers = await numberscursor.to_list(length=1000)
                if numbers:
                    code = getsms(**q)
                    upd['sms_waited'] = code
                    upd['sms_callie'] = random.choice(numbers).get('number', '~')

            if not (uam.get('smssend', False) and method == 'sms'):
                debug('not enabled smssend')
            elif sms_limit <= 0:
                debug('smssend limited')
            elif sms_timeout != False and device.get('sms_time') and now - device.get('sms_time') < sms_timeout:
                debug('smssend timeout')
                code = device.get('sms_sent', getsms(**q))
                debug("old code %s" % code)
                upd['sms_sent'] = code
            else:
                code = device.get('sms_sent', getsms(**q))
                debug(code)
                upd['sms_sent'] = code
                upd['sms_time'] = now

                tmpl = uam.get('smstmpl', False) or "wifi: {code}."
                text = tmpl.format(code=code)

                #request.app['config']['smsq'].put((phone,text))
                request.app['db'].sms_sent.insert(
                    {
                        'phone': phone,
                        'text': text,
                        'sent': now,
                        'callee': uam.get('_id', 'default')
                    })

        updq = {
            '$set': upd,
        }

        debug(upd)
        device = await coll.find_and_modify({'_id': device['_id']}, updq, new=True)#,fields=FIELDS)
        debug(device.__repr__())

    if device:
        device['sms_sent'] = device.get('sms_sent') and True
        if device.get('checked'):
            device['password'] = getpassw(device.get('username'), device.get('mac'))
            if uam.get('tarif'):
                await addinvoice(request.app['db'], device, uam)
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


