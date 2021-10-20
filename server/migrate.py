import asyncio,logging
logger = logging.getLogger('migration')
debug = logger.debug
info = logger.info

from server import setup_log

if __name__ == "__main__":
    import storage
    import json
    config = json.load(open('../config/config.json','r'))
    setup_log(config)
    db = storage.setup(
        config['DB']['SERVER'],
        config['DB']['NAME']
    )

    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(db.get_collection('devices').drop_indexes())
        loop.run_until_complete(db.get_collection('accounting').drop_indexes())
        loop.run_until_complete(db.get_collection('voucher').drop_indexes())
    except Exception as e:
        logger.critical(e.__repr__())
        raise e
    finally:

        import reindex
        reindex.index(config)
        #loop.close()
