'''
    This file contains code to make a standard item model to hold tree variables.
    Each tree variable has the following simple 'textual' fields:
    
    name - the name of the variable.
    value - The value of the variable.
    units - the variable units.
    
    We also provide a load method to fill the model given a client.
'''

from PyQt5.QtGui import QStandardItemModel, QStandardItem, QDoubleValidator
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QComboBox, QWidget, QPushButton, QCheckBox, QTableWidget, QAbstractItemView,
    QLabel, QLineEdit,
    QHBoxLayout, QVBoxLayout
)


class TreeVariableModel(QStandardItemModel):
    _colheadeings = ['Name', 'Value', 'Units']
    def __init__(self, *args):
        super().__init__(*args)
    def headerData(self, col, orient, role):
        if role == Qt.DisplayRole:
            if orient == Qt.Horizontal:
                return self._colheadings[col]
            else:
                return None
    # Public methods
                
    def load(self, client):
        raw_data = client.treevariable_list()
        self.clear()             # Get rid of prior data.
        for var in raw_data['detail']:
            self._add_line(var)
    
    def get_definition(self, name):
        ''' 
        Finds the one item that matches 'name' and returns it's definition.
        If there is no match, returns None  if there is a match returns a map of
        'name'   - name of the item.
        'value'  - Value of the item.
        'units'  - Units of the item.
        
        '''
        matches = self.findItems(name, Qt.MatchExactly, 0)   # only match name field.
        if len(matches) == 1:
            return self._name_item_to_def(matches[0])
        else:
            return None     # We don't know how to handle multiple matches.
    def get_matching_definitions(self, pattern):
        matches = self.findItems(pattern, Qt.MatchWildcard, 0)
        result = list()
        for match in matches:
            result.append(self._name_item_to_def(match))
        return result
    def set_definition(self, definition):
        matches = self.findItems(definition['name'], Qt.MatchExactly, 0)
        if len(matches)  ==1:
            index = self.indexFromItem(matches[0])
            row   = index.row()
            self.item(row,1).setText(str(definition['value']))
            self.item(row,2).setText(definition['units'])
            
    # Private methods:
    
    def _add_line(self, var):
        name = var['name']
        value= var['value']
        strvalue = f'{value}'
        units= var['units']
        
        self.appendRow([
            QStandardItem(name), QStandardItem(strvalue), QStandardItem(units)
        ])
    def _name_item_to_def(self, item):
        index = self.indexFromItem(item)
        row   = index.row()
        name  = self.item(row, 0).text()
        valueItem = self.item(row, 1)
        unitsItem = self.item(row, 2)
        value = float(valueItem.text().replace(',',''))
        units = unitsItem.text()
        
        return {
            'name': name, 'value': value, 'units': units
        }
        
common_treevariable_model = TreeVariableModel()
# Now some views:

class VariableChooser(QComboBox):
    '''
       Combobox that allows users to choose a variable.
    '''
    def __init__(self, *args):
        super().__init__(*args)
        self.setEditable(False)
        self.setModel(common_treevariable_model)
        
