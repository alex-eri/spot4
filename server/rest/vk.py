from .phone import setuser, json, datetime, getpassw,get_uam_config
from .logger import *

@json
async def vk_handler(request):
    now = datetime.utcnow()

    coll = request.app['db'].devices
    if 'json' in request.headers.get('Content-Type',''):
        DATA = await request.json()
    else:
        DATA = await request.post()
    try:
        user = DATA.get('vk')
        vk = user['id']
        ident = "vk:"+vk

    except:
        raise web.HTTPForbidden()

    uam = await get_uam_config(request.app['db'], DATA.get('profile','default'))
    uam = uam or {}

    q = dict(
        ident = ident,
        mac = DATA.get('mac').upper().replace('-',':')
        )

    updq = {
        '$set':{
            'seen':now,
            'ua': request.headers.get('User-Agent',''),
            'seen_callee': DATA.get('profile','default'),
            'vk': user
            },
        '$setOnInsert': {'registred': now, 'callee': DATA.get('profile','default')},
        #, "$set" {'sensor': request.ip }
        }

    device = await coll.find_one_and_update(q, updq, upsert=True, return_document=True)#,fields=FIELDS)
    debug(device.__repr__())

    upd = {}

    if device.get('username'):
        reg = False
    else:
        reg = True
        upd['username'] = (await setuser(request.app['db'],ident))

    if uam.get('vk_message'):
        if user.get('post_id'):
            upd['checked'] = True
            reg=True
    else:
        upd['checked'] = True
        reg=True


    if reg:
        updq = {
            '$set': upd,
        }

        device = await coll.find_one_and_update({'_id':device['_id']}, updq, return_document=True)#,fields=FIELDS)
        debug(device.__repr__())

    if device:
        if device.get('checked'):
            device['password'] = getpassw(device.get('username'), device.get('mac'))
        return device
    else:
        raise web.HTTPNotFound()
