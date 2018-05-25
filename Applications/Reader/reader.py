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
import buxpaper

from PyQt4.QtCore import pyqtSignal, QPoint, QPointF, QRect, QSize, Qt
from PyQt4.QtGui import *

class Window(buxpaper.Window):

    def __init__(self):
    
        buxpaper.Window.__init__(self)
        
        self.viewer = Viewer()
        self.viewer.pageShown.connect(self.updatePageButtons)
        
        self.documentList = DocumentChooser()
        self.documentList.chosen.connect(self.openDocument)
        
        # Add buttons to the panel.
        self.sleepButton.clicked.connect(self.setSleepImage)
        self.sleepButton.show()
        
        self.previousButton = buxpaper.Button(u"\u25c4")
        self.previousButton.clicked.connect(self.documentList.previousPage)
        self.documentList.previousButtonState.connect(self.previousButton.setEnabled)
        self.panel.addWidget(self.previousButton)
        
        self.nextButton = buxpaper.Button(u"\u25ba")
        self.nextButton.clicked.connect(self.documentList.nextPage)
        self.documentList.nextButtonState.connect(self.nextButton.setEnabled)
        self.panel.addWidget(self.nextButton)
        
        self.backButton = buxpaper.Button(u"\u00ab")
        self.backButton.clicked.connect(self.viewer.backMany)
        self.panel.addWidget(self.backButton)
        
        self.forwardButton = buxpaper.Button(u"\u00bb")
        self.forwardButton.clicked.connect(self.viewer.forwardMany)
        self.panel.addWidget(self.forwardButton)
        
        self.fontSizeButton = buxpaper.Button("F")
        self.fontSizeButton.clicked.connect(self.setFontSize)
        self.panel.addWidget(self.fontSizeButton)
        
        self.documentButton = buxpaper.Button("B")
        self.documentButton.clicked.connect(self.chooseDocument)
        self.panel.addWidget(self.documentButton)
        
        layout = QStackedLayout(self.contentWidget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.viewer)
        layout.addWidget(self.documentList)
        
        self.documentList.loadDocumentDetails()
    
    def closeEvent(self, event):
    
        self.viewer.saveConfiguration()
    
    def setFontSize(self):
    
        # Show a font size selection dialog.
        chooser = FontChooser(self.viewer.font())
        pos = self.mapToGlobal(self.fontSizeButton.geometry().bottomLeft())
        pos -= QPoint(0, max(self.fontSizeButton.height(),
                             chooser.maxButtonSize.height()))
        chooser.move(pos)
        chooser.exec_()
        self.viewer.updateFont(chooser.chosenFont)
    
    def chooseDocument(self):
    
        if self.contentWidget.layout().currentWidget() == self.viewer:
            self.sleepButton.hide()
            self.previousButton.show()
            self.nextButton.show()
            self.backButton.hide()
            self.forwardButton.hide()
            self.contentWidget.layout().setCurrentWidget(self.documentList)
        else:
            self.sleepButton.show()
            self.previousButton.hide()
            self.nextButton.hide()
            self.backButton.show()
            self.forwardButton.show()
            self.contentWidget.layout().setCurrentWidget(self.viewer)
    
    def updatePageButtons(self, page):
    
        self.previousButton.hide()
        self.nextButton.hide()
        self.backButton.show()
        self.forwardButton.show()
        
        self.backButton.setEnabled(self.viewer.hasPreviousPage())
        self.forwardButton.setEnabled(self.viewer.hasNextPage())
        self.sleepButton.setEnabled(True)
    
    def openDocument(self, path):
    
        self.contentWidget.layout().setCurrentWidget(self.viewer)
        self.viewer.openDocument(path)
        self.sleepButton.setEnabled(True)
    
    def setSleepImage(self):
    
        image = QImage(self.viewer.size(), QImage.Format_RGB16)
        self.viewer.render(image)
        
        self.sleepButton.setEnabled(False)
        self.saveSleepImage(image)


