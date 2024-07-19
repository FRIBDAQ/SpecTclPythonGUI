''' This file contains the widgets needed to edit parameters.  
This includes:
   *  Limit - a QLineEdit widget  that is either empty or a valid floating number.
   *  Bins  - A QLineEdit widget constrained to have positive non-zero integers.
   * ParameterTable - Which is a dynamically expandable
     table of parameter loaders and widgets describing  parameters.


'''
from PyQt5.QtWidgets import (
    QLineEdit, QPushButton, QCheckBox, QWidget, QLabel, QTableWidget,
    QDialog, QDialogButtonBox,
    QHBoxLayout, QVBoxLayout,
    QAbstractItemView, 
    QApplication, QMainWindow
)
from PyQt5.QtGui import QDoubleValidator, QIntValidator
from PyQt5.QtCore import pyqtSignal, Qt


from  ParameterChooser import (
    Chooser as PChooser, 
    LabeledParameterChooser as PLChooser
)


class Limit(QLineEdit):
    def __init__(self, *args):
        super().__init__(*args)
        self.setValidator(QDoubleValidator(self))
    
    def value(self):
        t = self.text()
        if t.isspace() or (t == ''):
            return None
        return float(t)
    def setValue(self, value):
        if value is not None:
            self.setText(f'{value}')
        else: 
            self.setText('')

class Bins(QLineEdit):
    def __init__(self, *args):
        super().__init__(*args)
        validator = QIntValidator(self)
        validator.setBottom(1)
        self.setValidator(validator)
    
    def value(self):
        t = self.text()
        if t.isspace() or (t == ''):
            return None
        return int(t)
    def setValue(self, value):
        if value is None:
            self.setText('')
        else:
            self.setText(f'{value}')

class ParameterTable(QTableWidget):
    '''
        This is a table of parameters.  Each line in the table
        consists of a label (name of the parameter) two limit widgets
        (high, low) and a Bins widget as well as an unconstrained line edit
        widget containing the units.  Unlike the SpecTcl tree GUI, the
        GUI wrapping this will have load/set/change_spectra buttons that
        operate on all lines in the table that are selected.  Similarly for the 'array'
        checkbutton.  

        Those are all external to the ParameterTable widget which is only a table.

        Attributes (per row)
            name  - Name of the parameter on the row.
            low   - low value for the row,
            high  - High v alue for the row.
            bins  - bins for the row.
            units - Units for the row.

        Methods:
           addRow -  Add a new row to the table.
           setRow -  Set the contents of a row.
           getRow -  Retrieves all there is about a row as a map containing:
                    ['name'], ['low'], ['high'], ['bins'], ['units'] with obvious
                    meanings.
           selectedRows- return the selected rows.
    '''
    def __init__(self, *args):
        super().__init__(*args)
        self.setColumnCount(5)
        self.setRowCount(0)
        self.showGrid()
        self.setHorizontalHeaderLabels(['Name', 'Low', 'High', 'Bins', 'Units'])
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)

    # Public methods:

    def add_row(self, name, low=None, high=None, bins=None, units = None):
        ''' Add a new row to the table.  Note that any parameters that have
          None values fill their cell with blanks.
          *  name - value to put in the name field of the row.
          *  low  - value to put in the low field of the row.
          *  high - value to put in the high field of the row
          *  units - Value to put in the units field of the row. 
        '''
        rows = self.rowCount() + 1     # After adding:
        self.setRowCount(rows)

        self.set_row(rows-1, name, low, high, bins, units)
    
    def set_row(self, row_num, name, low = None, high = None, bins = None, units = None):
        ''' Fill a row with data for a parameter. Any previous information is
            overwitten.  name, low, high, bins, units have the same meaning as for
            the add_row method. 
            *  row_num - is the number of the row to fill in.
        '''
        self._check_row(row_num)
        _name = QLabel()
        _name.setText(name)
        self.setCellWidget(row_num, 0, _name)

        _low = Limit()
        _low.setValue(low)
        self.setCellWidget(row_num, 1, _low)

        _high = Limit()
        _high.setValue(high)
        self.setCellWidget(row_num, 2, _high)

        _bins = Bins()
        _bins.setValue(bins)
        self.setCellWidget(row_num, 3, _bins)

        _units = QLineEdit()
        if units is not None:
            _units.setText(units)
        self.setCellWidget(row_num, 4, _units)

    def get_row(self, row_num):
        ''' Returns the contents of a row as a dict containing the
           keys:
           *  'name' - name of the parameter
           *  'low'  - Contents of low (None if empty).
           *  'high' - Contents of high (None if empty).
           *  'bins' - Contents of bins (None if empty).
           *  'units' - Content sof units (None if empty).
        '''
        self._check_row(row_num)
        
        name = self.cellWidget(row_num, 0).text()
        low  = self.cellWidget(row_num, 1).value()
        high = self.cellWidget(row_num, 2).value()
        bins = self.cellWidget(row_num, 3).value()
        units = self.cellWidget(row_num, 4).text()
        if units.isspace() or (units == ''):
            units = None
        
        return {'name': name, 'low': low, 'high': high, 'bins': bins, 'units':units}
    def delete_row(self, row):
        ''' Delete the specified row.  Note that this decrements the row indices
           of all subsequent rows in the table
        '''
        self.removeRow(row)

    def selected_rows(self):
        ''' Returns a list of selected rows.  For ourpurposes, this is much
           simpler to use than a selection range since we can just iterate
           over the rows.
           (returns a list of ints or empty if nothing is selected).

        '''
        result = list()
        selection_extents = self.selectedRanges()
        for srange in selection_extents:
            top = srange.topRow()
            bottom = srange.bottomRow()
            for r in range(bottom, top+1):
                result.append(r)
        return result


    # Private utilities:

    def _check_row(self, row_num):
        if row_num >= self.rowCount():
            raise IndexError(f'{row_num} is not a legal row number')

