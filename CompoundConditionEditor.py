'''
    Provides a module that create a compound condition.  Compound conditions are
    + and * conditions.  They consist of a set of dependent conditions so the
    chooser has the editable list to hold the conditiosn that have been added to
    the compound and a chooser to allow the user to select a condition to add to the
    list. Note that an array button makes no sense.  While ordering makes no sense, 
    the buttons are there for the user's convenience.
'''

from PyQt5.QtWidgets import (
    QPushButton, QLineEdit, QComboBox, QLabel, QWidget,
    QVBoxLayout, QHBoxLayout,
    QApplication, QMainWindow
)
from PyQt5.QtCore import pyqtSignal

from editablelist import EditableList
from gatelist import ConditionChooser, common_condition_model


class EditorView(QWidget):
    '''
    Signals: 
        commit - user wants to make a condition from all of this.
    Attributes:
        name  - Name of the condition.
        dependencies - names of the dependent conditions.
    '''
    commit = pyqtSignal()
    
    def __init__(self, *args):
        super().__init__(*args)
        
        layout = QVBoxLayout()
        
        # Top row is the name and name entry:
        
        top = QHBoxLayout()
        top.addWidget(QLabel('Name: ', self))
        self._name = QLineEdit(self)
        top.addWidget(self._name)
        layout.addLayout(top)
        
        # Middle row is the ConditionChooser and editable list:
        
        mid = QHBoxLayout()
        self._chooser = ConditionChooser(self)
        mid.addWidget(self._chooser)
        self._dependencies = EditableList('Dependent conditions', self)
        mid.addWidget(self._dependencies)
        mid.addStretch(1)
        layout.addLayout(mid)
        
        # On the bottom is just the commit button:
        
        commit = QHBoxLayout()
        self._commit = QPushButton('Create/Replace', self)
        commit.addWidget(self._commit)
        commit.addStretch(1)
        layout.addLayout(commit)
        layout.addStretch(1)
        
        
        self.setLayout(layout)
        
        #  Export the commit signal:
        
        self._commit.clicked.connect(self.commit)
        
        # Internal signal routing:
        
        self._dependencies.add.connect(self._addGate)
    
    def _addGate(self):
        newgate = self._chooser.currentText()
        self._dependencies.appendItem(newgate)
    
    # Attributes:
    
    def name(self):
        return self._name.text()
    def setName(self, name):
        self._name.setText(name)
    
    def dependencies(self):
        return self._dependencies.list()
    def setDependencies(self, cond_list):
        self._dependencies.clear()
        for name in cond_list:
            self._dependencies.appendItem(name)
    
    #   Public methods:
    
    def clear(self):
        self.setName('')
        self.setDependencies(list())
        self._chooser.setCurrentIndex(0)

#------------------------------ Test code -------------------------------
def commit():
    print("Make gate:")
    print("  name:", wid.name())
    print("  dependenciues:", ', '.join(wid.dependencies()))
    
if __name__ == '__main__':
    from rustogramer_client import rustogramer as cl
    client = cl({'host':'localhost', 'port': 8000})
    
    common_condition_model.load(client)
    
    app = QApplication([])
    win = QMainWindow()
    
    wid = EditorView()
    wid.commit.connect(commit)
    
    win.setCentralWidget(wid)
    win.show()
    app.exec()