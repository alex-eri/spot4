from aiohttp import web
import hashlib


async def xbillorg(request):
    cfg = request.app['config']
    params = request.query
    ok = False
    coll = request.app['db'].devices

    for sender in   cfg["SMS"]['pool'] if sender['driver'] == 'xbillorg':
        if hashlib.md5(
                (params['order']+ params['phone'] +params['merchant_price'] +secret).encode()
                ).hexdigest() == params['sign']:
            ok = True

    if ok:
        if params['order_status'] == "success":
            device =  params['order_id']
            await coll.find_and_modify({'_id': device}, {'$set':{'checked': True} }, new=True)

        return web.Response(
            body=b"ok",
            content_type='text/html')
