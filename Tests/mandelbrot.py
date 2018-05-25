#!/usr/bin/env python

"""
mandelbrot.py - A sleep screen for the Kobo Mini.

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

import linuxfb, mxink, renderer

def draw_mandelbrot(x1, y1, x2, y2, r1, i1, r2, i2, render, colours):

    y = y1
    while y < y2:
    
        i = i1 + y * (i2 - i1)/(y2 - y1)
        x = x1
        
        while x < x2:
        
            r = r1 + x * (r2 - r1)/(x2 - x1)

            ci = r + i * 1j
            c = ci
            count = 0
            while count < 10 and abs(c) <= 2:
                c = c * c + ci
                count += 1

            colour = colours[count]
            render.fill(x, y, 1, 1, colour)
            
            x += 1
        
        y += 1

fb = linuxfb.Framebuffer("/dev/fb0")
r = renderer.Renderer(fb)
colours = map(lambda t: r.pack_colour(*t), map(lambda x: (x, x, x), range(0, 275, 25)))
draw_mandelbrot(0, 0, 800, 600, -2.1, -1.4, 1.1, 1.4, r, colours)
