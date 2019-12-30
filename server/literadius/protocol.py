import literadius.constants as rad
from literadius.constants import typeofNAS
from literadius.packet import Packet
from uuid import uuid4
import logging
import asyncio
from datetime import datetime, timedelta
from utils.password import getsms, getpassw
import pytz
from bson.json_util import dumps, loads
from utils.codecs import ip2int
import pymongo
from literadius import decoders

from rest.front import get_uam_config

import time

logger = logging.getLogger('protocol')
debug = logger.debug

BURST_TIME = 5
BITMASK32 = 0xFFFFFFFF
TIMEOUT = 10
MAX_INT = 0xFFFFFFFF

class BaseRadius(asyncio.DatagramProtocol):
    radsecret = None
    db = None
    loop = None
    session_limit = None

    def connection_made(self, transport):
        self.transport = transport
        self.start_time = time.time()

    def respond(self, resp, nas):
        self.transport.sendto(resp.data(), nas)

        logger.info( "Reply {} to {}, user".format(resp.code,nas))
        logger.info( "Processing time: %s" % (time.time()-self.start_time) )

        if logger.isEnabledFor(logging.DEBUG):
            for attr in resp.keys():
                #break
                debug('{} :\t{}'.format(attr,resp.decode(attr)))

    def respond_cb(self,nas):
        def untask(task):
            if task.done():
                resp = task.result()
                self.respond(resp,nas)
            else:
                logger.warning('Droped request %s', task.exception())
        return untask

    def error_received(self, exc):
        logger.error('Error received: %s', exc)

    def connection_lost(self, exc):
        debug('Stop: %s', exc)

    def datagram_received(self, data, nas):
        debug('From {} received'.format(nas))
        req = Packet(data, self.radsecret)

        if req.code == rad.AccessRequest:
            handler = self.handle_auth
        elif req.code == rad.AccountingRequest:
            handler = self.handle_acct
        elif req.code == rad.CoARequest:
            handler = self.handle_coa
        else:
            raise Exception('Packet is not request')
        if logger.isEnabledFor(logging.DEBUG):
            for attr in req.keys():
                #break
                debug('{} :\t{}'.format(attr,req.decode(attr)))

        #f = asyncio.ensure_future(
        #    handler(req, caller),
        #    loop=asyncio.get_event_loop()
        #    )
        #f.add_done_callback(self.respond_cb(caller))

        #loop=asyncio.get_event_loop()
        f = self.loop.create_task(handler(req, nas))
        f.add_done_callback(self.respond_cb(nas))

#        try:
#            resp = f.result(TIMEOUT)
#        except asyncio.TimeoutError:
#            logger.warning('Droped request %s', task.exception())
#            f.cancel()
#        except Exception as exc:
#            logger.error('{} raised an exception: {!r}'.format(nas,exc))
#        else:
#            self.respond(resp, nas)

    def db_cb(self,r,e,*a,**kw):
        if e:
            logger.error(e.__repr__())

class CoA:
    async def handle_coa(self,req,nas):
        raise NotImplemented('Coa not yet')

