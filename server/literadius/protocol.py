import literadius.constants as rad
from literadius.packet import Packet
from uuid import uuid4
import logging
import asyncio
from datetime import datetime
from utils.password import getsms, getpassw
import pytz
from bson.json_util import dumps, loads

logger = logging.getLogger('protocol')
debug = logger.debug

BURST_TIME = 5
BITMASK32 = 2**32-1

class BaseRadius(asyncio.DatagramProtocol):
    radsecret = None
    db = None
    def __getitem__(self,y): #TODO: remove it
        r = self.pkt.decode(y)
        return r

    def connection_made(self, transport):
        self.transport = transport

    def respond(self,task):
        resp = task.result()
        self.transport.sendto(resp.data, self.caller)
        if logger.isEnabledFor(logging.DEBUG):
            for attr in resp.keys():
                debug('{} :\t{}'.format(attr,resp.decode(attr)))

    def error_received(self, exc):
        logger.error('Error received: %s', exc)

    def connection_lost(self, exc):
        debug('Stop: %s', exc)

    def datagram_received(self, data, addr):
        debug('From {} received'.format(addr))
        self.caller = addr
        self.pkt = Packet(data, self.radsecret)

        if self.pkt.code == rad.AccessRequest:
            handler = self.handle_auth
        elif self.pkt.code == rad.AccountingRequest:
            handler = self.handle_acct
        elif self.pkt.code == rad.CoARequest:
            handler = self.handle_coa
        else:
            raise Exception('Packet is not request')
        if logger.isEnabledFor(logging.DEBUG):
            for attr in self.pkt.keys():
                debug('{} :\t{}'.format(attr,self.pkt.decode(attr)))

        loop = asyncio.get_event_loop()
        c = handler() #coroutine
        f = asyncio.ensure_future(c,loop=loop)
        f.add_done_callback(self.respond)
        def wakeup():
            pass
        loop.call_soon(wakeup)


    def db_cb(self,r,e,*a,**kw):
        if e:
            logger.error(e.__repr__())

class CoA:
    async def handle_coa(self):
        raise NotImplemented('Coa not yet')

class Accounting:
    async def handle_acct(self):
        q = {
                'auth_class': self[rad.Class],
                'session_id': self[rad.AcctSessionId],
                #'sensor': self.caller[0]
            }
        account = {}

        if self[rad.AcctStatusType] == rad.AccountingStart:
            account={
                    'ip': self[rad.FramedIPAddress],
                    'nas': self[rad.NASIdentifier],
                    'callee': self[rad.CalledStationId],
                    'caller': self[rad.CallingStationId],
                    'username': self[rad.UserName],
                    'start_time': self[rad.EventTimestamp]
                }


        elif self[rad.AcctStatusType] in [rad.AccountingUpdate, rad.AccountingStop] :

            input_bytes = self[rad.AcctInputGigawords] or 0 << 32 | self[rad.AcctInputOctets]
            output_bytes = self[rad.AcctOutputGigawords] or 0 << 32 | self[rad.AcctOutputOctets]

            input_packets = self[rad.AcctInputPackets]
            output_packets = self[rad.AcctOutputPackets]

            if self[rad.CoovaChilliAcctViewPoint] == rad.CoovaChilliClientViewPoint:
                input_bytes, output_bytes = output_bytes, input_bytes
                input_packets, output_packets = output_packets, input_packets

            account = {
                'session_time': self[rad.AcctSessionTime],
                'input_bytes': input_bytes,
                'input_packets': input_packets,
                'output_bytes': output_bytes,
                'output_packets': output_packets,
                'delay':self[rad.AcctDelayTime],
                'event_time': self[rad.EventTimestamp]
            }

            if self[rad.AcctStatusType] == rad.AccountingStop:
                account['termination_cause'] =  self[rad.AcctTerminateCause]


        elif self[rad.AcctStatusType] in [rad.AccountingOn, rad.AccountingOff]:
            self.db.accounting.find_and_modify(
                {'nas': self[rad.NASIdentifier],'termination_cause':{'$exists': False}},
                {'$set':{'termination_cause': rad.TCNASReboot}},
                callback=self.db_cb
            )
            #TODO accountin on/off

        if account :
            account.update({
                'stop_date':datetime.now(pytz.utc),
                'sensor':{
                    'ip':self.caller[0],
                    'port':self.caller[1]
                    }
                })
            upd={
            '$setOnInsert':{'start_date':datetime.now(pytz.utc)},
            '$set':account
            }

            self.db.accounting.find_and_modify(q,upd,upsert=True,new=True,callback=self.db_cb)

        return self.pkt.reply(rad.AccountingResponse)


