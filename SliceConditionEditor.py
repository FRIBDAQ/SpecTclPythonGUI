'''
Provides an editor view for a slice condition. Slice conditions require
*  A name for the condition
*  A a parameter.
*  A low limit for the slice.
*  A high limit for the slice

Slices evaluate true for events when the parameter is present and within the limits
of the slice.

'''

from PyQt5.QtWidgets import (
    QLabel, QLineEdit, QWidget, QPushButton,
    QVBoxLayout, QHBoxLayout, QCheckBox
)
from PyQt5.QtGui import QDoubleValidator
from PyQt5.QtCore import  pyqtSignal
from PyQt5.Qt import *
from spectrumeditor import error
from ParameterChooser import LabeledParameterChooser
from editablelist import EditableList


default_low =  0.0
default_high = 4096.0

class EditorView(QWidget):
    '''
        Signals:
            commit - the Create/Replace button was clicked.
              Note there's some pre-validation that's done before 
              this is emitted:
                - Name is not empty as long as we're validating.
                - A parameter has been selected.
                - Low and high are not empty.
                - Low < High.
               If the Create/Replace button is clicked and any of these validation
               fail a message box is popped up and commit is not emitted.
        Slots:
            validate - called directly by the clicked signal of the Create/Replace button.
              performs the validations described above and conditionally emits commit
        Attributes:
            name - name of the gate.
            low, high - limits selected by the user.
            parameter - parameter selected by the user.
    '''
    commit = pyqtSignal()
    def __init__(self, *args):
        super().__init__(*args)
        
        layout = QVBoxLayout()
        
        # Top  is the Name:
        
        top = QHBoxLayout()
        top.addWidget(QLabel('Name', self))
        self._name = QLineEdit(self)
        top.addWidget(self._name)
        
        layout.addLayout(top)
        
        # Second line is Parameter:   labeled paramter chooser
        
        line2 = QHBoxLayout()
        line2.addWidget(QLabel("Parameter: "))
        self._parameter = LabeledParameterChooser(self)
        line2.addWidget(self._parameter)
        line2.addStretch(1)
        
        layout.addLayout(line2)
        
        
        # Next is:
        #   Low: []   High: []  
        #  With QDoubleValidators on the line edits.
        
        line3 = QHBoxLayout()
        line3.addWidget(QLabel('Low', self))
        self._low = QLineEdit('0.0', self)
        self._low.setValidator(QDoubleValidator())
        line3.addWidget(self._low)
        line3.addWidget(QLabel('High', self))
        self._high = QLineEdit('4096.0', self)
        self._high.setValidator(QDoubleValidator())
        line3.addWidget(self._high)
        line3.addStretch(1)
        layout.addLayout(line3)
        
        
        # Bottom is our button.
        
        commit = QHBoxLayout()
        self._commit = QPushButton('Create/Replace', self)
        commit.addWidget(self._commit)
        commit.addStretch(1)
        layout.addLayout(commit)
        layout.addStretch(1)
        
        self.setLayout(layout)
        
        # The commit button goes through validation:
        
        self._commit.clicked.connect(self.validate)
        
    # Attribute implementations:
    
    def name(self):
        return self._name.text()
    def setName(self, name):
        self._name.setText(name)
        
    def low(self):
        ''' can return None if the text is empty otherwise it's a float'''
        t = self._low.text()
        if t == '' or t.isspace():
            return None
        return float(t)
    def setLow(self, value):
        self._low.setText(f'{value}')
    
    def high(self):
        t = self._high.text()
        if t == '' or t.isspace():
            return None
        return float(t)
    def setHigh(self, value):
        self._high.setText(f'{value}')
        
    def parameter(self):
        return self._parameter.parameter()
    def setParameter(self, name):
        self._parameter.setParameter(name)
        
    # Public methods:
    
    def clear(self):
        ''' Clear the view for next use: '''
        self.setName('')
        self.setLow(default_low)
        self.setHigh(default_high)
        self.setParameter('')
        
    # Slots:
    
    def validate(self):
        '''
          Slot to validate the state of input and either pop a dialog if the state is not
          valid or emit commit if it is.
        '''
        # Must have a name:
        if self.name() == '' or self.name().isspace():
            error(f'A condition name must be specified')
            return
        # Must have a parameter:
        
        if self.parameter() == '' or self.parameter().isspace():
            error(f'A parameter must be selected')
            return
        # Must have both low and high
        l = self.low()
        h = self.high()
        
        if l is None or h is None:
            error(f'Both low and high limits must be specified')
            return
        
        # Low must be less than high:
        l = self.low()
        h = self.high()
        if l >= h:
            error(f'Low value ({l} must be strictly less than high value {h})')
        
        self.commit.emit()             