''' The parameter widget it's centered around a Paramteer Table but has
    other important controls:

    +------------------------------------------------------------+
    |  (parameter chooser) [Append] [Replace]  [] array          |
    |  [  Load ] [  Set ]  [ Change Spectra]                     |
    | +--------------------------------------------------------+ |
    |    parameter table ...                                     |
    | +--------------------------------------------------------+ |
    +------------------------------------------------------------+

'''
class ParameterEditor(QWidget):
    '''
        This is the view for the parameter editor.  It provides
        
        Attributes:

        * parameter - Value of the parameter chooser
        * array     - bool state of the array checkbox.
        * table      - (readonly) the encapsulated ParameterTable widget.

        Signals:
        *  newRow - the New button was clicked. The controller
           should fetch the parameter name, and create a new row
           containing its attributes.
        *  replaceRow - The Replace button was clicked.  The
           controller should:
            -  Determine the current row however they deem appropriate.
            -  Replace the contents of that row with the attributes
               of the selected parameter.
        *  remove - the selected table rows should be deleted.
        *  reload - the parameter model should be reloaded.
        *  loadClicked - The seleced row contents should be updated 
           with the current attributes of the parameter.
        *  setClicked  - The selected row attributes should be 
           loaded into the associated parameters.  Note  that if
           array is true, where row parameters are templates of a
           parameter array, all elements should be modified.
        *  changeClicked - Spectra that use parameters in the 
           selected rows should have the appropriate axis updated to
           match the attributes of the specified parameters.  Array should
           function as for setClicked - that is each parameter name
           that is a template for an array of parameters should 
           modify spectra that use any element of the array 
        
        What is an array of parameters?  This is a bit expanded
        from the TreeParameter's definition.  In our case if
        a parameter name is of the form a. ... .tail,  tail is replaced
        by * and any parameter whose name matches that glob pattern
        is considered part of the array.  For example consider
        parmaeters
        a.1, a.2 a.c  I _think_ that in treegui, only a.1 and 1.2 
        are considered array alements but in this GUI, a.1,a.2, and a.c
        are all array elements (think of allowing fully textual
        subscripts).
           
    '''
    newRow        =   pyqtSignal()
    replaceRow    = pyqtSignal()
    remove        = pyqtSignal()
    reload        = pyqtSignal()
    loadclicked   =   pyqtSignal()
    setclicked    =   pyqtSignal()
    changeclicked =   pyqtSignal()

    def __init__(self, *args):
        super().__init__(*args)

        layout = QVBoxLayout()    # Overall layout.

        top_row = QHBoxLayout()   # Top row of widgets:

        self._parameter = PLChooser(self)
        top_row.addWidget(self._parameter)

        self._new = QPushButton('Append', self)
        top_row.addWidget(self._new)

        self._replace = QPushButton('Replace', self)
        top_row.addWidget(self._replace)

        self._remove = QPushButton("Remove Selected", self)
        top_row.addWidget(self._remove)

        self._reload = QPushButton('Reload', self)
        top_row.addWidget(self._reload)

        self._array = QCheckBox('Array', self)
        top_row.addWidget(self._array)

        layout.addLayout(top_row)

        action_row = QHBoxLayout()
        self._load = QPushButton('Load', self)
        action_row.addWidget(self._load)
        self._set  = QPushButton('Set', self)
        action_row.addWidget(self._set)
        self._changeSpectra = QPushButton('Change Spectra', self)
        action_row.addWidget(self._changeSpectra)

        layout.addLayout(action_row)

        self._table = ParameterTable(self)
        layout.addWidget(self._table)

        self.setLayout(layout)

        # Connect the button click relays to our defined signals:

        self._new.clicked.connect(self.newRow)
        self._replace.clicked.connect(self.replaceRow)
        self._remove.clicked.connect(self.remove)
        self._reload.clicked.connect(self.reload)

        self._load.clicked.connect(self.loadclicked)
        self._set.clicked.connect(self.setclicked)
        self._changeSpectra.clicked.connect(self.changeclicked)

    #  Implement the attributes:

    def parameter(self):
        ''' Return the currently selected parameter if None is returned
           a full parameter path has not been selected.
        '''
        name = self._parameter.parameter()
        if name.isspace() or (name == ''):
            return None
        else:
            return name
    def setParameter(self, new_name):
        self._parameter.setParameter(new_name)
    
    def array(self):
        if self._array.checkState() == Qt.Checked:
            return True
        else:
            return False
    def setArray(self, value):
        if value:
            self._array.setCheckState(Qt.Checked)
        else:
            self._array.setCheckState(Qt.Unchecked)
    def table(self):
        return self._table

