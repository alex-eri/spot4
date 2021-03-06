import win32serviceutil
import win32service
import win32event
import os
import sys
import time
import servicemanager

import logging
logger = logging.getLogger('service')

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
    print(main)
    logger.debug(main)
    ServiceLauncher._exe_args_ += " ".join(exeargs)
    logger.debug('init')
    servicemanager.Initialize()
    logger.debug('prepare')
    servicemanager.PrepareToHostSingle(ServiceLauncher)
    logger.debug('start')
    try:
        servicemanager.StartServiceCtrlDispatcher()
    except Exception as e:
        logger.critical(e)
        raise e
    else:
        logger.debug('started')

def start(main,argv,exeargs):
    ServiceLauncher.main = main
    ServiceLauncher._exe_args_ += " ".join(exeargs)
    win32serviceutil.HandleCommandLine(ServiceLauncher,argv=argv)
