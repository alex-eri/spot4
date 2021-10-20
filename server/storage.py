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

def ensure_obj(result,error):
    if error:
        if isinstance(error, (pymongo.errors.DuplicateKeyError)):
            return
        logger.error(error.__repr__())
        raise error


def insert_cb(result,error):
    if error:
        logger.error(error.__repr__())

def setup(mongo_uri,db_name) -> motor.motor_asyncio.AsyncIOMotorDatabase:
    client = motor.motor_asyncio.AsyncIOMotorClient(mongo_uri)
    db = client[db_name]
    return db


async def create_capped(db,name,size):
    from bson import SON
    try:
        info = await db.command(SON([('listCollections',1),('filter',{'name':name})]))
        info = info['cursor'].get('firstBatch')
        if info:
            opts = info[0]
            if abs( size - opts['options'].get('size',0)) > 4096 :
                await db.command("convertToCapped", name, size=size)
        else:
            await db.create_collection(name,capped=True,size=size)
    except Exception as error:
        logger.error(error.__repr__())

