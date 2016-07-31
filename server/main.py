import logging,sys

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
    import api
    import radius
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

def main():
    services = setup()

    for proc in services:
        proc.start()

    sys.running = True
    while sys.running:
        try:
            for proc in services:
                proc.join(1)
        except:
            sys.running = False
            break

    for proc in services:
        proc.terminate()



if __name__ == "__main__":
    import multiprocessing,os
    multiprocessing.freeze_support()

    import argparse

    parser = argparse.ArgumentParser(description='Hotspot.')
    parser.add_argument('--config-dir', nargs='?', help='config dir')
    if os.name == 'nt':
        parser.add_argument('--service',
                             dest='service', action='store_true', help='Windows service')
    args = parser.parse_args()

    if args.config_dir:
        import utils.procutil
        utils.procutil.chdir(args.config_dir)

    if os.name == 'nt':
        import utils.win32
        if args.service :
            utils.win32.ServiceLauncher.main = classmethod(main)
            utils.win32.startservice()
        else:
            utils.win32.start()
    else:
        main()







    
