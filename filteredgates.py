''' 
This module provides a filterd gate list.
To provide this we provide our own gate model which is independentl loaded,
a table, to view that model and controls to set the filter, update the list 
based on the new filter and clear the filter back to the default '*'
'''

from PyQt5.QtWidgets import (
    QTableView, QAbstractItemView, QWidget, QPushButton, QLineEdit,
    QVBoxLayout, QHBoxLayout, 
    QApplication, QMainWindow
)

from PyQt5.QtCore import pyqtSignal, QSortFilterProxyModel
import gatelist
import parse

#  We need this separate model so that filters applied here don't affect the
#  comboboxes etc.
filtered_gate_model = QSortFilterProxyModel()
filtered_gate_model.setSourceModel(gatelist.common_condition_model)
filtered_gate_model.setFilterKeyColumn(0)
filtered_gate_model.setFilterWildcard('*')


class GateView(QTableView):
    select = pyqtSignal()
    ''' This is a gate (condition) list table where the selection model is set to allow
    users to select a single condition.   Specifically, a single item can be
    selected (selection mode) and that this is a single row (selection behavior).
    This allows a condition to be selected.
    '''
    def __init__(self, *args):
        global filtered_gate_model
        super().__init__(*args)
        self.setModel(filtered_gate_model)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
    def selectionChanged(self, new, old):
        # (override)
        super().selectionChanged(new, old)
        self.select.emit()   

class FilteredConditions(QWidget):
    ''' This is a filtered gate list with the needed elements to set the
    filter:
    Signals:
        update - Update button was clicked, user should update the filtered_gate_model
           in accordance with the filter pattern.
        select - An item in the list was selected.
        clear  - Clear the pattern back to whatever the default should be.

    Attributes:
        filter - the filter pattern
        selection - (readonly) the selected row.
    '''
    update = pyqtSignal()
    select = pyqtSignal()
    clear = pyqtSignal()
    def __init__(self, *args):
        super().__init__(*args)
        # Layout is two frames.  The top one is the list itself:
        layout = QVBoxLayout()

        self._list = GateView(self)
        layout.addWidget(self._list)

        # Bottom frame has the controls:

        bottom = QHBoxLayout()
        self._update = QPushButton('Update', self)
        bottom.addWidget(self._update)
        self._pattern = QLineEdit('*', self)
        bottom.addWidget(self._pattern)
        self._clear = QPushButton('Clear', self)
        bottom.addWidget(self._clear)

        layout.addLayout(bottom)
        self.setLayout(layout)

        # set up signal relays:

        self._update.clicked.connect(self.update)
        self._clear.clicked.connect(self.clear)
    
    #  Provide the selection changed signal:

        self._list.select.connect(self.select)

    # Attributes:

    def filter(self):
        return self._pattern.text()
    def setFilter(self, pattern):
        self._pattern.setText(pattern)
    
    def contents(self):
        result =list()
        model = self._list.model()
        row = 0
        while model.index(row, 0).isValid():
            result.append(self._make_row(row))
            row += 1
        return result

    def selection(self):
        # Returns none if there is no selection else the contents of the
        # selection in a manner similar to that of a query for that gate:
        # Note the selections include columns not just rows so the juggilinb below:
        
        selection = self._list.selectedIndexes()
        
        if len(selection) == 0:
            return list()
        sel_dict = dict()
        for item in selection:
            row_num = item.row()
            sel_dict[row_num] = row_num
        selected_rows = list()
        for r in sel_dict.keys():
            selected_rows.append(int(r))
        selected_rows.sort()          # For the heck of it.
        result = list()
        for row_num in selected_rows:
            result.append(self._make_row(row_num))
        return result
    #  private utilities:
    def _make_row(self, row_num):
        model = self._list.model()
        name =  model.index(row_num, 0).data()
        type_str = model.index(row_num, 1).data()
        gates    = self._make_string_list(model.index(row_num, 2).data())
        params = self._make_string_list(model.index(row_num, 3).data())
        points  = self._make_point_list(model.index(row_num, 4).data())
        hilo    = self._make_limits(model.index(row_num, 5).data())
        mask    = self._make_mask(model.index(row_num, 6).data())
        return {
                'name': name, 'type': type_str, 'gates' : gates,
                'parameters': params, 'points': points, 'low': hilo[0], 'high': hilo[1],
                'mask': mask
                }
    def _make_string_list(self, gates):
        if gates == '' or gates.isspace():
            return None
        return gates.split(', ')
    def _make_point_list(self, gates):
        if gates == '' or gates.isspace():
            return None
        text_list = gates.split('), ')
        result = list()
        for pt_s in text_list:
            pt = parse.parse('({}, {}', pt_s)
            result.append({'x': pt[0], 'y': pt[1]})
        return result
    def _make_limits(self, gates):
        if  gates == '' or gates.isspace():
            return [0.0, 0.0]
        return parse.parse('{}, {}', gates)
    def _make_mask(self, m):
        if m is not None and (not m == ''):
            return int(m)
        else:
            return None


class GateActionView(QWidget):
    ''' This provides buttons to:
       *  Delete all selected conditions
       *  Delete all displayed conditions.
       *  Load a condition into the editor - where the controller determines which one that is.
    '''
    delselected = pyqtSignal()
    delall      = pyqtSignal()
    loadeditor  = pyqtSignal()
    
    def __init__(self, *args):
        super().__init__(*args)
        layout = QHBoxLayout()
        
        self._delselected = QPushButton("Delete Selected", self)
        layout.addWidget(self._delselected)
        
        self._delall = QPushButton("Delete Displayed", self)
        layout.addWidget(self._delall)
        
        self._loadeditor = QPushButton("Load Editor")
        layout.addWidget(self._loadeditor)
        
        self.setLayout(layout)
        
        # Relay button clicked signals:
        
        self._delselected.clicked.connect(self.delselected)
        self._delall.clicked.connect(self.delall)
        self._loadeditor.clicked.connect(self.loadeditor)
# ---------------------- test code -------------------------------------

def update() :
    pattern = w.filter()
    gatelist.common_condition_model.load(c)
    filtered_gate_model.setFilterWildcard(pattern)
    print('contents:', w.contents())

def select():
    print(w.selection())

def clear():
    w.setFilter('*')
    update()
    
    
def delete_sel():
    names = [x['name'] for x in w.selection()]
    print('would delete', names)
    
def delete_all():
    names = [x['name'] for x in w.contents()]
    print("Would delete: ", names)

def load():
    names = [x['name'] for x in w.selection()]
    if len(names) == 0:
        print('would do nothing')
    elif len(names) == 1:
        print('Would load', names[0])
    else:
        print("would complain only one item can be loaded")

if __name__ == "__main__":
    from rustogramer_client import rustogramer as rc
    c = rc({'host': 'localhost', 'port': 8000})
    

    app = QApplication([])
    win = QMainWindow()
    gatelist.common_condition_model.load(c)
    w = FilteredConditions()
    
    # Check signals and attributes>
    
    w.update.connect(update)
    w.select.connect(select)
    w.clear.connect(clear)
    
    b = GateActionView()
    b.delselected.connect(delete_sel)
    b.delall.connect(delete_all)
    b.loadeditor.connect(load)
    
    widget = QWidget()
    layout = QVBoxLayout()
    layout.addWidget(b)
    layout.addWidget(w)
    widget.setLayout(layout)
    

    win.setCentralWidget(widget)
    win.show()
    app.exec()
