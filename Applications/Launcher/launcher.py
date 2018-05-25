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
import buxpaper

from PyQt4.QtCore import *
from PyQt4.QtGui import *

class MenuWidget(buxpaper.Window):

    def __init__(self):
    
        buxpaper.Window.__init__(self)
        
        self.config = buxpaper.Config(buxpaper.settings + "-launcher")
        self.config.load()
        
        self.this_appdir = os.path.abspath(os.path.split(__file__)[0])
        
        self.process = None
        self.processLabel = None
        
        # Hide the close button.
        self.closeButton.hide()
        
        # Add a power status indicator.
        self.statusWidget = StatusWidget()
        self.panel.insertWidget(0, self.statusWidget)
        
        # Add buttons to the panel.
        self.previousButton = buxpaper.Button(u"\u25c4")
        self.previousButton.clicked.connect(self.previousPage)
        self.panel.addWidget(self.previousButton)
        
        self.nextButton = buxpaper.Button(u"\u25ba")
        self.nextButton.clicked.connect(self.nextPage)
        self.panel.addWidget(self.nextButton)
        
        # Create widgets inside the content widget.
        self.pages = QStackedWidget()
        
        layout = QVBoxLayout(self.contentWidget)
        layout.addWidget(self.pages)
        
        self.loadApplicationDetails()
        self.statusWidget.updateStatus()
        self.updateButtons()
    
    def loadApplicationDetails(self):
    
        # Obtain a list of applications to exclude.
        exclude = self.config.get("Exclude applications", [])
        
        rows = self.config.get("Rows", 2)
        columns = self.config.get("Columns", 3)
        width = self.config.get("Thumbnail width", buxpaper.thumbnail_size[0])
        height = self.config.get("Thumbnail height", buxpaper.thumbnail_size[1])
        spacing = self.config.get("Thumbnail spacing", 12)
        row = column = 0
        
        for name in os.listdir(buxpaper.appdir):
        
            if name in exclude:
                continue
            
            # Construct the full application directory for this entry.
            appdir = os.path.abspath(os.path.join(buxpaper.appdir, name))
            
            # Don't include the launcher itself in the collection.
            if appdir == self.this_appdir:
                continue
            
            if not os.path.isdir(appdir):
                continue
            
            # Create a new widget if we are starting a new page.
            if row == 0 and column == 0:
                page = QWidget()
                pageLayout = QGridLayout(page)
                pageLayout.setSpacing(spacing)
                pageLayout.setMargin(spacing)
            
            container = QWidget()
            layout = QVBoxLayout(container)
            layout.setAlignment(Qt.AlignHCenter)
            layout.setMargin(0)
            
            icon_file = os.path.join(appdir, name.lower() + ".png")
            if os.path.isfile(icon_file):
            
                image = QImage(icon_file)
                image = image.scaled(width, height, Qt.KeepAspectRatio,
                                     Qt.SmoothTransformation)
                
                button = buxpaper.Button(image)
                button.data = appdir
                button.clicked.connect(self.runApplication)
                layout.addWidget(button)
                # Apparently necessary to update the layout...
                layout.setAlignment(button, Qt.AlignHCenter)
            
            label = buxpaper.Label(name, appdir)
            label.setAlignment(Qt.AlignHCenter)
            label.setFrameShape(QFrame.NoFrame)
            label.clicked.connect(self.runApplication)
            layout.addWidget(label)
            # Apparently necessary to update the layout...
            layout.setAlignment(label, Qt.AlignHCenter)
            
            pageLayout.addWidget(container, row, column)
            
            # Move to the next space in the page.
            column = (column + 1) % columns
            if column == 0:
                row = (row + 1) % rows
                if row == 0:
                    # If we need to start a new page then insert the current
                    # page into the stack.
                    page.adjustSize()
                    self.pages.addWidget(page)
        
        # Insert any unfinished page into the stack.
        if row != 0 or column != 0:
            page.adjustSize()
            self.pages.addWidget(page)
        
        self.pages.setCurrentIndex(0)
    
    def previousPage(self):
    
        self.pages.setCurrentIndex(self.pages.currentIndex() - 1)
        self.updateButtons()
    
    def nextPage(self):
    
        self.pages.setCurrentIndex(self.pages.currentIndex() + 1)
        self.updateButtons()
    
    def updateButtons(self):
    
        self.previousButton.setEnabled(self.pages.currentIndex() > 0)
        self.nextButton.setEnabled(self.pages.currentIndex() < self.pages.count() - 1)
        
        if not self.previousButton.isEnabled() and not self.nextButton.isEnabled():
            self.previousButton.hide()
            self.nextButton.hide()
        
        self.statusWidget.updateStatus()
    
    def runApplication(self):
    
        if self.process:
            return
        
        label = self.sender()
        
        for name in os.listdir(label.data):
        
            if name.endswith(".py"):
                appfile = os.path.join(label.data, name)
                self.processLabel = label
                self.startProcess(label.data, appfile)
                break
    
    def startProcess(self, working_dir, exec_path):
    
        process = self.process = QProcess()
        process.setWorkingDirectory(working_dir)
        process.started.connect(self.started)
        process.finished.connect(self.finished)
        process.start(exec_path)
    
    def started(self):
    
        self.processLabel.setEnabled(False)
    
    def finished(self):
    
        self.processLabel.setEnabled(True)
        self.process = None
        self.statusWidget.updateStatus()


class StatusWidget(QWidget):

    def __init__(self):
    
        QWidget.__init__(self)
        self.power = buxpaper.Power()
        
        font = QFont(QApplication.font())
        font.setWeight(QFont.Bold)
        self.setFont(font)
        
        fm = QFontMetricsF(font)
        self.idealWidth = max(fm.width("+"), fm.width("-")) * 1.5
        self.idealHeight = (2 * fm.height()) + 50
        
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        self.updateStatus()
    
    def mouseReleaseEvent(self, event):
    
        self.updateStatus()
        
    def updateStatus(self):
    
        d = self.power.status()
        self.voltage = int(d["POWER_SUPPLY_VOLTAGE_NOW"])
        self.status = d["POWER_SUPPLY_STATUS"]
        self.update()
    
    def paintEvent(self, event):
    
        painter = QPainter()
        painter.begin(self)
        painter.fillRect(event.rect(), QColor(Qt.white))
        fm = QFontMetricsF(self.font())
        painter.drawText(QRect(0, 0, self.width(), fm.height()), Qt.AlignCenter, "+")
        painter.drawText(QRect(0, self.height() - fm.height(), self.width(), fm.height()),
                         Qt.AlignCenter, "-")
        painter.fillRect(self.width()/4, fm.height() + 50 - self.voltage/2,
                         self.width()/2, self.voltage/2, QColor(Qt.gray))
        painter.drawRect(self.width()/4, fm.height(), self.width()/2, 50)
        painter.end()
    
    def sizeHint(self):
    
        return QSize(self.idealWidth, self.idealHeight)


if __name__ == "__main__":

    app = buxpaper.Application(server = True)
    w = MenuWidget()
    w.showFullScreen()
    sys.exit(app.exec_())
