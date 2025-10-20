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
                             QLabel, QLineEdit, QPushButton, QListView,
                             QTableView)
from PyQt5.QtCore import  pyqtSignal

import matplotlib
matplotlib.use('Qt5Agg')


from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure

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
    waveform_selected = pyqtSignal(str)
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
        

class WaveformDataEditor(QWidget):
    '''
        WaveformMetaDataEditor
        This widget provides a list of the metadata fields for a waveform
        and allows you to modify them or add to them.
        It consists of:
        
        A header at the top that will contain the name of a waveform and an entry
        for the number of samples in the waveform.
        
        A table containing metadata names and values.  The valus are editable.
        The names are not.
        A button at the bottom of the table to allow a new metadata item to be
        added to the table.
        A commit button that fires a signal to commit the changes to the server.
        
        Methods:
                set_name - sets the name field of the editor.
                name     - retrives the name field of the editor.
                set_samples - sets the number of samples field value.
                samples - retrievs the number of sampls field value.
                set_table_model - sets the model for the table.
            Signals:
                commit_changes() - emitted when the commit button is pressed.
                add_row()        - Emitted when the add row button was clicked.
        
    '''     
    commit_changes = pyqtSignal()
    add_row        = pyqtSignal()
    def __init__(self, parent=None):
        super(WaveformDataEditor, self).__init__(parent)
        
        self._layout = QVBoxLayout(self)
        self.setLayout(self._layout)
        
        # Header layout:
        self._header_layout = QHBoxLayout(self)
        self._layout.addLayout(self._header_layout)
        
        self._name_label = QLabel("Waveform Name:", self)
        self._header_layout.addWidget(self._name_label)
        self._name_edit = QLineEdit(self)
        self._header_layout.addWidget(self._name_edit)
        
        self._samples_label = QLabel("Number of Samples:", self)
        self._header_layout.addWidget(self._samples_label)
        self._samples_edit = QLineEdit(self)
        self._header_layout.addWidget(self._samples_edit)
        
        # Table would go here...
        
        self._table = QTableView(self)
        self._layout.addWidget(self._table)
        
        # Add row button.
        
        self._add_row_button  = QPushButton("Add Row", self)
        self._layout.addWidget(self._add_row_button)
        self._add_row_button.clicked.connect(self.add_row)
        
        # Commit button:
        self._commit_button = QPushButton("Commit Changes", self)
        self._layout.addWidget(self._commit_button)
        
        self._commit_button.clicked.connect(self.commit_changes)
    
    # Public methods:
    
    def set_name(self, name):
        ''' Set the waveform name in the editor.
            name - the waveform name string.
        '''
        self._name_edit.setText(name)
    
    def name(self):
        ''' Get the waveform name from the editor.
            returns - the waveform name string.
        '''
        return self._name_edit.text()
    
    def set_samples(self, samples):
        ''' Set the number of samples in the editor.
            samples - the number of samples (int).
        '''
        self._samples_edit.setText(str(samples))
    
    def samples(self):
        ''' Get the number of samples from the editor.
            returns - the number of samples (int).
        '''
        return int(self._samples_edit.text())
    
    def set_table_model(self, model):
        ''' Set the model for the metadata table.
            model - a QAbstractTableModel derived class that provides
                    the metadata.
        '''
        self._table.setModel(model)

class PlotWidget(FigureCanvasQTAgg):
    ''' 
        Encapsulates the magic needed to use matplottlib to plot a waveform.
        Methods:
           plot - erases any prior waveform plot and puts in new points.
           set_title - set plot title
    '''       
    def __init__(self, parent=None):
        self._fig=Figure()
        self._axis=None
        super().__init__(self._fig)
        
    def plot(self, samples):
        '''
            If there is an axis, remove it... then add a new one
            and plot in it.
        '''
        if self._axis is not None:
            self._fig.delaxes(self._axis)
        
        # make a new axis and plot in it.
        # note we need to make the xpts. the ypts are the samples.
        
        self._axis = self._fig.add_subplot(111, anchor='C')
        
        self._axis.plot(samples)
        self.draw()
    def set_title(self, text):
        '''
           Set figure title text (e.g. waveform name.)
        '''
        self._fig.suptitle(text)
    
