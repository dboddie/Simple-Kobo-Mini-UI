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

import os, sys

from PyQt4.QtCore import QPoint, QPointF, QRect, QSize, Qt
from PyQt4.QtGui import *

def openDocument(path):

    try:
        f = open(path)
        line = f.readline()
        width, height = map(int, line.strip().split("x"))
        
        image = QImage(800, 600, QImage.Format_RGB16)
        image.fill(QColor(255, 255, 255))
        
        painter = QPainter()
        painter.begin(image)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(QPen(QColor(0, 0, 0), 4))

        n = int(f.readline())

        while n > 0:
            line = f.readline().strip()
            if not line:
                break
            
            obj = []
            for point in line.split():
                x, y = map(int, point.split(","))
                obj.append(QPoint(x, y))
            painter.drawPolyline(*obj)
            n -= 1
    
    except (IOError, ValueError):
        return
    
    painter.end()
    
    return image
    

if __name__ == "__main__":

    app = QApplication(sys.argv)
    
    if len(app.arguments()) < 2:
    
        sys.stderr.write("Usage: %s <drawing file> ...\n" % app.arguments()[0])
        sys.exit(1)
    
    for path in app.arguments()[1:]:
    
        path = unicode(path)
        image = openDocument(path)
        name = os.path.split(path)[1]
        stem = os.path.splitext(name)[0]
        image.save(stem + os.extsep + "png")
    
    sys.exit()
