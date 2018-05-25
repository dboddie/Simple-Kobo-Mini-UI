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

import codecs, os, subprocess, sys
from json import JSONEncoder, JSONDecoder

class Config:

    def __init__(self, path, values = None):
    
        self.path = path
        if values:
            self.values = values
        else:
            self.values = {}
    
    def load(self):
    
        try:
            settings = codecs.open(self.path, "r", "utf8").read()
        except IOError:
            return False
        
        try:
            self.values = JSONDecoder().decode(settings)
        except ValueError:
            return False
        
        return True
    
    def save(self):
    
        try:
            f = codecs.open(self.path, "w", "utf8")
            f.write(JSONEncoder().encode(self.values))
            f.close()
        except IOError:
            return False
        
        return True
    
    def get(self, key, default):
    
        return self.values.get(key, default)
    
    def set(self, key, value):
    
        self.values[key] = value


# Load the configuration file and set the path so that the PyQt modules can be
# imported.
settings = os.path.abspath(os.path.join(os.getenv("HOME", ""), ".buxpaper"))

config = Config(settings)

path = config.get("PYTHONPATH", "/usr/local/arm-linux-gnueabi/lib/python2.6/site-packages")
sys.path.append(path)

fbdev = config.get("framebuffer device", "/dev/fb0")
touchinput = config.get("touch input driver", "linuxinput:/dev/input/event1")

appdir = config.get("applications directory",
                    os.path.join(os.path.split(settings)[0], "Applications"))
docdir = config.get("documents directory",
                    os.path.join(os.path.split(settings)[0], "Documents"))
picdir = config.get("pictures directory",
                    os.path.join(os.path.split(settings)[0], "Pictures"))
drawdir = config.get("drawings directory",
                     os.path.join(os.path.split(settings)[0], "Drawings"))

thumbnail_size = config.get("thumbnail size", [180, 180])

# Write the default values back to the configuration file.
config.set("PYTHONPATH", path)
config.set("framebuffer device", fbdev)
config.set("touch input device", touchinput)

config.set("applications directory", appdir)
config.set("documents directory", docdir)
config.get("pictures directory", picdir)
config.get("drawings directory", drawdir)

config.save()


# Application and framebuffer handling classes and modules.

from PyQt4.QtCore import QPoint, QRect, QSize, Qt, pyqtSignal
from PyQt4.QtGui import *

import linuxfb

class Application(QApplication):

    def __init__(self, server = False):
    
        argv = sys.argv[:]
        
        if server and "-qws" not in argv:
            argv.append("-qws")
        
        # Set the touch input driver before starting the application.
        QWSServer.setDefaultMouse(touchinput)
        
        QApplication.__init__(self, argv)
        
        # Set the default font to something readable.
        font_family = config.get("font", "DejaVu Serif")
        font_size = int(config.get("font size", 24))
        
        font = QFont(font_family)
        font.setPointSize(font_size)
        self.setFont(font)
        
        # Set the default palette to use white as the background colour.
        palette = QPalette()
        palette.setColor(QPalette.Window, Qt.white)
        self.setPalette(palette)
    
    def display_and_quit(self, widget):
    
        fb = linuxfb.Framebuffer(fbdev)
        vi = fb.virtual_screen_info()
        
        widget.resize(vi.xres, vi.yres)
        self.processEvents()
        
        image = QImage(vi.xres, vi.yres, QImage.Format_RGB16)
        p = QPainter()
        p.begin(image)
        widget.render(p)
        p.end()
        
        b = fb.get_buffer()
        data = image.bits()
        data.setsize(image.byteCount())
        b[:] = data.asstring()
        
        self.quit()

def top_layout():

    desktop = QApplication.desktop()
    geometry = desktop.screenGeometry()
    
    if geometry.width() < geometry.height():
        return QVBoxLayout, QHBoxLayout
    else:
        return QHBoxLayout, QVBoxLayout

def layout(n):
    "Returns the appropriate class for the nth layout in a window."
    return top_layout()[n % 2]

colourScheme = {" ": "\x00\x00\x00\x00",
                ".": "\x00\x00\x00\xff",
                "x": "\x80\x80\x80\xff"}

