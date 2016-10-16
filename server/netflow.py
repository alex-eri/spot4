import asyncio
import struct
import logging
from multiprocessing import Process, current_process
from collections import namedtuple
import threading
import time
logger = logging.getLogger('netflow')
debug = logger.debug

FLUSHINTERVAL = 15
FLUSHLEVEL = 4096

FLOW5HEADER = "!HHIIII"
FLOW5DATA = "!IIIHHIIIIHHxBBBHHBBxx"

#srcaddr,dstaddr,nexthop,input,output,dPkts,dOctets,first,last,srcport,dstport,tcp_flags,prot,tos,as[4]

Flow5Fields =  [
    'srcaddr','dstaddr','nexthop','input','output','dPkts','dOctets','first','last',
    'srcport','dstport','tcp_flags','prot','tos','src_as','dst_as','src_mask','dst_mask'
]

insert_cb = None

class Netflow5(asyncio.DatagramProtocol):

    def __init__(self,*a,**kw):
        super(Netflow5,self).__init__(*a,**kw)
        self.flows = []
        self.flowslock = threading.Lock()

    def datagram_received(self, data, addr):
        debug(addr)
        assert data[1] == 5
        ver,count,uptime,timestamp,nanosecs,sequence = struct.unpack_from(FLOW5HEADER, data)

        delta = timestamp*1000 + nanosecs//1000000 - uptime

        def flow_gen():
            for i in range(count):
                x = struct.unpack_from(FLOW5DATA, data, i*48 + 24)
                flow = dict(zip(Flow5Fields,x))
                flow['first'] += delta
                flow['last'] += delta
                flow.update({'sensor': addr[0] , 'sequence': sequence + i })
                yield flow

        with  self.flowslock:
            self.flows.extend(flow_gen())

        if len(self.flows) > FLUSHLEVEL:
            loop.call_soon(self.store_once)

        debug('collected {}'.format(len(self.flows)))


    def store_once(self):
        with self.flowslock:
            flows = self.flows[:]
            del self.flows[:]

        self.collector.insert(flows, callback=insert_cb)
        debug('inserted {}'.format(len(flows)))

    def store(self):
        loop = asyncio.get_event_loop()
        self.store_once()
        loop.call_later(FLUSHINTERVAL,self.store)

def run5(config):
    global insert_cb
    import storage
    insert_cb = storage.insert_cb

    HOST = config.get('RADIUS_IP','0.0.0.0')
    PORT = config.get('NETFLOW_PORT', 2055)

    SIZE = config.get('NETFLOW_SIZE', 2000) << 20

    print(SIZE)

    db = storage.setup(
        config['DB']['SERVER'],
        config['DB']['NAME']
    )

    loop = asyncio.get_event_loop()

    t = asyncio.Task(storage.create_capped(db,"collector",SIZE))
    loop.run_until_complete(t)

    Netflow5.collector = db.collector

    debug("starting")

    t = asyncio.Task(loop.create_datagram_endpoint(
        Netflow5, local_addr=(HOST,PORT)))

    debug("task set")
    transport, server = loop.run_until_complete(t)
    debug("started")

    loop.call_later(FLUSHINTERVAL,server.store)
    debug("flush sheduled")


    try:
        loop.run_forever()
    except Exception as e:
        logger.error(repr(e))
    finally:
        server.store_once()
        transport.close()
        loop.close()

def setup5(config):
    proc = Process(target=run5, args=(config,))
    proc.name = 'netflow.5'
    return [proc]


def setup(config):
    if 5 in config.get('NETFLOW'):
        return setup5(config)
    return []

def main():
    import json
    config = json.load(open('config.json','r'))
    run5(config)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    main()
