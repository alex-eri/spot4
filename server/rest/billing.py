from .decorators import json
from .logger import *
import uuid
import hashlib
import random
import bson
from datetime import datetime, timedelta

CHARS = 8
V_COUNT = 200
RANDOM_RANGE = 10**CHARS


async def addinvoice(db, device, uam):
    print("+" * 20)
    print(db, device, uam)
    now = datetime.utcnow()
    print(now)

    invoice = await db.get_collection("invoice").find_one(
        {
            "callee": uam["_id"],
            "username": device["username"],
            "paid": True,
            "start": {"$lte": now},
            "stop": {"$gt": now},
        }
    )
    print(invoice)
    if invoice:
        pass
    else:

        tarif = await db.get_collection("tarif").find_one({"_id": uam["tarif"]})
        print(tarif)

        if tarif.get("duration", 0) > 0:
            stop = now + timedelta(days=tarif["duration"])
        else:
            stop = 0

        invoice = await db.get_collection("invoice").insert_one(
            {
                "username": device["username"],
                "paid": True,
                "start": now,
                "stop": stop,
                "voucher": None,
                "tarif": tarif["_id"],
                "limit": tarif.get("limit", {}),
                "callee": uam["_id"],
            }
        )
        print(invoice)

    return invoice


@json
async def voucher(request):
    # TODO обернуть в транзакцию
    now = datetime.utcnow()
    coll = request.app["db"].voucher

    if "json" in request.headers.get("Content-Type", ""):
        DATA = await request.json()
    else:
        DATA = await request.post()

    callee = DATA.get("callee")

    q = {
        "voucher": DATA.get("voucher"),
        "callee": {"$in": [callee, "default"]},
        "invoiced": {"$exists": False},
        "closed": {"$gt": now},
    }

    upd = {
        "invoiced": now,
        "nas": DATA.get("nas"),
        "device": DATA.get("device"),
        "username": DATA.get("username"),
    }
    updq = {"$set": upd}
    voucher = await coll.find_one_and_update(
        q, updq, upsert=False, return_document=True
    )
    if voucher:
        tarif = await request.app["db"].tarif.find_one({"_id": voucher["tarif"]})
        invoices = request.app["db"].invoice

        if tarif.get("duration") > 0:
            stop = now + timedelta(days=tarif["duration"])
        else:
            stop = 0

        q = {
            "username": voucher["username"],
            "paid": True,
            "start": now,
            "stop": stop,
            "voucher": voucher["_id"],
            "tarif": tarif["_id"],
            "limit": tarif.get("limit", {}),
            "callee": callee,
        }

        debug(type(voucher["_id"]))
        invoice = await invoices.insert_one(q)

        return invoice.inserted_id

    return {"error": "wrongcode"}


async def nextseries(db):
    n = await db.get_collection("counters").find_one_and_update(
        {"_id": "voucher"}, {"$inc": {"seq": 1}}, return_document=True
    )
    return n.get("seq")


@json
async def generate(request):
    if "json" in request.headers.get("Content-Type", ""):
        DATA = await request.json()
    else:
        DATA = await request.post()

    db = request.app["db"]

    series = await nextseries(db)
    till = datetime.utcnow() + timedelta(days=DATA.get("expire", 32))

    q = {
        "tarif": bson.ObjectId(DATA.get("tarif")),
        "callee": DATA.get("callee"),
        "series": series,
        "closed": till,
    }

    datas = []

    codes = set()

    while len(codes) < V_COUNT:
        codes.add(random.randrange(RANDOM_RANGE))

    for r in codes:
        a = {"voucher": str(r).zfill(CHARS)}
        a.update(q)
        datas.append(a)

    await db.get_collection("voucher").insert_many(datas)

    return q


@json
async def close(request):
    if "json" in request.headers.get("Content-Type", ""):
        DATA = await request.json()
    else:
        DATA = await request.post()

    db = request.app["db"]

    q = {"series": series}

    return await db.get_collection("voucher").update(
        q, {"$set": {"closed": True}}, multi=True
    )
