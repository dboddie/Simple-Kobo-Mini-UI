#!/usr/bin/env python

"""
gallery.py - An image viewer for the Kobo Mini.

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
import buxpaper

from PyQt4.QtCore import *
from PyQt4.QtGui import *

import Image, ImageEnhance

brightness_icon = (
    ("fill", {"brush": "white"}),
    ("pie", {"brush": "#404040",
             "rect": (0.3, 0.3, 0.4, 0.4), "start": 0, "span": 360*16})
    )

for angle in range(0, 360, 45):
    brightness_icon += (
        ("polygon", {"pen": "none", "brush": "black",
                     "points": ((0.5 + 0.3 * math.cos(angle * math.pi/180),
                                 0.5 + 0.3 * math.sin(angle * math.pi/180)),
                                (0.5 + 0.4 * math.cos(angle * math.pi/180),
                                 0.5 + 0.4 * math.sin(angle * math.pi/180)))}),
        )

contrast_icon = (
    ("fill", {"brush": "white"}),
    ("pie", {"pen": "black", "brush": "black",
             "rect": (0.3, 0.3, 0.4, 0.4), "start": -90*16, "span": 180*16}),
    ("pie", {"pen": "black", "brush": "white",
             "rect": (0.3, 0.3, 0.4, 0.4), "start": 90*16, "span": 180*16})
    )

SecretGalleryDir = os.path.join(buxpaper.picdir, ".Gallery")
GalleryDir = os.path.join(buxpaper.picdir, "Gallery")

class Gallery(buxpaper.Window):

    def __init__(self):
    
        buxpaper.Window.__init__(self)
        
        self.index = 0
        
        self.sleepButton.clicked.connect(self.setSleepImage)
        self.sleepButton.show()
        
        browserIcon = buxpaper.icon_from_commands(buxpaper.browser_icon,
            self.closeButton.sizeHint().width(), self.closeButton.sizeHint().height())
        
        # Add a button for accessing the image browser.
        self.browserButton = buxpaper.Button(browserIcon)
        self.browserButton.clicked.connect(self.showBrowser)
        self.panel.addWidget(self.browserButton)
        
        # Add a button for accessing the adjustment panel.
        self.adjustImageWindow = AdjustImageWindow()
        self.adjustImageWindow.increaseBrightness.connect(self.increaseBrightness)
        self.adjustImageWindow.decreaseBrightness.connect(self.decreaseBrightness)
        self.adjustImageWindow.increaseContrast.connect(self.increaseContrast)
        self.adjustImageWindow.decreaseContrast.connect(self.decreaseContrast)
        self.adjustImageWindow.saveSettings.connect(self.saveSettings)
        
        self.adjustImageButton = buxpaper.Button(u"A")
        self.adjustImageButton.clicked.connect(self.adjustImage)
        self.panel.addWidget(self.adjustImageButton)
        
        self.saveThumbnailButton = buxpaper.Button(u"T")
        self.saveThumbnailButton.clicked.connect(self.saveThumbnail)
        self.saveThumbnailButton.hide()
        self.panel.addWidget(self.saveThumbnailButton)
        
        # Add a zoom button to the panel.
        self.zoomOutButton = buxpaper.Button("-")
        self.zoomOutButton.clicked.connect(self.zoomOut)
        self.panel.addWidget(self.zoomOutButton)

        self.previousButton = buxpaper.Button(u"\u25c4")
        self.previousButton.clicked.connect(self.previousPage)
        self.panel.addWidget(self.previousButton)
        
        self.nextButton = buxpaper.Button(u"\u25ba")
        self.nextButton.clicked.connect(self.nextPage)
        self.panel.addWidget(self.nextButton)
        
        self.config = buxpaper.Config(buxpaper.settings + "-gallery")
        self.config.load()
        
        # Use a stacked layout inside the main content widget.
        layout = QStackedLayout(self.contentWidget)
        layout.setContentsMargins(0, 0, 0, 0)
        self.createBrowserPage()
        layout.addWidget(self.browserPage)
        self.createPreviewPage()
        layout.addWidget(self.previewPage)
        
        self.showBrowser()
    
    def createBrowserPage(self):
    
        self.browserPage = QStackedWidget()
        
        self.names = os.listdir(GalleryDir)
        self.names = filter(lambda name:
            os.path.isfile(os.path.join(GalleryDir, name)), self.names)
        self.names.sort()
        
        rows = self.config.get("Rows", 3)
        columns = self.config.get("Columns", 3)
        width = self.config.get("Thumbnail width", buxpaper.thumbnail_size[0])
        height = self.config.get("Thumbnail height", buxpaper.thumbnail_size[1])
        spacing = self.config.get("Thumbnail spacing", 12)
        row = column = 0
        
        index = 0
        for name in self.names:
        
            if row == 0 and column == 0:
                box = QWidget()
                layout = QGridLayout(box)
                layout.setSpacing(spacing)
                layout.setMargin(0)
            
            path = os.path.join(GalleryDir, name)
            
            thumbnail_path = os.path.join(GalleryDir, "Thumbnails", name)
            if os.path.isfile(thumbnail_path):
                image = QImage(thumbnail_path)
            else:
                image = QImage(path).scaled(width, height, Qt.KeepAspectRatio)
                image.save(thumbnail_path)
            
            label = buxpaper.Label(name, index)
            label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
            label.setPixmap(QPixmap.fromImage(image))
            label.clicked.connect(self.showPreview)
            layout.addWidget(label, row, column)
            
            column = (column + 1) % columns
            if column == 0:
                row = (row + 1) % rows
                if row == 0:
                    box.adjustSize()
                    self.browserPage.addWidget(box)
            
            index += 1
        
        if row != 0 or column != 0:
            box.adjustSize()
            self.browserPage.addWidget(box)
        
        self.browserPage.setCurrentIndex(0)
    
    def createPreviewPage(self):
    
        self.previewPage = buxpaper.Picture()
        self.previewPage.clicked.connect(self.zoom)
    
    def showBrowser(self):
    
        # Change the buttons to reflect the place of the current page in the
        # directory.
        ### To do: Use the picture index to find the appropriate page in the
        ### browser to return to.
        self.previousButton.setEnabled(self.browserPage.currentIndex() > 0)
        self.nextButton.setEnabled(self.browserPage.currentIndex() < self.browserPage.count() - 1)
        
        self.sleepButton.hide()
        self.browserButton.hide()
        self.adjustImageButton.hide()
        self.saveThumbnailButton.hide()
        self.zoomOutButton.hide()
        
        # Hide the adjustment window.
        self.adjustImageWindow.hide()
        
        # Show the browser page.
        self.contentWidget.layout().setCurrentWidget(self.browserPage)
    
    def showPreview(self, index = None):
    
        if index is None:
            index = self.sender().data
        
        self.index = index
        self.path = os.path.join(GalleryDir, self.names[self.index])
        self.thumbnail_path = os.path.join(GalleryDir, "Thumbnails",
                                           self.names[self.index])
        self.image = QImage(self.path)
        w = self.image.width()
        h = self.image.height()
        
        # Load a copy of the saved adjustments so that any changes are not
        # automatically written to the stored values.
        self.adjustments = self.config.get(self.path, {}).copy()
        
        # Reset the brightness and contrast exponents.
        self.adjustments.setdefault("brightness", 0)
        self.adjustments.setdefault("contrast", 0)
        
        # Record the visible part of the image (x, y, w, h).
        self.adjustments.setdefault("bbox", (0, 0, w, h))
        self.adjustments.setdefault("zoom", 1)
        
        # Update the buttons in the adjustment window.
        self.adjustImageWindow.updateButtons(self.adjustments, initial = True)
        
        image = self.cropAndScaleImage()
        image = self.processImage(image)
        self.previewPage.setImage(image)
        
        # Change the buttons to reflect the place of the current image in the
        # directory.
        self.previousButton.setEnabled(self.index > 0)
        self.nextButton.setEnabled(self.index < len(self.names) - 1)
        
        self.sleepButton.setEnabled(True)
        self.sleepButton.show()
        self.browserButton.show()
        self.adjustImageButton.show()
        self.saveThumbnailButton.setEnabled(True)
        if "--developer" in sys.argv:
            self.saveThumbnailButton.show()
        self.zoomOutButton.show()
        
        # Show the preview page.
        self.contentWidget.layout().setCurrentWidget(self.previewPage)
    
    def previousPage(self):
    
        if self.contentWidget.layout().currentWidget() == self.previewPage:
            self.showPreview(self.index - 1)
        else:
            self.browserPage.setCurrentIndex(self.browserPage.currentIndex() - 1)
            self.showBrowser()
    
    def nextPage(self):
    
        if self.contentWidget.layout().currentWidget() == self.previewPage:
            self.showPreview(self.index + 1)
        else:
            self.browserPage.setCurrentIndex(self.browserPage.currentIndex() + 1)
            self.showBrowser()
    
    def zoom(self, pos, zoom_increment = 1):
    
        new_zoom_factor = self.adjustments["zoom"] + zoom_increment
        if new_zoom_factor < 1:
            return
        
        # Calculate the point clicked in original image coordinates.
        width = self.previewPage.width()
        height = self.previewPage.height()
        x, y, w, h = self.adjustments["bbox"]
        sx = x + (pos.x() * w) / width
        sy = y + (pos.y() * h) / height
        
        # Change the zoom factor to calculate the visible region.
        self.adjustments["zoom"] = new_zoom_factor
        
        w = self.image.width() / self.adjustments["zoom"]
        h = self.image.height() / self.adjustments["zoom"]
        
        # Adjust the width and height to match the aspect ratio of the preview
        # page.
        h = min(max(h, int(w * float(height)/width)), self.image.height())
        
        x1 = sx - w/2
        y1 = sy - h/2
        x2 = sx + w/2
        y2 = sy + h/2
        if x1 < 0:
            x1 = 0
            x2 = w
        elif x2 > self.image.width():
            x2 = self.image.width()
            x1 = x2 - w
        if y1 < 0:
            y1 = 0
            y2 = h
        elif y2 > self.image.height():
            y2 = self.image.height()
            y1 = y2 - h
        
        # Reduce the visible area by half in each dimension.
        self.adjustments["bbox"] = (x1, y1, x2 - x1, y2 - y1)
        
        image = self.cropAndScaleImage()
        image = self.processImage(image)
        self.previewPage.setImage(image)
        self.adjustImageWindow.updateButtons(self.adjustments)
    
    def zoomOut(self):
    
        pos = self.previewPage.rect().center()
        self.zoom(pos, -1)
    
    def cropAndScaleImage(self):
    
        self.zoomOutButton.setEnabled(self.adjustments["zoom"] > 1)
        
        width = self.previewPage.width()
        height = self.previewPage.height()
        
        # Crop the image to the currently visible area.
        if self.adjustments["bbox"] == (0, 0, self.image.width(), self.image.height()):
            image = self.image
        else:
            image = self.image.copy(*self.adjustments["bbox"])
        
        # Scale the visible part of the image to the widget size and cache it.
        return image.scaled(width, height, Qt.KeepAspectRatio)
    
    def processImage(self, image):
    
        self.adjustImageButton.setEnabled(True)
        self.adjustImageWindow.updateButtons(self.adjustments)
        
        if self.adjustments["contrast"] == 0 and \
            self.adjustments["brightness"] == 0:
            return image
        
        image.save("/tmp/image.png")
        im = Image.open("/tmp/image.png")
        
        if self.adjustments["contrast"] != 0:
            enhancer = ImageEnhance.Contrast(im)
            im = enhancer.enhance(1.5 ** self.adjustments["contrast"])
        
        if self.adjustments["brightness"] != 0:
            enhancer = ImageEnhance.Brightness(im)
            im = enhancer.enhance(1.5 ** self.adjustments["brightness"])
        
        im.save("/tmp/image.png")
        
        image = QImage("/tmp/image.png")
        return image
    
    def adjustImage(self):
    
        self.adjustImageWindow.setShown(not self.adjustImageWindow.isVisible())
        if not self.adjustImageWindow.isVisible():
            return
        
        pos = self.previewPage.mapToGlobal(self.previewPage.geometry().bottomLeft())
        pos -= QPoint(0, self.adjustImageWindow.height())
        self.adjustImageWindow.move(pos)
    
    def saveThumbnail(self):
    
        image = self.image.copy(*self.adjustments["bbox"])
        image = image.scaled(self.config.get("Thumbnail width", 180),
                             self.config.get("Thumbnail height", 180),
                             Qt.KeepAspectRatio)
        image = self.processImage(image)
        image.save(self.thumbnail_path)
        self.saveThumbnailButton.setEnabled(False)
    
    def increaseBrightness(self):
    
        self.adjustments["brightness"] = min(self.adjustments["brightness"] + 1, 16)
        image = self.cropAndScaleImage()
        image = self.processImage(image)
        self.previewPage.setImage(image)
    
    def decreaseBrightness(self):
    
        self.adjustments["brightness"] = max(-16, self.adjustments["brightness"] - 1)
        image = self.cropAndScaleImage()
        image = self.processImage(image)
        self.previewPage.setImage(image)
    
    def increaseContrast(self):
    
        self.adjustments["contrast"] = min(self.adjustments["contrast"] + 1, 16)
        image = self.cropAndScaleImage()
        image = self.processImage(image)
        self.previewPage.setImage(image)
    
    def decreaseContrast(self):
    
        self.adjustments["contrast"] = max(-16, self.adjustments["contrast"] - 1)
        image = self.cropAndScaleImage()
        image = self.processImage(image)
        self.previewPage.setImage(image)
    
    def saveSettings(self):
    
        # Update the configuration with the current image's adjustment settings.
        self.config.set(self.path, self.adjustments)
        self.config.save()
        self.adjustImageWindow.updateButtons(self.adjustments, initial = True)
    
    def setSleepImage(self):
    
        image = self.image.copy(*self.adjustments["bbox"])
        image = image.scaled(QApplication.desktop().geometry().size(),
                             Qt.KeepAspectRatio)
        image = self.processImage(image)
        
        self.sleepButton.setEnabled(False)
        self.saveSleepImage(image)
    
    def closeEvent(self, event):
    
        self.adjustImageWindow.close()


class AdjustImageWindow(QWidget):

    increaseBrightness = pyqtSignal()
    decreaseBrightness = pyqtSignal()
    increaseContrast = pyqtSignal()
    decreaseContrast = pyqtSignal()
    saveSettings = pyqtSignal()
    
    def __init__(self):
    
        QWidget.__init__(self)
        self.setWindowFlags(Qt.CustomizeWindowHint)
        
        layout = QGridLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.decreaseBrightnessButton = buxpaper.Button("-")
        self.increaseBrightnessButton = buxpaper.Button("+")
        self.decreaseBrightnessButton.clicked.connect(self.decreaseBrightness)
        self.increaseBrightnessButton.clicked.connect(self.increaseBrightness)

        brightnessIcon = buxpaper.icon_from_commands(brightness_icon,
            self.increaseBrightnessButton.sizeHint().width(),
            self.increaseBrightnessButton.sizeHint().height())
        
        label = buxpaper.Button(brightnessIcon)
        layout.addWidget(label, 0, 0)
        layout.addWidget(self.decreaseBrightnessButton, 0, 1)
        layout.addWidget(self.increaseBrightnessButton, 0, 2)
        
        self.decreaseContrastButton = buxpaper.Button("-")
        self.increaseContrastButton = buxpaper.Button("+")
        self.decreaseContrastButton.clicked.connect(self.decreaseContrast)
        self.increaseContrastButton.clicked.connect(self.increaseContrast)
        
        contrastIcon = buxpaper.icon_from_commands(contrast_icon,
            self.increaseContrastButton.sizeHint().width(),
            self.increaseContrastButton.sizeHint().height())
        
        label = buxpaper.Button(contrastIcon)
        layout.addWidget(label, 1, 0)
        layout.addWidget(self.decreaseContrastButton, 1, 1)
        layout.addWidget(self.increaseContrastButton, 1, 2)
        
        self.saveButton = buxpaper.Button(u"\u2713")
        self.saveButton.clicked.connect(self.saveSettings)
        layout.addWidget(self.saveButton, 0, 3, 2, 1)
    
    def updateButtons(self, adjustments, initial = False):
    
        if initial:
            self.adjustments = adjustments.copy()
        
        brightness = self.adjustments["brightness"]
        contrast = self.adjustments["contrast"]
        
        self.decreaseBrightnessButton.setEnabled(brightness > -16)
        self.increaseBrightnessButton.setEnabled(brightness < 16)
        self.decreaseContrastButton.setEnabled(contrast > -16)
        self.increaseContrastButton.setEnabled(contrast < 16)
        
        self.saveButton.setEnabled(self.adjustments != adjustments)


if __name__ == "__main__":

    if not buxpaper.unlock(SecretGalleryDir, GalleryDir):
        sys.exit(1)
    
    app = buxpaper.Application()
    window = Gallery()
    window.showFullScreen()
    sys.exit(app.exec_())
