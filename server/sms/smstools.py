from . import _sms
import uuid
import os.path

class Client(_sms.Client):
    def __init__(self,*a, **kw):
        self.incomming = kw.pop('incomming',"/var/spool/sms/incoming")
        self.outgoing = kw.pop('outgoing', "/var/spool/sms/outgoing")

        super(Client,self).__init__(*a, **kw)

    async def send(self,phone,text,*a,**kw):
        u = uuid.uuid4().hex
        path = os.path.join(self.outgoing, u)
        with open(path,'w') as f:
            f.write('To: %s\n' % phone[1:])
            f.write('Alphabet: UCS\n')
            f.write('\n')
            f.write(text.encode('utf-16be'))

    async def unread(self):
        '''
           returns list of dict{phone,text,to}
        '''
        return []

    async def capacity(self):
        return

    async def clean(self):
        return
