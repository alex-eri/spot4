import motor.motor_asyncio
import logging
import pymongo.errors

logger = logging.getLogger('db')
debug = logger.debug

def index_cb(result,error):
    debug('index done')
    if error:
        logger.error(error.__repr__())
        raise error

def insert_cb(result,error):
    if error:
        logger.error(error.__repr__())

def setup(mongo_uri,db_name):
    client = motor.motor_asyncio.AsyncIOMotorClient(mongo_uri)
    db = client[db_name]
    return db


async def create_capped(db,name,size):
    try:
        if name in await db.collection_names():
            await db.command("convertToCapped", name, size=size)
        else:
            await db.create_collection(name,capped=True,size=size)
    except Exception as error:
        logger.error(error.__repr__())

    
