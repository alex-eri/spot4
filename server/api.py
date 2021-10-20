from utils import procutil
from multiprocessing import Process, current_process


def setup_redirector(config, port=8082):
    import setproctitle
    setproctitle.setproctitle('captive')
    from rest.redirector import main
    import asyncio
    asyncio.get_event_loop().run_until_complete(main(port))


def setup_web(config, https=False, port=8080):
    import setproctitle
    setproctitle.setproctitle('web')
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

    debug('starting webapp')

    app = web.Application()
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

    port = config.get('HTTP_PORT', 8080)
    apple_port = config.get('APPLE_PORT', 8082)

    if apple_port:
        redirector = Process(target=setup_redirector, args=(config, apple_port))
        redirector.name = 'redirector'
        procs.append(redirector)
        """
:global portal 192.168.117.2

/ip firewall nat
add action=dst-nat chain=dstnat dst-address=$portal dst-port=80 \
    protocol=tcp to-addresses=$portal to-ports=8082


        """


    if port:
        web = Process(target=setup_web, args=(config, False,port))
        web.name = 'http'
        procs.append(web)

    port = config.get('HTTPS_PORT', False)
    if port:
        web = Process(target=setup_web, args=(config, True, port))
        web.name = 'https'
        procs.append(web)

    return procs
