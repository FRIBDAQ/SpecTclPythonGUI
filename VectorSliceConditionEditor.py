'''
Provides an editor view for a slice condition. Slice conditions require
*  A name for the condition
*  A a vector parameter.
*  A low limit for the slice.
*  A high limit for the slice

Vectors evaulate true if either all or at least one of the
items in the vector is in the slice (vs* or vs+).  This editor
is a view for both of the vector slice gates types.
'''

from PyQt5.QtWidgets import (
    QLabel, QLineEdit, QWidget, QPushButton,
    QVBoxLayout, QHBoxLayout, QCheckBox, QComboBox
)
from PyQt5.QtGui import QDoubleValidator
from PyQt5.QtCore import  pyqtSignal
from PyQt5.Qt import *
from spectrumeditor import error
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
            vector - parameter selected by the user.
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
        self._vector = QComboBox(self)
        line2.addWidget(self._vector)
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
        
    def vector(self):
        return self._vector.currentText()
    def setVector(self, name):
        self._vector.setCurrentText(name)
        
    # Public methods:
    
    def clear(self):
        ''' Clear the view for next use: '''
        self.setName('')
        self.setLow(default_low)
        self.setHigh(default_high)
        
    
    def load_vectors(self, vectors) :
        self._vector.clear()
        self._vector.addItems(vectors)
            
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
        
        if self.vector() == '' or self.vector().isspace():
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




## Test code

if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication, QMainWindow
    from rustogramer_client import rustogramer
    c = rustogramer({'host' : 'localhost', 'port' : 8000})
    
    def test_create():
        name = editor.name()
        vector = editor.vector()
        low = editor.low()
        high = editor.high()
        
        print(f"Make vector gate {name} checking {vector}")
        print (f"slice [{low}, {high})")
    
    app = QApplication([])
    win = QMainWindow()
    
    editor = EditorView()
    names = [v['name'] for v in c.vector_list()['detail']]
    editor.load_vectors(names)
    editor.commit.connect(test_create)
    
    win.setCentralWidget(editor)
    win.show()
    app.exec()