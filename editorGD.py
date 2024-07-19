'''  This module provides an editor for particle gamma spectra,
which SpecTcl calls, thanks to Dirk, Gamma Deluxe spectra.  These have
an arbitrary number of X parameters and an arbitrary number of Y parameters.
The GUI looks like a single parameter chooser with two lists, one each for
the X and Y parameters.  There are, therefore, two add arrows and two delete 
arrows, again, one each for each axis.  There is one array checkbutton.
The user chooses a parameter in the single selector and clicks the appropriate
arrow to add that parameter or parameter array to the desired axis list.
Each axis list supports the same sorts of editing that is supported by
the Summary,Gamma1D, Gamma2D editor.   Selected blocks of parameters can
be moved up or down, selected parameters can be removed from each  list
and lists can be cleared.

Here's a sample configuration:

+----------------------------------------+
| Name [    line edit  ]                 |
|                          X parameters  |
|                         +------------+ |
|                    >       ...         |
|                    x    +------------+ |
|  parameter chooser        ^ V [clear]  |
|  [ ] array                             |
|                           Y parameters | 
|                         +------------+ |
|                     >        ...       |
|                     X   +------------+ |
|                          ^ V [clear]   |
|  X axis          Y axis                |
| [axis input]    [ axis input]          |
|           [Create/Replace]             |
+----------------------------------------+

NOTE: Per Issue #155 - the two parameter lists are laid out side
by side. using a ParameterListSelector.DoubleList

'''

from PyQt5.QtWidgets import (
    QLabel, QLineEdit, QListWidget, QCheckBox, QPushButton, QWidget,
    QApplication, QMainWindow,
    QStyle,
    QVBoxLayout, QHBoxLayout, QGridLayout
)
from PyQt5.QtCore import pyqtSignal
from PyQt5.Qt import *

from axisdef import AxisInput
from ParameterChooser import Chooser as ParameterChooser
from editablelist import EditableList
from ParameterListselector import DoubleList

##  Internal widget that is a labeled axis input:

class _Axis(QWidget):
    ''' A labeled axis definition.
        no signals, but attributes are:
        label - text used to label the widget.
        low   - axis low limit
        high  - axis high limit.
        bins  - axis bin count.
    '''
    def __init__(self, label, *args):
        super().__init__(*args)
        layout = QVBoxLayout()
        self._label = QLabel(label, self)
        layout.addWidget(self._label)
        self._axis = AxisInput(self)
        layout.addWidget(self._axis)
        self.setLayout(layout)

    # Attribute getter/setters.

    def label(self):
        return self._label.text()
    def setLabel(self, newLabel):
        self._label.setText(newLabel)
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
    


class GammaDeluxeEditor(QWidget):
    '''
    Signals:
       addXParameters  - Click on add button for X parameters
       xParameterRemoved - A parameter was removed from the X list.
       addYParameters  - Click on add button for Y parameters
       yParameterRemoved - A parameter was removed from the Y list.
       
       commit          - Create/Replace spectrum.
    Attributes:
       name - spectrum name.
       xparameters - Contents of X parameters list box.
       yparameters  - Contents of Y parameters list box.
       selectedParameter -  currently selected parameter
       array       - State of array checkbutton.
       axis_from_parameters - state of axis from parameters checkbutton.
       xlow, xhigh, xbins - X axis specification.
       ylow, yhigh, ybins - Y Axis specification.

    '''
    addXParameters    = pyqtSignal()
    xParameterRemoved = pyqtSignal(str)
    addYParameters    = pyqtSignal()
    yParameterRemoved = pyqtSignal(str)
    commit            = pyqtSignal()
    def __init__(self, *args):
        super().__init__(*args)
        
        # As usual the whole thing is a bunch of vertically stacked
        # horizontal boxes.
        
        layout = QVBoxLayout()
        
        # Row 1 is the name of the spectrum:
        
        row1 = QHBoxLayout()
        row1.addWidget(QLabel('Name: ', self))
        self._name = QLineEdit(self);
        row1.addWidget(self._name)
        
        layout.addLayout(row1)
        
        # Row 2 is the double list:
        
        self._parameters = DoubleList(self)
        layout.addWidget(self._parameters)
        
        # Below are the axes and from parameters checkbox:
        
        axes = QHBoxLayout()
        self._xaxis = _Axis('X axis')
        axes.addWidget(self._xaxis)
        self._from_parameters = QCheckBox('From Parameters', self)
        axes.addWidget(self._from_parameters)
        self._yaxis = _Axis('Y  axis')
        axes.addWidget(self._yaxis)
        
        layout.addLayout(axes)
        
        # At the bottom of all of this is the Create/Replace button in an hbox 
        # WITH A Stretch to keep it from filling the horizontal extent:
        
        commit = QHBoxLayout()
        self._commit = QPushButton('Create/Replace', self)
        commit.addWidget(self._commit)
        commit.addStretch(1)
        
        layout.addLayout(commit)
        layout.addStretch(1)
        
        self.setLayout(layout)
        
        # Signal relays
        
        self._parameters.addXParameters.connect(self.addXParameters)
        self._parameters.xParameterRemoved.connect(self.xParameterRemoved)
        self._parameters.addYParameters.connect(self.addYParameters)
        self._parameters.yParameterRemoved.connect(self.yParameterRemoved)
        
        self._commit.clicked.connect(self.commit)
        
    #  Implementing attributes:

    def name(self):
        return self._name.text()
    def setName(self, name):
        self._name.setText(name)

    def xparameters(self):
        return self._parameters.xparameters()
    def setXparameters(self, param_list):
        self._parameters.setXparameters(param_list)
        
    def addXparameter(self, name):
        self._parameters.appendXparam(name)

    def yparameters(self):
        return self._parameters.yparameters()
    def setYparameters(self,param_list):
        self._parameters.setYparameters(param_list)
    def addYparameter(self, name):
        self._parameters.appendYparam(name)

    def selectedParameter(self):
        return self._parameters.selectedParameter()
    def setSelectedParameter(self, name):
        self._parameters.setSelectedParameter(name)
    def array(self):
        return self._parameters.array()
    def setArray(self, state):
        self._parameters.setArray(state)

    def axis_from_parameters(self):
        if self._from_parameters.checkState() == Qt.Checked:
            return True
        else:
            return False
    def setAxis_from_parameters(self, state):
        if state:
            self._from_parameters.setCheckState(Qt.Checked)
        else:
            self._from_parameters.setCheckState(Qt.Unchecked)

    def xlow(self):
        return self._xaxis.low()
    def setXlow(self, value):
        self._xaxis.setLow(value)
    def xhigh(self):
        return self._xaxis.high()
    def setXhigh(self, value):
        self._xaxis.setHigh(value)
    def xbins(self):
        return self._xaxis.bins()
    def setXbins(self,  value):
        self._xaxis.setBins(value)

    def ylow(self):
        return self._yaxis.low()
    def setYlow(self, value):
        self._yaxis.setLow(value)
    def yhigh(self):
        return self._yaxis.high()
    def setYhigh(self, value):
        self._yaxis.setHigh(value)
    def ybins(self):
        return self._yaxis.bins()
    def setYbins(self, value):
        self._yaxis.setBins(value)



# test code

def axis_test():
    app = QApplication([])
    c   = QMainWindow()
    w   = _Axis('test')
    c.setCentralWidget(w)

    c.show()
    app.exec()

def test_editor():
    app = QApplication([])
    c   = QMainWindow()
    w   = GammaDeluxeEditor(c)
    c.setCentralWidget(w)

    c.show()
    app.exec()

if __name__ == '__main__':
    test_editor()
