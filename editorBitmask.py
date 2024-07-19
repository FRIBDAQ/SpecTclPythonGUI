'''  This module provides an editor for bitmask spectra.
In this kind of spectrum, the single parameter is integerized and
treated as a bit vector.  Channels are incremented for each set bit in
the integerized parameter. 

Signals:
   commit - the Create/Replace button was clicked.

Attributes:
   name - proposed name of the spectrum.
   parameter - the parameter the spectrum is on.
   bits - Number bits to provide an axis for e.g. 32 means an axis:
        {0, 32, 32}
'''

from PyQt5.QtWidgets import (
    QWidget, QComboBox, QLabel,  QLineEdit, QPushButton,
    QVBoxLayout, QHBoxLayout,
    QApplication, QMainWindow
)
from PyQt5.QtGui import  QStandardItemModel, QStandardItem
from PyQt5.QtCore import Qt, pyqtSignal
from ParameterChooser import (
    LabeledParameterChooser as Parameter,
     _parameter_model as parameters
)

class BitmaskEditor(QWidget):
    commit = pyqtSignal()
    def __init__(self, *args):
        super().__init__(*args)
        
        layout = QVBoxLayout()
        name_l = QHBoxLayout()
        name_l.addWidget(QLabel("Name", self))
        self._name = QLineEdit(self);
        name_l.addWidget(self._name)
        layout.addLayout(name_l)

        param_l = QVBoxLayout()
        param_l.addWidget(QLabel('Parameter:', self))
        self._param = Parameter(self)
        param_l.addWidget(self._param)
        
        layout.addLayout(param_l)

        bits_l = QHBoxLayout()
        bits_l.addWidget(QLabel('Bits:', self))
        self._bits = QComboBox(self)
        self._bits.setEditable(False)
        for i in range(1,33):
            self._bits.addItem(f'{i}')
        bits_l.addWidget(self._bits)
        bits_l.addStretch(1)
        
        layout.addLayout(bits_l)

        commit = QHBoxLayout()
        self._commit = QPushButton('Create/Replace', self)
        commit.addWidget(self._commit)
        commit.addStretch(1)
        
        layout.addLayout(commit)
        layout.addStretch(1)

        self.setLayout(layout)

        # Connect the signal relay on the commmit button:

        self._commit.clicked.connect(self.commit)
    
    #  Attribute implementations.

    def name(self):
        return self._name.text()
    def setName(self, new_name):
        self._name.setText(new_name)

    def parameter(self):
        return self._param.parameter()
    def setParameter(self, new_param):
        self._param.setParameter(new_param)

    def bits(self):
        return int(self._bits.currentText())
    def setBits(self, num_bits):
        text = str(num_bits)
        index = self._bits.findText(text)
        if  index == -1:
            raise KeyError(text + ' is not a valid bit count')
        else:
            self._bits.setCurrentIndex(index)

#------------------------- Test code ----------------------

def _commit():
    print('Name: ', w.name())
    w.setName('')
    print('Parameter: ', w.parameter()) 
    w.setParameter('')
    print('bits ', w.bits())
    w.setBits(32)  

def _load_parameters():
    for i in range(16):
        name = f'parameter.{i:02d}'
        parameters.appendRow(QStandardItem(name))


if __name__ == "__main__":
    app = QApplication([])
    c   = QMainWindow()
    _load_parameters()

    w  = BitmaskEditor()
    w.commit.connect(_commit)



    c.setCentralWidget(w)



    c.show()
    app.exec()

