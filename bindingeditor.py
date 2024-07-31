
from PyQt5.QtWidgets import (
    QWidget,  QLineEdit, QLabel,
    QDialog, QDialogButtonBox,
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
        
        
        self.setLayout(layout)
        
        
        
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
        print("Setting source box to: ", items)
        self._editor.clearSource()
        self._editor.appendSource(items)

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
    
#   Dialog for a new bindings list.

class BindingEditorDialog(QDialog):
    '''   This class wraps a BindingEditor widget in a modal dialog.
            attributes:  editor - returns the editor widget.
            setSpectra: sets the spectra on the left side of the widget.
            setName:    sets the editor name.
            setDescription sets the descripton.
            getBindings: returns the current binding.
    '''
    def __init__(self, *args):
    
        super().__init__(*args)
        
        self.setWindowTitle('Create binding list')
        
        self._buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self._editor = BindingEditor()
        layout = QVBoxLayout()
        layout.addWidget(self._editor)
        layout.addWidget(self._buttonBox)
        self.setLayout(layout)
        
        self._buttonBox.accepted.connect(self.accept)
        self._buttonBox.rejected.connect(self.reject)
    
    def editor(self):
        ''' Return the editor widget '''        
        return self._editor
    def setSpectra(self, spectra):
        ''' Set the spectra in the left side of the box to 'specta' '''
        self._editor.setSource(spectra)
    def setName(self, name):
        ''' Set the name of the binding list '''
        self._editor.setName(name)
    def setDescription(self, descr):
        ''' Set the description of  the binding '''
        self._editor.setDescription(descr)
    def getBindings(self) :
        ''' Return the edited binding in dict form: '''
        
        name = self._editor.name()
        descr = self._editor.description()
        spects = self._editor.bindings()
        return {
            'name': name, 'description': descr, 'spectra': spects
        }
    def spectra(self):
        return self._editor.source()
    def setSpectra(self, spects):
        ''' The bindings in the editor '''
        print("Setting spectra to: ", spects)
        self._editor.setSource(spects)
    
# Dialog convenience methods:

def _handleDialog(dialog):
    if dialog.exec() :
        result = dialog.getBindings()
        if result['name'] == '':
            return None
        if len(result['spectra']) == 0:
                      return None
        return result
    else:
        return None

def promptNewBindingList(parent, spectra):
    ''' Starts a spectrum editor dialog with only the spectra stocked.
        Cancel click returns none as does an Ok clicked without a name 
        or with an empty bindings list. 
    '''
    print("Prompt for new binding from among: ", spectra)
    dialog = BindingEditorDialog(parent)
    dialog.setSpectra(spectra) 
    return _handleDialog(dialog)

#  Utility remove spectra fromt the list that are already bound.

def _removeBoundSpectra(spectra, bindings):
    result = []
    for s in spectra:
        if s not in bindings:
            result.append(s)
    
    return result
    
def editBindingList(parent, spectra, bindinglist):
    ''' Edit an existing binding list. 
        Return is as for promptNewBindingList
    '''
    dialog = BindingEditorDialog(parent)
    dialog.setName(bindinglist['name'])
    dialog.setDescription(bindinglist['description'])
    dialog.editor().setBindings(bindinglist['spectra'])
    dialog.setSpectra(_removeBoundSpectra(spectra, bindinglist['spectra']))
    return _handleDialog(dialog)


if __name__ == "__main__":
          
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
    
    main.setCentralWidget(editor)
    
    main.show()
    app.exec()
    
    