class GammaEditorView(QWidget):
    '''
    Provides the editor view for a gamma slice.  Gamma slices
    are like slices but allow for an arbitrary number of parameters
    to be accepted on the slice.
    Signals:
        appendarray - Help me by appending an array of params that match the
                    wild card.
       commmit - The condition is filled in and can be added.
    Slots:
       validate - Validates that the condition is fully filled.
    Attributes:
        name       - name of the condition.
        parameters - parameters selected.
        low        - low limit of the slice.
        high       - high limit of the slice.
        
        
    '''
    commit = pyqtSignal()
    appendarray = pyqtSignal(str)
    def __init__(self, *args):
        super().__init__(*args)
        layout = QVBoxLayout()
        
        # Top line contains the  name.
        line1 = QHBoxLayout()
        line1.addWidget(QLabel('Name: ', self))
        self._name= QLineEdit(self)
        line1.addWidget(self._name)
        
        layout.addLayout(line1)
        
        # Next line contains parameter chooser array and
        # editable list.
        
        line2 = QHBoxLayout()
        param = QVBoxLayout()
        self._parameter = LabeledParameterChooser(self)
        param.addWidget(self._parameter)
        self._array = QCheckBox('Array', self)
        param.addWidget(self._array)
        param.addStretch(1)
        line2.addLayout(param)
        self._parameters = EditableList('Parameters', self)
        line2.addWidget(self._parameters)
        line2.addStretch(1)
        
        layout.addLayout(line2)
        
        # next line contains low/high entries.
        
        line3 = QHBoxLayout()
        
        line3.addWidget(QLabel('Low:', self))
        self._low = QLineEdit('0.0', self)
        self._low.setValidator(QDoubleValidator())
        line3.addWidget(self._low)
        
        line3.addWidget(QLabel("High:", self))
        self._high = QLineEdit('4096.0', self)
        self._high.setValidator(QDoubleValidator())
        line3.addWidget(self._high)
        line3.addStretch(1)
        
        layout.addLayout(line3)
        
        # Finally the Create/ReplaceButton.
        
        commit = QHBoxLayout()
        self._accept = QPushButton('Create/Replace',self)
        commit.addWidget(self._accept)
        commit.addStretch(1)
        layout.addLayout(commit)
        
        layout.addStretch(1)
        
        self.setLayout(layout)
        
        # internal signal handling:
        
        self._accept.clicked.connect(self.validate)
        self._parameters.add.connect(self._add)
        
    
    # Implement attributes:
    
    def name(self):
        return self._name.text()
    def setName(self, txt):
        self._name.setText(txt)
    
    def parameters(self):
        return self._parameters.list()
    def setParameters(self, ps):
        self._parameters.setList(ps)
    def appendParameter(self, name):
        self._parameters.appendItem(name) 
        
    def low(self):
        txt = self._low.text()
        try:
            return float(txt)
        except:
            return None
    def setLow(self, value):
        self._low.setText(f'{value}')
    
    def high(self):
        txt = self._high.text()
        try:
            return float(txt)
        except:
            return None
    def setHigh(self, value):
        self._high.setText(f'{value}')
    
    # Public methods:
    
    def clear(self):
        self.setName('')
        self.setParameters(list())
        self.setLow(default_low)
        self.setHigh(default_high)
    
    # Slots:
    
    def validate(self):
        ''' Validates the contents and, if OK, emits commit
        '''
        
        n = self.name()
        if n == '' or n.isspace():
            error("A condition name is required")
            return
        ps = self.parameters()
        if len(ps) < 2:
            error("For a gamma gate there should be at least two parameters")
            return
        if self.low() is None or self.high() is None:
            error("Both low and high must be valid floating point valueas")
            return
        
        self.commit.emit()
    
    def _add(self):
        name = self._parameter.parameter()
        if self._arrayChecked():
            name_list = name.split('.')
            
            name_list = name_list[:-1]
            name_pattern = '.'.join(name_list) + '.*'
            self.appendarray.emit(name_pattern)
        else:
            self._parameters.appendItem(name) 
        
    def _arrayChecked(self):
        if self._array.checkState() == Qt.Checked:
            return True
        else:
            return False
#-------------------------- test code: ---------------------------------------


def create() :
    print("Create/replace")
    print("  name      : ", widget.name())
    print("  parameter : ", widget.parameter())
    print("  low/high  : ", widget.low(), widget.high())

def gcreate():
    print("Create:", gwidget.name())
    print("  parameters:", gwidget.parameters())
    print("  limits:" , gwidget.low(), gwidget.high())

if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication, QMainWindow
    from ParameterChooser import update_model
    from rustogramer_client import rustogramer as rc
    
    update_model(rc({'host': 'localhost', 'port': 8000}))   # Load parameter model.
    
    app = QApplication([])
    win = QMainWindow()
    
    w = QWidget()
    layout = QHBoxLayout()
    
    widget = EditorView()
    widget.commit.connect(create)
    layout.addWidget(widget)
    
    gwidget = GammaEditorView()
    gwidget.commit.connect(gcreate)
    layout.addWidget(gwidget)
    
    w.setLayout(layout)
    win.setCentralWidget(w)
    
    win.show()
    app.exec()