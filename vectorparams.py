'''
  This module provides a model and view for vector parameters.
  The view is a table with the colunns
  name - name of the vector parameter.
  low  - advisory low limit for the parameter.
  high - advisory high limit for the parameter.
  bins - advisory binning for the parameter.
  units - units of measure for the parameter.
  
  The main classes we have are:
  
  VectorParameterModel - instantiated on a client and responsible
    for loading the data that will be viewed by:
  VectorTableView      - The table that views the VectorParmaeterModel
  VectorEditor         - Widget that can be loaded with a vector and its properties
                         and edited.
  VectorWidget         - Megawidget of the vector parameter view and editor.
  VectorEditorController - handles events in the various views mediating
                     between them and the model and between subviews and views.
                     
                     
'''
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtWidgets import (QTableView, QWidget, QLineEdit, QFrame,
    QPushButton, QHBoxLayout, QVBoxLayout, QGridLayout)
from PyQt5.QtCore import pyqtSignal
from PyQt5.Qt import *

class VectorParameterModel(QStandardItemModel) :
    '''
      VectorParmameterModel holds and, as needed, updates
      the data shown in the parameter table.
    '''
    def __init__(self, client) :
      '''
        Parmameters:
          client - a rustogramer client that will be used to
                   load the model with data.  See
                   referesh - which clears the model and
                   updates it.
                   
      '''
      super(VectorParameterModel, self).__init__()
      self._client = client
      self.setHorizontalHeaderLabels(['Name', 'Low', 'High', 'Bins', 'Units'])
    
    def load(self, filter='*') :
      ''' 
        Loads the model with data. Only the vectors that 
        have names that match the filter glob pattern are
        loaded into the model.
      '''
      vectors = self._client.vector_list(filter)['detail']
      
      # Clear the model if it has data:
      if self.rowCount() > 0:
        self.removeRows(0, self.rowCount())
      
      #  Stuff the row:
      
      for vector in vectors:
        # Make the items.
        
        name = QStandardItem(vector['name'])
        low  = QStandardItem(vector['low'])
        high = QStandardItem(vector['high'])
        bins = QStandardItem(vector['bins'])
        units = QStandardItem(vector['units'])
        
        # Turn off editing and then append the row:
        
        items = [name, low, high, bins, units]
        clearflags = Qt.ItemIsEditable | Qt.ItemIsDragEnabled | Qt.ItemIsDropEnabled | Qt.ItemIsUserCheckable
        for item in items:
          flags = item.flags() & (~clearflags)   # Mask of what we don't want.
          item.setFlags(flags)
          
        self.appendRow(items)
        
    def get(self, row):
      '''
        Returns the item at the row as a dict with the same indices/values
        as a vector in the ReST interface:
        * 'name' - name of the vector.
        * 'low'  - advisory low limit
        * 'high' - advisory high limit.
        * 'bins' - advisory bin count.
        * 'units' - units of measure.
        Note all  values are strings!!!
        
        Parameters:
          row - row to fetch.
        Raises:
          IndexError if row is out of range.
      '''
      if row < 0 or row >= self.rowCount() :
        raise IndexError(f'The row index {row} is out of range')
      name = self.item(row, 0).text()
      low  = self.item(row, 1).text()
      high = self.item(row, 2).text()
      bins = self.item(row, 3).text()
      units= self.item(row,4).text()
      
      return {
        'name' : name, 'low' : low, 'high' : high, 'bins' : bins, 'units' : units
      }
      
      
class VectorTableView(QTableView) :
  '''
    This widget  is a table view that shows
    a VectorParameterModel.  It can signal double clicking
    on a row of the model, 
    
    Signals:
       onDoubleClick - When an item in the row is double clicked.  
                       the signal is passed the row number of the
                       double click.  Presumably, the handler
                       has access to the model and can access data at that row.
  '''
  onDoubleClick = pyqtSignal(int)
  def __init__(self, model, parent=None):
    super(VectorTableView, self).__init__(parent)
    self.setModel(model)
    
    #  Map the doubleClicked signal to onDoubleClick via
    #  our handler that fetches the clicked row:
    
    self.doubleClicked.connect(self._onDoubleClick)

  # Private methods:
  
  ## _onDoubleCLick
  #    Handles double clicks by figuring out the row
  #    and emitting onDoubleClick:
  #    We get passed the QModelIndex in wich the doubleclick
  #    happened.
  def _onDoubleClick(self, index) : 
    self.onDoubleClick.emit(index.row())
        
