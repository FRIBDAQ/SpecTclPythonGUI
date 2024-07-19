'''  This module provides a strip chart spectrum editor.   Strip chart
    spectra are spectra with two parameters.  An xparameter is usually
    time related.  The Y parameter is summed over the time the x parameter
    dwells in a bin.  The result is a 1-d spectrum that looks a lot like
    a strip chart.  If the x parameter goes off the end of the x axis,
    the x axis is redefined to includde the X parameter (and some slop) 
    and the data are scrolled - just like a real strip chart recorder.

    At the time this module is being written, only SpecTcl supports
    strip chart spectra.

    The GUI looks like this:

    +-------------------------------------------------+
    |  Name: [   line editor for spectrum name]       |
    |    [X parameter chooser.]  [parameter chooser]  |
    |             [x axis input]                      |
    |            [ create/replace ]                   |
    +-------------------------------------------------+

    Signals:
 *   commit - the Create/Replace button was clicked.
 
 
   Attributes:
 *    name  - spectrum name.
 *    xparam - Xparameter name.
 *    yparam - Yparameter name.
 *    low, high, bins - axis specification.

'''

from PyQt5.QtWidgets import (
    QWidget, QLabel, QLineEdit, QPushButton, 
    QVBoxLayout, QHBoxLayout,
    QApplication, QMainWindow
)
from PyQt5.QtCore import pyqtSignal, Qt
from ParameterChooser import LabeledParameterChooser, update_model

from axisdef import AxisInput
from rustogramer_client import rustogramer as Client


class StripChartEditor(QWidget):
    commit = pyqtSignal()
    def __init__(self, *args):
        super().__init__(*args)
        layout = QVBoxLayout()
        
        # Row 1 is the name:
        
        row1 = QHBoxLayout()
        

        row1.addWidget(QLabel('Name:', self))
        self._spectrumName = QLineEdit(self)
        row1.addWidget(self._spectrumName)
        layout.addLayout(row1)

        row2 = QHBoxLayout()
        xplayout = QVBoxLayout()
        xplayout.addWidget(QLabel('Time parameter', self))
        self._time = LabeledParameterChooser(self)
        xplayout.addWidget(self._time)
        row2.addLayout(xplayout)

        yplayout = QVBoxLayout()
        yplayout.addWidget(QLabel('Vertical parameter', self))
        self._vparam = LabeledParameterChooser(self)
        yplayout.addWidget(self._vparam)
        row2.addLayout(yplayout)
        row2.addStretch(1)
        layout.addLayout(row2)

        row3 = QHBoxLayout()
        self._axis = AxisInput(self)
        row3.addWidget(self._axis)
        row3.addStretch(1)
        layout.addLayout(row3)

        row4 = QHBoxLayout()
        self._commit = QPushButton('Create/Replace', self)
        row4.addWidget(self._commit)
        row4.addStretch(1)
        layout.addLayout(row4)
        layout.addStretch(1)

        self.setLayout(layout)

        # Relay the commit button click -> our commit signal:

        self._commit.clicked.connect(self.commit)
    
    #  Implement the attributes:

    def name(self):
        return self._spectrumName.text()
    def setName(self, new_name):
        self._spectrumName.setText(new_name)
    
    def xparam(self):
        return self._time.parameter()
    def setXparam(self, new_name):
        self._time.setParameter(new_name)
    
    def yparam(self):
        return self._vparam.parameter()
    def setYparam(self, new_name):
        self._vparam.setParameter(new_name)

    def low(self):
        return self._axis.low()
    def setLow(self, value):
        self._axis.setLow(value)
    
    def high(self):
        return self._axis.high()
    def setHigh(self, value):
        self._axis.setHigh(value)

    def bins(self):
        return self._axis.bins()
    def setBins(self, value):
        self._axis.setBins(value)

#-----------------------  test code ---------------------------------

def _commit() :
    print(" Create: ", w.name())  
    w.setName('')
    print('time parameter', w.xparam())
    w.setXparam('')
    print('vertical parameter', w.yparam())
    w.setYparam('')
    print("axis:", w.low(), w.high(), w.bins())
    w.setLow(0),
    w.setHigh(512),
    w.setBins(512)


if __name__ == '__main__':
    app = QApplication([])
    c   = QMainWindow()
    w   = StripChartEditor(c)

    client = Client({'host': 'localhost', 'port': 8000})
    update_model(client)
    w.commit.connect(_commit)

    c.setCentralWidget(w)
    c.show()
    app.exec()