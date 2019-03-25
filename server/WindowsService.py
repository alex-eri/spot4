import servicemanager
import socket
import sys
import win32event
import win32service
import win32serviceutil

import threading
import logging
import os
import signal

logger = logging.getLogger('service')
debug = logger.debug

import subprocess

class TestService(win32serviceutil.ServiceFramework):
    _svc_name_ = "TestService"
    _svc_display_name_ = "Test Service"

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        socket.setdefaulttimeout(60)
        import server
        self.startstop = server.premain(daemon=True)

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)

    def SvcDoRun(self):
        start,stop,wait,kill = self.startstop
        start()
        rc = None
        while rc != win32event.WAIT_OBJECT_0:
            rc = win32event.WaitForSingleObject(self.hWaitStop, 5000)
        stop()
        wait()


if __name__ == '__main__':
    if len(sys.argv) == 1:
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(TestService)
        servicemanager.StartServiceCtrlDispatcher()
    else:
        win32serviceutil.HandleCommandLine(TestService)