class WaveformPlot(QWidget) :
    '''
        This widget provides a plot widget for viewing waveforms.  It consists of
        a matplotlib canvas in which the plot is generated and updated and
        a button labeled refresh that is, initially disabled (plots can only
        be updated once the enclosing widget has selected a waveform in the
        larger scheme of things.
        
        Methods:
           enable  - enable the update method.
           plot    - Provides a waveform to the plot.
    '''
    refresh = pyqtSignal()                  # Refresh clicked.
    
    def __init__(self, parent=None):
            super(WaveformPlot, self).__init__(parent)
            
            # Layout the widget with the plot on top and the disabled
            # Refresh button on the bottom:
            
            self._layout = QVBoxLayout(self)
            self.setLayout(self._layout)
            
            # The plot     
            
            self._plot = PlotWidget()
            self._layout.addWidget(self._plot)
            
            # The push button and signal relay:
            
            self._button = QPushButton ("Refresh", self)
            self._button.setDisabled(True)
            self._button.clicked.connect(self.refresh)
            self._layout.addWidget(self._button)

    def plot(self, name,  samples):
        '''
          Plot a waveform in self._plot. 
        '''
        self._plot.plot(samples)
        self._plot.set_title(name)
        
    def enable(self):
        ''' turn on the refresh button: 
        '''
        self._button.setDisabled(False)
                

class WaveformViewTab(QWidget):
    ''' The waveform view tab.  This lays out the three subwidgets defined above.
        Methods:
            set_waveforms - sets the waveforms that are to be displayed in the list (model).
            set_metadata_waveform - sets the metadata editor.
            get_metadata_info  - Gets data from the meatdata editor.
            plot          - Plot a waveform.
        Signals:
            waveform_selected(waveform_id) - emitted when a waveform is selected from the list.
               via a double click.. this just relays the signal from the waveform list widget.
            commit_metadata commit the meatadata of the current waveform.
            add_meatadata_row - add a row to the metadata model.
            refresh_plot      - User clicked the plot refresh button. It is expected the
                    plot method will be called.
    '''
    
    waveform_selected = pyqtSignal(str)
    commit_metadata   = pyqtSignal()
    add_metadata_row  = pyqtSignal()
    refresh_plot      = pyqtSignal()
    
    def __init__(self, parent=None):
        super(WaveformViewTab, self).__init__(parent)
        
        self._layout = QVBoxLayout(self)
        self.setLayout(self._layout)
        
        # Waveform selector
        
        self._toplayout = QHBoxLayout(self)
        self.listing = WaveformListWidget(self)
        self._toplayout.addWidget(self.listing)
        
        # Metadata editor...disabled until loaded.
        
        self._metadata_editor = WaveformDataEditor(self)
        self._metadata_editor.setDisabled(True)
        self._toplayout.addWidget(self._metadata_editor)
        self._metadata_editor.commit_changes.connect(
            self.commit_metadata
        )       # Relay the signal.
        self._metadata_editor.add_row.connect(
            self.add_metadata_row
        )
        
        # Add the top part of the editor.
        
        self._layout.addLayout(self._toplayout)
        
        self.listing.waveform_selected.connect(self._waveform_selected)
        
        # Add the plot widget on the bottom:
        
        self._plot = WaveformPlot(self)
        self._layout.addWidget(self._plot)
        self._plot.refresh.connect(self.refresh_plot)
    
    # Public methods:
    
    def set_waveforms(self, model):
        ''' Set the waveforms to be displayed in the list.
            model - a QAbstractListModel derived class that provides
                    the waveform list.
        '''
        self.listing.set_model(model)
        
    def set_metadata_waveform(self, name, samples, model): 
        ''' Set the metadata editor to display the given waveform.
            name - the waveform name (string).
            samples - the number of samples (int).
            model - a QAbstractTableModel derived class that provides
                    the metadata.
        '''
        self._metadata_editor.set_name(name)
        self._metadata_editor.set_samples(samples)
        self._metadata_editor.set_table_model(model)
        self._metadata_editor.setDisabled(False)
        self._plot.enable()
    
    def get_metadata_info(self):
        ''' Get the metadata info from the editor.
            returns - a tuple (name, samples) where
                      name is the waveform name (string)
                      samples is the number of samples (int).
            The assumption is that caller already has access to the
            metadata model.
        '''
        name = self._metadata_editor.name()
        samples = self._metadata_editor.samples()
        return (name, samples)
    
    def plot(self, name, samples):
        ''' delegates to the waveform plotter: '''
        self._plot.plot(name, samples)
        
    # Private slots:
    
    def _waveform_selected(self, waveform_id):
        ''' Slot called when a waveform is selected in the list.
            Emits the waveform_selected signal.
        '''
        self.waveform_selected.emit(waveform_id)
    