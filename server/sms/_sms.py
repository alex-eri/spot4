import logging

class Client:

    def __init__(self,*a,**kw):
        self.logger = logging.getLogger(self.__class__.__module__)
        self.logger.debug(self.__class__)
        self.logger.debug(kw)
        self.sender = kw.pop('sender',False)
        self.callee = kw.pop('callee',[])
        self.reciever = kw.pop('reciever',False)
        self.anytext = kw.pop('anytext',False)
        if self.anytext and type(self.anytext) != int:
            self.anytext = 3600*4
        self.logger.debug(self.reciever)
        self.recieved_cb = kw.pop('recieved_cb',self.__recieved_cb)

    def __recieved_cb(self,sms):
        pass

    async def capacity(self):
        return 0
