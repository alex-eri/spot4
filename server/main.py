import radius
import logging
import api

logger = logging.getLogger('main')
debug = logger.debug

SALT = b'441dbf23b4d344f19b89c76fd65cc75c'

def polling_setup(config):
    ztes = config['SMS_POLLING'].get('ZTE',[])
    procs = []
    if ztes:
        import zte
        return zte.setup(config)
    return procs

def setup():
    import json
    config = json.load(open('config.json','r'))
    if config.get('DEBUG'):
        logging.basicConfig(level=logging.DEBUG)

    config['SALT'] = SALT
    config['SALT_ASCII'] = SALT.decode()

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

    
