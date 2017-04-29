from utils import procutil
from multiprocessing import Process, current_process

def setup_web(config, https=False, port=8080):
    name = current_process().name
    procutil.set_proc_name(name)

    from aiohttp import web

    import storage
    import asyncio
    import rest.urls

    import ssl
    import logging

    logger = logging.getLogger('http')
    debug = logger.debug


    db = storage.setup(
        config['DB']['SERVER'],
        config['DB']['NAME']
    )
    loop = asyncio.get_event_loop()

    debug('starting webapp')




    app = web.Application(loop=loop)
    app['db'] = db
    app['config'] = config
    app.logger = logger

    rest.urls.routers(app)


    if https:
        try:

            ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLSv1)
            ssl_context.load_cert_chain('../config/server.pem')
            web.run_app(app,port=port,ssl_context=ssl_context)
        except Exception as e:
            logger.critical(e)

    else:
        try:
            web.run_app(app,port=port)
        except Exception as e:
            logger.critical(e)

def setup(config):
    procs = []

    port = config.get('HTTP_PORT',8080)
    if port:
        web = Process(target=setup_web, args=(config,False,port))
        web.name = 'http'
        procs.append(web)

    port = config.get('HTTPS_PORT',False)
    if port:
        web = Process(target=setup_web, args=(config,True,port))
        web.name = 'https'
        procs.append(web)

    return procs
