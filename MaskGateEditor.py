'''
This module provides an editor for mask gates.  The assumption is that the bit masks are only 32 bits wide.
That, I believe is the SpecTcl limitation on the width of a mask.
We have the bits.py module to provide the bitmask.
'''

from PyQt5.QtWidgets import (
    QWidget, QPushButton, QLabel, QLineEdit,
    QHBoxLayout, QVBoxLayout
)
from PyQt5.QtCore import pyqtSignal

from ParameterChooser import LabeledParameterChooser
from bits import BitMask
from spectrumeditor import error

class View(QWidget):
    '''
        The editor view.  
        Signals:
            commit - the gate has been validated and accepted.
        Slots:
            validate - when the Create/Replace button is clicked, this ensures
                the gate is fully filled in before mitting commit.
                If overriding, invoke super().validate() _after_ all additional validations
                you supply are done.,
        Attributes:
            name      - name of the condition.
            parameter - parameter the condition is set on.
            mask      - the bitmask.
        Note:   
            It's up to the controller to decide what sort of condition is being accepted.

    ''' 
    commit = pyqtSignal()
    
    def __init__(self, *args):
        super().__init__(*args)
        
        # Layout the controls:
        
        layout = QVBoxLayout()
        
        # Top row has the condition name:
        
        top = QHBoxLayout()
        top.addWidget(QLabel('Name:', self))
        self._name = QLineEdit(self)
        top.addWidget(self._name)
        
        layout.addLayout(top)
        
        #  Middle row is the parameter chooser:
        
        self._parameter = LabeledParameterChooser(self)
        layout.addWidget(self._parameter)
        
        # Next the bitmask:
        
        self._mask = BitMask(self)
        layout.addWidget(self._mask)
        
        #  Finally the create/replace button:
        
        accept = QHBoxLayout()
        self._accept = QPushButton('Create/Replace')
        accept.addWidget(self._accept)
        accept.addStretch(1)
        
        layout.addLayout(accept)
        
        layout.addStretch(1)
        
        self.setLayout(layout)
        
        # Internal signal handling:  _accept button invokes validate:
        
        self._accept.clicked.connect(self.validate)
    
    # Implement attributes:
    
    def name(self):
        return self._name.text()
    def setName(self, new_name):
        self._name.setText(new_name)
        
    def parameter(self):
        return self._parameter.parameter()
    def setParameter(self, new_param):
        self._parameter.setParameter(new_param)
    
    def mask(self):
        return self._mask.mask()
    def setMask(self, new_mask):
        self._mask.setMask(new_mask)
    
    #   Public methods:
    
    def clear(self):
        self.setName('')
        self.setParameter('')
        self.setMask(0)    
        
    # Slots:
    
    def validate(self):
        ''' We perform the following validations.  If any fail, then commit is not emitted
            if all pass, then we emit commit:
            
            name must be non-empty
            A parameter must have been selected.
        '''
        n = self.name()
        if n == '' or n.isspace():
            error('A condition name is required')
            return
        p = self.parameter()
        if p is None or p == '' or p.isspace():
            error('A parameter must be selectded')
            return
        
        self.commit.emit()
    
        
#--------------------------- Test code: ---------------------------------------
if __name__ == '__main__':
    
    
    from PyQt5.QtWidgets import QApplication, QMainWindow
    from ParameterChooser import update_model
    from rustogramer_client import rustogramer as rc
    
    def newgate():
        print("Making condition:")
        print('  name', wid.name())
        print('  par ', wid.parameter())
        print('  mask', hex(wid.mask()))
    
    client = rc({'host': 'localhost', 'port': 8000})
    update_model(client)   
    
    app = QApplication([])
    win = QMainWindow()
    
    wid = View()
    wid.commit.connect(newgate)
    
    win.setCentralWidget(wid)
    win.show()
    app.exec()