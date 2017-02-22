def index(config):
    import storage
    import asyncio
    db = storage.setup(
        config['DB']['SERVER'],
        config['DB']['NAME']
    )
    tasks = [
        db.devices.ensure_index( [ ("username",1), ("mac",1) ], unique=True, sparse=True ),
        db.devices.ensure_index( [ ("phone",1), ("mac",1) ], unique=True, sparse=True ),
        db.devices.ensure_index( [ ("username",1) ], unique=False),
        db.accounting.ensure_index([ ("username",1) ], unique=False),
        db.accounting.ensure_index([ ("nas",1) ], unique=False),
        db.accounting.ensure_index([ ("callee",1) ], unique=False),
        db.voucher.ensure_index( [ ("voucher",1), ("callee",1),("closed",1) ], unique=True, sparse=True ),
        db.voucher.ensure_index( [ ("series",1)], unique=False),
    ]
    tasks = [ asyncio.ensure_future(t) for t in tasks ]
    storage.logger.info('reindexing')
    asyncio.wait(tasks)
    storage.logger.info('done')
