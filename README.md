Simple User Interface for the Kobo Mini 
=======================================

Introduction
------------

This repository contains Python packages, modules and tools to help construct a
simple user interface for the Kobo Mini eReader based on the Linux kernel
prepared by a Marek Gibek. See the following thread in the MobileRead forums
and repository on GitHub:

https://www.mobileread.com/forums/showthread.php?p=2737314#post2737314
https://github.com/marek-g/kobo-kernel-2.6.35.3-marek

Notes
-----

This is not a complete, out-of-the-box system in itself. Not everything needed
for a working system is included. In particular, it relies on having a suitable
Debian distribution installed on the device, which was Debian 6 (Squeeze) at
the time the system was created. It also requires a version of PyQt4 that was
built against a QWS version of Qt - one that uses the Linux framebuffer instead
of X11 as a display system.

Nonetheless, it is hoped that the software provided here is useful, or at least
helpful to others implementing similar systems and user interfaces.

Authors and License
-------------------

David Boddie <david@boddie.org.uk>

Unless indicated otherwise, the contents of this package are licensed under the
GNU General Public License version 3 (or later).

```
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
```
