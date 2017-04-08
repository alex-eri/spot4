from .decorators import json
import os
from aiohttp import web



async def get_uam_config(db,profile):
    default = await db.uamconfig.find_one({'_id':'default'})
    if default:
        conf = await db.uamconfig.find_one({'_id':profile})
        if conf:
            conf = {k: v for k, v in conf.items() if v or v is False }

            if not conf.get('theme',False):
                conf = {k: v for k, v in conf.items() if not k.startswith('theme_')}

            default.update(conf)
        return default

async def uam_config(request):
    profile = request.match_info.get('profile')
    config = await get_uam_config(request.app['db'],profile)
    if config:
        return config
    raise web.HTTPNotFound()



