from .decorators import json
import os
from aiohttp import web



async def get_uam_config(request,profile):
    default = await request.app['db'].uamconfig.find_one({'_id':'default'})
    if default:
        conf = await request.app['db'].uamconfig.find_one({'_id':profile})
        if conf:
            conf = {k: v for k, v in conf.items() if v or v is False }
            default.update(conf)
        return default

async def uam_config(request):
    profile = request.match_info.get('profile')
    config = await get_uam_config(request,profile)
    if config:
        return config
    raise web.HTTPNotFound()


