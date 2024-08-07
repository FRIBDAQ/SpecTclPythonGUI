from PyQt5.QtWidgets import (
    QWidget, QPushButton, QLabel, QTableWidget, QTableWidgetItem, QAbstractItemView,
    QHBoxLayout, QVBoxLayout,
    QApplication, QMainWindow
)
from PyQt5.QtCore import pyqtSignal
from PyQt5.Qt import *

class BindingGroupTab(QWidget) :
    '''
        This class provides the top level user interface for
        bindings groups.  A binding group is represented as a
        dict that conains the following keys: 
        - name:    The name of the group.
        - description : A brief descdription of the group.
        - spectra: An ordered list of the names of spectra  in the group.
        
        These are listed in a table that gives the name and the desription for each group.
        The table allows a single selection and there are controls that allow the application
        to operate on that seleted item:
    
        - Edit the selected bindings group to add or remove spectra... potentially makeing a new group
        - Load a bindings group into the server - which
            *  Unbinds all currently bound spectra from display memory
            *  Binds the spectra in the group into display memory.
        - Append a bindings group into the server - which binds the spectra in the group
          without removing existing bindings.
          
        Other operations can be performed:
        
        - Create a new bindings list 
        - Save the current set of bindings as a new bindings list.
        
        Note that the definitions database file is extended to support saving/restoring bindings
        lists.
        
        This widget can be thought of as just the view of a model that includes a set of bindings.
        
        The following attributes are supported:
        
        - bindingGroups - Fetches or stores the current binding groups (loads the table or gets the
        table contents and associated data).
        - selectedBinding - (RO) - returns the currently selected binding.
        - loaded  - The labels with the name/description of the loaded binding.
        - changed - Bool - true if the loaded binding is marked as changed (because it was added e.g.).
        
        The following public functions are provided:
        
        - addBindingGroup - add a new binding group to the table.
        - replaceBindingGroup - given a name and a description, overwrites the table row with that name. Note
        that if there is no matching name, this is like addBindingGroup.
    
        Signals:
        - new - New... button was clicked to create a new binding group.
        - edit - Edit... button was clicked to edit the selected binding group.
        - load - Load  button was clicked to overwrite the current bindings with the selected group.
        - add  - Add button was clicked to add the selected bindings to the current bindings.
        - save - Save button clicked the currently loaded bindings over the selected binding group.
        - saveas - Save As... button was clicked to save the currently loaded bindings as a new binding gropu.
        - bindall - 'Bind All' button was clicked to bind all known spectra to the display.
        - update - Update button was clicked.
        Internal note:  The table widget uses a row selection model...so full rows get selected at any time.
        There are two columns for each row:
        
        - Name - the name of a binding list.
        - Description - the description of the binding list with that name.
        
        TheTableWidgetItem associated with the name, in addition to having the text attribute set to the
        name of a binding list, has its user data set to the list of spectra in the binding list, so the
        table maintains the full binding list information.
        
        
        Rough layout:
        
        +-------------------------------------------------------------------+
        | Loaded: Name: ___________________(*) Description_________________ |
        |                                                                   |
        | +--------------------------------------------------------------+  |
        | |  Table with list of bindings                                 |  |
        | +--------------------------------------------------------------+  |
        |  [Edit ...] [Load ] [Add]                                         |
        |  [Save] [Save As...] [New...]                                     |
        |  [ Bind All]  [Update]                                            |
        +-------------------------------------------------------------------+
        
    '''
    new = pyqtSignal()
    edit = pyqtSignal()
    load = pyqtSignal()
    add = pyqtSignal()
    save = pyqtSignal()
    saveas = pyqtSignal()
    bindall = pyqtSignal()
    update = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        
        #  We stack a  bunch of horizontal layouts:
        
        layout = QVBoxLayout()
        
        # Top row has labels:
        
        top = QHBoxLayout()
        top.addWidget(QLabel("Loaded Name: ", self))
        self._loadedname = QLabel('                                    ', self)
        top.addWidget(self._loadedname)
        self._changed = QLabel(' ')
        top.addWidget(self._changed)
        top.addWidget(QLabel('Description:'))
        self._loadeddescription = QLabel('                                         ', self)
        top.addWidget(self._loadeddescription)
        
        layout.addLayout(top)
    
        
        # Second row is just the table:
        
        self._bindgroups = QTableWidget(self)
        self._bindgroups.setColumnCount(2)
        self._bindgroups.setHorizontalHeaderLabels(['Name', 'Description'])
        self._bindgroups.showGrid()
        self._bindgroups.setSelectionMode(QAbstractItemView.SingleSelection)
        self._bindgroups.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._bindgroups.setEditTriggers(QAbstractItemView.NoEditTriggers)
        
        layout.addWidget(self._bindgroups)
        
        # Third row are a buttons that operate on the selected group.
        
        row3 = QHBoxLayout()
        self._editbutton = QPushButton('Edit Selected...', self)
        row3.addWidget(self._editbutton)
        self._loadbutton = QPushButton('Load Selected', self)
        row3.addWidget(self._loadbutton)
        self._addbutton = QPushButton('Add Selected', self)
        row3.addWidget(self._addbutton)
        layout.addLayout(row3)
        
        # Row 4 are buttons to save the current set of bindings.
        
        row4 = QHBoxLayout()
        self._savebutton = QPushButton('Save as selected', self)
        row4.addWidget(self._savebutton)
        self._saveasbutton = QPushButton('Save as new...', self)
        row4.addWidget(self._saveasbutton)
        self._newbutton = QPushButton('New...', self)
        row4.addWidget(self._newbutton)
        layout.addLayout(row4)
        
        # Row 5 is bind all, Update buttons:
        
        row5 = QHBoxLayout()
        self._bindallbutton = QPushButton('Bind All', self)
        row5.addWidget(self._bindallbutton)
        self._updatebutton = QPushButton('Update (spectra)', self)
        row5.addWidget(self._updatebutton)
        layout.addLayout(row5)
        
        self.setLayout(layout)
        
        # Now bind the signals from the buttons to our own:
        
        self._newbutton.clicked.connect(self.new)
        self._editbutton.clicked.connect(self.edit)
        self._loadbutton.clicked.connect(self.load)
        self._addbutton.clicked.connect(self.add)
        self._savebutton.clicked.connect(self.save)
        self._saveasbutton.clicked.connect(self.saveas)
        self._bindallbutton.clicked.connect(self.bindall)
        self._updatebutton.clicked.connect(self.update)
    
    # Attributes:
    
    # bindingGroups
    
    # Reconstruct the list of binding group dicts from the rows of the table:
    
    def bindingGroups(self):
        result = list()
        for r in range(self._bindgroups.rowCount()):
            result.append(self._getBinding(r))
        
        return result
    def setBindingGroups(self, bindings) :
        # First clear the table:
        
        for row in range(self._bindgroups.rowCount()):
            self._bindgroups.takeItem(row,0)
            self._bindgroups.takeItem(row,1)
            
        #  Now fill it up:
        
        self._bindgroups.setRowCount(len(bindings))
        row = 0
        for binding in bindings :
            self._setBinding(row, binding)
            row += 1

    # Selected binding:
    def selectedBinding(self):
        selection = self._bindgroups.selectedItems()
        result = list()
        
        #  Only one row can be selected so this is going to be the items in the row
        #  But we don't assume the order.
        
        if len(selection) > 0 :
            row = self._bindgroups.row(selection[0])
            rowInfo = self._getBinding(row)
            result.append(rowInfo)
            
        return result
    
    def loaded(self):
        ''' Returns a pair containing the name and the description of the 'loaded' binding'''
        
        return (self._loadedname.text(), self._loadeddescription.text())
    
    def setLoaded(self, name, description):
        self._loadedname.setText(name)
        self._loadeddescription.setText(description)
    
    def changed(self):
        if self._changed.text() == '*':
            return True
        else:
            return False
    
    def setChanged(self, yes):
        if yes :
            self._changed.setText('*')
        else:
            self._changed.setText(' ')
            
    #----------------------  Public methods:
    
    def addBindingGroup(self, binding):
        ''' Add a new binding group to the table.  It's the caller's responsiblitity to 
            avoid duplicate names.
        '''
        row = self._bindgroups.rowCount()
        self._bindgroups.setRowCount(row+1)
        
        self._setBinding(row, binding)
        
    def replaceBindingGroup(self, binding) :
        found = self._findBinding(binding['name'])
        if found is not None:
            self._setBinding(found, binding) # found so replace
        else:
            self.addBindingGroup(binding)   # Not found so append
        
    
    #---------   private methods
    
    def _getBinding(self, row):
        # Return the binding information for a row:
        nameInfo = self._bindgroups.item(row, 0)
        name  = nameInfo.text()
        bindings = nameInfo.data(Qt.UserRole)
        desc = self._bindgroups.item(row, 1).text()
        return {
            'name': name, 'description': desc, 'spectra': bindings
        }
        
    def _setBinding(self, row, binding):    
        nameItem = QTableWidgetItem(binding['name'])
        nameItem.setData(Qt.UserRole, binding['spectra'])
        self._bindgroups.setItem(row, 0, nameItem)
        
        descitem = QTableWidgetItem(binding['description'])
        self._bindgroups.setItem(row, 1, descitem)
    
    def _findBinding(self, name):
        ''' 
          Return either the row a binding is in or the None if there is no match
          If there's more than one binding, the first found is returned.
        '''
        matches = self._bindgroups.findItems(name, Qt.MatchExactly)
        for match in matches:
            if self._bindgroups.column(match) == 0:
                # Name matches so this row.
                
                return  self._bindgroups.row(match)
        
        # no matching _names_
        return None
        
