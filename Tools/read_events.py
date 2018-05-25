#!/usr/bin/env python

"""
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

def read_events(f):

    b = ""
    
    while True:
    
        try:
            b += os.read(f, 16 - len(b))
        except OSError:
            continue
        
        if len(b) < 16:
            continue
        
        time1, time2, type, code, value = struct.unpack("<IIHHi", b[:16])
        b = b[16:]
        
        print time1, time2, type, code, value


if __name__ == "__main__":

    if len(sys.argv) == 2:
        dev = sys.argv[1]
    else:
        dev = "/dev/input/event0"
    
    f = os.open(dev, os.O_RDONLY | os.O_NONBLOCK)
    read_events(f)
