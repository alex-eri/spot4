from .decorators import json
import os
from aiohttp import web
import string
import re


async def get_uam_config(db, profile):
    # profile = str(profile)
    # for c in '!"#$%&\'()*+,/:;<=>?@[\\]^`{|}~':
    # profile = profile.replace(c,'')

    profile = re.sub(r"[^0-9A-Zaz\.\-]", "", str(profile))

    default = await db.get_collection("uamconfig").find_one_and_update(
        {"_id": "default"},
        {"$setOnInsert": {"auto": True}},
        upsert=True,
        return_document=True,
    )

    conf = await db.get_collection("uamconfig").find_one({"_id": profile})
    if conf:
        conf = {k: v for k, v in conf.items() if v or v is False or v == 0}
        if not conf.get("theme", False):
            conf = {k: v for k, v in conf.items() if not k.startswith("theme_")}
    else:
        conf = await db.get_collection("uamconfig").find_one_and_update(
            {"_id": profile},
            {"$setOnInsert": {"auto": True}},
            upsert=True,
            return_document=True,
        )
        limit = await db.get_collection("limit").find_one_and_update(
            {"_id": profile},
            {"$setOnInsert": {"auto": True}},
            upsert=True,
            return_document=True,
        )
    default.update(conf)
    return default


async def uam_config(request):
    # profile = request.match_info.get('profile')
    called = request.query.get("called")
    nasid = request.query.get("nasid")
    ischilli = request.query.get("ischilli")

    if ischilli.lower() in ("true", "1", "yes", "on"):
        profile = nasid
    else:
        profile = called
    config = await get_uam_config(request.app["db"], profile)
    if config:
        return config
    raise web.HTTPNotFound()
