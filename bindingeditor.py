
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
        
    # Attribute implementations:
    
    
    # name: 
    def name(self):
        ''' Return the contents of the name field: '''
        return self._name.text()
    def setName(self, name):
        ''' Sets the contents of the name field '''  
        self._name.setText(name)
        
    # description:
    
    def description(self):
        ''' Return the contents of the description field '''
        return self._description.text()
    def setDescription(self, description):
        ''' Set the contents of the description field '''
        self._description.setText(description)
        
    #  source
    
    def source(self): 
        ''' Return the current contents of the source listbox '''
        source = self._editor.sourcebox()
        result = list() 
        num = source.count()
        for row  in range(num):
            result.append(source.item(row).text())
        return result        
    def setSource(self, items):
        ''' Sets the contents of the source box:'''
        source = self._editor
        source.clearSource()
        source.appendSource(items)

    # Bindings:
    
    def bindings(self):
        ''' Return the names in the bindings: '''
        return self._editor.list()
    def setBindings(self, items):
        ''' Set the contents of the bindings box '''
        dest = self._editor.selectedbox()
        box = dest.listbox()
        
        # Clear the listbox:
        
        while box.count() > 0:
            box.takeItem(0)
        
        # Set new items:
        
        box.addItems(items)
    
if __name__ == "__main__":
    

    def Ok():
        print(editor.name())
        print(editor.description())
        print(editor.bindings())
        print("Leaving  ", editor.source())
    
    def Cancel():
        print('Cancelled')
          
    app = QApplication([])
    main = QMainWindow()
    editor = BindingEditor()
    editor.setSource([
        'one', 'two', 'three', 'four'
    ])
    editor.setBindings([
        'bound', 'hand', 'and', 'foot'
    ])
    editor.setName("Aname")
    editor.setDescription("Some inspirational list of stuff.")
    
    editor.ok.connect(Ok)
    editor.cancel.connect(Cancel)
    main.setCentralWidget(editor)
    
    main.show()
    app.exec()
    
    