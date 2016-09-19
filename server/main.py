import logging,sys
from multiprocessing import Manager, Queue

logger = logging.getLogger('main')
debug = logger.debug

def modem_setup(config):

    procs = []
    import zte
    return zte.setup(config)
    return procs

def setup():
    import api
    import radius
    import json
    manager = Manager()
    smsq = Queue()


    config = json.load(open('config.json','r'))
    FORMAT = '%(asctime)s %(processName)s\%(name)-8s %(levelname)s: %(message)s'

    level = logging.WARNING
    if config.get('DEBUG'):
        level = logging.DEBUG

    logging.basicConfig(format = FORMAT, level=level, filename = config.get('LOGFILE'))

    config['numbers'] = manager.list()

    services = []
    services.extend( radius.setup(config) )
    services.extend( api.setup(config) )

    services.extend( modem_setup(config) )

    if config.get('NETFLOW'):
        import netflow
        services.extend(netflow.setup(config))

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

    parser = argparse.ArgumentParser(description='Spot4 Hotspot controller')
    parser.add_argument('--config-dir', nargs='?', help='config dir')
    if os.name == 'nt':
        parser.add_argument('--service',
                             dest='service', action='store_true', help='Windows service')
    args,argv = parser.parse_known_args()

    if args.config_dir:
        import utils.procutil
        utils.procutil.chdir(args.config_dir)

    if os.name == 'nt':
        import utils.win32
        if args.service:
            utils.win32.startservice(sys.modules[__name__])
        else:

            exeargs = sys.argv[1:]
            for i in argv:
                exeargs.remove(i)

            argv.insert(0,sys.argv[0])
            print(argv)
            print(exeargs)

            utils.win32.start(sys.modules[__name__],  argv, exeargs)
    else:
        main()







    
