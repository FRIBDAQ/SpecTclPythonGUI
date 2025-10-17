'''
  This module provides the waveform view tab for the GUI if the 
  server supports waveforms.
  The final structure of this consists of the following elements:
  
  A waveform list - containing the list of existing waveforms.  
  This is normally static; waveforms are created  either in the 
  C++ code or in SpecTclRC.tcl. Typically.
  
  A waveform metdata editor - this can be loaded by selecting a waveform 
  from the waveform list.
  
  A waveform viewer that allows a plot to be created from the currently
  selected waveform.
  
  We just provide the view and slots to which a controller can connect
  to perform the actual work with the server as the model.
  
'''

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QLineEdit, QPushButton, QListView)

from PyQt5.QtCore import  pyqtSignal


class WaveformListWidget(QWidget):
    '''
        THis widget provides a listview which allows the user
        to select from some waveforms.
        
        Methods:
            set_model -sets the model with the waveforms to display
        Signals:
            waveform_selected(waveform_id) - emitted when a waveform
                is selected from the list.  The slot is passed the
                string name of the selected waveform.  This is emitted
                on a double click in the box.
            
    '''
    def __init__(self, parent=None):
        super(WaveformListWidget, self).__init__(parent)
        
        self._layout = QVBoxLayout(self)
        self.setLayout(self._layout)
        
        self._label = QLabel("Waveforms:", self)
        self._layout.addWidget(self._label)
        
        self._listview = QListView(self)
        self._layout.addWidget(self._listview)
        
        self._listview.doubleClicked.connect(self._waveform_double_clicked)
    
    # Public methods:
    
    def set_model(self, model):
        ''' Set the model for the waveform list.
            model - a QAbstractListModel derived class that provides
                    the waveform list.
        '''
        self._listview.setModel(model)
    
    # Private slots:
    
    def _waveform_double_clicked(self, index):
        ''' Slot called when a waveform is double clicked in the list.
            Emits the waveform_selected signal with the waveform id.
        '''
        waveform_id = index.data()    # Might be right...have to try it.
        self.waveform_selected.emit(waveform_id)
        
        

class WaveformViewTab(QWidget):
    ''' The waveform view tab.  This lays out the three subwidgets defined above.
    '''
    waveform_selected = pyqtSignal(str)
    def __init__(self, parent=None):
        super(WaveformViewTab, self).__init__(parent)
        
        self._layout = QVBoxLayout(self)
        self.setLayout(self._layout)
        
        self._toplayout = QHBoxLayout(self)
        self.listing = WaveformListWidget(self)
        self._toplayout.addWidget(self.listing)
        self._layout.addLayout(self._toplayout)