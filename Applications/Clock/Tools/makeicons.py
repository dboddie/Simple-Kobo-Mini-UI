#!/usr/bin/env python

"""
makeicons.py - Create icon for the Clock application.

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

import math, os, sys
from PyQt4.QtCore import *
from PyQt4.QtGui import *

def create_image(w, h):

    image = QImage(w, h, QImage.Format_ARGB32)
    image.fill(qRgba(0, 0, 0, 0))
    return image

if __name__ == "__main__":

    app = QApplication(sys.argv)
    
    w = 180
    h = 135
    cx = w / 2
    cy = h / 2
    r = min(w, h)/2 * 0.75
    image = create_image(w, h)
    
    painter = QPainter()
    painter.begin(image)
    painter.setRenderHint(QPainter.Antialiasing)
    
    painter.setBrush(QBrush(Qt.NoBrush))
    painter.setPen(QPen(Qt.black))
    painter.drawEllipse(cx - r * 1.1, cy - r * 1.1, 2.2 * r, 2.2 * r)
    
    painter.setBrush(QBrush(Qt.NoBrush))
    painter.setPen(QPen(Qt.black, 3))
    
    for i in range(12):
        angle = 2 * i * math.pi/12
        painter.drawLine(cx + (0.9 * r * math.cos(angle)),
                         cy + (0.9 * r * math.sin(angle)),
                         cx + (r * math.cos(angle)),
                         cy + (r * math.sin(angle)))
    
    painter.setPen(QPen(Qt.black, 2))
    
    for i in range(60):
        angle = 2 * i * math.pi/60
        painter.drawLine(cx + (0.95 * r * math.cos(angle)),
                         cy + (0.95 * r * math.sin(angle)),
                         cx + (r * math.cos(angle)),
                         cy + (r * math.sin(angle)))
    
    hour = QDateTime.currentDateTime().time().hour() % 12
    minute = QDateTime.currentDateTime().time().minute()
    
    angle = (-math.pi / 2) + (2 * hour * math.pi/12) + (2 * math.pi/12 * minute/60.0)
    
    painter.setPen(QPen(Qt.black, 5))
    painter.drawLine(cx, cy, cx + (0.5 * r * math.cos(angle)),
                             cy + (0.5 * r * math.sin(angle)))
    
    angle = (-math.pi / 2) + (2 * minute * math.pi/60)
    
    painter.setPen(QPen(Qt.black, 4))
    painter.drawLine(cx, cy, cx + (0.75 * r * math.cos(angle)),
                             cy + (0.75 * r * math.sin(angle)))
    
    painter.end()
    
    path = os.path.abspath(os.path.split(__file__)[0])
    path = os.path.split(path)[0]
    image.save(os.path.join(path, "clock.png"))
    
    sys.exit(0)
