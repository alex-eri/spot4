TERMINATOR = b'\r'
CTRLZ = b'\x1a'


import asyncio
import serial_asyncio
import serial.threaded


#http://pyserial.readthedocs.io/en/latest/pyserial_api.html

class Output(serial.threaded.LineReader):
    TERMINATOR = b'\r'

    def connection_made(self, transport):
        self.transport = transport

    def handle_line(self, data):
        print('data received', repr(data))

    def connection_lost(self, exc):
        print('port closed')
        #TODO reconnect

class Modem:
    def __init__(self,port, cb, baudrate=115200,*a,**kw):
        pass



class Client(_sms.Client):
    def __init__(self,*a,**kw):
        self.messages = []
        self.logger = logging.getLogger('at')
        baudrate = kw.pop('baudrate',115200)
        device = kw.pop('uiport')
        self.callie = kw.get('number','')
        self.modem = Modem(device,baudrate)

        super(Client,self).__init__(*a,**kw)

    async def send(self,phone,text,*a,**kw):
        pass

    async def unread(self):
        unread,self.messages = self.messages, []
        return unread

"""
from . import sms
import serial
#from gsmmodem.modem import GsmModem
#from gsmmodem.exceptions import TimeoutException
import asyncio
import logging
import threading
import sys, traceback
from collections import defaultdict

TERMINATOR = b'\r'
CTRLZ = b'\x1a'

TIMEOUT = 5

class NotConnectedError(Exception):
    pass

class Modem:
    def __init__(self,port, baudrate=115200):
        self.alive = False
        self.free = True
        self.port = port
        self.baudrate = baudrate
        self.timeout = 1
        self.com_args = []
        self.com_kwargs = dict(
            dsrdtr=True,
            rtscts=True,
        )
        self.buff = b''
        self._txLock = threading.RLock()
        self.rxThread = None
        self.events = defaultdict(threading.Event)
        self.responses = {}


    def onconnected(fu):
        def inner(self,*a,**kw):
            while not self.alive:
                if self.free:
                    self.connect()
            if self.alive:
                return fu(self,*a,**kw)
            raise NotConnectedError
        return inner

    def connect(self):
        self.free = False
        try:
            self.serial = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=self.timeout,
                *self.com_args,**self.com_kwargs)
            self.init()
        except Exception as e:
            self.alive = False
            raise e
        else:
            self.alive = True
            self.rxThread = threading.Thread(target=self._read_loop)
            self.rxThread.daemon = True
            self.rxThread.start()
        finally:
            self.free = True

    def init(self):
        for c in ['ATZ',
                'ATE0',
                'AT+CFUN=1',
                'AT+CMEE=1',
                #'AT+CLAC',
                'AT+CPMS="MT","MT","MT"',
                'AT+CSMP=49,167,0,8',
                'AT+CNMI=2,1,0,2',
                'AT+CLIP=1',
                'AT+CRC=1',
                'AT+CVHU=0',
                ]:
            self.command(c,b"OK")

    def close(self):
        self.alive = False
        if self.rxThread and self.rxThread.is_alive():
            self.rxThread.join()
        try:
            self.serial.close()
        except Exception: #pragma: no cover
            pass

    def default_cb(self,line):
        logging.debug(line)

    def command(self,cmd, wait=False):
        self.write(cmd+TERMINATOR)
        if wait:
            if self.events[wait].wait(TIMEOUT):
                return self.responses[wait]


    def write(self,data):
        logging.debug(data)
        self._txLock.acquire()
        try:
            self.serial.write(data)
        except serial.SerialException as e:
            self.close()

    def _read_loop(self):
        while self.alive:
            try:
                data = self.serial.read(1)
                if data:
                    self.buff += data
                    if b'\r\n' == self.buff[-2:]:
                        line  = self.buff[:]
                        self.buff = b''
                        self.handle_line(line)

            except serial.SerialException as e:
                self.close()

    def handle_line(self,line):
        logging.debug(line)
        line = line.strip()


    @onconnected
    def sms_all(self):
        self.command(b'AT+CMGF=1')
        self.command(b'AT+CMGL="ALL"')


class Client(sms.Client):
    inbox = []

    def __init__(self,*a,**kw):
        self.sema = asyncio.Lock()
        self.logger = logging.getLogger('at')

        baudrate = kw.pop('baudrate',115200)
        device = kw.pop('uiport')
        self.callie = kw.get('number','')
        self.modem = Modem(device,baudrate)
        super(Client,self).__init__(*a,**kw)


    def __del__(self):
        if self.modem.alive:
            self.modem.close()
        super(Client,self).__del__()


    async def all(self):
        pass

    async def read(self):
        return []

    async def send(self,phone,text,*a,**kw):

        pass
    async def unread(self):
        return []

    async def capacity(self):
        l = len(self.inbox)
        ret = {
            'inbox': l,
            'sent': 0,
            'total': l,
            'capacity': 00        }
        return ret


    async def clean(self):
        pass

"""
