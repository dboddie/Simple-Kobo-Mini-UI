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

import os, sys, time
import buxpaper

from PyQt4.QtCore import pyqtSignal, QPoint, QPointF, QRect, QSize, QString, \
                                     Qt, QTimer
from PyQt4.QtGui import *

class Window(buxpaper.Window):

    def __init__(self):
    
        buxpaper.Window.__init__(self)
        
        self.config = buxpaper.Config(buxpaper.settings + "-sketch")
        self.config.load()
        
        self.viewer = Viewer(self.config)
        self.currentTime = time.time()
        
        self.documentList = DocumentChooser(self.config)
        self.documentList.chosen.connect(self.openDocument)
        
        # Add buttons to the panel.
        self.sleepButton.clicked.connect(self.setSleepImage)
        self.sleepButton.show()
        
        browserIcon = buxpaper.icon_from_commands(buxpaper.browser_icon,
            self.closeButton.sizeHint().width(), self.closeButton.sizeHint().height())
        
        # Viewer buttons
        
        # Add a button for accessing the image browser.
        self.browserButton = buxpaper.Button(browserIcon)
        self.browserButton.clicked.connect(self.showBrowser)
        self.panel.addWidget(self.browserButton)
        
        self.annotateButton = buxpaper.Button(u"T")
        self.annotateButton.clicked.connect(self.annotateDocument)
        self.panel.addWidget(self.annotateButton)
        
        self.clearButton = buxpaper.Button(u"\u2718")
        self.clearButton.clicked.connect(self.clearDocument)
        self.panel.addWidget(self.clearButton)
        
        self.storeButton = buxpaper.Button(u"\u2714")
        self.storeButton.setEnabled(False)
        self.storeButton.clicked.connect(self.storeDocument)
        self.viewer.saved.connect(self.storeButton.setDisabled)
        self.panel.addWidget(self.storeButton)
        
        # Browser buttons
        
        # Add a button to allow creation of a new document.
        self.newButton = buxpaper.Button(u"+")
        self.newButton.clicked.connect(self.newDocument)
        self.panel.addWidget(self.newButton)
        
        # Add navigation buttons.
        self.previousButton = buxpaper.Button(u"\u25c4")
        self.previousButton.clicked.connect(self.previousPage)
        self.panel.addWidget(self.previousButton)
        self.documentList.hasPrevious.connect(self.previousButton.setEnabled)
        self.viewer.hasPrevious.connect(self.previousButton.setEnabled)
        self.viewer.changed.connect(self.sleepButton.setEnabled)
        self.viewer.changed.connect(self.storeButton.setEnabled)
        
        self.nextButton = buxpaper.Button(u"\u25ba")
        self.nextButton.clicked.connect(self.nextPage)
        self.panel.addWidget(self.nextButton)
        self.documentList.hasNext.connect(self.nextButton.setEnabled)
        self.viewer.hasNext.connect(self.nextButton.setEnabled)
        
        layout = QStackedLayout(self.contentWidget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.viewer)
        layout.addWidget(self.documentList)
        
        self.documentList.loadDocumentDetails()
        
        # Wait until the window has been given its final geometry before
        # attempting to lay out the browser.
        QTimer.singleShot(0, self.showBrowser)
    
    def closeEvent(self, event):
    
        self.viewer.saveConfiguration()
    
    def showBrowser(self):
    
        # Determine the current page to show, based on the current document
        # being shown.
        index = self.documentList.documentPage(self.viewer.document.path)
        if index == -1:
            index = max(0, min(self.documentList.index, self.documentList.count() - 1))
        
        self.contentWidget.layout().setCurrentWidget(self.documentList)
        self.documentList.setCurrentIndex(index)
        
        self.sleepButton.hide()
        self.browserButton.hide()
        self.annotateButton.hide()
        self.clearButton.hide()
        self.storeButton.hide()
        
        self.newButton.show()
        self.previousButton.show()
        self.nextButton.show()
    
    def newDocument(self):
    
        self.currentTime = time.time()
        self.viewer.document = Document()
        self.storeDocument()
        self.openDocument(self.viewer.document.path)
        self.documentList.loadDocumentDetails()
        self.documentList.showPage()
    
    def openDocument(self, path):
    
        # Convert the path to a unicode string; even though the signal should
        # deliver a unicode string, it delivers a QString instead.
        path = unicode(path)
        self.contentWidget.layout().setCurrentWidget(self.viewer)
        self.viewer.openDocument(path)
        
        self.sleepButton.show()
        self.sleepButton.setEnabled(True)
        self.browserButton.show()
        self.annotateButton.show()
        self.clearButton.setEnabled(True)
        self.clearButton.show()
        self.storeButton.show()
        
        self.newButton.hide()
        self.previousButton.hide()
        self.nextButton.hide()
    
    def clearDocument(self):
    
        if not self.viewer.document.isEmpty():
            # The document contains information, so clear it.
            self.currentTime = time.time()
            self.viewer.clearDocument()
            self.storeButton.setEnabled(True)
        else:
            # The document is already empty, so delete it.
            os.remove(self.viewer.document.path)
            self.documentList.loadDocumentDetails()
            self.documentList.showPage()
            self.showBrowser()
    
    def createPath(self):
    
        time_seq = time.gmtime(self.currentTime)
        file_name = time.strftime("%Y-%m-%d %H:%M:%S", time_seq)
        return os.path.join(buxpaper.drawdir, file_name)
    
    def storeDocument(self):
    
        if self.viewer.document.path:
            path = self.viewer.document.path
        else:
            path = self.createPath()
        
        self.viewer.storeDocument(path)
        self.clearButton.setEnabled(True)
        self.storeButton.setEnabled(False)
        
        self.documentList.loadDocumentDetails()
    
    def annotateDocument(self):
    
        dialog = AnnotationDialog(self.viewer.document.text)
        rect = self.viewer.geometry()
        rect.adjust(24, 24, -24, -24)
        pos = self.viewer.mapToGlobal(self.viewer.geometry().topLeft())
        dialog.move(pos + rect.topLeft())
        dialog.resize(rect.size())
        
        if dialog.exec_() == QDialog.Accepted:
            self.viewer.document.text = dialog.text()
            self.storeButton.setEnabled(True)
    
    def previousPage(self):
    
        self.documentList.previousPage()
    
    def nextPage(self):
    
        self.documentList.nextPage()
    
    def setSleepImage(self):
    
        image = QImage(self.viewer.size(), QImage.Format_RGB16)
        image.fill(Qt.white)
        painter = QPainter()
        painter.begin(image)
        painter.setRenderHint(QPainter.Antialiasing)
        self.viewer.document.paint(painter)
        painter.end()
        
        self.sleepButton.setEnabled(False)
        self.saveSleepImage(image)


