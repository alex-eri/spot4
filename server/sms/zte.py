from . import _httpclient

import logging
import time
import datetime
from dateutil.tz import tzlocal
from utils.codecs import trydecodeHexUcs2,encodeUcs2
import pytz

TZ = format(-time.timezone//3600,"+d")

RECIEVED = 10
SENT = 2
UNREAD = 1

class Client(_httpclient.Client):

    def __init__(self,*a,**kw):
        self.logger = logging.getLogger('zte')
        self.notCallback = kw.pop('notCallback',None)
        self.base_url = kw.pop('url')
        headers = {
            'Referer':self.base_url+"/index.html",
            'X-Requested-With':'XMLHttpRequest',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Pragma': 'no-cache',
            'Origin': self.base_url,
            #'Host': self.base_url.split('/')[2]
        }
        self.max = 100
        self.callie = kw.get('number','')
        super(Client,self).__init__(get_headers=headers,post_headers=headers, *a, **kw)

    @_httpclient.get_json
    def _send_sms(self,phone,text,**kw):
        uri = "{base}/goform/goform_set_cmd_process".format(
                base=self.base_url
            )

        postdata = dict(isTest="false",
                goformId="SEND_SMS",
                Number=phone,
                sms_time=time.strftime("%y;%m;%d;%H;%M;%S;")+TZ,
                MessageBody=encodeUcs2(text),
                encode_type="UNICODE",
                ID=-1
            )
        if self.notCallback:
            postdata['notCallback'] = "true"
        self.logger.debug(uri)
        self.logger.debug(postdata)

        return self.post(uri,data=postdata)


    @_httpclient.get_json
    def _get_count(self,*a,**kw):

        """
            {"sms_received_flag":"",
            "sms_unread_num":"0",
            "sms_dev_unread_num":"0",
            "sms_sim_unread_num":"0"}
        """

        uri = "{base}/goform/goform_get_cmd_process?"\
            "multi_data=1&isTest=false&sms_received_flag_flag=0&sts_received_flag_flag=0&"\
            "cmd=sms_received_flag,sms_unread_num,sms_read_num&_={date}".format(
                base=self.base_url,
                date=int(time.time()*1000)
            )
        return self.get(uri,*a,**kw)

    @_httpclient.get_json
    def _capacity_info(self,*a,**kw):

        """
        Request URL:http://192.168.0.1/goform/goform_get_cmd_process?isTest=false&cmd=sms_capacity_info&_=1477750277341

            returns {
            'sms_nv_send_total': '6',
            'sms_sim_rev_total': '0',
            'sms_sim_draftbox_total': '0',
            'sms_sim_send_total': '0',
            'sms_nv_draftbox_total': '0',
            'sms_sim_total': '5',
            'sms_nv_rev_total': '42',
            'sms_nv_total': '100'
            }

        """
        uri = "{base}/goform/goform_get_cmd_process?"\
            "isTest=false&cmd=sms_capacity_info&_={date}".format(
                base=self.base_url,
                date=int(time.time()*1000))
        return self.get(uri,*a,**kw)


    @_httpclient.get_json
    def _get_messages(self,tags=1,limit=100, *a,**kw):

        """
        {
            "messages": [
            {
            "id": "41",
            "number": "00420061006C0061006E00630065000D",
            "content": "04110430043B0430043D0441003A0030002C003600300440002C041B0438043C04380442003A0030002C0030003104400020041E043F043B0430044704380432043004390442043500200438043D044204350440043D043504420020043D04300020043204410435044500200443044104420440043E043904410442043204300445002004410020043504340438043D043E0433043E002004410447043504420430002004410020043E043F0446043804350439002000AB041504340438043D044B043900200438043D044204350440043D0435044200BB0021002000200418043D0444043E003A0020006F006E0065002E006D00740073002E00720075",
            "tag": "1",
            "date": "16,07,13,13,40,42,+16",
            "draft_group_id": "",
            "received_all_concat_sms": "1",
            "concat_sms_total": "2",
            "concat_sms_received": "2",
            "sms_class": "4",
            "sms_mem": "nv"
            }
            ]
            }
        """
        #TODO: urlencode вместо format
        uri = "{base}/goform/goform_get_cmd_process?"\
            "isTest=false&cmd=sms_data_total&page=0&data_per_page={max}&mem_store=1&tags={tags}&"\
            "order_by=order+by+id+desc&_={date}".format(
                max=limit,
                base=self.base_url,
                date=int(time.time()*1000),
                tags=tags
            )
        return self.get(uri,*a,**kw)

    @_httpclient.get_json
    def _set_msg_read(self,msg_id,*a,**kw):
        to_mark = ';'.join(msg_id)+';'
        uri = "{base}/goform/goform_set_cmd_process".format(
                base=self.base_url
            )
        postdata = dict(isTest="false",
                    goformId="SET_MSG_READ",
                    msg_id=to_mark,
                    tag=0
            )
        if self.notCallback:
            postdata['notCallback'] = "true"

        self.logger.debug(uri)
        self.logger.debug(postdata)
        return self.post(uri,data=postdata)

    @_httpclient.get_json
    def _delete_msg(self,msg_id,*a,**kw):
        to_mark = ';'.join(msg_id)
        uri = "{base}/goform/goform_set_cmd_process".format(
                base=self.base_url
            )
        postdata = dict(isTest="false",
                    goformId="DELETE_SMS",
                    msg_id=to_mark,
            )
        if self.notCallback:
            postdata['notCallback'] = "true"
        return self.post(uri,data=postdata)

    async def send(self,phone,text,*a,**kw):
        try:
            res = await self._send_sms(phone,text)
            assert res.get("result") == "success", 'Modem cant send message'
        except Exception as e:
            self.logger.error(e)
            return False
        else:
            return True

    def unread(self):
        '''
           returns async
        '''
        return self.messages(tags=1)

    async def messages(self,tags=RECIEVED,limit=100):
        '''
        messages from modem
        '''

        msgs = await self._get_messages(tags=tags,limit=limit)
        msgs = msgs.get('messages',[])

        read = []
        for m in msgs:
            m['phone'] = trydecodeHexUcs2(m.get('number'))
            m['text'] = trydecodeHexUcs2(m.get('content'))
            m['to'] = self.callie
            try:
                date = pytz.datetime.datetime.strptime(m['date'].rsplit(',',1)[0], '%y,%m,%d,%H,%M,%S' )
                date = date.replace(tzinfo=tzlocal())
            except Exception as e:
                self.logger.warning(e)
            else:
                m['rawdate'],m['date'] = m['date'],date
            read.append(m['id'])
        if read:
            await self.mark_read(read)
        return msgs

    def mark_read(self,ids):
        return self._set_msg_read(ids)


    async def delete(self,ids_to_delete):
        ids = ids_to_delete[:]
        while ids:
            to,ids = ids[:50],ids[50:]
            await self._delete_msg(to)


    async def capacity(self):
        cap = await self._capacity_info()
        inbox = int(cap.get('sms_sim_rev_total',0)) + int(cap.get('sms_nv_rev_total',0))
        sent =  int(cap.get('sms_sim_send_total',0)) + int(cap.get('sms_nv_send_total',0))
        capacity = max(int(cap.get('sms_nv_total',0)), int(cap.get('sms_sim_total',0)))

        ret = {
            'inbox': inbox,
            'sent': sent,
            'total': inbox + sent,
            'capacity': capacity or 100
        }

        self.total_count = inbox + sent
        self.max = capacity or 100
        self.logger.debug(ret)
        return ret

    async def clean(self,limit=100):
        ids = []
        for m in await self.messages(tags=10, limit=limit):
            ids.append(m['id'])
        for m in await self.messages(tags=2, limit=limit):
            ids.append(m['id'])
        return await self.delete(ids)


