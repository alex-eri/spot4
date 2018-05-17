import logging,sys
import reindex

#sys.path.insert(0, '.')

from multiprocessing import Manager

logger = logging.getLogger('main')
debug = logger.debug

manager = Manager()

def modem_setup(config):

    procs = []
    import zte
    return zte.setup(config)
    return procs


def lic(config, module):
    lic = config.get('LIC')

    signature = None

    if lic:
        digest,signature = lic.split("::")

    if signature:

        pubkey = b"""-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEArYI6YEadMmtOVRODBIZ1
py774embTyz7evat+vp31J0roayn2MugIcfBxOW/Kv9Aei5VAQ6uuozXykbfJGlx
IMv9XQ7HtQkzF//DHAbq/ir3XE3gB6DSil9MxqceJlnYWJKNAVKlfkb2+j3sustx
v1pRajn35IVuZbhtg5xtc/kyFb7nrPcYWW0QJ53/Ybd4OC8i/RQAqjxtDYpgTkqq
JlvAnH0PJ4um4HvaY4myG31cFjzLM1YmFOAp0hWMkP9PPMS+UvvufPMHl3oPEqKH
c/Xp/QAhzxT35SPhzNQRxLls33pelKY/8L0oxpnGiRin1FKVEn0orQfW06ox87TF
3wIDAQAB
-----END PUBLIC KEY-----"""
        from base64 import b64decode
        signature = b64decode(signature)
        digest = digest.encode('utf-8')

        from ctypescrypto.pkey import PKey
        verifier=PKey(pubkey=pubkey)
        if verifier.verify(digest,signature):
            logger.info('Lic ok')
            return

    if module == "radius":
        import radius
        radius.TTL = 2
        radius.SESSIONLIMIT = 600

    elif module == "zte":
        import zte
        zte.INTERVAL = 30
    logger.warning('No Lic')



def setup_log(config):

    if config.get('LOGFILE'):
        FORMAT = '%(asctime)s %(processName)s\%(name)-8s %(levelname)s: %(message)s'
    else:
        FORMAT = '%(processName)s\%(name)-8s %(levelname)s: %(message)s'

    level = logging.INFO

    debug_level = config.get('DEBUG')

    if type(debug_level) == int:
            level = debug_level
    elif debug_level:
        level = logging.DEBUG
    else:
        level = logging.WARNING



    logfile = config.get('LOGFILE', None)

    #TODO https://docs.python.org/3/howto/logging-cookbook.html#logging-to-a-single-file-from-multiple-processes
    logging.basicConfig(format = FORMAT, level=level, filename = logfile )

def setup(services=[],args=None):
    import api
    import radius
    import json
    import codecs
    import caller

    config = json.load(codecs.open('../config/config.json','r','utf-8'))

    config['numbers'] = manager.list()
    config['call_numbers'] = manager.list()

    if args.noreindex :
        logger.info('no reindexing')
    else:
        p = reindex.setup(config)
        p[0].start()
        p[0].join()
        logger.info('done')

    services.extend( radius.setup(config) )
    services.extend( api.setup(config) )

    services.extend( modem_setup(config) )

    services.extend( caller.setup(config) )

    if config.get('NETFLOW'):
        import netflow
        services.extend(netflow.setup(config))

    return services


def main(args=None):

    import signal,os
    from multiprocessing import Lock

    restart_lock = Lock()

    services = []

    def start(*a):
        for proc in services:
            proc.start()

    def stop(*a):
        for proc in services:
            if proc.is_alive():
                if os.name == 'posix':
                    os.kill(proc.pid, signal.SIGINT)
                elif os.name == 'nt':
                    os.kill(proc.pid, signal.CTRL_C_EVENT)
                    os.kill(proc.pid, signal.CTRL_C_EVENT)

    def kill(*a):
        for proc in services:
            debug('terminate %s' % proc.name)
            proc.terminate()

    def wait(n=1):
        for proc in services:
            proc.join(n)

    def restart(*a):
        restart_lock.acquire()
        #stop()
        #wait(10)
        kill()
        wait(10)
        while services:
            del services[-1]
        setup(services,args=args)
        start()
        restart_lock.release()

    if os.name == 'posix':
        signal.signal(signal.SIGUSR1, restart)


    setup(services,args=args)
    start()

    sys.running = True
    while sys.running:
        try:
            wait()
        except Exception as e:
            logger.error(e)
            sys.running = False
            break

    kill()


def premain():
    print('starting spot4')
    import multiprocessing,os
    multiprocessing.freeze_support()
    import argparse

    parser = argparse.ArgumentParser(description='Spot4 Hotspot controller')
    parser.add_argument('--config-dir', nargs='?', help='Config dir')
    parser.add_argument('--reindex', action='store_true', help='Ensure indexes')

    parser.add_argument('--noreindex', action='store_true', help='Fast start')

    if os.name == 'nt':
        parser.add_argument('--service',
                             dest='service', action='store_true', help='Windows service')
        parser.add_argument('--fg',
                             dest='fg', action='store_true', help='Windows foreground')
    args,argv = parser.parse_known_args()


    import utils.procutil
    if args.config_dir:
        utils.procutil.chdir(args.config_dir)
    else:
        if getattr(sys, 'frozen', False):
            # frozen
            print('frozen')
            dir_ = os.path.dirname(sys.executable)
        else:
            # unfrozen
            dir_ = os.path.dirname(os.path.realpath(__file__))
        utils.procutil.chdir(
            dir_
            )

    print(dir_)

    import json,codecs
    config = json.load(codecs.open('../config/config.json','r','utf-8'))
    setup_log(config)


    if os.name == 'nt':
        if args.fg:
            main(args)
        if args.service:
            import utils.windows
            utils.windows.startservice(sys.modules[__name__])
        else:
            exeargs = sys.argv[1:]
            for i in argv:
                exeargs.remove(i)

            argv.insert(0,sys.argv[0])
            print(argv)
            print(exeargs)
            import utils.windows
            utils.windows.start(sys.modules[__name__],  argv, exeargs)
    else:
        main(args)

if "__main__" in __name__ :
    premain()


