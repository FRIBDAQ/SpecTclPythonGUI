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
    QPushButton, QMessageBox, QHBoxLayout, QVBoxLayout, QGridLayout)
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
      super().__init__()
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
    super().__init__(parent)
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


class  VectorFilterBar(QWidget):
  '''
    This is a widget of the form:
    +---------------------------------------+
    | [Update] [filter string] [clear]      |
    +---------------------------------------+
    
    
    The clear button is autonomously handed to load "*" in the
    filter string (QLineEdit) widget.
    
    Signals:
    
    update - the update button was clicked passed the current filter string.
  '''
  update = pyqtSignal(str)
  def __init__(self, *args) :
    '''
      Construction  
      Parameters 
        *args - passed uninterpreted to the QWidget constuctor.
    '''
    super().__init__(*args)
    
    self._layout = QHBoxLayout()   # Widgets laid out horizontally:
    self.setLayout(self._layout)
    
    self._update = QPushButton('Update', self)
    self._filter = QLineEdit('*', self)
    self._clear  = QPushButton('Clear', self);
    
    self._layout.addWidget(self._update)
    self._layout.addWidget(self._filter)
    self._layout.addWidget(self._clear)
    
    # Set internal signal handling:
    
    self._update.clicked.connect(self._emitUpdate)
    self._clear.clicked.connect(self._clearFilter)
    
  def getPattern(self): 
    '''
      Returns the contents of the filter string line edit.
    '''
    return self._filter.text()
  
  #-------------------- internal methods ---------------------------------
  
  def _emitUpdate(self) :
    # The update button got clicked.  We fetch the pattern and emit
    # update:
    
    self.update.emit(self._filter.text())
    
  def _clearFilter(self) :
    # The clear button was clicked.  Set the filter mask back to '*' 
    
    self._filter.setText('*')
    
    
class VectorWidget(QWidget):
  '''
    This megawidget combines the vector table view and
    vetor editor.   It autonously handles double clicks in the
    table to load the editor. Simiarly the cancel button on 
    the editor is autonomously handled to clear the editor.
    We also autonomou8seul handle the update signal from the
    filter bar and update the model with that filter string
    
    Signals:
      vectoredited - the Ok button was clicked on the edtor
      

  '''
  vectoredited = pyqtSignal()
  def __init__(self, model, *args) :
    '''
      Construction.
      Parameters:
         model - the module that will be used by the vector table.
         *args - passed uninterpreted to the QWidget constructor.
         
    '''
    super().__init__(*args)
    
    self._model  = model
    self._layout = QVBoxLayout()
    self.setLayout(self._layout)
    self._table  = VectorTableView(model, self)
    self._editor = VectorEditor(self)
    self._filter  = VectorFilterBar(self)
  
    self._layout.addWidget(self._editor)
    self._layout.addWidget(self._table)
    self._layout.addWidget(self._filter)
    
    
    #  Now the autonomously handled signals:
    
    self._table.onDoubleClick.connect(self._selectVector)
    self._editor.cancel.connect(self._clearEditor)
    self._filter.update.connect(self._newFilter)    
    # Relay the ok signal to vectoredited:
    
    self._editor.ok.connect(self.vectoredited)
    

    
    # Get get the table up to date:
    
    self.update()
  #-----------------------------  public  methods ---------------
  
  def update(self) :
    '''
      Update the model.
    '''

    self._model.load(self._filter.getPattern())
    
  def getEditor(self) :
    '''
      Return the data in the editor.  See VectorEditor.get  -- since we just call that.
    '''
    return self._editor.get()
  
    
  def clearEditor(self):
    ''' Clear the contents of the editor'''
    self._editor.clear()
  #--------------------------- autonomous signal handlers --------

  def _selectVector(self, row) :
    #  Load the selected vector into the editor:
    
    info = self._model.get(row)
    self._editor.load(info)
    
  def _clearEditor(self):
    # Clear the editor data and update the model.
    
    self.clearEditor()
    self.update()
  
  def _newFilter(self, pattern) :
    self.update() 
    
class VectorController:
  '''
    This controller links the signals not handled by the VectorWidget
    to the model and, application specific operations.
  '''
  
  def __init__(self, view, model, client):
    '''
    Parameters:
      view - is the VectorWidget, we will connect to signals in it.
      model - is the VectorParameterModel that links to the actual 
              vector data in the server and provides those data to the
              view.
      client- the server client.
           
    '''
    # First save the parameters for use within our methods.
    
    self._model = model
    self._view  = view
    self._client = client
    
    #  Connect to signals:
    
    view.vectoredited.connect(self._edit)
  
  def _edit(self):
    #  Handles requested changes of vector properties.
    #  We don't  bother to figure out what's changed but just
    #  assert all of the properties in the editor of the view
    #  we also ask the model to update so the table will reflect
    #  the changes.
    
    info = self._view.getEditor()
    
    name = info['name']
    
    # don't bother to do anything if there's no vector loaded.
    if name !=  '':
      try:
        low = float(info['low'])    
        high = float(info['high'])
        bins = int(info['bins'])
        units = info['units']
      except ValueError:
        # This happens if one of the conversions above fails.
        
        QMessageBox.warning(self._view, 'Value eror', 
          'Bad values in the editor. Be sure low, high are valid floats and bins a valid integer'
        )
        return
      
      # Update the server blindly for now:
      
      self._client.vector_setlow(name, low)
      self._client.vector_sethigh(name, high)
      self._client.vector_setbins(name, bins)
      self._client.vector_setunits(name, units)
      
      # clear the editor and update the model.
      # note that asking the view to run the update allows
      # it to apply its filter mask transparently.
      self._view.clearEditor()
      self._view.update()  
    
# Test code here:


if __name__ == "__main__":
  
  from rustogramer_client import rustogramer as rc
  from PyQt5.QtWidgets import QApplication, QMainWindow
  
  def edit() :
    info = main.getEditor()
    name = info['name']
    
    # don't bother to do anything if there's no vector loaded.
    if name !=  '':
      low = int(info['low'])    
      high = int(info['high'])
      bins = int(info['bins'])
      units = info['units']
      
      # Update the server blindly for now:
      
      c.vector_setlow(name, low)
      c.vector_sethigh(name, high)
      c.vector_setbins(name, bins)
      c.vector_setunits(name, units)
      
      # clear the editor and update the model.
      
      main.clearEditor()
      main.update()
  
  
  
      
  c = rc({'host': 'localhost', 'port': 8000})
  app = QApplication([])
  win = QMainWindow()
  
  model = VectorParameterModel(c)
  model.load()
  
  main = VectorWidget(model)
  main.vectoredited.connect(edit)
  
  win.setCentralWidget(main)
  win.show()
  
  app.exec()
  
  