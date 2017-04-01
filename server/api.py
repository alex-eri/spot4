from utils import procutil
from multiprocessing import Process, current_process

def setup_web(config):
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

    port = config.get('API_PORT',8080)

    #ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLSv1)
    #ssl_context.load_cert_chain('../config/server.pem')
    try:
        web.run_app(app,port=port)#,ssl_context=ssl_context)
    except Exception as e:
        logger.error(e)


def setup(config):
    web = Process(target=setup_web, args=(config,))
    web.name = 'web'
    return [web]
