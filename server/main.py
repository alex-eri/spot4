import radius
import json
import logging
import db
import api

logger = logging.getLogger('main')
debug = logger.debug

def polling_setup(config):
    ztes = config['SMS_POLLING'].get('ZTE',[])
    if ztes:
        import zte
        return zte.setup(ztes)

def setup():
    config = json.load(open('config.json','r'))
    if config.get('DEBUG'):
        logging.basicConfig(level=logging.DEBUG)

    db.setup(
        config['DB']['SERVER'],
        config['DB']['NAME']
    )

    services = []
    services.extend( radius.setup(config))
    services.extend( api.setup(config))

    if config.get('SMS_POLLING'):
        services.extend(polling_setup(config))


    return services


if __name__ == "__main__":
    import multiprocessing
    multiprocessing.freeze_support()

    services = setup()

    for proc in services:
        proc.start()

    for proc in services:
        proc.join()

    
