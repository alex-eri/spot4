import win32serviceutil
import win32service
import win32event
import os
import sys
import time
import servicemanager

class ServiceLauncher(win32serviceutil.ServiceFramework):
    _svc_name_ = 'Spot4'
    _scv_display_name_ ='hotspot controller'

    main = None

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        sys.running = False
        win32event.SetEvent(self.hWaitStop)

    def SvcDoRun(self):
        self.main()


def start():
    if len(sys.argv) == 1:
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(ServiceLauncher)
        servicemanager.StartServiceCtrlDispatcher()
    else:
        win32serviceutil.HandleCommandLine(ServiceLauncher)
