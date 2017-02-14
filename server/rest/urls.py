from .views import *
from .decorators import check_auth
from .decorators import json
from .admin import list_templates
from .front import uam_config
from .billing import voucher

def index_factory(path,filename):
    async def static_view(request):
        route = web.StaticResource('/', path)
        request.match_info['filename'] = filename
        return await route._handle(request)
    return static_view


def routers(app):
    app.router.add_get('/generate_204', generate_204)
    app.router.add_get('/hotspot-detect.html', hotspot_detect)

    if app['config'].get('SMS'):

        app.router.add_route('GET', '/register/+{phone:\d+}/{mac}', phone_handler)
        app.router.add_route('GET', '/register/%2B{phone:\d+}/{mac}', phone_handler)
        app.router.add_route('POST', '/register', phone_handler)

        app.router.add_route('POST', '/sms_callback', check_auth(sms_handler))

    app.router.add_route('*', '/device/{oid}', device_handler)

    app.router.add_route('POST', '/db/{collection}/{skip:\d+}/{limit:\d+}', check_auth(db_handler))
    app.router.add_route('POST', '/db/{collection}', check_auth(db_handler))

    app.router.add_get('/uam/config/{profile}.json', json(uam_config))
    app.router.add_static('/uam/theme/', path='../uam/theme', name='uam-theme')
    #app.router.add_static('/uam/config/', path='../uam/config', name='uam-config')
    app.router.add_get('/uam/{path:.*}', index_factory("../static/ht_docs/","uam.html"))


    app.router.add_get('/admin/themes.json', check_auth(list_templates))
    app.router.add_get('/admin/{path:.*}', check_auth(index_factory("../static/ht_docs/","admin.html")))
    app.router.add_static('/static/', path='../static/ht_docs/', name='static')


    app.router.add_route('*', '/billing/voucher', voucher)


    #app.router.add_route('OPTIONS', '/{path:.*}', db_options)
