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

class PreferencesWidget(buxpaper.Window):

    ThumbnailSize = QSize(buxpaper.thumbnail_size[0],
                          buxpaper.thumbnail_size[1])
    
    def __init__(self):
    
        buxpaper.Window.__init__(self)
        
        self.pages = buxpaper.PagedWidget()
        self.pages.previousButton.hide()
        self.pages.nextButton.hide()
        self.pages.padding = 12
        
        self.previousButton = buxpaper.Button(u"\u25c4")
        self.panel.addWidget(self.previousButton)
        
        self.nextButton = buxpaper.Button(u"\u25ba")
        self.panel.addWidget(self.nextButton)
        
        self.pages.previousButtonState.connect(self.previousButton.setEnabled)
        self.pages.nextButtonState.connect(self.nextButton.setEnabled)
        self.previousButton.clicked.connect(self.pages.previousPage)
        self.nextButton.clicked.connect(self.pages.nextPage)
        
        layout = QVBoxLayout(self.contentWidget)
        layout.addWidget(self.pages)
        
        self.loadImageDetails()
    
    def loadImageDetails(self):
    
        self.start_dir = os.path.join(buxpaper.picdir, "Start")
        start_name, self.start_path = self.getLinkedImage(self.start_dir)
        self.sleep_dir = os.path.join(buxpaper.picdir, "Sleep")
        sleep_name, self.sleep_path = self.getLinkedImage(self.sleep_dir)
        
        self.startButtons = {}
        self.sleepButtons = {}
        
        self.startGroup = QButtonGroup()
        self.startGroup.buttonClicked.connect(self.setStartPicture)
        self.sleepGroup = QButtonGroup()
        self.sleepGroup.buttonClicked.connect(self.setSleepPicture)
        
        for name in os.listdir(buxpaper.picdir):
        
            path = os.path.join(buxpaper.picdir, name)
            
            if os.path.isfile(path):
            
                thumbnail_path = os.path.join(buxpaper.picdir, "Thumbnails", name)
                if os.path.isfile(thumbnail_path):
                    im = QImage(thumbnail_path)
                else:
                    im = QImage(path)
                    if im.isNull():
                        continue
                    im = im.scaled(self.ThumbnailSize, Qt.KeepAspectRatio)
                    im.save(thumbnail_path)
                
                frame = QFrame()
                frame_layout = QHBoxLayout(frame)
                
                label = QLabel()
                label.setPixmap(QPixmap.fromImage(im))
                
                startButton = QCheckBox("Start")
                startButton.setFocusPolicy(Qt.NoFocus)
                startButton.setChecked(path == self.start_path)
                self.startGroup.addButton(startButton)
                self.startButtons[startButton] = path
                
                sleepButton = QCheckBox("Sleep")
                sleepButton.setFocusPolicy(Qt.NoFocus)
                sleepButton.setChecked(path == self.sleep_path)
                self.sleepGroup.addButton(sleepButton)
                self.sleepButtons[sleepButton] = path
                
                frame_layout.addWidget(label)
                frame_layout.addSpacing(32)
                frame_layout.addWidget(startButton)
                frame_layout.addSpacing(32)
                frame_layout.addWidget(sleepButton)
                
                frame.adjustSize()
                self.pages.addWidget(frame)
        
        self.pages.setCurrentPage(0)
    
    def getLinkedImage(self, directory):
    
        try:
            name = os.listdir(directory)[0]
            path = os.path.join(directory, name)
            if os.path.islink(path):
                return name, os.readlink(path)
            else:
                return name, path
        
        except IndexError:
            return None, None
    
    @pyqtSlot(QAbstractButton)
    def setStartPicture(self, button):
    
        path = self.startButtons[button]
        name = os.path.split(path)[1]
        
        # Remove any existing link in the Start directory.
        if self.start_path:
            old_name = os.path.split(self.start_path)[1]
            link_path = os.path.join(self.start_dir, old_name)
            os.remove(link_path)
        
        os.symlink(path, os.path.join(self.start_dir, name))
    
    @pyqtSlot(QAbstractButton)
    def setSleepPicture(self, button):
    
        path = self.sleepButtons[button]
        name = os.path.split(path)[1]
        
        # Remove any existing link in the Start directory.
        if self.sleep_path:
            old_name = os.path.split(self.sleep_path)[1]
            link_path = os.path.join(self.sleep_dir, old_name)
            os.remove(link_path)
        
        os.symlink(path, os.path.join(self.sleep_dir, name))


if __name__ == "__main__":

    app = buxpaper.Application()
    w = PreferencesWidget()
    w.showFullScreen()
    sys.exit(app.exec_())