class DocumentChooser(QWidget):

    hasDocuments = pyqtSignal(bool)
    chosen = pyqtSignal(unicode)
    hasPrevious = pyqtSignal(bool)
    hasNext = pyqtSignal(bool)
    
    def __init__(self, config, parent = None):
    
        QWidget.__init__(self, parent)
        
        self.config = config
        self.names = []
        self.rows = self.config.get("Rows", 2)
        self.columns = self.config.get("Columns", 3)
        self.index = 0
    
    def loadDocumentDetails(self):
    
        self.names = os.listdir(buxpaper.drawdir)
        self.names.sort()
    
    def count(self):
    
        number = len(self.names) / (self.rows * self.columns)
        if len(self.names) % (self.rows * self.columns) != 0:
            number += 1
        return number
    
    def currentIndex(self):
    
        return self.index
    
    def setCurrentIndex(self, index):
    
        self.index = index
        self.showPage()
    
    def showPage(self):
    
        width = self.config.get("Thumbnail width", buxpaper.thumbnail_size[0])
        height = self.config.get("Thumbnail height", buxpaper.thumbnail_size[1])
        spacing = self.config.get("Thumbnail spacing", 12)
        row = column = 0
        this = self.index * self.rows * self.columns
        next = (self.index + 1) * self.rows * self.columns
        
        # Remove any existing child widgets.
        for child in self.children():
            child.deleteLater()
        
        # Use a single child widget that can be disposed of later.
        pageWidget = QWidget(self)
        pageWidget.setGeometry(0, 0, self.width(), self.height())
        pageLayout = QGridLayout(pageWidget)
        pageLayout.setMargin(spacing)
        pageLayout.setSpacing(spacing)
        
        for name in self.names[this:next]:
        
            container = QWidget(self)
            layout = QVBoxLayout(container)
            layout.setAlignment(Qt.AlignHCenter)
            layout.setMargin(0)
            
            drawing_path = os.path.join(buxpaper.drawdir, name)
            d = Document()
            if d.load(drawing_path):
            
                image = QImage(d.width, d.height, QImage.Format_RGB16)
                image.fill(Qt.white)
                p = QPainter()
                p.begin(image)
                d.paint(p)
                p.end()
                image = image.scaled(width, height, Qt.KeepAspectRatio,
                                     Qt.SmoothTransformation)
            else:
                image = QImage(width, height, QImage.Format_RGB16)
                image.fill(Qt.gray)
            
            button = buxpaper.Button(image)
            button.data = drawing_path
            button.clicked.connect(self.chooseDocument)
            layout.addWidget(button)
            layout.setAlignment(button, Qt.AlignHCenter)
            
            label = buxpaper.Label(name, drawing_path)
            label.setAlignment(Qt.AlignHCenter)
            label.setWordWrap(True)
            label.setFrameShape(QFrame.NoFrame)
            label.clicked.connect(self.chooseDocument)
            layout.addWidget(label)
            layout.setAlignment(label, Qt.AlignHCenter)
            
            pageLayout.addWidget(container, row, column)
            
            column = (column + 1) % self.columns
            if column == 0:
                row = row + 1
        
        pageWidget.show()
        
        self.hasDocuments.emit(len(self.names) > 0)
        self.hasPrevious.emit(self.currentIndex() > 0)
        self.hasNext.emit(self.currentIndex() < self.count() - 1)
    
    def chooseDocument(self):
    
        label = self.sender()
        path = label.data
        self.chosen.emit(path)
        
        name = os.path.split(path)[1]
        index = self.names.index(name)
        self.hasPrevious.emit(index > 0)
        self.hasNext.emit(index < len(self.names) - 1)
    
    def previousPage(self):
    
        self.setCurrentIndex(self.currentIndex() - 1)
        self.hasPrevious.emit(self.currentIndex() > 0)
    
    def nextPage(self):
    
        self.setCurrentIndex(self.currentIndex() + 1)
        self.hasNext.emit(self.currentIndex() < self.count() - 1)
    
    def documentPage(self, path):
    
        "Return the browser page index for the document specified by the path."
        
        index = self.documentIndex(path)
        if index != -1:
            return index / (self.rows * self.columns)
        else:
            return -1
    
    def documentIndex(self, path):
    
        "Return the document index for the document specified by the path."
        
        if path is None:
            return -1
        
        name = os.path.split(path)[1]
        try:
            return self.names.index(name)
        except ValueError:
            return -1
    
    def addDocument(self, path):
    
        self.names.append(os.path.split(path)[1])


