from .decorators import json
import os

@json
async def list_templates(request):
    thedir = "../uam/theme"
    return [ name for name in os.listdir(thedir) if os.path.isdir(os.path.join(thedir, name)) ]
