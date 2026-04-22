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
from PyQt5.QtWidgets import QAbstractItemView,  QTableView
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
        self.removeROws(0, self.rowCount())
      
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
   
# Test code here:


if __name__ == "__main__":
  
  from rustogramer_client import rustogramer as rc
  from PyQt5.QtWidgets import QApplication, QMainWindow
  
  def selectItem(row) :
    print("Selected ", row)
    info = model.get(row)
    print(info)
  
  c = rc({'host': 'localhost', 'port': 8000})
  app = QApplication([])
  win = QMainWindow()
  
  model = VectorParameterModel(c)
  model.load()
  view = VectorTableView(model)
  
  view.onDoubleClick.connect(selectItem)
  win.setCentralWidget(view)
  win.show()
  app.exec()
  
  