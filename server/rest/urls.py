from .views import *
from .decorators import check_auth

def routers(app):
    if app['config'].get('SMS'):

        app.router.add_route('GET', '/register/+{phone:\d+}/{mac}', phone_handler)
        app.router.add_route('GET', '/register/%2B{phone:\d+}/{mac}', phone_handler)
        app.router.add_route('POST', '/register', phone_handler)

        app.router.add_route('POST', '/sms_callback', check_auth(sms_handler))

    app.router.add_route('*', '/device/{oid}', device_handler)

    app.router.add_route('POST', '/db/{collection}/{skip}::{limit}', check_auth(db_handler))
    app.router.add_route('POST', '/db/{collection}', check_auth(db_handler))

    app.router.add_static('/uam/theme/', path='../uam/theme', name='uam-theme')
    app.router.add_static('/uam/config/', path='../uam/config', name='uam-config')
    app.router.add_get('/uam/{path:.*}', uam_index)
    app.router.add_static('/static/', path='../static/ht_docs/', name='static')
    app.router.add_static('/admin/', path='../admin/ht_docs', name='admin-static')



    #app.router.add_route('OPTIONS', '/{path:.*}', db_options)
