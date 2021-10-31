from threading import Thread
from Logger import Logger
import board
import busio
import adafruit_tlc59711
from time import perf_counter as timer
import time

MODES = {'eye':[],'ring':[]}

def registerMode(buttonName):    
    def deco(func):
        if func.__name__.startswith('eye'):
            MODES['eye'].append((buttonName,func.__name__))
        elif func.__name__.startswith('ring'):
            MODES['ring'].append((buttonName,func.__name__))
        else:
            raise Exception('Invalid mode name')
        return func    
    return deco

# LED orders:
# on the ring: 1,2,3,6,7,4,5
# Eyes: E1L 8,  E1R: 9
#       E2L: 10, E2R: 11



class LEDControl(Thread,Logger):
    _RING_ORDER = [1,2,3,6,7,4,5]
    _EYE_ORDER = [8,9,10,11]
    _ORDER = [1,2,3,6,7,4,5, # ring order
                8,9,10,11] # eye order
    def __init__(self,main):
        self.main = main
        super().__init__(daemon=True)
        Logger.__init__(self,'LED',fileHandler = self.main.fileHandler)
        spi = busio.SPI(board.SCK, MOSI=board.MOSI)
        self.pixels = adafruit_tlc59711.TLC59711(spi, pixel_count=12)
        self._FPS = 24
        self.state = [[0,0,0]]*(len(self._ORDER))
        self.ringGenerator = None
        self.eyeGenerator = None
        self.brightness = 100 # between 0 - 100
    
    def show(self,mode=''):
        self.debug(f'Showing LED mode {mode}')
        if mode.startswith('eye'):
            self.eyeGenerator = getattr(self,mode,lambda x:None)()
        elif mode.startswith('ring'):
            self.ringGenerator = getattr(self,mode,lambda x:None)()
        else:
            self.debug(f'LED mode {mode} not found')

    @registerMode('Blink')
    def eyeBlink(self):
        "eye blink"
        state = 0
        last = self._FPS 
        while 1:
            if last:
                yield [[state * 255,state * 255,state * 255]]*(len(self._EYE_ORDER))
                last -= 1
            if last == 0:
                state = 1 if state == 0 else 0
                last = self._FPS
            
    
    def getNextRingState(self):
        "return next ring state"
        if self.ringGenerator is None:
            return [[0,0,0]]*(len(self._RING_ORDER))
        try:
            return next(self.ringGenerator)
        except StopIteration:
            self.ringGenerator = None
            return [[0,0,0]]*(len(self._RING_ORDER))


    def getNextEyeState(self):
        "return next eye state"
        if self.eyeGenerator is None:
            return [[0,0,0]]*(len(self._EYE_ORDER))
        try:
            return next(self.eyeGenerator)
        except StopIteration:
            self.eyeGenerator = None
            return [[0,0,0]]*(len(self._EYE_ORDER))

    def Brightness(self,color):
        "adjust brightness, the color I will just use 0 - 255"
        return [max(0,min(int(65535/255*c*self.brightness/100),65535)) for c in color]

    def run(self):
        while 1:
            t0 = timer()
            r = self.getNextRingState()
            e = self.getNextEyeState()
            ns = r + e
            for i,n,o in zip(self._ORDER,ns,self.state):
                if n != o:                    
                    self.pixels.set_pixel(i,self.Brightness(n))
                    self.state[i] = n
            self.pixels.show()
            dt = timer()-t0
            if dt < 1/self._FPS:
                time.sleep(1/self._FPS-dt)
            else:
                self.debug(f'LED update took {dt}s')


        
    