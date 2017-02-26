import literadius.constants as rad
from literadius.constants import typeofNAS
from literadius.packet import Packet
from uuid import uuid4
import logging
import asyncio
from datetime import datetime
from utils.password import getsms, getpassw
import pytz
from bson.json_util import dumps, loads
from utils.codecs import ip2int

logger = logging.getLogger('protocol')
debug = logger.debug

BURST_TIME = 5
BITMASK32 = 2**32-1
TIMEOUT = 10

class BaseRadius(asyncio.DatagramProtocol):
    radsecret = None
    db = None
    loop = None

    def connection_made(self, transport):
        self.transport = transport

    def respond(self, resp, caller):
        self.transport.sendto(resp.data(), caller)

        if logger.isEnabledFor(logging.DEBUG):
            for attr in resp.keys():
                #break
                debug('{} :\t{}'.format(attr,resp.decode(attr)))

    def respond_cb(self,caller):
        def untask(task):
            if task.done():
                resp = task.result()
                self.respond(resp,caller)
            else:
                logger.warning('Droped request %s', task.exception())
        return untask

    def error_received(self, exc):
        logger.error('Error received: %s', exc)

    def connection_lost(self, exc):
        debug('Stop: %s', exc)

    def datagram_received(self, data, caller):
        debug('From {} received'.format(caller))
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
        f = self.loop.create_task(handler(req, caller))
        f.add_done_callback(self.respond_cb(caller))

#        try:
#            resp = f.result(TIMEOUT)
#        except asyncio.TimeoutError:
#            logger.warning('Droped request %s', task.exception())
#            f.cancel()
#        except Exception as exc:
#            logger.error('{} raised an exception: {!r}'.format(caller,exc))
#        else:
#            self.respond(resp, caller)

    def db_cb(self,r,e,*a,**kw):
        if e:
            logger.error(e.__repr__())

class CoA:
    async def handle_coa(self,req,caller):
        raise NotImplemented('Coa not yet')

class Accounting:
    async def handle_acct(self,req,caller):
        q = {
                'auth_class': req.decode(rad.Class),
                'session_id': req.decode(rad.AcctSessionId)
            }
        account = {}

        if req.decode(rad.AcctStatusType) == rad.AccountingStart:
            account={
                    'ip': req.decode(rad.FramedIPAddress),
                    'nas': req.decode(rad.NASIdentifier),
                    'callee': req.decode(rad.CalledStationId),
                    'caller': req.decode(rad.CallingStationId),
                    'username': req.decode(rad.UserName),
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
                'sensor':ip2int(caller[0])
                })
            upd={
            '$setOnInsert':{'start_date':datetime.utcnow()},
            '$set':account
            }

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


    async def billing(self,user,callee,limit):
        now = datetime.utcnow()
        #debug(now)

        invoice = await self.db.invoice.find_one( {
            'callee':callee,
            'username': user['_id'],
            'paid':True,
            'start':{'$lte':now},
            'stop':{'$gt':now},
            })

        debug(invoice)
        debug(limit)
        if invoice:
            tarif = invoice.get('limit',{})
            for k,v in tarif.items():
                debug((k,v))
                if v in [0,"0"]:
                    limit.pop(k)
                elif v:
                    limit[k] = v
            if invoice.get('stop'):
                t = round((invoice['stop'] - now).total_seconds())+28
                if limit.get('time'):
                    limit['time'] = min(limit.get('time'),t)
                else:
                    limit['time'] = t
        debug(limit)
        return limit


    async def set_limits(self,user,req,reply):
        nas = self.get_type(req)
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
                    limit.pop(k)
                elif v:
                    limit[k] = v
        limit.pop('_id')

        if limit.pop('payable',False):
            limit = await self.billing(user,callee,limit)

        with reply.lock:
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
                    reply[rad.SessionTimeout] = v
                elif k == 'ports':
                    reply[rad.PortLimit] = v #TODO decrease for sessions online
                elif k == 'bytes':
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
        return reply

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


    def mark_device(self,q):
        return self.db.devices.find_and_modify(
                q,
                {'$currentDate':{'seen':True},'$set':{'checked':True}},
                upsert=True
            )


    async def handle_auth(self,req,caller):
        code = rad.AccessReject
        reply = req.reply(code)
        device = None
        user = await self.db.users.find_one({'_id':req.decode(rad.UserName)})

        if not user:
            return  reply

        q = {
            'username':user['_id'],
            'mac':req.decode(rad.CallingStationId)
             }

        psw = user.get('password')

        if False and rad.EAPMessage in req.keys():
            code = await self.handle_eap(req,reply,psw)
            if code == rad.AccessChallenge:
                return reply
            elif code == rad.AccessAccept:
                device = self.mark_device(q)

        elif rad.MSCHAP2Response in req.keys():
            success = req.check_password(psw)
            if success:
                device = self.mark_device(q)
                code = rad.AccessAccept
                reply[rad.MSCHAP2Success] = success

        elif psw and req.check_password(psw):
            device = self.mark_device(q)
            code = rad.AccessAccept
        else:
            for n in [0,-1]:
                psw = getpassw(n=n, **q)
                if req.check_password(psw):
                    code = rad.AccessAccept
                    break

        if code == rad.AccessReject:
            asyncio.sleep(1)

        elif code == rad.AccessAccept:
            reply[rad.Class]=uuid4().bytes
            q['checked'] = True
            device = device or await self.db.devices.find_one(q)
            if device:
                reply.code = code
                reply = await self.set_limits(user,req,reply)
        return reply


class RadiusProtocol(Accounting,Auth,CoA,BaseRadius):
    """
    Implementation with Auth and Accounting
    """

