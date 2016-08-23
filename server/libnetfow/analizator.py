import logging
logger = logging.getLogger('netflow')
debug = logger.debug

RX=1
TX=0

async def aggregate_remoteaddr(db, account):
    sensor = account['sensor']
    start = account['start_time']
    end = account['event_time']
    ip = account['ip']

    def group_remoteaddr(direction=TX):
        match = {
                    'sensor': sensor,
                    'first': {'$lte': (end+1) * 1000 },
                    'last': {'$gte': (start-1) * 1000 }
                }
        if direction == TX:
            match['srcaddr']=ip
            remote = '$dstaddr'
        else:
            match['dstaddr']=ip
            remote = '$srcaddr'

        pipe =  [
            {
                '$match': match
            },
            {
                '$group': { '_id': {'remote': remote} ,
                    'octets' : { '$sum' : '$dOctets' },
                    'pkts': { '$sum' : '$dPkts' },
                    'flows': { '$sum': 1 }
                }
            }
        ]
        debug(pipe)
        return db.collector.aggregate( pipe )

    try:
        rxc = group(RX)
        txc = group(TX)
        return  {
            'rx': await rxc.to_list(),
            'tx': await txc.to_list(),
        }
    except Exception as e:
        logger.error(e)
