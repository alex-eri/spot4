from multiprocessing import Process, current_process, Semaphore
import logging
import asyncio
import aiohttp
import json



def setup_reciever(db,config,clients):




def setup_loop(config):
    clients = []
    for modem in config['CALL'].get('pool',[]):
        driver = modem.get('driver', None)
        if driver:
            try:
                module = importlib.import_module('call.'+ driver)
            except:
                logger.error('driver "%s" load failed' % (driver))
                logger.error(traceback.format_exc())
                continue
        else:
            logger.error('driver not specified')
            continue

        clients.append( module.Client(**modem ))

        if modem.get('numbers',False) and modem.get('reciever',True):
            config['call_numbers'].extend(modem['numbers'])
        if modem.get('number',False) and modem.get('reciever',True):
            config['call_numbers'].append(modem['number'])


    loop = asyncio.get_event_loop()
    import storage

    db = storage.setup(
        config['DB']['SERVER'],
        config['DB']['NAME']
    )

    async def handler(modem,number,text,called_number):



    try:
        while True:
            asyncio.sleep(2)
    except (KeyboardInterrupt, SystemExit):
        for client in clients:
            client.stop()



def setup(config):
    if not (config.get('CALL') and config.get['CALL'].get('enabled')):
        return []
    caller = Process(target=setup_loop,args=(config,))
    caller.name = 'caller'
    return [caller]