# For testing:

if __name__ == '__main__':
    
    def new() :
        print('new')
        print(widget.bindingGroups())
    def edit() :
        print('edit')
        print(widget.selectedBinding())
    def load() :
        print('load')
        print(widget.loaded())
    def add() :
        print('add')
        changed = widget.changed()
        print(changed)
        widget.setChanged(not changed)
    def save() :
        print('save')
        widget.addBindingGroup({
            'name': 'NewGroup',
            'description': 'A dynamically added group of bindings',
            'spectra': [
                'newspec1', 'newspec2', 'newspect3'
            ]
        })
    def saveas() :
        print('saveas')
        widget.replaceBindingGroup(
            {
                'name': 'binding1',
                'description': 'A replaced binding',
                'spectra': ['spec1', 'spec1', 'spec3', 'added']
            }
        )  #existing
    def bindall():
        print('bindall')
        widget.replaceBindingGroup(
            {
                'name': 'noSuch',
                'description': "replace -> new",
                'spectra': ['s1', 's2', 's3']
            }
        )
    
    app = QApplication([])
    main = QMainWindow()
    
    widget = BindingGroupTab()
    widget.new.connect(new)
    widget.edit.connect(edit)
    widget.load.connect(load)
    widget.add.connect(add)
    widget.save.connect(save)
    widget.saveas.connect(saveas)
    widget.bindall.connect(bindall)

    bindings = [
        {'name': 'binding1' ,'description' : 'a binding', 'spectra' : [
            'spec1' ,'spec2', 'spec3'
        ]},
        {'name':'summary', 'description': 'A second binding', 'spectra': [
            'twod', 'gamma', 'gamma-summary'
        ]}
    ]
    
    widget.setBindingGroups(bindings)
    widget.setLoaded("summary", "A second binding")
    main.setCentralWidget(widget)
    
    main.show()
    app.exec()
        

