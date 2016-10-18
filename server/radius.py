from multiprocessing import Process, current_process
import logging
import os
from utils import procutil
import asyncio
import socket
from literadius.protocol import RadiusProtocol

logger = logging.getLogger('radius')
debug = logger.debug
TTL = 56

def setup_radius(config,PORT):

    name = current_process().name
    procutil.set_proc_name(name)
    debug("{}`s pid is {}".format(name, os.getpid()))

    loop = asyncio.get_event_loop()

    import storage
    db = storage.setup(
        config['DB']['SERVER'],
        config['DB']['NAME']
    )

    db.accounting.ensure_index([ ("username",1) ], unique=False, callback=storage.index_cb)

    HOST = config.get('RADIUS_IP','0.0.0.0')

    RadiusProtocol.radsecret = config.get('RADIUS_SECRET','testing123').encode('ascii')
    RadiusProtocol.db = db

    t = asyncio.Task(loop.create_datagram_endpoint(
        RadiusProtocol, local_addr=(HOST,PORT)))

    transport, server = loop.run_until_complete(t)

    sock = transport.get_extra_info('socket')
    sock.setsockopt(socket.SOL_IP, socket.IP_TTL, TTL)

    try:
        loop.run_forever()
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
