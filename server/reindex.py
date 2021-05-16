from multiprocessing import Process

def admins(db,config):
    for (k,v) in config['API_SECRET'].items():
        yield db.administrator.find_and_modify(
            {'name':k},
            {"$setOnInsert":{'password':v,'superadmin':True}},
            upsert=True)
    config.pop('API_SECRET')



def index(config):
    import storage
    import asyncio
    db = storage.setup(
        config['DB']['SERVER'],
        config['DB']['NAME']
    )
    tasks = [
        db.counters.find_and_modify(
            {'_id':'userid'}, { '$setOnInsert': {'seq':0}}, upsert=True,new=True),

        db.counters.find_and_modify(
        {'_id':'voucher'}, { '$setOnInsert': {'seq':0}}, upsert=True,new=True),

        db.devices.ensure_index( [ ("username",1), ("mac",1) ], unique=True, sparse=True ),
        db.devices.ensure_index( [ ("phone",1), ("mac",1) ], unique=True, sparse=True ),
        db.devices.ensure_index( [ ("username",1) ], unique=False),
        db.accounting.ensure_index([ ("username",1) ], unique=False),
        db.accounting.ensure_index([ ("nas",1) ], unique=False),
        db.accounting.ensure_index([ ("callee",1) ], unique=False),
        db.voucher.ensure_index( [ ("voucher",1), ("callee",1),("closed",1) ], unique=True, sparse=True ),
        db.voucher.ensure_index( [ ("series",1)], unique=False),

        db.collector.ensure_index( [ ("first",1) ], unique=False, sparse=True),
        db.collector.ensure_index( [ ("last",1) ], unique=False, sparse=True),
        db.collector.ensure_index( [ ("dstaddr",1) ], unique=False, sparse=True),
        db.collector.ensure_index( [ ("srcaddr",1) ], unique=False, sparse=True),
        db.collector.ensure_index( [ ("sensor",1) ], unique=False, sparse=True),
        db.rad_sessions.ensure_index( [ ("stop",-1) ], unique=False),
        db.rad_sessions.ensure_index( [ ("caller",1),("callee",1)], unique=False),
    ]

    tasks.extend(admins(db,config))
    tasks = [ asyncio.ensure_future(t) for t in tasks ]
    storage.logger.info('reindexing')
    waiter = asyncio.gather(*tasks)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(waiter)




def setup(config):
    proc = Process(target=index, args=(config,))
    proc.name = 'index'
    return [proc]