def icon_from_sequence(sequence, palette = colourScheme):

    height = len(sequence)
    width = len(sequence[0])
    
    data = "".join(map(lambda x: colourScheme.get(x, "\x00\x00\x00\x00"), "".join(sequence)))
    
    return QIcon(QPixmap.fromImage(QImage(data, width, height, QImage.Format_ARGB32)))

def icon_from_commands(sequence, width, height, palette = colourScheme):

    image = QImage(width, height, QImage.Format_ARGB32)
    painter = QPainter()
    painter.begin(image)
    
    for command, arguments in sequence:
    
        if "pen" not in arguments:
            arguments["pen"] = QColor(0, 0, 0, 0)
        if "brush" not in arguments:
            arguments["brush"] = QColor(0, 0, 0, 0)
        
        if command == "fill":
            painter.fillRect(QRect(0, 0, width, height), QColor(arguments["brush"]))
        
        elif command == "polygon":
            painter.setPen(QColor(arguments["pen"]))
            painter.setBrush(QColor(arguments["brush"]))
            painter.drawPolygon(QPolygon(map(lambda (x, y):
                                         QPoint(x * width, y * height),
                                         arguments["points"])))
        
        elif command == "polyline":
            painter.setPen(QColor(arguments["pen"]))
            painter.setBrush(QColor(arguments["brush"]))
            painter.drawPolyline(QPolygon(map(lambda (x, y):
                                          QPoint(x * width, y * height),
                                          arguments["points"])))
        
        elif command == "pie":
            painter.setPen(QColor(arguments["pen"]))
            painter.setBrush(QColor(arguments["brush"]))
            painter.drawPie(QRect(arguments["rect"][0] * width,
                                  arguments["rect"][1] * height,
                                  arguments["rect"][2] * width,
                                  arguments["rect"][3] * height),
                            arguments["start"], arguments["span"])
    
    painter.end()
    
    return QIcon(QPixmap.fromImage(image))


browser_icon = (
    ("fill", {"brush": "white"}),
    ("polygon", {"pen": "black", "brush": "#404040",
                 "points": ((0.2, 0.1), (0.4, 0.1), (0.5, 0.2),
                            (0.85, 0.2), (0.9, 0.25), (0.9, 0.9),
                            (0.1, 0.9), (0.1, 0.2))}),
    ("polygon", {"pen": "black", "brush": "black",
                 "points": ((0.2, 0.3), (0.9, 0.3))})
    )

sleep_icon = (
    ("fill", {"brush": "white"}),
    ("polygon", {"brush": "black",
                 "points": ((0.1, 0.5), (0.5, 0.5), (0.5, 0.6), (0.2, 0.8),
                            (0.5, 0.8), (0.5, 0.9), (0.1, 0.9), (0.1, 0.8),
                            (0.4, 0.6), (0.1, 0.6))}),
    ("polygon", {"brush": "#404040",
                 "points": ((0.5, 0.1), (0.9, 0.1), (0.9, 0.2), (0.6, 0.4),
                            (0.9, 0.4), (0.9, 0.5), (0.5, 0.5), (0.5, 0.4),
                            (0.8, 0.2), (0.5, 0.2))})
    )

class Window(QWidget):

    def __init__(self):
    
        QWidget.__init__(self)
        
        self.closeButton = Button(u"\u2716")
        self.closeButton.clicked.connect(self.close)
        
        sleepIcon = icon_from_commands(sleep_icon,
            self.closeButton.sizeHint().width(),
            self.closeButton.sizeHint().height())
        
        self.sleepButton = Button(sleepIcon)
        self.sleepButton.hide()
        
        OuterLayout, InnerLayout = top_layout()
        layout = OuterLayout(self)
        self.panel = InnerLayout()
        
        self.panel.addWidget(self.closeButton)
        self.panel.addStretch()
        self.panel.addWidget(self.sleepButton)
        self.panel.addStretch()
        
        self.contentWidget = QWidget()
        
        layout.addLayout(self.panel)
        layout.addWidget(self.contentWidget, 1)
    
    def setSleepImage(self):
    
        # The default implementation takes a screenshot of the content widget.
        image = QImage(self.contentWidget.size(), QImage.Format_RGB16)
        self.contentWidget.render(image)
        
        self.saveSleepImage(image)
    
    def saveSleepImage(self, image):
    
        sleep_dir = os.path.join(picdir, "Sleep")
        
        # Remove any existing images in the directory.
        for name in os.listdir(sleep_dir):
            os.remove(os.path.join(sleep_dir, name))
        
        # Reduce the image if necessary.
        size = QApplication.desktop().geometry().size()
        if image.width() > size.width() or image.height() > size.height():
            image = image.scaled(size, Qt.KeepAspectRatio)
        
        # Pad the image if necessary.
        if image.size() != size:
        
            sleepImage = QImage(size, QImage.Format_RGB16)
            sleepImage.fill(QColor(255, 255, 255))
            
            p = QPainter()
            p.begin(sleepImage)
            p.drawImage((sleepImage.width() - image.width())/2,
                        (sleepImage.height() - image.height())/2, image)
            p.end()
            
            image = sleepImage
        
        # Save the image to the directory.
        image.save(os.path.join(sleep_dir, "saved.png"))