class FontChooser(QDialog):

    def __init__(self, font):
    
        QDialog.__init__(self)
        self.setWindowFlags(Qt.CustomizeWindowHint)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        for i in range(-4, 6, 2):
            f = QFont(font)
            f.setPointSize(font.pointSize() + i)
            button = buxpaper.Button("F")
            button.setFont(f)
            button.clicked.connect(self.chooseFont)
            layout.addWidget(button)
        
        self.maxButtonSize = button.sizeHint()
    
    def chooseFont(self):
    
        self.chosenFont = self.sender().font()
        self.accept()


class DocumentChooser(buxpaper.PagedWidget):

    chosen = pyqtSignal(unicode)
    
    def __init__(self, parent = None):
    
        buxpaper.PagedWidget.__init__(self, parent)
        self.previousButton.hide()
        self.nextButton.hide()
    
    def loadDocumentDetails(self):
    
        names = os.listdir(buxpaper.docdir)
        names.sort()
        
        for name in names:
        
            doc_path = os.path.join(buxpaper.docdir, name)
            label = buxpaper.Label(name, doc_path)
            label.setFrameShape(QFrame.NoFrame)
            label.adjustSize()
            label.clicked.connect(self.chooseDocument)
            self.addWidget(label)
        
        self.setCurrentPage(0)
    
    def chooseDocument(self):
    
        label = self.sender()
        self.chosen.emit(label.data)


