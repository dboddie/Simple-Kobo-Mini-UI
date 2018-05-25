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

import calendar, datetime, os, sys
import buxpaper

from PyQt4.QtCore import QProcess, QString, QTimer, Qt, pyqtSignal
from PyQt4.QtGui import *

SecretCalendarDir = os.path.join(os.path.split(buxpaper.settings)[0], ".Calendar")
CalendarDir = os.path.join(os.path.split(buxpaper.settings)[0], "Calendar")

class CalendarLabel(QWidget):

    clicked = pyqtSignal()
    
    def __init__(self, parent = None):
    
        QWidget.__init__(self, parent)
        self.text = u""
        self.colour = "white"
        self.borders = ""
        self.text = ""
    
    def mouseReleaseEvent(self, event):
    
        self.clicked.emit()
    
    def paintEvent(self, event):
    
        painter = QPainter()
        painter.begin(self)
        painter.fillRect(self.rect(), QColor(self.colour))
        painter.setPen(QPen(Qt.black))
        painter.drawText(self.rect(), Qt.AlignCenter, self.text)
        if "l" in self.borders:
            painter.drawLine(self.rect().topLeft(), self.rect().bottomLeft())
        if "r" in self.borders:
            painter.drawLine(self.rect().topRight(), self.rect().bottomRight())
        if "t" in self.borders:
            painter.drawLine(self.rect().topLeft(), self.rect().topRight())
        if "b" in self.borders:
            painter.drawLine(self.rect().bottomLeft(), self.rect().bottomRight())
        painter.end()


