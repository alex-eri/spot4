from .decorators import json
from bson.objectid import ObjectId


@json
async def get_sensors(request):
    if 'json' in request.headers.get('Content-Type',''):
        DATA = await request.json()
    else:
        DATA = await request.post()

    session = DATA.get('session')

    qsensors = {}

    if session:
        q = {
            "_id" : ObjectId(session['_id']['$oid'])
            }

        session = await request.app['db'].accounting.find_one(q)

        qsensors = { 'last': {'$gte': session['start_time'] },
                     'first': {'$lte': session['event_time'] },
                     '$or': [
                        {'srcaddr': session['ip'] },
                        {'dstaddr': session['ip'] }
                        ]
                    }
        sensors = await request.app['db'].collector.distinct('sensor', qsensors)

        ret = []
        for c in sensors:
            qflow = {'sensor': c }
            qflow.update(qsensors)
            ret.append(qflow)

        return {'response':ret}



@json
async def get_flows(request):
    if 'json' in request.headers.get('Content-Type',''):
        q = await request.json()
    else:
        return

    return {'response':await request.app['db'].collector.find(q)}