class Auth:
    async def set_limits(self,user,reply):
        profiles = [
            'default',
            self[rad.NASIdentifier],
            self[rad.CalledStationId],
            user['_id']
            ]
        limits = await self.db.limit.find( {'_id': {'$in':profiles}}).to_list(4)
        ordered = sorted(limits,key=lambda l:profiles.index(l['_id'])) #TODO: enum style
        limit = {}
        for l in ordered:
            for k,v in l.items():
                if v == 0:
                    limit.pop(k)
                if v:
                    limit[k] = v
        limit.pop('_id')

        with reply.lock:
            for k,v in limit.items():
                if k == 'rate':
                    v = int(v * 1024)
                    b = int(v * 1.3)
                    r = int(v * 0.9)
                    reply[rad.MikrotikRateLimit] = \
                        "{0}k/{0}k {1}k/{1}k {2}k/{2}k {3}/{3}".format(v,b,r, BURST_TIME)

                    bps = v << 10

                    reply[rad.AscendDataRate] = bps
                    reply[rad.AscendXmitRate] = bps
                    reply[rad.WISPrBandwidthMaxDown] = bps
                    reply[rad.WISPrBandwidthMaxUp] = bps
                elif k == 'time':
                    reply[rad.SessionTimeout] = v
                elif k == 'ports':
                    reply[rad.PortLimit] = v #TODO decrease for sessions online
                elif k == 'bytes':
                    v = v << 20
                    g = v >> 32
                    b = v & BITMASK32
                    reply[rad.MikrotikRecvLimit] = b
                    reply[rad.MikrotikXmitLimit] = b
                    if g > 0:
                        reply[rad.MikrotikRecvLimitGigawords] = g
                        reply[rad.MikrotikXmitLimitGigawords] = g
                elif k == 'redir':
                    reply[rad.WISPrRedirectionURL] = v
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


    async def handle_auth(self):
        code = rad.AccessReject
        reply = self.pkt.reply(rad.AccessReject)
        user = await self.db.users.find_one({'_id':self[rad.UserName]})

        if not user:
            return  reply

        reply[rad.Class]=uuid4().bytes

        q = {
            'username':user['_id'],
            'mac':self[rad.CallingStationId]
             }

        if user.get('password') and self.pkt.check_password(user.get('password')):
            self.db.devices.find_and_modify(q,
                    {'$currentDate':{'seen':True},'$set':{'checked':True}},
                    upsert=True, new=True, callback=self.db_cb
                )
            code = rad.AccessAccept
        else:
            for n in [0,-1]:
                psw = getpassw(n=n, **q)
                if self.pkt.check_password(psw):
                    code = rad.AccessAccept
                    break
        if code == rad.AccessReject:
            return reply
        else:
            q['checked'] = True
            device = await self.db.devices.find_one(q)
            if device:
                reply.code = code
                reply = await self.set_limits(user,reply)
        return reply


class RadiusProtocol(Accounting,Auth,CoA,BaseRadius):
    """
    Implementation with Auth and Accounting
    """

class Legacy:
    def handle_auth(self):
        self.reply = self.pkt.reply(rad.AccessReject)
        self.reply[rad.Class]=uuid4().bytes

        self.db.users.find_one({'_id':self[rad.UserName]},callback=self.got_user)
        debug('user was {}'.format(self[rad.UserName]))

    def got_user(self,response,error):
        if error:
            logger.error(error.__repr__())
        if response:
            q = {
                'username':response['_id'],
                'mac':self[rad.CallingStationId]
                 }

            self.get_limits(response)

            if response.get('password') and self.pkt.check_password(response.get('password')):
                self.db.devices.find_and_modify(q,
                    {'$currentDate':{'seen':True},'$set':{'checked':True}},
                    upsert=True, new=True,
                    callback=self.got_device
                    )
                self.reply.code = rad.AccessAccept
            else:
                for n in [0,-1]:
                    psw = getpassw(n=n, **q)
                    if self.pkt.check_password(psw):
                        q['checked']=True
                        self.db.devices.find_one(q,callback=self.got_device)
                        return
                    else:
                        debug('otp was {}'.format(psw))
        #reject
        self.respond( self.reply )


    def got_device(self,response,error):
        if error:
            logger.error(error.__repr__())
        if response:
            self.reply.code = rad.AccessAccept
        self.respond( self.reply )

    def get_limits(self,user):
        profiles = [
            user._id,
            self[rad.CalledStationId],
            self[rad.NASIdentifier],
            'default'
            ]
        self.db.limit.find(
            {'_id': {'$in':profiles}},
            callback = self.set_limits
        )

    def set_limits(self,response):
        limit = {}
        for l in response:
            for k,v in l.items:
                limit[k] = limit.get(k) or v
        debug(limit)


