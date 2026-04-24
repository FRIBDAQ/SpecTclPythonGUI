'''
    This module implements a megawidget that creates/edits
    vector 1d spectra (type 1v).  At this point in time,
    it's a mostly copy of editor1d.py with the difference that the
    'parameters' selector is replaced with a selector for
    the vectors.  
'''

from axisdef import AxisInput

from PyQt5.QtWidgets import (
    QLineEdit, QWidget, QHBoxLayout, QVBoxLayout, QLabel,
    QPushButton, QComboBox, 
    
)
from PyQt5.QtCore import pyqtSignal, Qt
from rustogramer_client import rustogramer as cl
from editor1d import oneDEditor
class vector1Deditor(QWidget) :
    nameChanged = pyqtSignal(str)
    vectorSelected = pyqtSignal(str)
    axisModified = pyqtSignal(dict)
    commit = pyqtSignal()
    
    def __init__(self, *args):
        super().__init__(*args)

        layout = QVBoxLayout()
        
        # The top horizontal line names the spectrum and provides
        # an option to make an array:

        line1 = QHBoxLayout()

        line1.addWidget(QLabel('Name:', self))
        self.sname  = QLineEdit(self)
        line1.addWidget(self.sname)
        layout.addLayout(line1)
        
        # Next the parameter chooser and axis on line 2:
        
        line2 = QHBoxLayout()
        pchooser = QVBoxLayout()
        
        pchooser.addWidget(QLabel('Vector', self))
        self.vchooser = QComboBox(self)
        pchooser.addWidget(self.vchooser)
        self.chosen_vector = QLabel('')
        pchooser.addWidget(self.chosen_vector)
        line2.addLayout(pchooser)
        
        
       

        axisl = QLabel('X Axis:', self)
        self.axis = AxisInput(self)
        axis_layout = QVBoxLayout()
        axis_layout.addWidget(axisl)
        axis_layout.addWidget(self.axis)
        line2.addLayout(axis_layout)
        line2.addStretch(1)            # Left justified.
        layout.addLayout(line2)

        line3 = QHBoxLayout()
        c = QPushButton('Create/Replace')
        line3.addWidget(c)
        line3.addStretch(1)
        
        layout.addLayout(line3)
        layout.addStretch(1)
        
        self.setLayout(layout)


        # Connect internal signals to slots:

        self.sname.textChanged.connect(self.nameTextChanged)
        self.vchooser.currentTextChanged.connect(self.vectorChanged)
        self.axis.lowChanged.connect(self.axisChanged)
        self.axis.highChanged.connect(self.axisChanged)
        self.axis.binsChanged.connect(self.axisChanged)
        c.pressed.connect(self.make_spectrum)

    # Attribute getter/setter methods.

    def name(self):
        return self.sname.text()
    def setName(self, text):
        self.sname.setText(text)
    def vector(self):
        return self.chosen_vector.text()
    def setVector(self, p):
        # Caller is responsible for ensuring this is is a legal name
        self.chosen_vector.setText(p)

    def low(self):
        return self.axis.low()
    def setLow(self, value):
        self.axis.setLow(value)

    def high(self):
        return self.axis.high()
    def setHigh(self, value):
        self.axis.setHigh(value)
    
    def bins(self):
        return self.axis.bins()
    def setBins(self, value):
        self.axis.setBins(value)

    # Define slot methods:

    def nameTextChanged(self, new_name):
        self.nameChanged.emit(new_name)
    

    def vectorChanged(self, vector):
        # We turn the new_path, a list of path
        # elements into a full parameter name:

       
        self.chosen_vector.setText(vector)
        self.vectorSelected.emit(vector)

    def axisChanged(self, value):
        # Marshall the dict:

        axis_def = {
            'low'  : self.axis.low(),
            'hi' : self.axis.high(),
            'bins' : self.axis.bins()
        }
        self.axisModified.emit(axis_def)
    
    def make_spectrum(self):
        self.commit.emit()

    def load_vectors(self, vlist):
        self.vchooser.clear()
        self.vchooser.addItems(vlist)
        

if __name__ == "__main__": 
    from PyQt5.QtWidgets import QApplication, QMainWindow
    
    def loadVectorList(client, widget):
        vectors = client.vector_list()['detail']
        names =[]
        for v in vectors:
            names.append(v['name'])
        widget.load_vectors(names)
    
    c = cl({'host' : 'localhost', 'port': 8000})
    
    app = QApplication([])
    win = QMainWindow()
    
    main = vector1Deditor()
    loadVectorList(c, main)
    win.setCentralWidget(main)
    
    win.show()
    app.exec()
    
    
    