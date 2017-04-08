from multiprocessing import Process

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
        db.collector.ensure_index( [ ("first",1)], unique=False),
        db.collector.rad_sessions( [ ("stop",-1)], unique=False),
        db.collector.rad_sessions( [ ("caller",1),("callee",1)], unique=False),
    ]
    tasks = [ asyncio.ensure_future(t) for t in tasks ]
    storage.logger.info('reindexing')
    asyncio.wait(tasks)



def setup(config):
    proc = Process(target=index, args=(config,))
    proc.name = 'index'
    return [proc]
