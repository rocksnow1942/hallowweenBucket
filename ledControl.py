from threading import Thread

from websockets import framing
from Logger import Logger
import board
import busio
import adafruit_tlc59711
from time import perf_counter as timer
import time
import random

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
    _NAMED_COLOR = {
            'red':[255,0,0],
            'green':[0,255,0],
            'blue':[0,0,255],
            'yellow':[255,255,0],
            'cyan':[0,255,255],
            'purple':[255,0,255],
            'white':[255,255,255],
            'black':[0,0,0],
            'orange':[255,165,0],            
            'pink':[255,192,203],
            'brown':[165,42,42],            
        }
    _COLOR_NAMES = ['red','green','blue','yellow','cyan','purple','white','orange','pink','brown']
    def __init__(self,main):
        self.main = main
        super().__init__(daemon=True)
        Logger.__init__(self,'LED',fileHandler = self.main.fileHandler)
        spi = busio.SPI(board.SCK, MOSI=board.MOSI)
        self.pixels = adafruit_tlc59711.TLC59711(spi, pixel_count=12)
        self._FPS = 24     
        self.ringGenerator = None
        self.eyeGenerator = None
        self.brightness = 70 # between 0 - 100
    
    @property
    def eyeLength(self):
        return len(self._EYE_ORDER)
    @property
    def ringLength(self):
        return len(self._RING_ORDER)

    def frames(self,duration=1):
        return int(duration*self._FPS)

    def color(self,name=None):
        "return a named color"
        if not name:
            name = random.choice(self._COLOR_NAMES)            
        return self._NAMED_COLOR.get(name,[0,0,0])

    def randColor(self):
        return [random.randint(0,255) for _ in range(3)]

    def show(self,mode=''):
        self.debug(f'Showing LED mode {mode}')
        if mode.startswith('eye'):
            self.eyeGenerator = getattr(self,mode,lambda x:None)()
        elif mode.startswith('ring'):
            self.ringGenerator = getattr(self,mode,lambda x:None)()
        else:
            self.debug(f'LED mode {mode} not found')

    @registerMode('White Blink')
    def eyeBlink(self):
        "eye blink"
        state = 0
        last = self._FPS 
        while 1:
            if last:
                yield [[state * 255,state * 255,state * 255]]*self.eyeLength
                last -= 1
            if last == 0:
                state = 1 if state == 0 else 0
                last = self._FPS

    @registerMode('Random Blink')
    def eyeBlinkRand(self):
        "eye blink"
        state = 0
        last = self._FPS / 2
        eyc = [ self.randColor() for i in range(self.eyeLength)]
        while 1:
            if last:
                yield eyc
                last -= 1
            if last == 0:
                state = 1 if state == 0 else 0
                last = self._FPS
                if state:
                    eyc = [ self.randColor() for i in range(self.eyeLength)]
                else:
                    eyc = [ [0,0,0] ] * self.eyeLength

    @registerMode('Random Breath')
    def eyeBreathRand(self):
        "eye breath"                
        while 1:
            eye  = [self.color() for i in range(self.eyeLength)]
            for e in zip(*[self.breath(i,duration=1.8) for i in eye]):
                yield e
            # keep dark for 0.3 seconds
            for _ in range(self.frames(duration = 0.5)):
                yield [self.color('black')]* self.eyeLength

    @registerMode('Twin Breath')
    def eyeBreathTwinRand(self):
        "eye breath"                
        while 1:
            c1 = self.color() 
            c2 = self.color() 
            eye  = [c1,c1,c2,c2]
            for e in zip(*[self.breath(i,duration=1.8,end=[j*0.002 for j in i]) for i in eye]):
                yield e
            # keep dark for 0.3 seconds
            for _ in range(self.frames(duration = 1)):
                yield [[j*0.002 for j in i] for i in eye]
    
    @registerMode('Cycle Breath')
    def eyeBreathCycle(self):
        "eye breath"                
        while 1:
            for color in ['red','green','blue','cyan','purple','white']:
                # blink random times then change color 
                for i in range(random.randint(1,5)):                                                
                    eye  = [self.color(color) for i in range(self.eyeLength)]
                    for e in zip(*[self.breath(i,duration=1.8) for i in eye]):
                        yield e
                    # keep dark for 0.3 seconds
                    for _ in range(self.frames(duration = 0.5)):
                        yield [self.color('black')]* self.eyeLength

    @registerMode('Random Wheel')
    def ringRandomWheel(self):
        "cycle ring"
        current = 0
        onCount = 2
        moveTime = 0.1
        transitionTime = 0.5
        currentColor = self.color('green')
        colorTransition = self.transition(self.color('white'),self.color('green'),transitionTime)
        while 1:
            newState = [self.color('black')] * self.ringLength
            for i in range(current,current+onCount):
                idx = i % self.ringLength
                try:
                    color = next(colorTransition)
                except StopIteration:
                    newColor = self.randColor()
                    colorTransition = self.transition(currentColor,newColor,transitionTime)
                    currentColor = newColor
                    color = next(colorTransition)
                newState[idx] = color
            for i in range(self.frames(moveTime)):
                yield newState            
            current += 1
            if current > self.ringLength:
                current = 0

    @registerMode('Breath')
    def ringBreathCycle(self):
        dimPercent = 0.03
        while 1:
            for color in ['red','green','blue','cyan','purple','white']:
                # blink random times then change color 
                for i in range(random.randint(1,3)):                                                
                    ring  = [self.color(color) for i in range(self.ringLength)]
                    for e in zip(*[self.breath(i,duration=1.8,end=[j*dimPercent for j in i]) for i in ring]):
                        yield e
                    # keep dark for 0.3 seconds
                    for _ in range(self.frames(duration = 0.5)):
                        yield [[j*dimPercent for j in i] for i in ring]


    def transition(self,f,t,duration):
        "transition from f to t, over duration seconds"
        frames = self.frames(duration)
        for i in range(frames):
            yield [ fi + (ti-fi) / (frames-1) * i  for fi,ti in zip(f,t)]
            

    def breath(self,color=[255,255,255],duration=1,end=[0,0,0],):
        "breath effect, from dark to color, then back to dark, total last for duration seconds"
        yield from self.transition(end,color,duration/2)
        yield from self.transition(color,end,duration/2)
    
        
    
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

    def Brightness(self,color,dim=False):
        "adjust brightness, the color I will just use 0 - 255"
        if dim:
            brightness = self.brightness
        else:
            brightness = 100
        return [max(0,min(int(65535/255*c*brightness/100),65535)) for c in color]

    def run(self):
        while 1:
            t0 = timer()
            r = self.getNextRingState()
            e = self.getNextEyeState()
            # only adjust brightness for the eyle leds
            ns = [self.Brightness(n,dim=True) for n in r]  + [self.Brightness(n,dim=True) for n in e]
            for i,n in zip(self._ORDER,ns):
                self.pixels.set_pixel(i,n)
            self.pixels.show()
            dt = timer()-t0
            if dt < 1/self._FPS:
                time.sleep(1/self._FPS-dt)
            else:
                self.debug(f'LED update took {dt}s')


        
    