class Accounting:
    async def handle_acct(self,req,nas):
        q = {
                'auth_class': req.decode(rad.Class),
                'session_id': req.decode(rad.AcctSessionId)
            }
        account = {}
        unset = {}

        username = req.decode(rad.UserName)

        if req.get(rad.CallingStationId) == req.get(rad.UserName):
            session = await self.db.rad_sessions.find_one(
            {
                'caller': req.decode(rad.CallingStationId),
                'callee': req.decode(rad.CalledStationId),
            },
                 sort=[("$natural", pymongo.DESCENDING)]
            )
            if session:
                username = session['username']


        if req.decode(rad.AcctStatusType) == rad.AccountingStart:
            account={
                    'ip': req.decode(rad.FramedIPAddress),
                    'nas': req.decode(rad.NASIdentifier),
                    'callee': req.decode(rad.CalledStationId),
                    'caller': req.decode(rad.CallingStationId),
                    'username': username,
                    'start_time': req.decode(rad.EventTimestamp)
                }


        elif req.decode(rad.AcctStatusType) in [rad.AccountingUpdate, rad.AccountingStop] :

            input_bytes = req.decode(rad.AcctInputGigawords) or 0 << 32 | req.decode(rad.AcctInputOctets)
            output_bytes = req.decode(rad.AcctOutputGigawords) or 0 << 32 | req.decode(rad.AcctOutputOctets)

            input_packets = req.decode(rad.AcctInputPackets)
            output_packets = req.decode(rad.AcctOutputPackets)

            if req.decode(rad.CoovaChilliAcctViewPoint) == rad.CoovaChilliClientViewPoint:
                input_bytes, output_bytes = output_bytes, input_bytes
                input_packets, output_packets = output_packets, input_packets

            account = {
                'session_time': req.decode(rad.AcctSessionTime),
                'input_bytes': input_bytes,
                'input_packets': input_packets,
                'output_bytes': output_bytes,
                'output_packets': output_packets,
                'delay':req.decode(rad.AcctDelayTime),
                'event_time': req.decode(rad.EventTimestamp)
            }

            if req.decode(rad.AcctStatusType) == rad.AccountingStop:
                account['termination_cause'] =  req.decode(rad.AcctTerminateCause)
            else:
                unset['termination_cause']=""


        elif req.decode(rad.AcctStatusType) in [rad.AccountingOn, rad.AccountingOff]:
            self.db.accounting.find_and_modify(
                {'nas': req.decode(rad.NASIdentifier),
                'termination_cause':{'$exists': False}},
                {'$set':{'termination_cause': rad.TCNASReboot}}
            )
            #TODO accountin on/off

        if account :
            account.update({
                'stop_date':datetime.utcnow(),
                'sensor':ip2int(nas[0])
                })
            upd={
            '$setOnInsert':{'start_date':datetime.utcnow()},
            '$set':account,
            }
            if unset:
                upd['$unset'] = unset

            self.db.accounting.find_and_modify(q,upd,upsert=True)

        return req.reply(rad.AccountingResponse)

#from collections import defaultdict
#from eap.session import peap_session
#import eap.session as eap
from mschap import mschap

