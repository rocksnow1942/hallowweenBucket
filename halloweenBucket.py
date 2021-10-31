
# for work on pi and adata fruit circuit python lib


# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT

# simple demo of the TLC59711 16-bit 12 channel LED PWM driver.
# Shows the minimal usage - how to set pixel values in a few ways.
# Author: Tony DiCola

import board
import busio

import adafruit_tlc59711

print("tlc59711_simpletest.py")

# Define SPI bus connected to chip.
# You only need the clock and MOSI (output) line to use this chip.
spi = busio.SPI(board.SCK, MOSI=board.MOSI)
p = adafruit_tlc59711.TLC59711(spi, pixel_count=8)

# examples how to set the p:
# range:
# 0 - 65535
# or
# 0.0 - 1.0
# every pixel needs a color -
# give it just a list or tuple with 3 integer values: R G B

# set all p to a very low level
p.set_pixel_all((10, 10, 10))

# there are a bunch of other ways to set pixel.
# have a look at the other examples.
i = 0
c = 0
d = 1000
while True:
    color = [0,0,0]
    color[i%3] = c
    p.set_pixel_all(color)
    p.show()
    c+=d
    if c>64000:
        d=-d
    if c<1000:
        d=-d
        i+=1
    

    
    
        



    


