from multiprocessing import Process, current_process
import logging


logger = logging.getLogger('radius')
debug = logger.debug
TTL = 56
BILLING = False
SESSIONLIMIT = False


async def close_sessions(db):
    import literadius.constants as rad
    return await db.accounting.update(
                {'termination_cause':{'$exists': False}},
                {'$set':{'termination_cause': rad.TCAdminReboot}},
                multi=True
            )


def setup_radius(config, PORT):
    import asyncio
    import uvloop
    uvloop.install()
    
    from literadius.protocol import RadiusProtocol

    from utils import procutil
    import socket
    import os
    import storage

    name = current_process().name
    procutil.set_proc_name(name)
    debug("{}`s pid is {}".format(name, os.getpid()))

    loop = asyncio.get_event_loop()

    from server import lic
    lic(config,"radius")

    db = storage.setup(
        config['DB']['SERVER'],
        config['DB']['NAME']
    )

    t = asyncio.Task(close_sessions(db))
    closed = loop.run_until_complete(t)

    logger.info('{nModified}/{n} sessions closed'.format(**closed))

    HOST = config.get('RADIUS_IP','0.0.0.0')

    RadiusProtocol.radsecret = config.get('RADIUS_SECRET','testing123').encode('ascii')
    RadiusProtocol.db = db
    RadiusProtocol.loop = loop
    RadiusProtocol.session_limit = SESSIONLIMIT

    t = asyncio.Task(loop.create_datagram_endpoint(
        RadiusProtocol, local_addr=(HOST,PORT)))

    transport, server = loop.run_until_complete(t)

    sock = transport.get_extra_info('socket')
    sock.setsockopt(socket.SOL_IP, socket.IP_TTL, TTL)

    try:
        loop.run_forever()
    except Exception as e:
        import traceback
        logger.critical(e)
        logger.error(traceback.format_exc())
    finally:
        transport.close()
        loop.close()


def setup(config):

    acct = Process(target=setup_radius, args=(config, config.get('ACCT_PORT', 1813)))
    acct.name = 'radius.acct'

    auth = Process(target=setup_radius, args=(config, config.get('AUTH_PORT', 1812)))
    auth.name = 'radius.auth'

    return [acct,auth]



def main():
    import json
    config = json.load(open('config.json','r'))

    servers = setup(config)

    for proc in servers:
        proc.start()

    for proc in servers:
        proc.join()


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    main()