class VariableSelector(QWidget):
    '''
    Provides the controls needed to choose tree variables and add them to some
    editable thing.  This consists of a variable chooser and the buttons:
    Append, Replace, Remove, Load and Set. A checkbutton called 'array' is also present.
    
    Signals:
        append  - the append button was clicked.
        replace - the replace button was clicked.
        remove  - the remove button was clicked.
        load    - the load button was clicked.
        set     - the set button was clicked.
        
    Slots:
        None
    Attributes:
        name - (readonly) Selected name.
        definition - (readonly) - definition of selected item.
        array - Value of the array checkbutton.
        
    '''
    append = pyqtSignal()
    replace = pyqtSignal()
    remove = pyqtSignal()
    load   = pyqtSignal()
    set    = pyqtSignal()
    
    def __init__(self, *args):
        super().__init__(*args)
        
        layout = QVBoxLayout()
        
        # Top row is the chooser, the append replace and array controls:
        
        top = QHBoxLayout()
        
        self._chooser = VariableChooser(self)
        top.addWidget(self._chooser)
        self._append = QPushButton('Append', self)
        top.addWidget(self._append)
        self._replace = QPushButton('Replace', self)
        top.addWidget(self._replace)
        self._remove = QPushButton('Remove', self)
        top.addWidget(self._remove)
        self._array = QCheckBox('Array', self)
        top.addWidget(self._array)
        
        layout.addLayout(top)
        
        # The bottom row is just the Load and Set buttons...with a strectch on the
        # end:
        
        bottom = QHBoxLayout()
        
        self._load = QPushButton('Load', self)
        bottom.addWidget(self._load)
        self._set  = QPushButton('Set', self)
        bottom.addWidget(self._set)
        bottom.addStretch(1)
        
        layout.addLayout(bottom)
        
        self.setLayout(layout)
    
        # Relay signals:
        
        self._append.clicked.connect(self.append)
        self._replace.clicked.connect(self.replace)
        self._remove.clicked.connect(self.remove)
        self._load.clicked.connect(self.load)
        self._set.clicked.connect(self.set)
    # Implement attributes:
    
    def name(self):
        return self._chooser.currentText()
    def definition(self):
        name = self._chooser.currentText()
        return self._chooser.model().get_definition(name)
    def array(self):
        return self._array.checkState() == Qt.Checked
    def setArray(self, value):
        if value:
            newstate = Qt.Checked
        else:
            newstate = Qt.Unchecked
        self._array.setCheckState(newstate)
    
    

class VariableTable(QTableWidget):
    '''
    This is a table for tree variables each row has a name, value and units column.
    Methods:
       clear - Remove all rows from the table.
       append - Append a row.
       replace - Replace an existing row.
       remove  - Remove an existing row.
       selection - Return the currently selected rows.
    '''
    def __init__(self, *args):
        super().__init__(*args)
        self.setColumnCount(3)
        self.setHorizontalHeaderLabels(['Name', 'Value', 'Units'])
        self.showGrid()
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
    
    # Public methods:
    def clear(self):
        ''' Clear all table rows.'''
        while self.rowCount() > 0:
            self.remove(0)
    def append(self, definition):
        ''' 
            Appends a new row to the table.  definition is a definition of a tree variable
            that may have come from the model's get_definition  method.
        '''
        
        self._append_row(definition)
    
    def replace(self, row, definition):
        ''' 
        Replaces the contents of 'row' with 'definition'.  If row is out of range, 
        raises indexerror.
        '''

        self._check_row(row)
        row_items = self._make_row(definition)
        col = 0
        for item in row_items:
            self.setCellWidget(row, col, item)
            col += 1
    
    def remove(self, row):
        '''
        Remove row number 'row' from the table.  Again if row is out of range raises index error
        '''
        self._check_row(row)
        self.removeRow(row)
    
    def selection(self):
        '''
        Return the contents of the current selection. This is a (possibly empty) list of dicts
        with the keys:
        'name'   - Name of the treevariable in that row.
        'value'  - Value field in that row.
        'units'  - Units in that row.
        'row'    - Row number in the table.
        '''
        
        
        selected_rows = self._selected_rows()
        result = list()
        for row in selected_rows:
            name = self.cellWidget(row, 0).text()
            value = float(self.cellWidget(row,1).text().replace(',',''))
            units = self.cellWidget(row, 2).text()
            result.append({
                'name': name, 'value': value, 'units': units, 'row' : row
            })
        return result
        
        
    #   Utilities (private):
    def _selected_rows(self):
        ranges=  self.selectedRanges()
        rows = list()
        for r in ranges:
            bottom = r.bottomRow()
            top    = r.topRow()
            for row in range(top, bottom+1):
                rows.append(row)
        return rows
        
    def _append_row(self, definition):
        oldcount =self.rowCount()
        self.setRowCount(oldcount + 1)
        self.replace(oldcount, definition)
    
    def _check_row(self, row):
        if row > self.rowCount() - 1:
            raise IndexError(f"No such row in VariableTable {row}")
    def _make_row(self, definition):
        name = QLabel(definition['name'], self)
        value = QLineEdit(str(definition['value']) ,self) 
        value.setValidator(QDoubleValidator(self))
        units = QLineEdit(definition['units'], self)
        return [name, value, units]


