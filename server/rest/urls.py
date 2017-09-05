from .views import *
from .decorators import check_auth
from .decorators import json
from .admin import list_templates, config,kill,whoami
from .front import uam_config
from .billing import voucher, generate

from .vk import vk_handler

from .netflow import *

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
        app.router.add_route('POST', '/register/phone', phone_handler)

        app.router.add_route('POST', '/register/vk', vk_handler)

        app.router.add_route('POST', '/sms_callback', check_auth(sms_handler))

    app.router.add_route('*', '/device/{oid}', device_handler)

    app.router.add_route('POST', '/db/{collection}/{skip:\d+}/{limit:\d+}', check_auth(db_handler))
    app.router.add_route('POST', '/db/{collection}', check_auth(db_handler))

    app.router.add_get('/config/uam/{profile}.json', json(uam_config))
    app.router.add_static('/uam/theme/', path='../uam/theme', name='uam-theme')
    app.router.add_get('/uam/{path:.*}', index_factory("../static/","uam.html"))


    app.router.add_get('/admin/themes.json', check_auth(list_templates))

    app.router.add_get('/admin/config.json', check_auth(config))
    app.router.add_post('/admin/kill', check_auth(kill))
    app.router.add_post('/admin/whoami', check_auth(whoami))
    app.router.add_post('/admin/voucher/create.json', check_auth(generate))

    app.router.add_get('/admin/{path:.*}', check_auth(index_factory("../static/","admin.html")))

    app.router.add_static('/static/', path='../static/', name='static')
    app.router.add_static('/data/', path='../data/', name='static-data')

    app.router.add_route('POST', '/billing/voucher', voucher)


    app.router.add_route('POST', '/netflow/sensors', get_sensors)
    app.router.add_route('POST', '/netflow/session', get_flows)

    #app.router.add_route('OPTIONS', '/{path:.*}', db_options)
