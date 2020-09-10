from .decorators import json
import os
from aiohttp import web

async def get_uam_config(db,profile):
    default = await db.uamconfig.find_one({'_id':'default'})
    if default and profile.isidentifier():
        conf = await db.uamconfig.find_and_modify({'_id': profile}, {'$setOnInsert': { 'auto': True }}, upsert=True, new=False)
        if conf:
            conf = {k: v for k, v in conf.items() if v or v is False or v == 0 }
            if not conf.get('theme',False):
                conf = {k: v for k, v in conf.items() if not k.startswith('theme_')}
            default.update(conf)
        else:
            limit = await db.limit.find_and_modify( {'_id':profile} , {'$setOnInsert': { 'auto': True }}, upsert=True)
        return default

async def uam_config(request):
    profile = request.match_info.get('profile')
    config = await get_uam_config(request.app['db'],profile)
    if config:
        return config
    raise web.HTTPNotFound()



