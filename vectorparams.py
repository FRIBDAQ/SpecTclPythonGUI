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
  VectorParameterView  - The table that views the VectorParmaeterModel
  VectorEditorView         - Megawidget that has the parameter view and
                        controls to allow vector properties to be edited.

  VectorEditorController - handles events in the various views mediating
                     between them and the model and between subviews and views.
                     
                     
'''
from PyQt5.QtGui import QStandardItemModel
from PyQt5.QtWidgets import QAbstractItemView,  QTableView
from PyQt5.QtCore import pyqtSignal

class VectorParameterModel(QStandardItemModel) :
    '''
      VectorParmameterModel holds and, as needed, updates
      the data shown in the parameter table.
    '''
    pass
