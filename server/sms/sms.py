from . import sms

class Client:

    def __init__(self,*a,**kw):
        self.sender = kw.pop('sender',False)
        self.recieved_cb = kw.pop('recieved_cb',self.__recieved_cb)

    def __recieved_cb(self,sms):
        pass