class AnnotationDialog(QDialog):

    def __init__(self, text, parent = None):
    
        QDialog.__init__(self, parent)
        self.setWindowFlags(Qt.CustomizeWindowHint)
        
        layout = QVBoxLayout(self)
        self.textBrowser = QTextBrowser()
        self.textBrowser.setPlainText(text)
        layout.addWidget(self.textBrowser)
        
        layout.addStretch()
        
        buttons = QHBoxLayout()
        editButton = buxpaper.Label(self.tr("Edit"))
        editButton.clicked.connect(self.editText)
        buttons.addWidget(editButton)
        
        updateButton = buxpaper.Label(self.tr("Update"))
        updateButton.clicked.connect(self.accept)
        buttons.addWidget(updateButton)
        
        discardButton = buxpaper.Label(self.tr("Discard"))
        discardButton.clicked.connect(self.reject)
        buttons.addWidget(discardButton)
        
        layout.addLayout(buttons)
    
    def editText(self):
    
        text = self.textBrowser.toPlainText().toUtf8()
        text = buxpaper.get_keyboard_input(text)
        self.textBrowser.setPlainText(text)
    
    def text(self):
    
        return unicode(self.textBrowser.toPlainText())


class Document:

    def __init__(self, path = None):
    
        self.objects = []
        self.points = []
        self.text = u""
        
        if path and self.load(path):
            self.path = path
        else:
            self.path = None
    
    def load(self, path):
    
        try:
            f = open(path)
            line = f.readline()
            self.width, self.height = map(int, line.strip().split("x"))
            
            n = int(f.readline().strip())
            
            while n > 0:
                line = f.readline().strip()
                if not line:
                    break
                
                obj = []
                for point in line.split():
                    x, y = map(int, point.split(","))
                    obj.append(QPoint(x, y))
                self.objects.append(obj)
                n -= 1
            
            self.text = u""
            while True:
                line = unicode(f.readline(), "utf8")
                if not line:
                    break
                
                self.text += line
            
            self.path = path
        
        except (IOError, ValueError):
            return False
        
        return True
    
    def save(self, path, width, height):
    
        try:
            f = open(path, "w")
            f.write("%ix%i\n" % (width, height))
            f.write("%i\n" % len(self.objects))
            
            for obj in self.objects:
                line = []
                for point in obj:
                    line.append("%i,%i" % (point.x(), point.y()))
                f.write(" ".join(line) + "\n")
            
            f.write(self.text.encode("utf8"))
            f.close()
            self.path = path
        
        except IOError:
            return False
        
        return True
    
    def clear(self):
    
        self.points = []
        self.objects = []
    
    def isEmpty(self):
    
        return not (self.objects or self.points)
    
    def addPoint(self, point):
    
        self.points.append(point)
    
    def lastPoint(self):
    
        if self.points:
            return self.points[-1]
        else:
            return None
    
    def makeObject(self):
    
        self.objects.append(self.points)
        self.points = []
    
    def lines(self, index):
    
        p = None
        for q in self.objects[index]:
            if p:
                yield p, q
            p = q
    
    def paint(self, painter):
    
        painter.setPen(QPen(QColor(0, 0, 0), 4))
        
        for obj in self.objects:
            self.drawObject(painter, obj)
        
        self.drawObject(painter, self.points)
    
    def drawObject(self, painter, obj):
    
        p = None
        for point in obj:
            if p is not None:
                painter.drawLine(p, point)
            p = point


