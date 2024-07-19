
''' A common need in spectrum editors is to select a list of parameters.
    This module provides re-usable widgets to support that.  The idea as that
    we have a parameter selector and an array checkbutton.  This is then
    paired with either one or two editable lists which can be stocked by
    interacting with signals from these widgets by the client.
    The two widgets we provide are:
    
    SingleList - Which selects a single list of parameters and
    DoubleList - Which selects a pair of lists (e.g. x and y parameters for Twod sum or Gamma deluxe).
    
'''


from PyQt5.QtWidgets import (
    QLabel, QVBoxLayout, QHBoxLayout, QWidget, QCheckBox
)
from PyQt5.Qt import *
from PyQt5.QtCore import pyqtSignal
from ParameterChooser import LabeledParameterChooser as pChooser
from editablelist import EditableList

class SingleList(QWidget):
    '''
       Provides a selection into a single list oif parameters.  
       Attributes:
          selectedParameters - The list of parameters currently selected
          parameter          - The parameter in the parameter selection.
          chooserLabel       - label above the parameter chooser (defaults to 'parameter')
          listLabel          = Label on list box, defaults to 'Parameters'
          array              - state of array checkbutton.
        Signals:
           add - Add a parameter to the list.
           remove - A parameter was removed from the list.  This signal
                 is passed the name of the removed parameter.
                 NOTE: Normally it's not necessary to catch this signal as
                 the editable list box handles removal autonomously
        Methods:
            appendItem - Adds a parameter to the list
            insertItem - Inserts an item at a specific row.
            clear      - Clears th parameter list
            
            Note:  These are just delegates to the editable list:
            
    '''
    add = pyqtSignal()
    remove = pyqtSignal(str)
    
    def __init__(self, *args):
        super().__init__(*args)
        layout = QHBoxLayout()
        
        #  At the left is a labeled parameter chooser with a label
        # above it:
        
        left = QVBoxLayout()
        self._chooser_label = QLabel('Parameter', self)
        left.addWidget(self._chooser_label)
        self._parameter_chooser = pChooser(self)
        left.addWidget(self._parameter_chooser)
        
        
        layout.addLayout(left)
        
        # In the middle an array checkbox/
        
        self._array = QCheckBox('array', self)
        layout.addWidget(self._array)
        
        #  At the right is just an editable list box:
        
        self._list = EditableList('Parameters', self)
        layout.addWidget(self._list)
        
        layout.addStretch(1)
        
        # Set our layout
        
        self.setLayout(layout)
        
        # Relay the Editable list signals:
        
        self._list.add.connect(self.add)
        self._list.remove.connect(self.remove)
        
    #  Implement the attributes:
    
    def selectedParameters(self):
        return self._list.list()
    def setSelectedParameters(self, l):
        self._list.setList(l)
        
    def parameter(self):
        return self._parameter_chooser.parameter()
    def setParameter(self, pname):
        self._parameter.setParameter(pname)
        
    def chooserLabel(self):
        return self._chooser_label.text()
    def setChooserLabel(self, t):
        self._chooser_label.setText(t)
        
    def listLabel(self):
        return self._list.label()
    def setListLabel(self, l):
        self._list.setLabel(l)
        
    def array(self):
        return self._array.checkState() == Qt.Checked
    def setArray(self, selected):
        if selected:
            state = Qt.Checked
        else:
            state =Qt.Unvhecked
        self._array.setCheckState(state)
        
    # Public methods:
    
    def appendItem(self, s):
        self._list.appendItem(s)
    def insertItem(self, row, s):
        self._list.insertItem(row, s)
    def clear(self):
        self._list.clear()
        

class DoubleList(QWidget):
    ''' 
    This is a widget suitable for getting two lists of parameters. It consists of a single
    parameter selector and side by side editable lists to hold the parameters.
    
    Signals:
        addXParameters    = pyqtSignal()
        xParameterRemoved = pyqtSignal(str)
        addYParameters    = pyqtSignal()
        yParameterRemoved = pyqtSignal(str)
    Attributes:
        xparameters       - Contents of X parameters list box.
        yparameters       - Contents of Y parameters list box.
        selectedParameter -  currently selected parameter
        array             - State of array checkbutton.
        parameterLabel    - Label on the parameter chooser.
        xLabel            - label on the xparameter list.
        yLabel            - label on the yparameter list.
       
    Methods
        appendXparam - Adds a parameter to the X list
        insertXparam - Inserts an item at a specific row in the X list
        clearX       - Clears the X parameter list
        appendYparam - Adds a parameter to the Y list
        insertYparam - Inserts an item at a specific row in the Y list
        clearY       - Clears the Y parameter list
            
    '''
    addXParameters    = pyqtSignal()
    xParameterRemoved = pyqtSignal(str)
    addYParameters    = pyqtSignal()
    yParameterRemoved = pyqtSignal(str)
    
    def __init__(self, *args):
        super().__init__(*args)
        
        layout = QHBoxLayout()
        
        #At the left is a single parameter chooser to which we add an editable listbox:
        
        self._left = SingleList(self)
        self._left.setListLabel('X parameters')
        layout.addWidget(self._left)
        
        self._right = EditableList('Y Parameters', self)
        layout.addWidget(self._right)
        
        self.setLayout(layout)
        
        # Hook in some signals to relays:
         
        self._left.add.connect(self.addXParameters)
        self._left.remove.connect(self.xParameterRemoved)
        
        self._right.add.connect(self.addYParameters)
        self._right.remove.connect(self.yParameterRemoved)
        
    # Public methods:
    '''
    Methods
        appendXparam - Adds a parameter to the X list
        insertXparam - Inserts an item at a specific row in the X list
        clearX       - Clears the X parameter list
        appendYparam - Adds a parameter to the Y list
        insertYparam - Inserts an item at a specific row in the Y list
        clearY       - Clears the Y parameter list
    '''
    
    def appendXparam(self, name):
        self._left.appendItem(name)
    def insertXParam(self, row, name):
        self._left.insertItem(row, name)
    def clearX(self):
        self._left.clear()
        
    def appendYparam(self, name):
        self._right.appendItem(name)
    def insertYParam(self, row, name):
        self._right.insertItem(row, name)
    def clearY(self):
        self._right.clear()
    
    # Attribute implementations.
    '''
        xparameters       - Contents of X parameters list box.
        yparameters       - Contents of Y parameters list box.
        selectedParameter -  currently selected parameter
        array             - State of array checkbutton.
        parameterLabel    - Label on the parameter chooser.
        xLabel            - label on the xparameter list.
        yLabel            - label on the yparameter list.
    '''
    
    def xparameters(self):
        return self._left.selectedParameters()
    def setXparameters(self, l):
        self._left.setSelectedParameters(l) 
        
    def yparameters(self):
        return self._right.list()
    def setYparameters(self, l):
        self._right.setList(l)       
    
    def selectedParameter(self):
        return self._left.parameter()
    def setSelectedParameter(self, name):
        self._right.setParameter(name)
    
    def array(self):
        return self._left.array()
    def setArray(self, b):
        self._left.setArray(b)
        
    def parameterLabel(self):
        return self._left.chooserLabel()
    def setParameterLabel(self, l):
        self._left.setChooserLabel(l)
        
    def xLabel(self):
        return self._left.listLabel()
    def setXLabel(self, s):
        self._left.setListLabel(s)
        
    def yLabel(self):
        return self._right.label()
    def setYLabel(self, s):
        self._right.setLabel(s)