class TreeVariableView(QWidget):
    ''' 
    This is the full tree variable editor view.  It's just a stack of the 
    Variable selector on top of a VariableTable with
    - Signals relayed from the two componets for convenience and
    - Read-only attributes that allow access to the compnents of the view.
    Signals:
        append  - the append button was clicked.
        replace - the replace button was clicked.
        remove  - the remove button was clicked.
        load    - the load button was clicked.
        set     - the set button was clicked.
    Attributes:
        table - return the table widget.
        selector - return the selector widget.
    Slots:
        None
    Attributes:
        selector - return the VariableSelector widget reference (readonly).
        table    - return the VariableTable widget reference (readonly).
    '''       
    append = pyqtSignal()
    replace= pyqtSignal()
    remove = pyqtSignal()
    load   = pyqtSignal()
    set    = pyqtSignal()
    
    def __init__(self, *args):
        super().__init__(*args)
        layout = QVBoxLayout()
        
        self._selector = VariableSelector(self)
        layout.addWidget(self._selector)
        
        self._table = VariableTable(self)
        layout.addWidget(self._table)
        
        self.setLayout(layout)
        
        # Relay signals from the selector for convenience:
        
        self._selector.append.connect(self.append)
        self._selector.replace.connect(self.replace)
        self._selector.remove.connect(self.remove)
        self._selector.load.connect(self.load)
        self._selector.set.connect(self.set)
        
    # Implement the attributes:
    
    def table(self):
        return self._table
    def selector(self):
        return self._selector
        
        
#------------------------------------- Test code ------------------------



if __name__ == '__main__':
    
    from rustogramer_client import rustogramer as rcl
    from PyQt5.QtWidgets import (QApplication, QMainWindow)
    
    def _find_def(name, data):
        # Find the matching definition in data.
        
        for item in data:
            if name == item['name']:
                return item
        return None
    
    def selected():
        return  wid.selector().definition()
    def append():
        wid.table().append(selected())
    def replace():
        selection = wid.table().selection()
        if len(selection) == 1:
            row = selection[0]['row']
            wid.table().replace(row, selected())
        selected()
    def remove():
        sel = wid.table().selection()
        rows = [x['row'] for x in sel]
        rows.sort(reverse=True)
        for row in rows:
            wid.table().remove(row)
    def load():
        print('load', wid.selector().array())
        selection = wid.table().selection()
        data = client.treevariable_list()['detail']    # Load current data from server.
        for item in selection:
            name = item['name']
            info = _find_def(name, data)
            if info is not None:
                wid.table().replace(item['row'], info)
            
    def setvalue(): 
        print('set', wid.selector().array())   # We don't respect that....
        selection = wid.table().selection()
        for var in selection:
            client.treevariable_set(var['name'], var['value'], var['units'])
            common_treevariable_model.set_definition(var) # update the model.
    
    client = rcl({'host':'localhost', 'port': 8000})
    common_treevariable_model.load(client)
    
    app = QApplication([])
    win = QMainWindow();
    
    wid = TreeVariableView()
    wid.append.connect(append)
    wid.replace.connect(replace)
    wid.remove.connect(remove)
    wid.load.connect(load)
    wid.set.connect(setvalue)
    
    
    
    
    win.setCentralWidget(wid)
    win.show()
    app.exec()
        
    
    

