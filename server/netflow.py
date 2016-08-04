import asyncio
import struct
import logging
from multiprocessing import Process, current_process
logger = logging.getLogger('netflow')
debug = logger.debug

FLOW5HEADER = "!HHIIII"
FLOW5 = "!IIIHHIIIIHHxBBBHHBBxx"

#srcaddr,dstaddr,nexthop,input,output,dPkts,dOctets,first,last,srcport,dstport,tcp_flags,prot,tos,as[4]

insert_cb = None

async def aggregate(db, nasip, account):
    debug(nasip)
    debug(account)
    debug("!"*100)

    db.collector.group({'sensor':nasip,'flow.0':178488283})
    #c = await db.collector.aggregate()


class Netflow5:
    def connection_made(self, transport):
        #self.transport = transport
        pass

    def datagram_received(self, data, addr):
        self.caller = addr
        debug(addr)
        debug(len(data))
        ver,count,uptime,time,nanosecs,sequence = struct.unpack_from(FLOW5HEADER, data)
        debug([ver,count,uptime,time,sequence])

        delta = time*1000 + nanosecs//1000000 - uptime

        flows = []

        for i in range(count):
            x = struct.unpack_from(FLOW5, data, i*48 + 24)
        #for x in struct.iter_unpack(FLOW5, data[24:]):
            flow = list(x)
            flow[7] += delta #start
            flow[8] += delta #stop
            debug(flow)
            flows.append({'flow':flow, 'sensor': addr[0] , 'sequence': sequence + i })

        self.collector.insert(flows, callback=insert_cb)


    def respond(self,resp):
        #self.transport.sendto(resp, self.caller)
        pass

    def error_received(self, exc):
        #debug('Error received:', exc)
        pass

    def connection_lost(self, exc):
        #debug('stop', exc)
        pass

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

    t = asyncio.Task(loop.create_datagram_endpoint(
        Netflow5, local_addr=(HOST,PORT)))

    transport, server = loop.run_until_complete(t)
    try:
        loop.run_forever()
    finally:
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
