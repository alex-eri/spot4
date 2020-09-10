import aiohttp

async def smsru_call(key, phone):
    key = key.split('::', 1)[-1]
    phone = phone.strip('+')

    params = dict(api_id=key, phone=phone, json=1)

    async with aiohttp.ClientSession() as session:
        async with session.get('https://sms.ru/callcheck/add', params=params) as resp:
            resp = await resp.json()
            if int(resp.get('status_code')) == 100:
                return resp.get('call_phone', None), dict(api_id=key, check_id=resp.get('check_id', None), json=1)
            else:
                return None, {}


async def smsru_check(key):
    params = dict(key)
    params['json'] = 1

    async with aiohttp.ClientSession() as session:
        async with session.get('https://sms.ru/callcheck/status', params=params) as resp:
            resp = await resp.json()
            if int(resp.get('check_status')) == 401:
                return True
