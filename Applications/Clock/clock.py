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

import math, sys
import buxpaper

from PyQt4.QtCore import QDateTime, QRect, QTimer, Qt
from PyQt4.QtGui import QApplication, QBrush, QFont, QFontMetrics, QPainter, QPen

class Clock(buxpaper.Window):

    def __init__(self):
    
        buxpaper.Window.__init__(self)
        
        start_time = QDateTime.currentDateTime().time()
        self.displayTime = (start_time.hour(), start_time.minute())
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.updateTime)
        self.timer.setInterval(5000)
        self.timer.start()
        
        self.foreground = QPen(self.palette().foreground().color())
        self.background = self.palette().background()
        
        font = QFont(QApplication.font())
        desktop = QApplication.desktop()
        geometry = desktop.screenGeometry()
        font.setPixelSize(min(geometry.width()/8, geometry.height()/4))
        self.setFont(font)
        
        self.maxHeight = QFontMetrics(font).height()
    
    def updateTime(self):
    
        now = QDateTime.currentDateTime().time()
        newTime = (now.hour(), now.minute())
        
        if newTime != self.displayTime:
        
            self.displayTime = newTime
            
            w, h, cx, cy, r = self.clockFaceDetails()
            self.update(QRect(cx - r * 1.1, cy - r * 1.1, 2.2 * r, 2.2 * r))
            
            QTimer.singleShot(500, self.updateText)
    
    def updateText(self):
    
        rect = QRect(0, self.height() * 0.75, self.width(), self.maxHeight)
        self.update(rect)
    
    def clockFaceDetails(self):
    
        w = self.width()
        h = self.height() * 0.75
        cx = w / 2
        cy = h / 2
        r = min(w, h)/2 * 0.75
        
        return w, h, cx, cy, r
        
    def paintEvent(self, event):
    
        w, h, cx, cy, r = self.clockFaceDetails()
        
        painter = QPainter()
        painter.begin(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        painter.fillRect(event.rect(), self.background)
        
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
        
        hour, minute = self.displayTime
        hour = hour % 12
        
        angle = (-math.pi / 2) + (2 * hour * math.pi/12) + (2 * math.pi/12 * minute/60.0)
        
        painter.setPen(QPen(Qt.black, 8, Qt.SolidLine, Qt.RoundCap))
        painter.drawLine(cx, cy, cx + (0.55 * r * math.cos(angle)),
                                 cy + (0.55 * r * math.sin(angle)))
        
        angle = (-math.pi / 2) + (2 * minute * math.pi/60)
        
        painter.drawLine(cx, cy, cx + (0.8 * r * math.cos(angle)),
                                 cy + (0.8 * r * math.sin(angle)))
        
        painter.setPen(QPen(self.foreground))
        painter.setFont(self.font())
        rect = QRect(0, self.height() * 0.75, self.width(), self.maxHeight)
        painter.drawText(rect, Qt.AlignCenter,
                         "%02i:%02i" % self.displayTime)
        painter.end()


if __name__ == "__main__":

    app = buxpaper.Application()
    c = Clock()
    c.showFullScreen()
    sys.exit(app.exec_())