class Button(QWidget):

    pressed = pyqtSignal()
    clicked = pyqtSignal()
    released = pyqtSignal()
    
    def __init__(self, contents, parent = None):
    
        QWidget.__init__(self, parent)
        
        self.contents = contents
        self._pressed = False
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        
        font = QFont(QApplication.font())
        font.setPointSize(font.pointSize() * 1.5)
        self.setFont(font)
    
    def mousePressEvent(self, event):
    
        if not self._pressed:
            self._pressed = True
            self.pressed.emit()
    
    def mouseReleaseEvent(self, event):
    
        if self._pressed:
            self._pressed = False
            self.clicked.emit()
            self.released.emit()
    
    def paintEvent(self, event):
    
        painter = QPainter()
        painter.begin(self)
        painter.fillRect(event.rect(), self.palette().background())
        
        if isinstance(self.contents, str) or isinstance(self.contents, unicode):
            painter.drawText(0, 0, self.width() - 1, self.height() - 1,
                             Qt.AlignCenter, self.contents)
        
        elif isinstance(self.contents, QIcon):
            mode = {False: QIcon.Disabled, True: QIcon.Normal}[self.isEnabled()]
            pixmap = self.contents.pixmap(self.width(), self.height(), mode)
            painter.drawPixmap(0, 0, pixmap)
        
        else:
            dx = (self.width() - self.contents.width())/2
            dy = (self.height() - self.contents.height())/2
            painter.drawImage(dx, dy, self.contents)
        
        painter.drawRect(self.rect().adjusted(0, 0, -1, -1))
        painter.end()
    
    def sizeHint(self):
    
        if isinstance(self.contents, str) or isinstance(self.contents, unicode):
            fm = QFontMetrics(self.font())
            size = fm.size(Qt.TextSingleLine, self.contents)
            l = max(size.width(), size.height())
            return QSize(l * 1.5, l * 1.5)
        
        elif isinstance(self.contents, QIcon):
            sizes = self.contents.availableSizes()
            if len(sizes):
                return self.contents.availableSizes()[0]
            else:
                return QSize(0, 0)
        
        else:
            l = max(self.contents.width(), self.contents.height())
            return QSize(l, l)

class Label(QLabel):

    clicked = pyqtSignal()
    pressed = pyqtSignal()
    released = pyqtSignal()
    
    def __init__(self, name, data = None):
    
        QLabel.__init__(self, name)
        
        self.data = data
        self._pressed = False
        self.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Preferred)
        self.setFrameShape(QFrame.Box)
    
    def mousePressEvent(self, event):
    
        if not self._pressed:
            self._pressed = True
            self.pressed.emit()
    
    def mouseReleaseEvent(self, event):
    
        if self.pressed:
            self._pressed = False
            self.clicked.emit()
            self.released.emit()
    
    def sizeHint(self):
    
        if not self.text().isEmpty():
            fm = QFontMetrics(QApplication.font())
            return fm.size(Qt.TextSingleLine, self.text())
        else:
            return QLabel.sizeHint(self)

