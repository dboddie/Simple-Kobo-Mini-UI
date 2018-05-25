#!/usr/bin/env python

"""
make_test_picture_data.py - Make display test data for the Kobo Mini.

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

import struct, sys

red_shift, red_bits = 11, 5
green_shift, green_bits = 5, 6
blue_shift, blue_bits = 0, 5

red_max = (1 << red_bits) - 1
green_max = (1 << green_bits) - 1
blue_max = (1 << blue_bits) - 1

red_scale = red_max/255.0
green_scale = green_max/255.0
blue_scale = blue_max/255.0

if __name__ == "__main__":

    if len(sys.argv) != 2:
    
        sys.stderr.write("Usage: %s <output file>\n" % sys.argv[0])
        sys.exit(1)
    
    f = open(sys.argv[1], "wb")
    
    for i in range(256):
    
        r = int(i * red_scale) << red_shift
        g = int(i * green_scale) << green_shift
        b = int(i * blue_scale) << blue_shift
        v = struct.pack("<H", r | g | b)
        # Write two lines of data.
        f.write(v * 800 * 2)
    
    f.write(88 * 800 * "\xff\xff")
    
    sys.exit()
