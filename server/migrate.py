import asyncio,logging
logger = logging.getLogger('migration')
debug = logger.debug
info = logger.info

async def login2hash(db):
    import hashlib
    from main import SALT
    print(SALT)


    try:
        await db.devices.drop_index("login_1_mac_1")
        await db.devices.drop_index("login_1")
    except:
        pass

    async for d in db.devices.find( {"login": {"$ne" : None}} ):
        print(d)
        m = hashlib.md5()
        m.update(SALT)
        m.update(d['login'].encode('ascii'))
        h = m.hexdigest()

        r = await db.devices.update({'_id':d['_id']}, {
            "$unset":{'login':''},
            "$set":{
                "phone":d['login'],
                "phonehash": h,
                "username": d.get('username',h)
            } } )
        print(r)



if __name__ == "__main__":
    import storage
    import json
    config = json.load(open('config.json','r'))
    db = storage.setup(
        config['DB']['SERVER'],
        config['DB']['NAME']
    )

    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(login2hash(db))
    except Exception as e:
        logger.critical(e.__repr__())
        raise e
    finally:
        loop.close()
