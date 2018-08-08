from .decorators import json
import os
import signal
from .logger import *

from aiohttp import web

@json
async def list_templates(request):
    thedir = "../uam/theme"
    return [ name for name in os.listdir(thedir) if os.path.isdir(os.path.join(thedir, name)) ]


@json
async def config(request):

    if request.administrator.get('filters'):
        conf = {}
        #conf['numbers'] = [ i for i in request.app['config'].get('numbers',[])]
        return {'response': conf}

    conf = request.app['config'].copy()
    #conf['numbers'] = [ i for i in request.app['config'].get('numbers',[])]
    #conf['call_numbers'] = [ i for i in request.app['config'].get('call_numbers',[])]

    conf['numbers'] = await request.app['db'].numbers.find({'sms_recv':True}).to_list(length=1000)

    return {'response': conf}



@json
async def kill(request):
    if request.administrator.get('filters'):
        raise web.HTTPForbidden()

    if os.name == 'posix':
        ppid = os.getppid()
        debug(ppid)
        os.kill(ppid, signal.SIGUSR1)
        return {'response':'ok'}
    return {'error':'unimplemented in '+os.name}

@json
async def whoami(request):
    return {'response':request.administrator}
