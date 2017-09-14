import asyncio
import struct
import logging
from multiprocessing import Process, current_process
from collections import namedtuple
import threading
import time
logger = logging.getLogger('netflow')
debug = logger.debug

from utils.codecs import ip2int

FLUSHINTERVAL = 60
FLUSHLEVEL = 16<<10

FLOW5HEADER = "!HHIIII"
FLOW5DATA = "!IIIHHIIIIHHxBBBHHBBxx"

IPFIXHEADER = "!HHIII"

#srcaddr,dstaddr,nexthop,input,output,dPkts,dOctets,first,last,srcport,dstport,tcp_flags,prot,tos,as[4]

Flow5Fields =  [
    'srcaddr','dstaddr','nexthop','input','output','dPkts','dOctets','first','last',
    'srcport','dstport','tcp_flags','prot','tos','src_as','dst_as','src_mask','dst_mask'
]

Fields =  set(['sensor','sequence'] + Flow5Fields)

insert_cb = None

from utils.codecs import ip2int
from collections import defaultdict

#import numpy as np
#import pandas as pd


#TODO year 2038 problem


def aggregate(flows):
    return flows
    #df = pd.DataFrame(flows,columns=Fields,dtype='uint32')
    #return df.to_dict('records')



class Netflow5(asyncio.DatagramProtocol):

    def __init__(self,*a,**kw):
        super(Netflow5,self).__init__(*a,**kw)
        self.flows = []

        #self.flows = pd.DataFrame([],columns=Fields,dtype='uint32')

        self.flowslock = threading.Lock()
        self._waiter = asyncio.Event()
        loop = asyncio.get_event_loop()
        self._flush_future = loop.create_task(self.store())

        self.templates = defaultdict(dict)



    def datagram_received(self, data, addr):
        if data[1] == 5:
            self.nf5(data, addr)
        #elif data[1] == 10:
        #    self.ipfix(data, addr)


    def on_ipfix_data(self,sensor_ident, data,set_length):
        return -255

    def on_ipfix_template(self,sensor_ident, data,set_length):
        x=0

        def tmplt_gen(x, count):
            for i in range(count):
                yield struct.unpack_from("!HH", data, x )

        while set_length:
            ident, count = struct.unpack_from("!HH", data, x )
            x+=8
            self.templates[sensor_ident][ident] = list(tmplt_gen(x, count))
            x+=8*count

    def ipfix(self, data, addr):
        ver,count,timestamp,sequence,observation_id = struct.unpack_from(IPFIXHEADER, data)

        x = 16
        sensor = ip2int(addr[0])
        sensor_ident = (sensor,addr[1],observation_id)

        while count > 0 and x < len(data):
            ident, set_length = struct.unpack_from("!HH", data, x )
            if ident == 2:
                count -= self.on_ipfix_template(sensor_ident, data[x+4:x+set_length],set_length)
            else:
                count -= self.on_ipfix_data(sensor_ident, data[x+4:x+set_length],set_length)

            x+=set_length

    def nf5(self, data, addr):
        ver,count,uptime,timestamp,nanosecs,sequence = struct.unpack_from(FLOW5HEADER, data)

        delta = timestamp*1000 + nanosecs//1000000 - uptime

        sensor = ip2int(addr[0])

        def flow_gen():
            for i in range(count):
                x = list(struct.unpack_from(FLOW5DATA, data, i*48 + 24))
                x[7] = (x[7] + delta) // 1000
                x[8] = (x[8] + delta) // 1000
                flow = dict(zip(Flow5Fields,x))
                #flow['first'] += delta
                #flow['last'] += delta

                flow.update({'sensor': sensor , 'sequence': sequence + i })
                yield flow

        with  self.flowslock:
            #self.flows = self.flows.append(list(flow_gen()), ignore_index=True)
            self.flows.extend(flow_gen())

        #debug('{} collected {}'.format(addr[0],len(self.flows)))

        if len(self.flows) > FLUSHLEVEL:
            self._waiter.set()

    async def store_once(self):
        with self.flowslock:
            flows,self.flows = self.flows, []
            #del self.flows[:]
            #self.flows = pd.DataFrame([],columns=Fields,dtype='uint32')
        #l = len(flows)
        #debug('colected {}'.format(l))
        if flows:
            flows = aggregate(flows)
            a = await self.collector.insert(flows)
            debug('inserted {}'.format(len(a)))

    async def store(self):
        while True:
            try:
                await asyncio.wait_for(self._waiter.wait(), timeout=FLUSHINTERVAL)
            except asyncio.TimeoutError:
                pass
            try:
                await self.store_once()
            except Exception as e:
                logger.error(e)
            self._waiter.clear()


def run5(config):
    global insert_cb
    import storage
    insert_cb = storage.insert_cb

    HOST = config.get('RADIUS_IP','0.0.0.0')
    PORT = config.get('NETFLOW_PORT', 2055)

    SIZE = config.get('NETFLOW_SIZE', 2000) << 20


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

    try:
        loop.run_forever()
    except Exception as e:
        logger.error(repr(e))
    finally:
        t = server.store_once()
        loop.run_until_complete(t)
        transport.close()
        loop.close()

def setup5(config):
    proc = Process(target=run5, args=(config,))
    proc.name = 'netflow.5'
    return [proc]


def setup(config):
    services = []
    if 5 in config.get('NETFLOW'):
        services.extend(setup5(config))
    return services

def main():
    import json
    config = json.load(open('config.json','r'))
    run5(config)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    main()
