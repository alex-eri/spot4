

class Client(sms._httpclient.Client):
    def __init__(self,*a,**kw):
        self.messages = []
        self.logger = logging.getLogger('at')
        self.apiid = kw.pop('call-api-id','')

    def call(self,number):
        
