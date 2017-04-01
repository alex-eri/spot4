from .decorators import json
import os
import signal
from .logger import *

@json
async def list_templates(request):
    thedir = "../uam/theme"
    return [ name for name in os.listdir(thedir) if os.path.isdir(os.path.join(thedir, name)) ]


@json
async def config(request):

    conf = request.app['config'].copy()
    conf['numbers'] = [ i for i in request.app['config'].get('numbers',[])]

    return {'response': conf}



@json
async def kill(request):
    if os.name == 'posix':
        ppid = os.getppid()
        debug(ppid)
        os.kill(ppid, signal.SIGUSR1)
        return {'response':'ok'}
    return {'error':'unimplemented in '+os.name}
