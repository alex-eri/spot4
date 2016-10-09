import asyncio,logging
logger = logging.getLogger('migration')
debug = logger.debug
info = logger.info

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
        loop.run_until_complete(db.devices.drop_indexes())
        loop.run_until_complete(db.accounting.drop_indexes())
    except Exception as e:
        logger.critical(e.__repr__())
        raise e
    finally:
        loop.close()
