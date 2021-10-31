from threading import Thread
from Logger import Logger,systemLogFile
from wsServer import ClientModule,wifi_connected
from httpServer import HttpServerModule
from ledControl import LEDControl
import RPi.GPIO as GPIO
import asyncio
import time
import subprocess


class Main(Logger):
    def __init__(self):        
        fh = systemLogFile('system.log')
        self.fileHandler = fh
        super().__init__('main',fileHandler=fh)

        # init GPIO
        GPIO.setmode(GPIO.BCM)

        self.mainLoop = asyncio.get_event_loop()
        if not self.mainLoop.is_running():
            Thread(name='mainLoopThread',target=self.mainLoop.run_forever,daemon=True).start()


        # start modules
        self.client = ClientModule(self)        
        self.client.start()
        self.http = HttpServerModule(self)
        self.http.start()
        self.led = LEDControl(self)
        self.led.start()

    def enableAP(self):
        "enable AP mode"
        subprocess.run(['systemctl', 'enable', 'wpa_supplicant@ap0.service'])
        subprocess.run(['systemctl', 'disable', 'wpa_supplicant@wlan0.service'])
        subprocess.run(['systemctl', 'start', 'wpa_supplicant@ap0.service'])        
        self.debug('Switched to <AccessPoint> mode.')
        

    def enableClient(self):
        subprocess.run(['systemctl', 'enable', 'wpa_supplicant@wlan0.service'])
        subprocess.run(['systemctl', 'disable', 'wpa_supplicant@ap0.service'])
        subprocess.run(['systemctl', 'start', 'wpa_supplicant@wlan0.service'])        
        self.debug('Switched to <Client> mode.')
        

    def start(self):
        while True:
            time.sleep(10)
            if not wifi_connected():
                self.debug('Wifi not connected, Switching to AP mode')
                # self.enableAP()
           


if __name__ == '__main__':
    main = Main()
    main.start()