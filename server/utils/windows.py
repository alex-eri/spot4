from win32 import win32serviceutil
from win32 import win32service
from win32 import win32event
import os
import sys
import time
import servicemanager

class ServiceLauncher(win32serviceutil.ServiceFramework):
    _svc_name_ = 'Spot4'
    _svc_display_name_ ='Spot4 Hotspot controller'
    _exe_args_ = '--service '

    main = None

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        sys.running = False
        win32event.SetEvent(self.hWaitStop)

    def SvcDoRun(self):
        self.main.main()


def startservice(main,exeargs=[]):
    ServiceLauncher.main = main
    ServiceLauncher._exe_args_ += " ".join(exeargs)
    servicemanager.Initialize()
    servicemanager.PrepareToHostSingle(ServiceLauncher)
    servicemanager.StartServiceCtrlDispatcher()

def start(main,argv,exeargs):
    ServiceLauncher.main = main
    ServiceLauncher._exe_args_ += " ".join(exeargs)
    win32serviceutil.HandleCommandLine(ServiceLauncher,argv=argv)
