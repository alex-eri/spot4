from multiprocessing import Process

def admins(db,config):
    for (k,v) in config['API_SECRET'].items():
        yield db.get_collection('administrator').find_one_and_update(
            {'name':k},
            {"$setOnInsert":{'password':v,'superadmin':True}},
            upsert=True)
    config.pop('API_SECRET')



def index(config):
    import storage
    import asyncio
    
    import setproctitle
    setproctitle.setproctitle('reindex')
    
    db = storage.setup(
        config['DB']['SERVER'],
        config['DB']['NAME']
    )
    tasks = [
        db.get_collection('counters').find_one_and_update(
            {'_id':'userid'}, { '$setOnInsert': {'seq':0}}, upsert=True,return_document=True),

        db.get_collection('counters').find_one_and_update(
        {'_id':'voucher'}, { '$setOnInsert': {'seq':0}}, upsert=True,return_document=True),

        db.get_collection('devices').create_index( [ ("username",1), ("mac",1) ], unique=True, sparse=True ),
        db.get_collection('devices').create_index( [ ("phone",1), ("mac",1) ], unique=True, sparse=True ),
        db.get_collection('devices').create_index( [ ("username",1) ], unique=False),
        db.get_collection('accounting').create_index([ ("username",1) ], unique=False),
        db.get_collection('accounting').create_index([ ("nas",1) ], unique=False),
        db.get_collection('accounting').create_index([ ("callee",1) ], unique=False),
        db.get_collection('voucher').create_index( [ ("voucher",1), ("callee",1),("closed",1) ], unique=True, sparse=True ),
        db.get_collection('voucher').create_index( [ ("series",1)], unique=False),

        db.get_collection('collector').create_index( [ ("first",1) ], unique=False, sparse=True),
        db.get_collection('collector').create_index( [ ("last",1) ], unique=False, sparse=True),
        db.get_collection('collector').create_index( [ ("dstaddr",1) ], unique=False, sparse=True),
        db.get_collection('collector').create_index( [ ("srcaddr",1) ], unique=False, sparse=True),
        db.get_collection('collector').create_index( [ ("sensor",1) ], unique=False, sparse=True),
        db.rad_sessions.create_index( [ ("stop",-1) ], unique=False),
        db.rad_sessions.create_index( [ ("caller",1),("callee",1)], unique=False),
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