class Calendar(buxpaper.Window):

    LabelFormat = "%d"
    CurrentLabelColour = "#c0c0c0"
    AppointmentLabelColour = "#d0d0d0"
    
    DayHeadingsRow = 1
    DayRows = range(2, 8)
    
    def __init__(self):
    
        buxpaper.Window.__init__(self)
        
        self.editing = False
        
        self.sleepButton.clicked.connect(self.setSleepImage)
        self.sleepButton.show()
        
        self.previousButton = buxpaper.Button(u"\u25c4")
        self.previousButton.clicked.connect(self.previousMonth)
        self.panel.addWidget(self.previousButton)
        
        self.nextButton = buxpaper.Button(u"\u25ba")
        self.nextButton.clicked.connect(self.nextMonth)
        self.panel.addWidget(self.nextButton)
        
        self.config = buxpaper.Config(os.path.join(CalendarDir, "calendar.json"))
        self.config.load()
        
        self.label_format = self.config.get(
            "Label format", self.LabelFormat)
        self.current_label_colour = self.config.get(
            "Current label colour", self.CurrentLabelColour)
        self.appointment_label_colour = self.config.get(
            "Appointment label colour", self.AppointmentLabelColour)
        
        self.appointments = self.config.get("Appointments", {})
        
        # Use a stacked layout inside the main content widget.
        layout = QStackedLayout(self.contentWidget)
        layout.setContentsMargins(0, 0, 0, 0)
        self.createMonthPage()
        layout.addWidget(self.monthPage)
        self.createDayPage()
        layout.addWidget(self.dayPage)
        
        today = datetime.date.today()
        self.showMonth(today.year, today.month)
    
    def createMonthPage(self):
    
        self.monthPage = QWidget()
        
        # Create a grid layout inside the month page so that we can lay out
        # labels for the days.
        layout = QGridLayout(self.monthPage)
        layout.setSpacing(0)
        
        # There should be at most six rows shown at any time, plus one row for
        # the headings, and another for the month name.
        self.monthLabel = CalendarLabel()
        f = QFont(self.monthLabel.font())
        f.setWeight(QFont.Bold)
        self.monthLabel.setFont(f)
        
        layout.addWidget(self.monthLabel, 0, 0, 1, 7)
        layout.setRowStretch(0, 2)
        
        for column in range(7):
            label = CalendarLabel()
            label.text = calendar.day_abbr[column]
            label.borders = "tb"
            label.borders += "l     r"[column]
            layout.addWidget(label, self.DayHeadingsRow, column)
        
        layout.setRowStretch(self.DayHeadingsRow, 1)
        
        self.dayLabels = {}
        
        for row in self.DayRows:
            for column in range(7):
                label = CalendarLabel()
                label.clicked.connect(self.showDay)
                self.dayLabels[(row,column)] = label
                layout.addWidget(label, row, column)
            
            layout.setRowStretch(row, 2)
    
    def showMonth(self, year, month):
    
        self.current_date = (year, month)
        
        self.monthLabel.text = u"%s %i" % (calendar.month_name[month], year)
        self.monthLabel.update()
        
        day_date = datetime.date(year, month, 1)
        
        for row in self.DayRows:
            for column in range(7):
                label = self.dayLabels[(row, column)]
                label.text = ""
                label.colour = "white"
                label.borders = ""
                label.update()
        
        today = datetime.date.today()
        
        row = self.DayRows[0]
        while True:
        
            column = day_date.weekday()
            label = self.dayLabels[(row, column)]
            
            template = day_date.strftime(self.label_format)
            
            if self.appointments.has_key(day_date.isoformat()):
                label.colour = self.AppointmentLabelColour
            elif day_date == today:
                label.colour = self.CurrentLabelColour
            else:
                label.colour = "white"
            
            if day_date == today:
                label.borders = "lrtb"
            else:
                label.borders = ""
            
            label.text = template
            label.update()
            
            if column == 6:
                row += 1
            
            day_date += datetime.timedelta(days = 1)
            
            if day_date.day == 1:
                break
        
        self.contentWidget.layout().setCurrentWidget(self.monthPage)
        self.sleepButton.setEnabled(True)
    
    def showMonthPage(self):
    
        year, month = self.current_date
        self.showMonth(year, month)
    
    def previousMonth(self):
    
        year, month = self.current_date
        
        if month > 1:
            month -= 1
        else:
            month = 12
            year -= 1
        
        self.showMonth(year, month)
    
    def nextMonth(self):
    
        year, month = self.current_date
        
        if month < 12:
            month += 1
        else:
            month = 1
            year += 1
        
        self.showMonth(year, month)
    
    def createDayPage(self):
    
        self.dayPage = QWidget()
        layout = QVBoxLayout(self.dayPage)
        
        self.dayTitle = QLabel()
        layout.addWidget(self.dayTitle)
        self.dayBrowser = QTextBrowser()
        layout.addWidget(self.dayBrowser)
        
        layout.addStretch()
        
        buttons = QHBoxLayout()
        editButton = buxpaper.Label(self.tr("Edit"))
        editButton.clicked.connect(self.editDayText)
        buttons.addWidget(editButton)
        
        backButton = buxpaper.Label(self.tr("Back"))
        backButton.clicked.connect(self.showMonthPage)
        buttons.addWidget(backButton)
        
        layout.addLayout(buttons)
    
    def showDay(self):
    
        year, month = self.current_date
        monthText = calendar.month_name[month]
        button = self.sender()
        self.day = button.text
        self.dayTitle.setText(self.tr("%1 %2 %3").arg(button.text).arg(monthText).arg(year))
        
        day_date = datetime.date(year, month, int(self.day))
        try:
            text = self.appointments[day_date.isoformat()]
            self.dayBrowser.setPlainText(text)
        except KeyError:
            self.dayBrowser.clear()
        
        self.contentWidget.layout().setCurrentWidget(self.dayPage)
        self.sleepButton.setEnabled(True)
    
    def editDayText(self):
    
        self.sleepButton.setEnabled(False)
        self.editing = True
        
        text = self.dayBrowser.toPlainText().toUtf8()
        text = buxpaper.get_keyboard_input(text)
        self.dayBrowser.setPlainText(text)
        
        year, month = self.current_date
        day_date = datetime.date(year, month, int(self.day))
        new_text = unicode(text)
        if new_text:
            self.appointments[day_date.isoformat()] = new_text
        else:
            del self.appointments[day_date.isoformat()]
        
        QTimer.singleShot(0, self.finishEditing)
    
    def finishEditing(self):
    
        self.sleepButton.setEnabled(True)
        self.editing = False
    
    def setSleepImage(self):
    
        if self.contentWidget.layout().currentWidget() == self.dayPage:
            image = QImage(self.dayPage.size(), QImage.Format_RGB16)
            self.dayPage.render(image)
        else:
            image = QImage(self.monthPage.size(), QImage.Format_RGB16)
            self.monthPage.render(image)
        
        self.saveSleepImage(image)
        self.sleepButton.setEnabled(False)
    
    def closeEvent(self, event):
    
        if self.editing:
            event.ignore()
            return
        
        self.config.set("Label format", self.label_format)
        self.config.set("Current label colour", self.current_label_colour)
        self.config.set("Appointment label colour", self.appointment_label_colour)
        self.config.set("Appointments", self.appointments)
        self.config.save()
    
    def display_and_quit(self):
    
        # Use a special Application method.
        QApplication.display_and_quit(self.calendar)


if __name__ == "__main__":

    if not buxpaper.unlock(SecretCalendarDir, CalendarDir):
        sys.exit(1)
    
    app = buxpaper.Application()
    c = Calendar()
    c.showFullScreen()
    sys.exit(app.exec_())
