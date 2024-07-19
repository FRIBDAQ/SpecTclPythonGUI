''' This module provides a handy widget that can set the
x or y direction for a projection.  It consists of a parent widget
and two radio buttons laid out horizontally labeled X and Y respectively.
Since the parents of the radiobuttons are the same Qt will only allow
one to be set at a time since they all have the same parent.

Signals:
  *  xSelected - The x direction was selected.
  *  ySelected - The Y direction was selected.

Properties:
  * selection sets/returns either Direction.X or Direction.Y depending on the
  selected button.  Note that setSelection will not emit the corresponding
  signal.

Initially X is selected.
'''
from enum import Enum, auto
from PyQt5.QtWidgets import (
    QWidget, QRadioButton, QHBoxLayout,
    QApplication, QMainWindow
)
from PyQt5.QtCore import pyqtSignal
#  Direction codes.

class Direction(Enum):
    X = 1
    Y = 2

class DirectionChooser(QWidget):
    xSelected = pyqtSignal()
    ySelected = pyqtSignal()

    def __init__(self, *args):
        super().__init__(*args)
        layout = QHBoxLayout()
        
        self._x = QRadioButton('X', self)
        self._x.setChecked(True)
        self._y = QRadioButton('Y', self)
        self._y.setChecked(False)

        layout.addWidget(self._x)
        layout.addWidget(self._y)
        self.setLayout(layout)

        #  Since toggling one toggles all I think we can do this:

        self._x.toggled.connect(self._changed)

        self._nosignal = False

    #   Signal relay:

    def _changed(self):
        #  selection sets _nosignal:

        if self._nosignal:
            self._nosignal = False
            return
        # X button toggled signal the appropriate selection
        if self._x.isChecked():
            self.xSelected.emit()
        if self._y.isChecked():
            self.ySelected.emit()
    # Attributes:

    def selection(self):
        if self._x.isChecked():
            return Direction.X
        else:
            return Direction.Y
    def setSelection(self, dir):
        # Success sets _nosignal so that there's no signal from this
        if dir.value == Direction.X.value:
            self._nosignal = True
            self._x.setChecked(True)
            self._y.setChecked(False)
        elif dir.value == Direction.Y.value:
            self._nosignal = True
            self._x.setChecked(False)
            self._y.setChecked(True)
        else:
            raise TypeError


#-------------------- Test code -----------

def _x():
    print("X")
def _y():
    print("Y")

if __name__ == "__main__":
    app = QApplication([])
    c   = QMainWindow()

    w  = DirectionChooser()
    w.xSelected.connect(_x)
    w.ySelected.connect(_y)

    print(w.selection().name)
    w.setSelection(Direction.Y)

    c.setCentralWidget(w)

    c.show()
    app.exec()

