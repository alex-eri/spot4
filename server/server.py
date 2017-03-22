import logging,sys
import reindex

#sys.path.insert(0, '.')

from multiprocessing import Manager, Queue

logger = logging.getLogger('main')
debug = logger.debug

def modem_setup(config):

    procs = []
    import zte
    return zte.setup(config)
    return procs


def setup_log(config):

    if config.get('LOGFILE'):
        FORMAT = '%(asctime)s %(processName)s\%(name)-8s %(levelname)s: %(message)s'
    else:
        FORMAT = '%(processName)s\%(name)-8s %(levelname)s: %(message)s'

    level = logging.INFO
    if config.get('DEBUG'):
        level = logging.DEBUG
    else:
        level = logging.WARNING

    logging.basicConfig(format = FORMAT, level=level, filename = config.get('LOGFILE'))


def setup(services=[]):
    import api
    import radius
    import json
    manager = Manager()

    config = json.load(open('../config/config.json','r'))

    config['numbers'] = manager.list()

    services.extend( radius.setup(config) )
    services.extend( api.setup(config) )

    services.extend( modem_setup(config) )

    if config.get('NETFLOW'):
        import netflow
        services.extend(netflow.setup(config))

    return services


def main():
    import signal
    services = []

    def start():
        for proc in services:
            proc.start()

    def stop():
        for proc in services:
            proc.terminate()

    def wait(n=1):
        for proc in services:
            proc.join(n)

    def restart(*a):
        debug(a)
        stop()
        wait(5)
        while services:
            del services[0]
        setup(services)
        start()

    signal.signal(signal.SIGUSR1, restart)

    setup(services)
    start()

    sys.running = True
    while sys.running:
        try:
            wait()
        except Exception as e:
            debug(e)
            sys.running = False
            break

    stop()


def premain():
    print('starting spot4')
    import multiprocessing,os
    multiprocessing.freeze_support()
    import argparse
    import json
    import codecs

    parser = argparse.ArgumentParser(description='Spot4 Hotspot controller')
    parser.add_argument('--config-dir', nargs='?', help='Config dir')
    parser.add_argument('--reindex', action='store_true', help='Ensure indexes')
    if os.name == 'nt':
        parser.add_argument('--service',
                             dest='service', action='store_true', help='Windows service')
    args,argv = parser.parse_known_args()


    if args.config_dir:
        import utils.procutil
        utils.procutil.chdir(args.config_dir)
    
    config = json.load(codecs.open('../config/config.json','r','utf-8'))
    setup_log(config)

    p = reindex.setup(config)
    p[0].start()
    p[0].join()
    logger.info('done')

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

if "__main__" in __name__ :
    premain()


