from .decorators import json
from aiohttp import web
from utils.password import getsms, getpassw
from utils.phonenumbers import check as phcheck
import random
from .logger import *



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
    coll = request.app['db'].devices
    if 'json' in request.headers.get('Content-Type',''):
        DATA = await request.json()
    else:
        DATA = await request.post()
    phone = DATA.get('phone')

    debug(DATA)
    try:
        phcheck(phone)
    except:
        raise web.HTTPForbidden()

    q = dict(
        phone = phone,
        mac = DATA.get('mac').upper().replace('-',':')
        )

    updq = {
        '$currentDate':{'seen':True}
        #, "$set" {'sensor': request.ip }
        }

    device = await coll.find_and_modify(q, updq, upsert=True, new=True)
    debug(device.__repr__())
    if device.get('username'):
        pass
    else:
        upd = {'try': 0 }
        smsmode = DATA.get('smsmode','wait')
        numbers = request.app['config'].get('numbers')
        if numbers:
            code = getsms(**q)
            upd['sms_waited'] = code
            upd['sms_callie'] = random.choice(numbers),


            if smsmode == "send" and not device.get('sms_sended'):
                code = getsms(**q)
                upd['sms_sended'] = code

                text = "Код подтвеждения {code}.".format(code=code)
                debug(phone)
                debug(text)
                request.app['config']['smsq'].put((phone,text))

        upd['username'] = (await setuser(request.app['db'],phone))

        updq = {
            '$set': upd,
            '$currentDate':{'registred':True}
        }

        debug(upd)
        device = await coll.find_and_modify({'_id':device['_id']}, updq, new=True)
        debug(device.__repr__())

    debug(device.get('seen') - device.get('registred'))
    if device:
        return {
            'id': device.get('_id'),
            'sms_sended':device.get('sms_sended') and True
            }
    else:
        raise web.HTTPNotFound()

@json
async def sms_handler(request):
    POST = await request.post()

    q = dict(
        phone = POST.get('phone'),
        sms_waited = POST.get('sms_waited')
        )
    device = await request.app['db'].devices.update(q, {'$set':{'checked':True}})
    debug(device)
    return {'response': 'OK'}