class Auth:
#    peap = defaultdict(eap.peap_session)

    def get_type(self,req):
        nas = 0
        vendors = set(x for x,y in filter( lambda x: isinstance(x, tuple) ,req.keys()))
        for x in vendors:
            if x == rad.Mikrotik:
                nas |= typeofNAS.mikrotik
            elif x == rad.ChilliSpot :
                 nas |= typeofNAS.chilli
            elif x == rad.WISPr:
                nas |= typeofNAS.wispr
        return nas


    async def billing(self,user,callee, climit):
        now = datetime.utcnow()
        invoice = await self.db.invoice.find_one( {
            'callee': callee,
            'username': user.get('_id',None),
            'paid':True,
            'start':{'$lte':now},
            'stop':{'$gt':now},
            })

        if invoice:
            tarif = invoice.get('limit',{})

            for k,v in tarif.items():
                if v in [0, "0"]:
                    climit.pop(k,None)

            tarif = await self.reduce_limits(user['_id'],callee,tarif,invoice.get('start'))

            if invoice.get('stop'):
                t = round((invoice['stop'] - now).total_seconds())+28
                if tarif.get('time', None) is None:
                    tarif['time'] = t
                else:
                    tarif['time'] = min(tarif.get('time'), t)

            for k,v in tarif.items():
                if type(v) == int and v <= 0:
                    return climit

            for k,v in tarif.items():
                climit[k] = v


        return climit


    async def reduce_limits(self,username,callee,limit,start):
        accs = await self.db.accounting.aggregate([
            {'$match':{
                    'username': username,
                    'callee': callee,
                    'start_date' : {'$gte': start}
            }},
            {'$group': {
                '_id': None,
                'time': {'$sum': "$session_time"},
                'input_bytes':  {'$sum': "$input_bytes"},
                'output_bytes': {'$sum': "$output_bytes"},
                'count': {'$sum': 1},
                'closed': { '$push': '$termination_cause'}
            }},
            {'$project':{
                'count':1,
                'time':1,
                'bytes': { '$sum': ['$output_bytes',"$input_bytes"]},
                'closed':{ '$size': "$closed" }
            }}
        ]).to_list(1)

        if accs:
            if limit.get('time'):
                limit['time'] -= accs[0]['time']
            if limit.get('bytes'):
                limit['bytes'] -= accs[0]['bytes']
            if limit.get('ports'):
                limit['ports'] -= accs[0]['count'] - accs[0]['closed']
        return limit


    async def get_limits(self,user,req,reply):
        callee = req.decode(rad.CalledStationId)
        profiles = [
            'default',
            callee
            ]
        limits = await self.db.limit.find( {'_id': {'$in':profiles}}).to_list(3)
        if len(limits) == 0:
            return reply
        ordered = sorted(limits,key=lambda l:profiles.index(l['_id'])) #TODO: enum style
        limit = {}
        for l in ordered:
            for k,v in l.items():
                if v in [0,"0"]:
                    limit.pop(k,None)
                elif v:
                    limit[k] = v
        limit.pop('_id',None)

        if limit.pop('payable',False):
            limit = await self.billing(user,callee,limit)

        if self.session_limit:
            limit['time'] = self.session_limit

        return limit

    async def set_limits(self,limit,req,reply):
        nas = self.get_type(req)
        with reply.lock:
            k = None
            try:
                for k,v in limit.items():
                    if k == 'rate':
                        v = int(v * 1024)
                        if nas & typeofNAS.mikrotik:
                            b = int(v * 1.3)
                            r = int(v * 0.9)
                            reply[rad.MikrotikRateLimit] = \
                                "{0}k/{0}k {1}k/{1}k {2}k/{2}k {3}/{3}".format(v,b,r, BURST_TIME)
                        else:
                            bps = v << 10
                            if nas & (typeofNAS.wispr | typeofNAS.chilli) :
                                reply[rad.WISPrBandwidthMaxDown] = bps
                                reply[rad.WISPrBandwidthMaxUp] = bps
                            else:
                                reply[rad.AscendDataRate] = bps
                                reply[rad.AscendXmitRate] = bps

                    elif k == 'time':
                        assert v>0, 'E=691 {} limit exceed'.format(k)
                        reply[rad.SessionTimeout] = v
                    elif k == 'ports':
                        assert v>0, 'E=691 {} limit exceed'.format(k)
                        reply[rad.PortLimit] = v
                    elif k == 'bytes':
                        assert v>0, 'E=691 {} limit exceed'.format(k)
                        v = v << 20
                        g = v >> 32
                        b = v & BITMASK32
                        if nas | typeofNAS.mikrotik:
                            reply[rad.MikrotikRecvLimit] = b
                            reply[rad.MikrotikXmitLimit] = b
                            if g > 0:
                                reply[rad.MikrotikRecvLimitGigawords] = g
                                reply[rad.MikrotikXmitLimitGigawords] = g
                        elif nas | typeofNAS.chilli:
                            if g > 0:
                                reply[rad.ChilliSpotMaxInputOctets] = MAX_INT
                                reply[rad.ChilliSpotMaxOutputOctets] = MAX_INT
                            else:
                                reply[rad.ChilliSpotMaxInputOctets] = b
                                reply[rad.ChilliSpotMaxOutputOctets] = b

                    elif k == 'redir':
                        reply[rad.WISPrRedirectionURL] = v.replace('rel://','')
                    elif k == 'filter':
                        reply[rad.FilterId] = v
                    else:
                        try:
                            jk = loads(k)
                        except Exception:
                            logger.warning("Bad limit: %s",k)
                        else:
                            if isinstance(jk,int):
                                reply[jk] = v
                            elif isinstance(jk,list):
                                reply[tuple(jk)] = v
            except AssertionError as e:
                reply.code = rad.AccessReject
                reply[rad.ReplyMessage] = e.args[0]
        return reply
    '''
    async def handle_eap(self,req,reply,psw):
        state = req.get(rad.State,uuid4().bytes)

        ses = self.peap[state]
        ses.feed(req[rad.EAPMessage])

        debug('---')
        reply.code = rad.AccessChallenge

        try:
            if ses.handshaked:
                debug('--->>>')
                stage2 = ses.read()
                debug(stage2)
                if stage2.get('type'):
                    if stage2['type'] == eap.Identity:
                        ses.s2challenge(stage2)
                    elif stage2['type'] == eap.MSCHAPV2:
                        debug('MSCHAPV2 !!!')
                        debug(ses.challenge)
                        debug('MSCHAPV2 !!!')
                        if stage2['ChapType'] == eap.Response:
                            success = mschap.generate_nt_response_mschap2(
                                ses.challenge,
                                stage2['PeerChallenge'],
                                stage2['Identity'],
                                psw) == stage2['NTResponse']

                            if success:
                                debug('success')
                                auth_resp = mschap.generate_authenticator_response(
                                    psw,
                                    stage2['NTResponse'],
                                    stage2['PeerChallenge'],
                                    ses.challenge,
                                    stage2['Identity'])

                                ses.s2success(stage2,auth_resp)
                                reply.code = rad.AccessAccept
                            else:
                                debug('fail')
                                reply.code = rad.AccessReject
                elif ses.o.pending:
                    pass
                else:
                    ses.s2challenge(stage2)
            else:
                ses.do_handshake()


        except Exception as e:
            logging.error(e)
            reply.code = rad.AccessReject

        with reply.lock:
            reply[rad.State] = state
            reply[rad.EAPMessage] = ses.next()
            reply[rad.MessageAuthenticator] = True

        return reply.code
    '''

    def mark_device(self,q):
        return self.db.devices.find_and_modify(
                q,
                {'$currentDate':{'seen':True},'$set':{'checked':True}},
                upsert=True
            )

    async def check_password(self,req,reply,psw):
        if rad.MSCHAP2Response in req.keys():
            success = req.check_password(psw)
            if success:
                with reply.lock:
                    reply[rad.MSCHAP2Success] = success
                return True
        elif req.check_password(psw):
            return True


    async def handle_auth(self,req,nas):
        now = datetime.utcnow()
        code = rad.AccessReject
        reply = req.reply(code)
        device = None
        success = False
        session = False
        limit = False
        uam = None

        callee = req.decode(rad.CalledStationId)
        username = req.decode(rad.UserName)
        mac = req.decode(rad.CallingStationId)

        session = await self.db.rad_sessions.find_one(
            {
                'username':username,
                'callee': callee,
                'caller':mac,
                'stop':{'$gt':now}
            },
                 sort=[("$natural", pymongo.DESCENDING)]
        )

        if session:
            user = {'_id':session['username'],'password':session.get('password')}
        else:
            user = await self.db.users.find_one({'_id':username})

        if not user:
            psw = None
            device_q = {
                'mac': mac,
                'checked': True
            }
        else:
            device_q = {
                'username':user.get('_id'),
                'mac':mac
                 }
            psw = user.get('password')

        if req.get(rad.CallingStationId) == req.get(rad.UserName):
            uam = await get_uam_config(self.db, callee)
            if uam and uam.get('macauth',False):
                session = await self.db.rad_sessions.find_one(
                    { 'caller':mac, 'callee': callee, 'stop':{'$gt':now} },
                    sort=[("$natural", pymongo.DESCENDING)]
                    )

                if session:
                    success = session
                    limit = session['limit']
                    code = rad.AccessAccept
                    user = {'_id':success['username']}

        elif psw:
            success = await self.check_password(req,reply,psw)
            if success:
                device = self.mark_device(device_q)
                code = rad.AccessAccept

        if user and not success:
            for n in [0,-1]:
                psw = getpassw(n=n, **device_q)
                if await self.check_password(req,reply,psw):
                    code = rad.AccessAccept
                    break


        if code == rad.AccessReject:
            await asyncio.sleep(1)
            return reply

        elif code == rad.AccessAccept:
            reply[rad.Class]=uuid4().bytes
            device_q['checked'] = True
        else:
            return reply

        if limit and session:
            reply.code = code
            limit = await self.reduce_limits(session['username'],session['callee'],limit,session['start'])
            reply = await self.set_limits(limit,req,reply)
            if reply.code == rad.AccessAccept:
                return reply



        device = device or await self.db.devices.find_one(device_q)

        if device:
            reply.code = code
            limit = await self.get_limits(user,req,reply)
            reply = await self.set_limits(limit,req,reply)

            expires = limit.get('time',3600)

            await self.db.rad_sessions.insert({

                'username': user['_id'],
                'password': psw,
                'caller': mac,
                'callee': req.decode(rad.CalledStationId),
                'limit': limit,
                'start': now,
                'stop': now + timedelta(seconds=expires)

            })


        return reply


class RadiusProtocol(Accounting,Auth,CoA,BaseRadius):
    """
    Implementation with Auth and Accounting
    """

