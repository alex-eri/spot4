import logging
from . import http
import urllib.parse
import time

import sys, traceback


class Client(http.Client):
    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self.confirm_url = kw.pop('confirm_url')

    def _send_sms(self, phone, text):
        if super()._send_sms(phone, text):
            return self.request(self.confirm_url)