class VectorEditor(QWidget) :
  '''
    This widget allows users to edit a vector.  Visual appearance is:
    +--------------------------------------+
    |   Name    Low   High  Bins   Units   | 
    |  <name>  [low]  [hi ] [bins] [units] |
    +--------------------------------------+
    |    [ OK ]  [Cancel]                  |
    +--------------------------------------+
    
    The <name> is a non-editable name of the vector, the items in
    square brackets are entries that are editable.
    
    Signals:
      ok     - The OK button was clicked.
      cancel - the Cancel button was clicked.
  '''
  ok     = pyqtSignal()
  cancel = pyqtSignal()
  
  def __init__(self, *args) :
    print("Initializing editor")
    super().__init__(*args)
    
    
    self._widgetlayout = QVBoxLayout()  
    self.setLayout(self._widgetlayout)
    
    # The top widget contains the labels and edits and
    # live in a frame to support the line between them and
    # the buttons:
  
      
    
    self._editor = QFrame(self)
    self._editor.setFrameShape(QFrame.Box)
    self._editor.setLineWidth(2)
  
    self._editorlayout = QGridLayout()
    
    
    # The labels:
    self._editor_nameLabel = QLabel("Name", self._editor)
    self._editor_lowLabel  = QLabel("Low", self._editor)
    self._editor_highLabel = QLabel("High", self._editor)
    self._editor_binsLabel = QLabel("Bins", self._editor)
    self._editor_unitsLabel= QLabel("UNits", self._editor)
    self._editorlayout.addWidget(self._editor_nameLabel, 0,0)
    self._editorlayout.addWidget(self._editor_lowLabel,  0,1)
    self._editorlayout.addWidget(self._editor_highLabel, 0,2)
    self._editorlayout.addWidget(self._editor_binsLabel, 0,3)
    self._editorlayout.addWidget(self._editor_unitsLabel, 0,4)
    
    # THe editor itself, note that the name is not editable and
    # therefore is a label. THe others are lineentries.
  
    self._editor_name = QLabel(self._editor)   # We don't know the contents yet.
    self._editor_low  = QLineEdit(self._editor)  
    self._editor_high = QLineEdit(self._editor)
    self._editor_bins = QLineEdit(self._editor)
    self._editor_units= QLineEdit(self._editor)
    self._editorlayout.addWidget(self._editor_name,  1,0)
    self._editorlayout.addWidget(self._editor_low,   1,1)
    self._editorlayout.addWidget(self._editor_high,  1,2)
    self._editorlayout.addWidget(self._editor_bins,  1,3)
    self._editorlayout.addWidget(self._editor_units, 1,4)
    
    self._editor.setLayout(self._editorlayout)
    
    # The widget is a vertical box with the editor on top
    # and a horizontal row of buttons on the bottom.
    
    
    self._widgetlayout.addWidget(self._editor)
    self.setLayout(self._widgetlayout)
    
    self.setLayout(self._widgetlayout)
    
    
    # Now the buttons.
    
  
    buttonlayout = QHBoxLayout()
    self._ok     = QPushButton("Ok", self)
    self._cancel = QPushButton("Cancel", self)
    buttonlayout.addWidget(self._ok)
    buttonlayout.addWidget(self._cancel)
    self._widgetlayout.addLayout(buttonlayout) 
    
    # map signals  for the buttons.
    
    self._ok.clicked.connect(self.ok)
    self._cancel.clicked.connect(self.cancel)

  def load(self, vector):
    '''
      retrieves the editor contents with the data from 
      the vector description map passed.
      
      Parameters:
         vector - a map with the indices (all values are text).
          * 'name' - name of the vector.
          * 'low'  - advisory low limit
          * 'high' - advisory high limit.
          * 'bins' - advisory bin count.
          * 'units' - units of measure.
          
    '''
    self._editor_name.setText(vector['name'])
    self._editor_low.setText(vector['low'])
    self._editor_high.setText(vector['high'])
    self._editor_bins.setText(vector['bins'])
    self._editor_units.setText(vector['units'])
    
  def get(self):
    '''
      Returns:
         A description of the vector that is currently in the editor.
         It is up to the caller to do any validation (e.g. low, high, units integers
         low < high?) etc 
         The return value is a dict withthe keys described in load.
         Note that the values are all textual.
         
    '''
    name  = self._editor_name.text()
    low   = self._editor_low.text()
    high  = self._editor_high.text()
    bins  = self._editor_bins.text()
    units = self._editor_units.text()
    
    return {
      'name' : name, 'low' : low, 'high' : high,
      'bins' : bins, 'units' : units
    }
    
  def clear(self):  
    '''
      clear the contents of the editor
    '''
    self._editor_name.setText('')
    self._editor_low.setText('')
    self._editor_high.setText('')
    self._editor_bins.setText('')
    self._editor_units.setText('')
   
# Test code here:


if __name__ == "__main__":
  
  from rustogramer_client import rustogramer as rc
  from PyQt5.QtWidgets import QApplication, QMainWindow
  
  def selectItem(row) :
    
    info = model.get(row)
    editor.load(info)
    
  def ok() :
    info = editor.get()
    name = info['name']
    low  = int(info['low'])
    high = int(info['high'])
    bins = int(info['bins'])
    units = info['units']
    
    c.vector_setlow(name, low)
    c.vector_sethigh(name, high)
    c.vector_setbins(name, bins)
    c.vector_setunits(name, units)
    
    editor.clear()
    
    model.load()     #That updates the table.
  
  
  def cancel() :
    editor.clear()
      
  c = rc({'host': 'localhost', 'port': 8000})
  app = QApplication([])
  win = QMainWindow()
  
  model = VectorParameterModel(c)
  model.load()
  view = VectorTableView(model)
  view.onDoubleClick.connect(selectItem)
  
  editor = VectorEditor()
  editor.ok.connect(ok)
  editor.cancel.connect(cancel)
  
  main = QWidget()
  layout = QVBoxLayout()
  main.setLayout(layout)
  layout.addWidget(view)
  layout.addWidget(editor)
  
  
  win.setCentralWidget(main)
  win.show()
  
  app.exec()
  
  