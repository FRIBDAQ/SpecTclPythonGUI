'''  This module provides a gamma 2d editor.  Really this is just a 
    summary/gamma1d editor with an additional axis input.  However given that
    we are now laying things out with boxes, which decouples the
    layout from the contents, we need to do our own full layout and
    implementation. 
    We use the base class editor's axis input for the y axis and
    our additional one as the Xaxis as we have additional space above
    the axis for more stuff.

'''

from PyQt5.QtWidgets import (
    QLabel, QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QLineEdit,
    QCheckBox, QPushButton, QWidget
)
from PyQt5.Qt import *
from PyQt5.QtCore import pyqtSignal 
from editorSummary import SummaryEditor
from axisdef import AxisInput
from ParameterListselector import SingleList


'''
Provide an editor for gamma summary spectra.  These have a single
list of parameters and two axes:
    Signals:
        commit  - the Create/Replace button was clicked.
        add     - a parameter (or set) of parameters should be added
                  to the list box.
        remove  - A parameter was removed from the list box.
    Attributes:
        name - spectrum  name
        selected_parameter - parameter curreently selected in the parameter chooser.
        axis_parameters - The list of parameters selected by the user for the spectrum.
        array           - The parameter  list chooser array button is checked.
        axis_from_parameters - the axis defintions from parameters button is checkedd.
        xlow,xhigh, xbins - X axis specification.
        ylow,yhigh,ybins  - Y axis specification.
    Methods:
        appendItem - Adds a parameter to the list
        insertItem - Inserts an item at a specific row.
        clear      - Clears th parameter list
        
        these are just delegates to the SingleList widget
'''
class Gamma2DEditor(QWidget):
    commit = pyqtSignal()
    add    = pyqtSignal()
    remove = pyqtSignal(str)
    
    def __init__(self, *args):

        super().__init__(*args)

        # As usual, we have, primariliy a VBox layout with HBox if
        # needed for each row:
        
        layout = QVBoxLayout()
        
        # Row1 is the name and a label for it:
        
        row1 = QHBoxLayout()
        row1.addWidget(QLabel("Name:", self))
        self._name = QLineEdit(self)
        row1.addWidget(self._name)
        layout.addLayout(row1)
        
        # In the middle is the parameter chooser:
        
        self._list = SingleList(self)
        layout.addWidget(self._list)
        
        #  X and Y axis with a checkbutton in the middle for axis from parameters
        
        axes = QHBoxLayout()
        
        x = QVBoxLayout()
        x.addWidget(QLabel("X axis", self))
        self._xaxis = AxisInput(self)
        x.addWidget(self._xaxis)
        axes.addLayout(x)
        
        y = QVBoxLayout()
        y.addWidget(QLabel("Y axis", self))
        self._yaxis = AxisInput(self)
        y.addWidget(self._yaxis)
        axes.addLayout(y)
        
        self._from_params = QCheckBox('From Paramters', self)
        axes.addWidget(self._from_params)
        layout.addLayout(axes)
        
        # Finally the create/replace button - in a row to prevent it
        # from expanding across the entire editor:
        
        commit = QHBoxLayout()
        self._commit = QPushButton('Create/Replace', self)
        commit.addWidget(self._commit)
        commit.addStretch(1)
        layout.addLayout(commit)
        
        layout.addStretch(1)
        self.setLayout(layout)
        
        # Signal relays:
        
        self._list.add.connect(self.add)
        self._list.remove.connect(self.remove)
        self._commit.clicked.connect(self.commit)
    
    # Public methods (delegated to the parameter list selection widget).
    
    def appendItem(self, s):
        self._list.addItem(s)
    def insertItem(self, row, s):
        self._list.insertItem(row, s)
    def clear(self):
        self._list.clear()  
   
    # Implement the attributes
    
    def name(self):
        return self._name.text()
    def setName(self, n):
        self._name.setText(n)
        
    def selected_parameter(self):
        return self._list.parameter()
    def setSelected_parameter(self, pname):
        self._list.setParameter(pname)
    
    def axis_parameters(self):
        return self._list.selectedParameters()

    def setAxis_parameters(self, itemList):
        self._list.setSelectedParameters(itemList)
        
    def array(self):
        return self._list.array()
    def setArray(self, onoff):
        self._list.setArrray(onoff)
        
    def axis_from_parameters(self):
        if self._from_params.checkState() == Qt.Checked:
            return True
        else:
            return False
    def setAxis_from_prameters(self, onoff):
        if onoff:
            self._from_params.setCheckState(Qt.Checked)
        else:
            self._from_params.setCheckState(Qt.Unchecked)    
     
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
    def setXbins(self, value):
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
        
    # For compatibility:
    
    def low(self):
        return self.xlow()
    def high(self):
        return self.xhigh()
    def bins(self):
        return self.xbins()

    

if __name__ == "__main__":
    app = QApplication([])
    c   = QMainWindow()
    w   = Gamma2DEditor()
    c.setCentralWidget(w)

    c.show()
    app.exec()

    