class Viewer(QWidget):

    pageShown = pyqtSignal(int)
    
    def __init__(self, parent = None):
    
        QWidget.__init__(self, parent)
        
        self.pressed = False
        self.setFont(QApplication.font())
        
        self.document = None
        self.page = 0
        self.paragraphs = []
        self.paragraph_index = [(0, 0)]
        self.image = QImage()
        
        self.config = buxpaper.Config(buxpaper.settings + "-reader")
        self.config.load()
    
    def mousePressEvent(self, event):
    
        if self.pressed:
            return
        
        self.pressed = True
        
        if event.pos().x() >= 500:
            self.nextPage()
        elif event.pos().x() <= 300:
            self.previousPage()
    
    def mouseReleaseEvent(self, event):
    
        self.pressed = False
    
    def paintEvent(self, event):
    
        painter = QPainter()
        painter.begin(self)
        painter.drawImage(event.rect(), self.image, event.rect())
        painter.end()
    
    def showEvent(self, event):
    
        document = self.config.get("Current", None)
        if document:
            self.openDocument(document)
    
    def openDocument(self, path):
    
        self.document = unicode(path)
        self.config.set("Current", self.document)
        
        text = unicode(open(path).read(), "utf8")
        text = text.replace(u"\r", u"")
        
        self.paragraphs = []
        for paragraph in text.split(u"\n\n"):
        
            self.paragraphs.append(paragraph.lstrip(u"\n").replace(u"\n", u" "))
        
        details = self.config.get(self.document, {"Page": 0, "Index": [(0, 0)]})
        
        self.page = details["Page"]
        self.paragraph_index = details["Index"]
        
        self.showPage()
    
    def new_layout(self, text_option, current, start):
    
        while current < len(self.paragraphs) and \
            not self.paragraphs[current]:
        
            current += 1
        
        if current == len(self.paragraphs):
            return None, current, start
        
        layout = QTextLayout(self.paragraphs[current][start:], self.font())
        layout.setTextOption(text_option)
        return layout, current, start
    
    def new_page(self):
    
        self.image = QImage(self.size(), QImage.Format_RGB16)
        self.image.fill(QColor(255, 255, 255))
        painter = QPainter(self.image)
        painter.setFont(self.font())
        painter.setRenderHint(QPainter.TextAntialiasing)
        
        return painter
    
    def showPage(self):
    
        painter = self.new_page()
        
        self.formatPage(painter)
        
        if self.document:
            self.config.set(self.document, {"Page": self.page,
                                            "Index": self.paragraph_index})
        
        self.pageShown.emit(self.page)
    
    def formatPage(self, painter):
    
        text_option = QTextOption(Qt.AlignJustify)
        text_option.setWrapMode(QTextOption.WordWrap)
        
        cx = 8
        pending_line = False
        
        # Read the current paragraph index and start index inside the paragraph
        # for this page.
        current, start = self.paragraph_index[self.page]
        layout, current, start = self.new_layout(text_option, current, start)
        if not layout:
            return lines
        
        # Update the paragraph index and start index to hold the correct values
        # for the current paragraph.
        self.paragraph_index[self.page] = (current, start)
        layout.beginLayout()
        
        metrics = QFontMetricsF(self.font(), self.image)
        leading = metrics.leading()
        paragraph_spacing = abs(leading * 4)
        first_line = True
        
        cy = 0
        
        while current < len(self.paragraphs):
        
            if not pending_line:
                line = layout.createLine()
            else:
                pending_line = False
            
            if not line.isValid():
            
                # Not a valid line. Start a new layout with a new paragraph.
                layout.endLayout()
                current += 1
                layout, current, start = self.new_layout(text_option, current, 0)
                
                if not layout:
                    pending_line = False
                    break
                
                if not first_line:
                    cy += paragraph_spacing
                else:
                    first_line = False
                
                layout.beginLayout()
                continue
            
            else:
                first_line = False
                
                line.setLineWidth(self.width() - 2*cx)
                cy += max(0, leading)
                line.setPosition(QPointF(cx, cy))
                
                if cy + line.height() >= self.height():
                    pending_line = True
                    break
                
                # Record the text in the paragraph, starting part way through
                # the string continuing a paragraph.
                line.draw(painter, QPointF(0, 0))
                cy += line.height()
        
        if pending_line:
            start = start + line.textStart()
        else:
            start = 0
        
        # If the starting paragraph for the current page has not been added to
        # the paragraph index then append it.
        if current < len(self.paragraphs):
            if self.page == len(self.paragraph_index) - 1:
                self.paragraph_index.append((current, start))
            else:
                self.paragraph_index[self.page + 1] = (current, start)
    
    def hasPreviousPage(self):
    
        return self.page > 0
    
    def hasNextPage(self):
    
        # Return True if there is a following page.
        return self.page < (len(self.paragraph_index) - 1)
    
    def previousPage(self):
    
        if self.hasPreviousPage():
            self.page -= 1
            self.showPage()
            self.update()
    
    def nextPage(self):
    
        if self.hasNextPage():
            self.page += 1
            self.showPage()
            self.update()
    
    def backMany(self):
    
        if self.page > 10:
            self.page -= 10
        else:
            self.page = 0
        
        self.showPage()
        self.update()
    
    def forwardMany(self):
    
        page = self.page + 10
        while self.page < page:
            if self.hasNextPage():
                self.page += 1
            else:
                break
        
        self.showPage()
        self.update()
    
    def updateFont(self, font):
    
        # Reformat the document using the new font up to the paragraph at the
        # top of the current page.
        current, start = self.paragraph_index[self.page]
        
        self.setFont(font)
        
        self.page = 0
        self.paragraph_index = [(0, 0)]
        
        while self.paragraph_index[-1][0] < current:
            self.formatPage()
            if self.hasNextPage():
                self.page += 1
            else:
                break
        
        last_para, last_start = self.paragraph_index[-1]
        if last_para > current:
            self.page -= 1
        elif last_para == current and last_start > 0:
            self.page -= 1
        
        self.showPage()
        self.update()
    
    def saveConfiguration(self):
    
        self.config.save()


if __name__ == "__main__":

    app = buxpaper.Application()
    
    window = Window()
    window.showFullScreen()
    
    sys.exit(app.exec_())
