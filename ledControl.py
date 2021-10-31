from threading import Thread
from Logger import Logger
import board
import busio
import adafruit_tlc59711


class LEDControl(Thread,Logger):
    def __init__(self,main):
        self.main = main
        super().__init__()
        Logger.__init__(self,'LED',fileHandler = self.main.fileHandler)
        spi = busio.SPI(board.SCK, MOSI=board.MOSI)
        self.pixels = adafruit_tlc59711.TLC59711(spi, pixel_count=12)
        
    
        
    def run(self):
        pass    
        
    