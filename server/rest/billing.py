from .decorators import json

@json
async def voucher(request):
    now = datetime.utcnow()
    coll = request.app['db'].voucher
    
    if 'json' in request.headers.get('Content-Type',''):
        DATA = await request.json()
    else:
        DATA = await request.post()

    q = {
        'voucher' : DATA.get('voucher'),
        'callee': DATA.get('callee')
        }

    upd = {
        'seen': now,
        'nas': DATA.get('nas'),
        'device' : DATA.get('device'),
        'username': DATA.get('username'),
        }
    updq = {
        '$set': upd
        }
    voucher = await coll.find_and_modify(q, updq, upsert=False, new=True)
    return
