'''  This module provides a summary spectrum editor.  It needs to be paired
     with a controller that can handle its signals and knows how to create
     a summary spectrum.
     A summary spectrum needs the user to be able to select a  list of
     spectra for the y axis and a yaxis definition in addition to the
     spectrum name.  

     To make things simpler we support pushing an 'array'  of parameters
     into the list selection box.  The axis definitions can be filled in from
     metadata associated with the parameters, if there is any or
     manually.

     Here's a sketch of the editor:

     +------------------------------------------+
     | Name: [              ]                   |
     | {param selector}  [] array  +-----------+|
     |                    >        | parameter ||
     |                    <        |           ||
     | [] axis from parameter(s)   | list box  ||
     | {axis selector}  Y-axis     |           ||
     |                             +-----------+|
     |                               [^] [V]    |
     |                              [Clear]     |
     |          [ Create/replace ]              |
     +------------------------------------------+

     The idea is that users choose parameters and click the right arrow button
     to add those to the list of parameters in the parameter list box.
     If the array checkbutton is checked this should add a list of 
     parameters;  parameter names are period separated pathed items and
     an array substitues the last element of the path with * adding matching
     parameters.  Note that arrays of parameters are added alphabetically sorted.

     A certain amount of parameter list editing is supported:
     *  The clear button removes all parameters from the listbox.
     *  The < button removes all of the parameters from the list box.
     *  The ^ button moves the selected parameters up one slot in the list box
        if they are not already at the top.
     *  Similarly the V button moves the selected parameters down one slot in

        the list box if they are not already at the bottom.
     If the [] axis from paramerter(s) checkbutton is set, then as each parameter
     is added to the selected parameter list, if it has metadata, that metadata
     is used to populate the axis definition.

     Attributes:
        *  name       - Current spectrum name.
        *  selected_parameter - the parameter selected in the parameter selector
        *  axis_parameters - Ordered list of parameters in the list box.
        *  low       - Y axis low limit.
        *  high      - Y axis high limit.
        *  bins      - Y axis bins.
        *  array     - state of the array check button.
        *  axis_from_parameters - State of the axis from parameters checkbutton.

    Signals:
        commit - The create/replace button was clicked. Requires
        add    - The right arrow was clicked, the signal handler will need to
         access the 'selected_parameter', 'array' and 'axis_from_parameters' 
         attributes to properly function.
        remove = An item was removed from the selected parameters.
       
        The remove signal is provided if, in the future, we decide we want to
        prevent adding duplicate parameters by removing them from the 
        selection list.

        Note that editing, other than insertion, is handled autonomously via
        internal signals.

'''

from PyQt5.QtWidgets import (
    QLabel, QPushButton, QCheckBox, QLineEdit,
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout,
    QWidget 
)
from PyQt5.Qt import *
from PyQt5.QtCore import pyqtSignal
from ParameterChooser import Chooser as pChooser
from axisdef import AxisInput
from editablelist import EditableList
from ParameterListselector import SingleList
class SummaryEditor(QWidget):
    commit = pyqtSignal()
    add    = pyqtSignal()
    remove = pyqtSignal(str)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args)
        
        main_layout = QVBoxLayout()

        # Top row has title and QLineEditor for name:

        row1 = QHBoxLayout()
        row1.addWidget(QLabel('Name:', self))
        self._name = QLineEdit(self)
        row1.addWidget(self._name)
        row1.addStretch(1)
        
        main_layout.addLayout(row1)

        # Left side of next row is parameter chooser and 
        # array button.
        
        
        self._list = SingleList(self)
        main_layout.addWidget(self._list)


        # The axis specification with a from parameters checkbutton.

        axis = QHBoxLayout()
        self._axis = AxisInput(self)
        axis.addWidget(self._axis)
        self._from_params = QCheckBox('From Parameters', self)
        axis.addWidget(self._from_params)
        axis.addStretch(1)
        main_layout.addLayout(axis)

        # Finally the Create/Replace button in 10, all centered

        button = QHBoxLayout()
        self._commit = QPushButton('Create/Replace', self)
        button.addWidget(self._commit)
        button.addStretch(1)
        main_layout.addLayout(button)
        main_layout.addStretch(1)

        self.setLayout(main_layout)

        # Signal relays:

        self._list.add.connect(self.add)
        self._list.remove.connect(self.remove)
        self._commit.clicked.connect(self.commit)
        

        
        self.main_layout = main_layout
    
    #  Implement the attributes:

    def name(self):
        return self._name.text()
    def setName(self, name):
        self._name.setText(name)

    def selected_parameter(self):
        return self._list.parameter()
    def setSelected_parameter(self, pname):
        self._list.setParameter(pname)
    
    def axis_parameters(self):
        return self._list.selectedParameters()

    def setAxis_parameters(self, itemList):
        self._list.setSelectedParameters(itemList)

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
    
    # slots:

    

def test():
    app = QApplication([])
    c = QMainWindow()
    w = SummaryEditor(c)

    w.setAxis_parameters(['a', 'b', 'c', 'd'])

    c.setCentralWidget(w)
    c.show()
    app.exec()

if __name__ == "__main__":
    test()        
