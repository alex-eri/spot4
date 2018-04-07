import _call


class Modem():
    def __init__(self,port, baudrate=115200,*a,**kw):
        self.modem = open(port,'rw')
        self.reader =

class Client(_call.Client):
    def __init__(self,*a,**kw):
        self.messages = []
        self.logger = logging.getLogger('at')
        baudrate = kw.pop('baudrate',115200)
        device = kw.pop('uiport')
        self.callie = kw.get('number','')
        self.modem = Modem(device,baudrate)
