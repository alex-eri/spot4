def index(config):
    import storage
    db = storage.setup(
        config['DB']['SERVER'],
        config['DB']['NAME']
    )

    db.devices.ensure_index( [ ("username",1), ("mac",1) ], unique=True, sparse=True ,callback=storage.index_cb)
    db.devices.ensure_index( [ ("phone",1), ("mac",1) ], unique=True, sparse=True ,callback=storage.index_cb)
    db.devices.ensure_index( [ ("username",1) ], unique=False, callback=storage.index_cb)

    db.accounting.ensure_index([ ("username",1) ], unique=False, callback=storage.index_cb)
    db.accounting.ensure_index([ ("nas",1) ], unique=False, callback=storage.index_cb)
    db.accounting.ensure_index([ ("callee",1) ], unique=False, callback=storage.index_cb)

