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

import sys
import buxpaper

from PyQt4.QtCore import *
from PyQt4.QtGui import *

class Window(buxpaper.Window):

    def __init__(self):
    
        buxpaper.Window.__init__(self)
        
        self.mandelbrotWidget = MandelbrotWidget()
        
        self.sleepButton.clicked.connect(self.setSleepImage)
        self.sleepButton.show()
        self.mandelbrotWidget.viewChanged.connect(self.sleepButton.setEnabled)
        
        # Add a zoom button to the panel.
        zoomOutButton = buxpaper.Button("-")
        zoomOutButton.clicked.connect(self.mandelbrotWidget.zoomOut)
        self.panel.addWidget(zoomOutButton)
        
        layout = QVBoxLayout(self.contentWidget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.mandelbrotWidget)
    
    def closeEvent(self, event):
    
        self.mandelbrotWidget.worker.abort()
    
    def setSleepImage(self):
    
        self.sleepButton.setEnabled(False)
        self.saveSleepImage(self.mandelbrotWidget.image)


class MandelbrotWidget(QWidget):

    viewChanged = pyqtSignal(bool)
    
    def __init__(self, parent = None):
    
        QWidget.__init__(self, parent)
        self.setAttribute(Qt.WA_OpaquePaintEvent)
        
        self.image = QImage()
        self.pressed = False
        
        self.worker = Worker()
        self.worker.dataReady.connect(self.draw, Qt.QueuedConnection)
    
    def zoomIn(self, x, y):
    
        r1, i1, r2, i2 = self.worker.limits
        
        r = r1 + (x * (r2 - r1)) / self.width()
        i = i1 + (y * (i2 - i1)) / self.height()
        
        dr = (r2 - r1)/4
        di = (i2 - i1)/4
        
        # Take a copy of the part of the image we will zoom into.
        copy = self.image.copy(x - self.width()/4, y - self.height()/4,
                               self.width()/2, self.height()/2)
        
        self.image = copy.scaled(self.image.size())
        self.update()
        self.worker.draw(self.size(), r - dr, i - di, r + dr, i + di)
        self.viewChanged.emit(True)
    
    def zoomOut(self):
    
        r1, i1, r2, i2 = self.worker.limits
        
        r = (r1 + r2)/2
        i = (i1 + i2)/2
        
        dr = (r2 - r1)
        di = (i2 - i1)
        
        # Take a copy of the part of the image we will zoom into.
        copy = self.image.scaled(self.image.size()/2)
        self.image = QImage(self.image.size(), QImage.Format_RGB16)
        self.image.fill(QColor(255, 255, 255))
        painter = QPainter(self.image)
        painter.drawImage(self.width()/4, self.height()/4, copy)
        painter.end()
        self.update()
        self.worker.draw(self.size(), r - dr, i - di, r + dr, i + di)
        self.viewChanged.emit(True)
    
    def draw(self, rect, image):
    
        painter = QPainter()
        painter.begin(self.image)
        painter.drawImage(rect.topLeft(), image)
        painter.end()
        
        self.update(QRect(rect))
    
    def mousePressEvent(self, event):
    
        if self.pressed:
            return
        
        self.pressed = True
        self.zoomIn(event.x(), event.y())
    
    def mouseReleaseEvent(self, event):
    
        self.pressed = False
    
    def paintEvent(self, event):
    
        painter = QPainter()
        painter.begin(self)
        painter.drawImage(0, 0, self.image)
        painter.end()
    
    def resizeEvent(self, event):
    
        self.image = QImage(event.size(), QImage.Format_RGB16)
        self.image.fill(QColor(255, 255, 255))
        self.worker.draw(event.size(), -3.3, 2.8, 2.3, -2.8)
        self.viewChanged.emit(True)


class Worker(QThread):

    dataReady = pyqtSignal(QRect, QImage)
    
    def __init__(self):
    
        QThread.__init__(self)
        self.stop = False
        self.mutex = QMutex()
    
    def abort(self):
    
        self.mutex.lock()
        self.stop = True
        self.mutex.unlock()
        self.wait()
    
    def draw(self, size, r1, i1, r2, i2):
    
        if self.isRunning():
            self.abort()
        
        self.size = QSize(size)
        self.limits = (r1, i1, r2, i2)
        self.stop = False
        self.start()
    
    def run(self):
    
        self.mutex.lock()
        x2 = self.size.width()
        y2 = self.size.height()
        r1, i1, r2, i2 = self.limits
        self.mutex.unlock()
        
        rows = 8
        
        image = QImage(x2, rows, QImage.Format_RGB16)
        
        y = 0
        while y < y2:
        
            i = i1 + y * (i2 - i1)/y2
            x = 0
            
            while x < x2:
            
                self.mutex.lock()
                stop = self.stop
                self.mutex.unlock()

                if stop:
                    return

                r = r1 + x * (r2 - r1)/x2
    
                ci = r + i * 1j
                c = ci
                count = 0
                while count < 18 and abs(c) <= 2:
                    c = c * c + ci
                    count += 1
    
                colour = qRgb(count * 15, count * 15, count * 15)
                image.setPixel(x, y % rows, colour)
                
                x += 1
            
            y += 1
            
            if y % rows == 0:
                self.dataReady.emit(QRect(0, y/rows * rows, x2, rows), image)
        
        if y % rows != 0:
            self.dataReady.emit(QRect(0, y/rows * rows, x2, y % rows), image)


if __name__ == "__main__":

    app = buxpaper.Application()
    w = Window()
    w.showFullScreen()
    sys.exit(app.exec_())
