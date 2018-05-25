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

import sys
import buxpaper

from PyQt4.QtCore import *
from PyQt4.QtGui import *

class KeyWidget(QWidget):

    keyEntered = pyqtSignal(unicode)
    
    def __init__(self, lower, upper):
    
        QWidget.__init__(self)
        
        self.lower = lower
        self.upper = upper
        self.pressed = False
        
        self.smallFont = QFont(QApplication.font())
        self.smallFont.setPointSize(self.smallFont.pointSize()/2)
    
    def sizeHint(self):
    
        return QSize(80, 60)
    
    def paintEvent(self, event):
    
        painter = QPainter()
        painter.begin(self)
        painter.fillRect(event.rect(), self.palette().background())
        painter.drawRect(self.rect().adjusted(0, 0, -1, -1))
        
        painter.setFont(self.smallFont)
        painter.drawText(0, 0, self.width() - 1, self.height()/3,
                         Qt.AlignCenter, self.upper)
        painter.setFont(QApplication.font())
        painter.drawText(0, self.height()/3, self.width() - 1, 2*self.height()/3 - 1,
                         Qt.AlignCenter, self.lower)
        painter.end()
    
    def mousePressEvent(self, event):
    
        if not self.pressed:
        
            self.pressed = True
            self.keyEntered.emit(self.lower)
    
    def mouseReleaseEvent(self, event):
    
        if self.pressed:
            self.pressed = False
    
    def shiftKey(self):
    
        self.lower, self.upper = self.upper, self.lower
        self.update()


class ControlWidget(KeyWidget):

    commandEntered = pyqtSignal(int)
    Shift, Control, Tab, Return, Backspace = range(5)
    
    def __init__(self, command, text):
    
        QWidget.__init__(self)
        
        self.command = command
        self.text = text
        self.pressed = False
        
        self.font = QFont(QApplication.font())
        self.font.setPointSize(self.font.pointSize() * 2)
    
    def sizeHint(self):
    
        return QSize(80, 30)
    
    def paintEvent(self, event):
    
        painter = QPainter()
        painter.begin(self)
        painter.fillRect(event.rect(), self.palette().background())
        painter.drawRect(self.rect().adjusted(0, 0, -1, -1))
        
        painter.setFont(self.font)
        painter.drawText(0, 0, self.width() - 1, self.height() - 1,
                         Qt.AlignCenter, self.text)
        painter.end()
    
    def mousePressEvent(self, event):
    
        if not self.pressed:
        
            self.pressed = True
            self.commandEntered.emit(self.command)
            self.update()


class KeyboardWidget(buxpaper.Window):

    rows = [("1234567890-=", '!"`$%^&*()_+'),
            ("qwertyuiop[]", "QWERTYUIOP{}"),
            ("asdfghjkl;'#", "ASDFGHJKL:@~"),
            ("\zxcvbnm,./",  "|ZXCVBNM<>?")]
    
    def __init__(self, password = False):
    
        buxpaper.Window.__init__(self)
        self.password = password
        self.text = u""
        
        self.sleepButton.clicked.connect(self.setSleepImage)
        
        if self.password:
            self.editor = QTextBrowser()
            f = QFont()
            f.setPointSize(f.pointSize() * 2)
            self.editor.setFont(f)
        else:
            self.editor = QTextEdit()
        
        self.grid = QGridLayout()
        self.grid.setContentsMargins(0, 0, 16, 0)
        
        self.keys = []
        i = 0
        for lower_row, upper_row in self.rows:
            j = 0
            for lower, upper in zip(lower_row, upper_row):
                button = KeyWidget(lower, upper)
                button.keyEntered.connect(self.insertCharacter)
                self.grid.addWidget(button, i, j)
                self.keys.append(button)
                j += 1
            i += 1
        
        backspaceButton = ControlWidget(ControlWidget.Backspace, u"\u21d0")
        backspaceButton.commandEntered.connect(self.backspace)
        self.grid.addWidget(backspaceButton, i - 1, j)
        
        shiftButton = ControlWidget(ControlWidget.Shift, u"\u21d1")
        shiftButton.commandEntered.connect(self.shiftKeys)
        self.grid.addWidget(shiftButton, i, 0)
        
        leftButton = ControlWidget(QTextCursor.Left, u"\u2190")
        leftButton.commandEntered.connect(self.moveCursor)
        self.grid.addWidget(leftButton, i, 1)
        
        rightButton = ControlWidget(QTextCursor.Right, u"\u2192")
        rightButton.commandEntered.connect(self.moveCursor)
        self.grid.addWidget(rightButton, i, 2)
        
        spaceButton = KeyWidget(" ", " ")
        spaceButton.keyEntered.connect(self.editor.insertPlainText)
        self.grid.addWidget(spaceButton, i, 3, 1, 5)
        
        upButton = ControlWidget(QTextCursor.Up, u"\u2191")
        upButton.commandEntered.connect(self.moveCursor)
        self.grid.addWidget(upButton, i, 8)
        
        downButton = ControlWidget(QTextCursor.Down, u"\u2193")
        downButton.commandEntered.connect(self.moveCursor)
        self.grid.addWidget(downButton, i, 9)
        
        returnButton = ControlWidget(ControlWidget.Return, u"\u21b5")
        returnButton.commandEntered.connect(self.insertReturn)
        self.grid.addWidget(returnButton, i, 10, 1, 2)
        
        if self.password:
            leftButton.setEnabled(False)
            rightButton.setEnabled(False)
            upButton.setEnabled(False)
            downButton.setEnabled(False)
            returnButton.setEnabled(False)
        
        layout = QVBoxLayout(self.contentWidget)
        if self.password:
            layout.addWidget(QLabel(self.tr("Insert password:")))
        layout.addWidget(self.editor)
        layout.addLayout(self.grid)
    
    def shiftKeys(self):
    
        for key in self.keys:
            key.shiftKey()
    
    def insertCharacter(self, character):
    
        if self.password:
            self.text += character
            self.editor.insertPlainText(u"*")
        else:
            self.editor.insertPlainText(character)
    
    def insertReturn(self):
    
        self.editor.insertPlainText("\n")
    
    def backspace(self):
    
        if self.password:
            self.text = self.text[:-1]
        
        cursor = self.editor.textCursor()
        cursor.deletePreviousChar()
        self.editor.setTextCursor(cursor)
    
    def moveCursor(self, operation):
    
        cursor = self.editor.textCursor()
        cursor.movePosition(operation)
        self.editor.setTextCursor(cursor)


if __name__ == "__main__":

    app = buxpaper.Application()
    read_password = "--password" in app.arguments()
    kbd = KeyboardWidget(password = read_password)
    kbd.showFullScreen()
    
    if "--edit" in app.arguments():
        length = int(sys.stdin.readline().strip())
        text = sys.stdin.read(length)
        kbd.editor.setPlainText(QString.fromUtf8(text))
    
    result = app.exec_()
    if read_password:
        text = kbd.text
    else:
        text = kbd.editor.toPlainText().toUtf8()
    
    print len(text)
    sys.stdout.write(text)
    sys.exit(result)