class Picture(QWidget):

    clicked = pyqtSignal(QPoint)
    pressed = pyqtSignal(QPoint)
    released = pyqtSignal(QPoint)
    
    def __init__(self, image = None, data = None):
    
        QWidget.__init__(self)
        
        if not image:
            image = QImage()
        
        self.image = image
        self.data = data
        self._pressed = False
        self.setSizePolicy(QSizePolicy.MinimumExpanding,
                           QSizePolicy.MinimumExpanding)
    
    def mousePressEvent(self, event):
    
        if not self._pressed:
            self._pressed = True
            self.pressed.emit(event.pos())
    
    def mouseReleaseEvent(self, event):
    
        if self.pressed:
            self._pressed = False
            self.clicked.emit(event.pos())
            self.released.emit(event.pos())
    
    def paintEvent(self, event):
    
        p = QPainter()
        p.begin(self)
        image = self.image.scaled(self.size(), Qt.KeepAspectRatio,
                                               Qt.SmoothTransformation)
        x = (self.width() - image.width())/2
        y = (self.height() - image.height())/2
        p.drawImage(x, y, image)
        p.end()
    
    def sizeHint(self):
    
        return self.image.size()
    
    def setImage(self, image):
    
        self.image = image
        self.update()

class PagedWidget(QWidget):

    previousButtonState = pyqtSignal(bool)
    nextButtonState = pyqtSignal(bool)
    
    def __init__(self, parent = None):
    
        QWidget.__init__(self, parent)
        
        self.padding = 32
        self.stack = QStackedLayout()
        self.alignment = Qt.AlignHCenter
        
        OuterLayout, InnerLayout = top_layout()
        
        if OuterLayout == QHBoxLayout:
            self.previousButton = PagedWidget.Indicator("left")
            self.nextButton = PagedWidget.Indicator("right")
        else:
            self.previousButton = PagedWidget.Indicator("up")
            self.nextButton = PagedWidget.Indicator("down")
        
        self.previousButton.clicked.connect(self.previousPage)
        self.nextButton.clicked.connect(self.nextPage)
        
        self.updateIndicators()
        
        layout = OuterLayout(self)
        layout.setSpacing(0)
        layout.addWidget(self.previousButton)
        layout.addLayout(self.stack, 1)
        layout.addWidget(self.nextButton)
        
        # Add a default page.
        self.addPage()
    
    def addPage(self, layout = None):
    
        page = QWidget()
        
        if not layout:
            layout = QVBoxLayout(page)
        else:
            page.setLayout(layout)
        
        layout.addStretch()
        
        self.stack.addWidget(page)
        self.stack.setCurrentIndex(self.stack.count() - 1)
        self.updateIndicators()
        self.space_used = 0
        
        return page, layout
    
    def previousPage(self):
    
        self.stack.setCurrentIndex(self.stack.currentIndex() - 1)
        self.updateIndicators()
    
    def nextPage(self):
    
        self.stack.setCurrentIndex(self.stack.currentIndex() + 1)
        self.updateIndicators()
    
    def currentPage(self):
    
        return self.stack.currentIndex()
    
    def setCurrentPage(self, index):
    
        self.stack.setCurrentIndex(index)
        self.updateIndicators()
    
    def pageCount(self):
    
        return self.stack.count()
    
    def addWidget(self, widget):
    
        """Adds a widget to the page, creating a new page for it if there is
        not enough room for it. It may help to call adjustSize() on the widget
        before passing it to this method."""
        
        page = self.stack.widget(self.stack.count() - 1)
        layout = page.layout()
        
        # If there is not enough space for a spacer and another widget then
        # create a new page.
        if page.height() - self.space_used < widget.height() + self.padding:
            page, layout = self.addPage()
        
        last = layout.count() - 1
        
        layout.insertSpacing(last, self.padding)
        layout.insertWidget(last + 1, widget)
        layout.setAlignment(widget, self.alignment)
        self.space_used += self.padding + widget.height()
        
        if page.height() - self.space_used >= self.padding:
            layout.insertSpacing(last + 2, self.padding)
    
    def updateIndicators(self):
    
        self.previousButton.setEnabled(self.stack.currentIndex() > 0)
        self.nextButton.setEnabled(self.stack.currentIndex() < self.stack.count() - 1)
        
        # Emit signals to interested components.
        self.previousButtonState.emit(self.stack.currentIndex() > 0)
        self.nextButtonState.emit(self.stack.currentIndex() < self.stack.count() - 1)
    
    class Indicator(QWidget):
    
        clicked = pyqtSignal()
        
        def __init__(self, direction, parent = None):
        
            QWidget.__init__(self, parent)
            
            self.pressed = False
            self.direction = direction
            
            if direction == "up":
                self.gradient = QLinearGradient(0, 0, 0, 32)
                self.path = QPainterPath()
                self.path.moveTo(32, 0)
                self.path.lineTo(64, 32)
                self.path.lineTo(0, 32)
                self.path.closeSubpath()
                self.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Fixed)
                self.size_hint = QSize(0, 32)
            
            elif direction == "down":
                self.gradient = QLinearGradient(0, 32, 0, 0)
                self.path = QPainterPath()
                self.path.moveTo(32, 32)
                self.path.lineTo(64, 0)
                self.path.lineTo(0, 0)
                self.path.closeSubpath()
                self.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Fixed)
                self.size_hint = QSize(0, 32)
            
            elif direction == "left":
                self.gradient = QLinearGradient(0, 0, 32, 0)
                self.path = QPainterPath()
                self.path.moveTo(0, 32)
                self.path.lineTo(32, 64)
                self.path.lineTo(32, 0)
                self.path.closeSubpath()
                self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.MinimumExpanding)
                self.size_hint = QSize(32, 0)
            
            elif direction == "right":
                self.gradient = QLinearGradient(32, 0, 0, 0)
                self.path = QPainterPath()
                self.path.moveTo(32, 32)
                self.path.lineTo(0, 64)
                self.path.lineTo(0, 0)
                self.path.closeSubpath()
                self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.MinimumExpanding)
                self.size_hint = QSize(32, 0)
            
            self.gradient.setColorAt(0, Qt.black)
            self.gradient.setColorAt(1, Qt.white)
    
        def mousePressEvent(self, event):
        
            if not self.pressed:
            
                self.pressed = True
                self.clicked.emit()
        
        def mouseReleaseEvent(self, event):
        
            if self.pressed:
                self.pressed = False
        
        def paintEvent(self, event):
        
            painter = QPainter()
            painter.begin(self)
            
            if self.isEnabled():
            
                painter.setBrush(self.gradient)
                painter.setPen(QPen(Qt.NoPen))
                
                if self.direction in ("up", "down"):
                    n = event.rect().x() / 64
                    r = event.rect().x() % 64
                    v1 = event.rect().x() - r
                    v2 = event.rect().right()
                    dx, dy = 64, 0
                    painter.translate(v1, 0)
                else:
                    n = event.rect().y() / 64
                    r = event.rect().y() % 64
                    v1 = event.rect().y() - r
                    v2 = event.rect().bottom()
                    dx, dy = 0, 64
                    painter.translate(0, v1)
                
                while v1 < v2:
                    painter.drawPath(self.path)
                    painter.translate(dx, dy)
                    v1 += 64
            else:
                painter.fillRect(event.rect(), QColor(200, 200, 200))
            
            painter.end()
        
        def sizeHint(self):
        
            return self.size_hint

