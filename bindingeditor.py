
from PyQt5.QtWidgets import (
    QWidget, QPushButton, QLineEdit, QLabel,
    QHBoxLayout, QVBoxLayout,
    QApplication, QMainWindow
)
from PyQt5.QtCore import pyqtSignal
from PyQt5.Qt import *


from editablelist import ListToListEditor, EditableList


class BindingEditor(QWidget):
    '''
        Provides a widget that can edit bindings.  At the heart, the widget is a ListToListEditor
        The  left list can be initialized to items that are not in the binding being edited while the
        right list will hold the current bindings (note that this will be empty when creating a new binding).
        
        At the top of the widget are text line editorsfor the name of the binding (r/w attribute)
        and description of the binding (r/w attribute).
        
        At the bottom are two buttons:
        
        - Ok - signals ok - the slot that catches this should treat the signal as accepting the current widget 
        state for a new or replaced binding set.
        - Cancel - signals cancel - The slot that catches this should treat the signal as a rejrection of the
        contents of the widget.
        
        It is normal (but not required) for this widget to be a dialog.
        
        
        Attributes:
        - name   - Set/get the name field.
        - description - set/get the description field.
        - source - Read/Write attribute that sets/gets the list of text items in the left list box.
        - bindings - R/W attributes that sets/gets the list of atext items in the right list box.
        - editor  - Readonly - returns the editor widget.
        
        Signals:
        - ok - the 'Ok' button was clicked (no parameters).
        - cancel - The 'Cancel' button was clicked (no parameters).
        
        As you can see it is up to the application to manage the widget so that it's available to the slots.
        Normally this is done by instantiating the widget within another object which maintains the widget
        in its internal data.
    '''

    ok = pyqtSignal()
    cancel = pyqtSignal()
    
    def __init__(self) :
        super().__init__()
        
        layout = QVBoxLayout()     # The elements are created inside Hboxes and stacked vertically:
        
        # Top has labels and editors for name/description.
        top  = QHBoxLayout()
        top.addWidget(QLabel("Name: ", self))
        self._name = QLineEdit(self)
        top.addWidget(self._name)
        top.addWidget(QLabel("Description", self))
        self._description = QLineEdit(self)
        top.addWidget(self._description)
        
        layout.addLayout(top)
        
        # Middle just has the ListToListEditor:
        
        self._editor = ListToListEditor(self)
        layout.addWidget(self._editor)
        
        # Bottom has the action buttons:
        
        bottom = QHBoxLayout()
        self._ok = QPushButton("Ok", self)
        bottom.addWidget(self._ok)
        self._cancel = QPushButton("Cancel", self)
        bottom.addWidget(self._cancel)
        
        layout.addLayout(bottom)
        
        self.setLayout(layout)
        
        #  Now relay the clicked signals from the buttons appropriately:
        
        self._ok.clicked.connect(self.ok)
        self._cancel.clicked.connect(self.cancel)
        
        
if __name__ == "__main__":
    app = QApplication([])
    main = QMainWindow()
    editor = BindingEditor()
    main.setCentralWidget(editor)
    
    main.show()
    app.exec()