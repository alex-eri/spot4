from .decorators import json
import os
from aiohttp import web

@json
async def uam_config(request):
    profile = request.match_info.get('profile')
    conf = await request.app['db'].uamconfig.find_one({'_id':profile})
    default = await request.app['db'].uamconfig.find_one({'_id':'default'})
    if default:
        if conf: default.update(conf)
        return default
    raise web.HTTPNotFound()