# System status

class Power:

    def __init__(self, path = None, sep = "="):
    
        if not path:
            self.path = ("/sys/devices/platform/pmic_battery.1/power_supply/"
                         "mc13892_bat/uevent")
        else:
            self.path = path
        
        self.sep = sep
    
    def status(self):
    
        d = {}
        for line in open(self.path).readlines():
            key, value = line.strip().split(self.sep)
            d[key] = value
        
        return d

# Keyboard input

KeyboardExecutable = os.path.join(appdir, "Keyboard", "keyboard.py")
UnlockExectutable = os.path.join(appdir, "Keyboard", "unlock.py")

def get_keyboard_input(text):

    utf8 = unicode(text).encode("utf8")
    p = subprocess.Popen([KeyboardExecutable, "--edit"],
                         stdin=subprocess.PIPE,
                         stdout=subprocess.PIPE)
    p.stdin.write("%i\n" % len(utf8))
    p.stdin.write(utf8)
    result = p.wait()
    if result == 0:
        length = int(p.stdout.readline().strip())
        utf8 = p.stdout.read(length)
    
    return unicode(utf8, "utf8")

# Security - access encrypted files using encfs

def unlock(secret_dir, mount_dir):

    p = subprocess.Popen(
        ["mount"], stdout = subprocess.PIPE)
    p.wait()
    for line in p.stdout.readlines():
        if mount_dir in line:
            return True
    
    p = subprocess.Popen(
        ["sudo", "encfs", secret_dir, mount_dir,
         "--extpass", UnlockExectutable,
         "--", "-o", "allow_other,uid=1000,gid=1000"])
    
    return p.wait() == 0
