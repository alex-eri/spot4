import motor.motor_asyncio

client = None
db = None

import logging
logger = logging.getLogger('db')
debug = logger.debug

def index_cb(result,error):
    debug('index done')
    if error:
        logger.error(error.__repr__())
        raise error


def setup(mongo_uri,db_name):
    global client, db
    client = motor.motor_asyncio.AsyncIOMotorClient(mongo_uri)
    db = client[db_name]
    return db
