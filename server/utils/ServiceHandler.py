
import threading
import sys
import logging
import os
import signal

logger = logging.getLogger('service')
debug = logger.debug

import subprocess

class Handler(object):

    # no parameters are permitted; all configuration should be placed in the
    # configuration file and handled in the Initialize() method
    def __init__(self):
        self.stopEvent = threading.Event()
        self.stopRequestedEvent = threading.Event()

    # called when the service is starting
    def Initialize(self, configFileName):
        import server
        #self.startstop = server.premain(daemon=True)
        #debug(self.startstop)
        #debug(configFileName)
        self.command_line = 'spot4.exe'


    # called when the service is starting immediately after Initialize()
    # use this to perform the work of the service; don't forget to set or check
    # for the stop event or the service GUI will not respond to requests to
    # stop the service
    def Run(self):
        #start,stop,wait,kill = self.startstop
        #debug(self.startstop)
        #start()
        debug(0)
        proc = subprocess.Popen([self.command_line], stderr=sys.stderr, shell=False)
        debug(1)
        self.stopRequestedEvent.wait()
        debug(2)
        #stop()
        os.kill(proc.pid, signal.SIGINT)
        #proc.terminate()
        #proc.wait(30)
        #proc.kill()
        debug(3)
        #wait()
        debug(4)
        self.stopEvent.set()
        #kill()
        debug(5)

    # called when the service is being stopped by the service manager GUI
    def Stop(self):
        self.stopRequestedEvent.set()
        self.stopEvent.wait()