class CheckTable(QTableWidget):
    ''' This provides a table of spectra containing:
        A check box a the left of each table row.
        The name of the spectrum.
        The x axis specifications.
        The y axis specifications.
          The idea is that this is a table that allows changes to
        several spectra to be modified, accepted or rejected when
        encapsulated in SpectrumFilterDialog (see below).
    
    Attributes:
        acceptedSpectra -(readonly) Returns a list of the accepted spectra as a dict
          containing the checked proposed changes.

    Public methods:
        load - Takes a list of spectra and loads the table.
        checkAll - checks/ or unchecks all spectra.

    '''
    def __init__(self, *args):
        super().__init__(*args)

        self.setColumnCount(8)
        self.setRowCount(0)
        self.showGrid()
        self.setHorizontalHeaderLabels([
            'Accept', 'Name', 
            'X Low', 'X High', 'X Bins', 
            'Y Low', 'Y High', 'Y Bins']
        )
        self._defs = list()
    
    # Attribute implementations:

    def acceptedSpectra(self):
        #  Returns a list of the spectra that have checkmarks by them.
        #  The list is a dict of (possibly modified) spectrum definitions.
        #  Note that only the xaxis and yaxis can be modified.
        result = list()
        for row in range(self.rowCount()):
            checkbox = self.cellWidget(row, 0)
            if checkbox.checkState() == Qt.Checked:
                definition = self._defs[row]
                
                #Override axis definitions:
                low = self.cellWidget(row, 2)
                if low is not None:
                    definition['xaxis']['low'] = low.value()
                    definition['xaxis']['high'] = self.cellWidget(row, 3).value()
                    definition['xaxis']['bins'] = self.cellWidget(row, 4).value()

                high = self.cellWidget(row, 5)
                if high is not None:
                    definition['yaxis']['low'] = high.value()
                    definition['yaxis']['high'] = self.cellWidget(row, 6).value()
                    definition['yaxis']['bins'] = self.cellWidget(row, 7).value()

                result.append(definition)
        return result
    # Public methods:

    def checkAll(self, state):
        if state:
            value = Qt.Checked
        else:
            value = Qt.Unchecked
        for row in range(self.rowCount()):
            self.cellWidget(row, 0).setCheckState(value)

    def load(self, defs):
        # Load all definitions in to the table...which is first cleared:

        # Clear previous countent:
        self.setRowCount(0)
        self._defs = list()

        for d in defs:
            self._defs.append(d)
            row = self.rowCount()
            self.setRowCount(row+1)
            self._loadRow(row, d)

        self.checkAll(True)       # Start all accepted.
    # Private utilities:

    def _loadRow(self, row, d):

        # Load row row, with the spectrum in def - assumed already in self._defs

        self.setCellWidget(row, 0, QCheckBox())
        self.setCellWidget(row, 1, QLabel(d['name']))

        # Xaxis:

        if d['xaxis'] is not None:
            low = Limit()
            low.setValue(d['xaxis']['low'])
            high = Limit()
            high.setValue(d['xaxis']['high'])
            bins = Bins()
            bins.setValue(d['xaxis']['bins'])
            self.setCellWidget(row, 2, low)
            self.setCellWidget(row, 3, high)
            self.setCellWidget(row, 4, bins)

        # Yaxis
        if d['yaxis'] is not None:
            low = Limit()
            low.setValue(d['yaxis']['low'])
            high = Limit()
            high.setValue(d['yaxis']['high'])
            bins = Bins()
            bins.setValue(d['yaxis']['bins'])
            self.setCellWidget(row, 5, low)
            self.setCellWidget(row, 6, high)
            self.setCellWidget(row, 7, bins)

