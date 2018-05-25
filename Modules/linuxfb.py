"""
linuxfb.py - Classes for accessing the Linux framebuffer.

Copyright (C) 2009 David Boddie <david@boddie.org.uk>

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

import array, fcntl, mmap, struct

# See /usr/include/linux/fb.h for the origin of these values:
FBIOGET_VSCREENINFO = 0x4600
FBIOPUT_VSCREENINFO = 0x4601
FBIOGET_FSCREENINFO = 0x4602

FBIOBLANK = 0x4611
VESA_NO_BLANKING   = 0
VESA_VSYNC_SUSPEND = 1
VESA_HSYNC_SUSPEND = 2
VESA_POWERDOWN     = 3

FB_TYPE_PACKED_PIXELS      = 0
FB_TYPE_PLANES             = 1
FB_TYPE_INTERLEAVED_PLANES = 2
FB_TYPE_TEXT               = 3
FB_TYPE_VGA_PLANES         = 4

FB_VISUAL_MONO01             = 0
FB_VISUAL_MONO10             = 1
FB_VISUAL_TRUECOLOR          = 2
FB_VISUAL_PSEUDOCOLOR        = 3
FB_VISUAL_DIRECTCOLOR        = 4
FB_VISUAL_STATIC_PSEUDOCOLOR = 5

class ScreenInfo:

    def __init__(self, device):
    
        self._device = device
        
        self._array_map = {}
        i = 0
        for name, format in self._definitions:
            self._array_map[name] = (i, format)
            i += struct.calcsize(format)
        
        self._struct_length = i
        
        self.get_info()
    
    def __getattr__(self, name):
    
        try:
            index, format = self._array_map[name]
        except KeyError:
            raise AttributeError
        
        bytes = struct.calcsize(format)
        value = struct.unpack(format, self._array[index:index + bytes])
        if len(value) == 1:
            return value[0]
        else:
            return value
    
    def __setattr__(self, name, value):
    
        if name.startswith("_"):
            self.__dict__[name] = value
            return
        
        try:
            index, format = self._array_map[name]
        except KeyError:
            raise AttributeError
        
        if type(value) != tuple:
            value = (value,)
        
        data = array.array("c", struct.pack(format, *value))
        self._array[index:index + len(data)] = data
    
    def get_info(self):
    
        self._array = array.array("c", ["\x00"]*self._struct_length)
        # Obtain data about the device in the array (mutable = 1).
        fcntl.ioctl(self._device, self._get, self._array, 1)
    
    def put_info(self):
    
        if hasattr(self, "_put"):
            # Obtain data about the device in the array (mutable = 1).
            fcntl.ioctl(self._device, self._put, self._array, 0)
        
        self.get_info()
    

class VirtualScreenInfo(ScreenInfo):

    _definitions = (
        ("xres", "I"),
        ("yres", "I"),
        ("xres_virtual", "I"),
        ("yres_virtual", "I"),
        ("xoffset", "I"),
        ("yoffset", "I"),
        ("bits_per_pixel", "I"),
        ("grayscale", "I"),
        ("red", "III"),
        ("green", "III"),
        ("blue", "III"),
        ("transp", "III"),
        ("nonstd", "I"),
        ("activate", "I"),
        ("height", "I"),
        ("width", "I"),
        ("accel_flags", "I"),
        ("pixclock", "I"),
        ("left_margin", "I"),
        ("right_margin","I"),
        ("upper_margin", "I"),
        ("lower_margin", "I"),
        ("hsync_len", "I"),
        ("vsync_len", "I"),
        ("sync", "I"),
        ("vmode", "I"),
        ("rotate", "I"),
        ("reserved", "IIIII")
        )
    
    _get = FBIOGET_VSCREENINFO
    _put = FBIOPUT_VSCREENINFO


class FixedScreenInfo(ScreenInfo):

    _definitions = (
        ("id", "16s"),
        ("smem_start", "L"),
        ("smem_len", "I"),
        ("type", "I"),
        ("type_aux", "I"),
        ("visual", "I"),
        ("xpanstep", "H"),
        ("ypanstep", "H"),
        ("ywrapstep", "H"),
        ("line_length", "I"),
        ("mmio_start", "L"),
        ("mmio_len", "I"),
        ("accel", "I"),
        ("reserved", "HHH")
        )
    
    _get = FBIOGET_FSCREENINFO


class Framebuffer:

    def __init__(self, path):
    
        self._device = open(path, "r+")
        self._buffer = None
    
    def blank(self, value = VESA_POWERDOWN):
    
        fcntl.ioctl(self._device, FBIOBLANK, value)
    
    def unblank(self):
    
        fcntl.ioctl(self._device, FBIOBLANK, VESA_NO_BLANKING)
    
    def virtual_screen_info(self):
    
        return VirtualScreenInfo(self._device)
    
    def fixed_screen_info(self):
    
        return FixedScreenInfo(self._device)
    
    def get_buffer(self):
    
        if not self._buffer:
        
            v = VirtualScreenInfo(self._device)
            
            bytes_per_pixel = v.bits_per_pixel / 8
            if v.bits_per_pixel % 8 != 0:
                bytes_per_pixel += 1
            
            extra = v.xres % 32
            if extra != 0:
                extra = (32 - extra)*bytes_per_pixel
            
            self._buffer = mmap.mmap(self._device.fileno(), ((v.xres * bytes_per_pixel) + extra) * v.yres)
        
        return self._buffer
