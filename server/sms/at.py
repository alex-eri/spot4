from . import sms
import serial
from gsmmodem.modem import GsmModem
from gsmmodem.exceptions import TimeoutException
import asyncio
import logging
import threading
import sys, traceback

class Client(sms.Client):
    inbox = []

    def __init__(self,*a,**kw):
        self.inboxLock = threading.Lock()
        self.sema = asyncio.Lock()
        self.logger = logging.getLogger('at')

        baudrate = kw.pop('baudrate',9600)
        device = kw.pop('uiport')
        self.callie = kw.get('number','')

        self.modem = GsmModem(device,baudrate,
                              dsrdtr=True,
                              rtscts=True,
                              smsReceivedCallbackFunc=self.recieved_cb)

        super(Client,self).__init__(*a,**kw)
        self._connected = False

    def recieved_cb(self,sms,*a,**kw):
        self.logger.debug('recieved_cb')
        with self.inboxLock:
            self.logger.debug('recieved_cb inboxLock')
            self.inbox.append({
                'phone':sms.number, 'time':sms.time, 'text':sms.text, 'to':self.callie
                              })


    async def connect(self):
        while not self._connected:
            await self.sema.acquire()
            try:
                self.modem.connect()
            except (TimeoutException,IOError) as e:
                self.modem.close()
                await asyncio.sleep(10)
                continue
            else:
                self._connected = True
                break
            finally: self.sema.release()

            await self.sema.acquire()
            try:
                self.modem.processStoredSms()
            except Exception as e:
                self.logger.error(traceback.format_exc())
            finally: self.sema.release()

    def __del__(self):
        self.modem.close()

    async def send(self,phone,text,*a,**kw):
        if not self._connected:
            await self.connect()

        await self.sema.acquire()
        try:
            res = self.modem.sendSms(phone,text)
            self.logger.info(res)
            #assert res.get("result") == "success", 'Modem cant send message'
        except Exception as e:
            self.logger.error(e)
            return False
        else:
            return True
        finally: self.sema.release()

    async def unread(self):
        await self.connect()
        with self.inboxLock:
            messages = self.inbox[:]
            del self.inbox[:]
        return messages

    async def capacity(self):
        l = len(self.inbox)
        ret = {
            'inbox': l,
            'sent': 0,
            'total': l,
            'capacity': 4096
        }
        return ret
    