class ConfirmSpectra(QDialog):
    def __init__(self, *args):
        super().__init__(*args)
        self.setWindowTitle("Modify spectra?")

        self.buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )

        layout = QVBoxLayout()

        #  Check all/none buttons:

        self._checkall = QPushButton('Check All')
        self._checknone = QPushButton('Uncheck all')
        checklayout = QHBoxLayout()
        checklayout.addWidget(self._checkall)
        checklayout.addWidget(self._checknone)

        layout.addLayout(checklayout)

        self._table = CheckTable(self)
        layout.addWidget(self._table)

        layout.addWidget(self.buttons)

        self.setLayout(layout)

        # Connect internal signals:

        self._checkall.clicked.connect(self._selectAll)
        self._checknone.clicked.connect(self._selectNone)

        self.buttons.accepted.connect(self._accept)
        self.buttons.rejected.connect(self._reject)

    def getTable(self):
        return self._table

    #internal slot handlers:

    def _selectAll(self):
        self._table.checkAll(True)
    def _selectNone(self):
        self._table.checkAll(False)

    def _accept(self):
        self.done(QDialog.Accepted)
    def _reject(self):
        self.done(QDialog.Rejected)

#-------------------- Test code -------------------------

def new_row():
    print("Want a new row")

def replace_row():
    print("replace row: ", w.table().currentRow())

def log(what):
    rows = w.table().selected_rows()
    array = w.array()

    print(what , rows, " array state: ", array)

def load():
    log('load data')

def set_params():
    log("set parameters")

def change():
    log('change spectra')
if __name__ == '__main__':
    app = QApplication([])
    main = QMainWindow()

    w = ParameterEditor()
    w.newRow.connect(new_row)
    w.replaceRow.connect(replace_row)
    w.loadclicked.connect(load)
    w.setclicked.connect(set_params)
    w.changeclicked.connect(change)

    table = w.table()
    for name in ['moe', 'curly', 'shemp', 'laurel', 'hardy', 'stan', 'ollie']:
        table.add_row(name)

    main.setCentralWidget(w)

    main.show()
    app.exec()