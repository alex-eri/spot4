import logging

class Client:

    def __init__(self,*a,**kw):
        self.logger = logging.getLogger('sms')
        self.logger.debug(kw)
        self.sender = kw.pop('sender',False)
        self.reciever = kw.pop('reciever',True)
        self.logger.debug(self.reciever)
        self.recieved_cb = kw.pop('recieved_cb',self.__recieved_cb)

    def __recieved_cb(self,sms):
        pass
