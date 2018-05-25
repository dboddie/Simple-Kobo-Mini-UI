#!/usr/bin/env python
# -*- coding: UTF-8 -*-

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

import os, sys
import daemon
import buxpaper

def main():

    launcher_path = os.path.join(buxpaper.appdir, "Launcher", "launcher.py")
    sys.exit(os.system(launcher_path))

if __name__ == "__main__":

    if "-d" in sys.argv:
        with daemon.DaemonContext():
            main()
    else:
        main()
