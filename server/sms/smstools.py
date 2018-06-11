from . import _sms
import uuid
import os.path
import os
import email, email.parser, email.policy
import pytz
import glob

class Client(_sms.Client):
    def __init__(self, *a, **kw):
        self.incomming = kw.pop('incomming', "/var/spool/sms/incoming")
        self.outgoing = kw.pop('outgoing', "/var/spool/sms/outgoing")
        self.sentbox = kw.pop('sentbox', "/var/spool/sms/sent")
        self.readbox = kw.pop('readbox', "/var/spool/sms/read")
        self.callie = kw.get('number', '')
        self.modem = kw.get('modem', None)
        os.makedirs(self.readbox, exist_ok=True)
        self.parser = email.parser.BytesParser(policy=email.policy.HTTP)
        super(Client, self).__init__(*a, **kw)

    async def send(self, phone, text, *a, **kw):
        u = uuid.uuid4().hex
        path = os.path.join(self.outgoing, u)
        with open(path, 'wb') as f:
            f.write(b'To: %s\n' % phone[1:].encode('ascii'))
            f.write(b'Alphabet: UCS\n')
            if self.modem:
                f.write(b'Modem: %s\n' % self.modem.encode('ascii'))
            f.write(b'\n')
            f.write(text.encode('utf-16be'))
        self.logger.debug(u)

    async def unread(self):
        '''
           returns list of dict{phone,text,to}
        '''
        ret = []

        if self.modem:
            modem_file = self.modem + '.*'
        else:
            modem_file = "*"

        for path in glob.glob(os.path.join(self.incomming, modem_file)):
            # ... in os.listdir(self.incomming):
            # path = os.path.join(self.incomming, n)
            if not os.path.isfile(path):
                continue

            with open(path, 'rb') as f:
                try:
                    e = self.parser.parse(f)
                except:
                    self.logger.error('Bad file %s' % path)
                    continue
                num = "+" + e.get('From', '*')
                self.logger.debug(num)
                alphabet = e.get('Alphabet', 'ISO')
                # if alphabet == "UCS2":
                #     e.set_charset('utf-16be')
                #     text = e.get_payload()
                #     text = codecs.decode(text,'base64')
                #     text = codecs.decode(text,'utf-16be')
                if alphabet == "UCS2":
                    payload = e.get_payload(decode=True)
                    if isinstance(payload, bytes):
                        text = payload.decode('utf-16be')
                    else:
                        self.logger.warning('Bad payload %s', path)
                        self.logger.debug(payload)
                else:
                    text = e.get_payload()
                self.logger.debug(text)

                date = e.get('Sent') or e.get('Received')

                m = dict(phone=num, text=text, to=self.callie, date=date)

                try:
                    date = pytz.datetime.datetime.strptime(
                        m['date'].rsplit(',', 1)[0], '%y-%m-%d %H:%M:%S')
                    date = pytz.datetime.datetime.astimezone(date)
                except Exception as e:
                    self.logger.warning(e)
                else:
                    m['rawdate'], m['date'] = m['date'], date

                ret.append(m)

            os.rename(path, os.path.join(self.readbox, n))
        self.logger.debug(ret)
        return ret

    async def capacity(self):

        inbox = len(os.listdir(self.incomming))
        inbox += len(os.listdir(self.readbox))
        sent = len(os.listdir(self.outgoing))
        sent += len(os.listdir(self.sentbox))

        ret = {
            'inbox': inbox,
            'sent': sent,
            'total': inbox + sent,
            'capacity': 65256
        }

        return ret

    async def clean(self):

        return
