#!/usr/bin/env python

"""
scribble.py - A simple touch input to framebuffer demo for the Kobo Mini.

Copyright (C) 2014 David Boddie <david@boddie.org.uk>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import os, struct, sys, time
import linuxfb, renderer

def get_touch(f):

    """Read events from the input device until a complete touch point has been
    processed. Returns the x and y coordinates in device units and the pressure
    of the touch.
    """
    
    x = y = p = None
    b = ""
    
    while True:
    
        try:
            b += os.read(f, 16 - len(b))
        except OSError:
            if x != None and y != None and p != None:
                break
        
        if len(b) < 16:
            continue
        
        time1, time2, type, code, value = struct.unpack("<IIHHi", b[:16])
        b = b[16:]
        
        if type == 3:         # EV_ABS
            if code == 0:       # ABS_X
              x = value
            elif code == 1:     # ABS_Y
              y = value
            elif code == 0x18:  # ABS_PRESSURE
              p = value
    
    return x, y, p


if __name__ == "__main__":

    if len(sys.argv) == 3:
        dev = sys.argv[1]
        fbdev = sys.argv[2]
    else:
        dev = "/dev/input/event0"
        fbdev = "/dev/fb0"
    
    fb = linuxfb.Framebuffer(fbdev)
    r = renderer.Renderer(fb)
    
    f = os.open(dev, os.O_RDONLY | os.O_NONBLOCK)
    
    r.fill(0, 0, r._width, r._height, r.pack_colour(255, 255, 255))
    
    while True:
    
        x, y, p = get_touch(f)
        r.fill(x-3, y-3, 7, 7, r.pack_colour(0, 0, 0))

