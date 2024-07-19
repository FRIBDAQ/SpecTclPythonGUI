'''
This module provides a megawidget that supports entering axis definitions.
It consists of a low limit (RealInputBox) a high limit (RealInputBox) and
a bins (UnsignedInputBox)  All of the instances of this widget share
a common set of data models for their inputs (low, high, bins models).
This means that as users add to the set of values they use, these values
are seen in all axis def instances (each spectrum definition editor will
have one or two of these).  The initial stocking of the
model includes typical powers of two from 512 - 16384.  Since the
comboboxes are editable, as users use values other than those in the
initial model they are added to the model by Qt (I hope), and become
usable in all instances of the comboboxes.
'''

import  NumericInput as Ni
from PyQt5.QtCore import QStringListModel, pyqtSignal
from PyQt5.QtWidgets import (
    QLabel, QFrame, QGridLayout, QVBoxLayout, QMainWindow, QWidget,
    QApplication
)

_realStrings = [
    "0.0", "512.0", "1024.0", "2048.0", "4096.0", "8192.0", "16384.0"
]

_integerStrings = [
    "512", "1024", "2048", "4096", "8192", "16384"
]

# Shared models:

_lowModel = QStringListModel()
_lowModel.setStringList(_realStrings)

_highModel = QStringListModel()
_highModel.setStringList(_realStrings)

_binsModel = QStringListModel()
_binsModel.setStringList(_integerStrings)


class AxisInput(QFrame):
    ''' Axis input widget.  Provides RealInputBoxes for 
    the low and high limits and an UnsignedInputBox for bins.
    Properties:
        -   low - current low limit.
        -   high - current high limit.
        -   bins - current bins.
    Signals (which pass the value):
       lowChanged - the low limit changed.
       highChanged- the high limit changed.
       binsCHanged- the bins selected changed.

    '''

    lowChanged = pyqtSignal(float)
    highChanged = pyqtSignal(float)
    binsChanged = pyqtSignal(int)

    def __init__(self, *args):
        global _lowModel
        global _highModel
        global _binsModel
        super().__init__(*args)
        layout = QGridLayout()

        low_label = QLabel('Low', self)
        layout.addWidget(low_label, 0, 0)
        self.low_value = Ni.RealInputBox(self)
        self.low_value.setModel(_lowModel)
        self.low_value.currentIndexChanged.connect(self.new_low)
        layout.addWidget(self.low_value, 1, 0)

        high_label = QLabel('High', self)
        layout.addWidget(high_label, 0, 1)
        self.high_value = Ni.RealInputBox(self)
        self.high_value.setModel(_highModel)
        self.high_value.currentIndexChanged.connect(self.new_high)
        layout.addWidget(self.high_value, 1,1 )

        bins_label = QLabel('Bins', self)
        layout.addWidget(bins_label, 0, 2)
        self.bins_value = Ni.UnsignedInputBox(self)
        self.bins_value.setModel(_binsModel)
        self.bins_value.currentIndexChanged.connect(self.new_bins)
        layout.addWidget(self.bins_value, 1, 2)

        self.setLayout(layout)

    # slots:

    def new_low(self, new_index):
        self.lowChanged.emit(self.low())
    def new_high(self, new_index):
        self.highChanged.emit(self.high())
    def new_bins(self, new_index):
        self.binsChanged.emit(self.bins())

    # properties:

    def low(self):
        return float(self.low_value.currentText())
    def setLow(self, value):
        self.low_value.setCurrentText("{}".format(value))

    def high(self):
        return float(self.high_value.currentText())
    def setHigh(self, value):
        self.high_value.setCurrentText("{}".format(value))

    def bins(self):
        return int(self.bins_value.currentText())
    def setBins(self, value):
        self.bins_value.setCurrentText("{}".format(value))
    
#  Testing:

def low(nv):
    print("Low value now: ", nv)
def high(nv):
    print("High value: ", nv)
def bins(nv):
    print("Bins: ", nv)


def testing():
    # We need two to test the common model:

    app = QApplication([])
    w = QMainWindow()
    c = QWidget()
    l = QVBoxLayout()

    one = AxisInput(c)
    one.lowChanged.connect(low)
    one.highChanged.connect(high)
    one.binsChanged.connect(bins)
    l.addWidget(one)
    two = AxisInput(c)
    two.lowChanged.connect(low)
    two.highChanged.connect(high)
    two.binsChanged.connect(bins)
    l.addWidget(two)

    c.setLayout(l)
    w.setCentralWidget(c)

    w.show()
    app.exec()