class Viewer(QWidget):

    saved = pyqtSignal(bool)
    hasPrevious = pyqtSignal(bool)
    hasNext = pyqtSignal(bool)
    stored = pyqtSignal(unicode)
    changed = pyqtSignal(bool)
    
    def __init__(self, config, parent = None):
    
        QWidget.__init__(self, parent)
        
        self.config = config
        self.pressed = False
        
        self.document = Document()
        document = self.config.get("Current", None)
        self.openDocument(document)
    
    def mousePressEvent(self, event):
    
        self.pressed = True
        
        p1 = QPoint(event.pos())
        self.document.addPoint(p1)
        
    def mouseMoveEvent(self, event):
    
        if not self.pressed:
            return
        
        p1 = QPoint(event.pos())
        p0 = self.document.lastPoint()
        if not p0:
            p0 = p1
        
        self.document.addPoint(p1)
        self.updateLine(p0, p1)
    
    def updateLine(self, p0, p1):
    
        x0, y0 = p0.x(), p0.y()
        x1, y1 = p1.x(), p1.y()
        x = min(x0, x1) - 2
        y = min(y0, y1) - 2
        w = max(x0, x1) - x + 3
        h = max(y0, y1) - y + 3
        
        self.update(QRect(x, y, w, h))
    
    def mouseReleaseEvent(self, event):
    
        self.pressed = False
        self.document.makeObject()
        
        # Update the areas covered by the lines in the last object.
        for p, q in self.document.lines(-1):
            self.updateLine(p, q)
        
        self.saved.emit(False)
        self.changed.emit(True)
    
    def paintEvent(self, event):
    
        painter = QPainter()
        painter.begin(self)
        self.document.paint(painter)
        painter.end()
    
    def openDocument(self, path):
    
        self.clearDocument()
        
        if not path:
            return
        
        loaded = self.document.load(path)
        if loaded:
            self.config.set("Current", self.document.path)
        
        self.saved.emit(loaded)
    
    def saveConfiguration(self):
    
        self.config.save()
    
    def clearDocument(self):
    
        self.document.clear()
        self.update()
    
    def storeDocument(self, path):
    
        saved = self.document.save(path, self.width(), self.height())
        self.saved.emit(saved)
        self.stored.emit(path)


if __name__ == "__main__":

    app = buxpaper.Application()
    
    window = Window()
    window.showFullScreen()
    
    sys.exit(app.exec_())
