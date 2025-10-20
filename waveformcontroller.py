'''
    This module provides a controller which will be used
    to connect the waveform view to the ReST client.
    It handles view signals and handles updating the view
'''
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtWidgets import QAbstractItemView
class WaveformController:
    def __init__(self, view, client):
        '''
            view - the WaveformViewTab instance to control
            client - the RestClient instance to use to get waveform data
        '''
        self._view = view
        self._client = client
        self._listmodel = QStandardItemModel()
        self._load_waveform_list()
        
        self._metadatamodel = QStandardItemModel()
        
        
        
        # Connect view signals to slots:
        self._view.waveform_selected.connect(
            self._waveform_selected
        )
        self._view.add_metadata_row.connect(
            self._add_metadata
        )
        self._view.commit_metadata.connect(
            self._update_waveform
        )
        self._view.refresh_plot.connect(self._update_plot)
        
        
    
    def _load_waveform_list(self):
        ''' Load the waveform list from the server and set
            the model in the view.
        '''
        waveform_defs = self._client.waveform_list()
        waveform_names = [wf['name'] for wf in waveform_defs['detail']]
        for name in waveform_names:
            item = QStandardItem(name)
            self._listmodel.appendRow(item)
        self._view.set_waveforms(self._listmodel)
        
    def _load_metadata_model(self, metadata):
        ''' Load the metadata model from the given metadata dict.
            metadata - the metadata dict from the server.
            Note that only the values are editable.
        '''
        self._metadatamodel.clear()
        self._metadatamodel.setHorizontalHeaderLabels(['Key', 'Value'])
        for key, value in metadata.items():
            key_item = QStandardItem(str(key))
            key_item.setEditable(False)
            
            value_item = QStandardItem(str(value))
            value_item.setEditable(True)
            self._metadatamodel.appendRow([key_item, value_item])
    # Internal slots.
    def _waveform_selected(self, waveform_id):
        ''' Slot called when a waveform is selected in the view.
            waveform_id - the string id of the selected waveform.
        '''
        # Get the waveform description from the server and
        # load the metadata:
        
        waveform_info = self._client.waveform_list(waveform_id)
        info = waveform_info['detail'][0]
        self._load_metadata_model(info['metadata'])
        self._view.set_metadata_waveform(info['name'], info['samples'], self._metadatamodel)
    
    def _add_metadata(self):
        ''' Add a metadata row with editable name/value'''
        
        key = QStandardItem('')
        value = QStandardItem('')
        key.setEditable(True)
        value.setEditable(True)
        self._metadatamodel.appendRow([key, value])
        
        
    def _update_waveform(self):
        ''' Called when the metadata editor part of the view signals the commit button was pushed.'''
        
        (name, samples) = self._view.get_metadata_info()
        
        # PUll the metadata out of the model... if there are empty keys we ignore them 
        # those represent added rows that were not filled in.  Metadata can have "" values.
        
        metadata = {}
        for i in range(0, self._metadatamodel.rowCount()):
            keyItem = self._metadatamodel.item(i, 0)
            valItem = self._metadatamodel.item(i, 1)
            key = keyItem.text()
            if key:             # Checks for non None and not empty (both are falsy).
                val = valItem.text()
                metadata[key] = val
        
        # Now update the waveform: first the samples then the metadata:
        
        self._client.waveform_resize(name, samples)
        self._client.waveform_set_metadata(name, metadata)
        
    def _update_plot(self):
        ''' Called to update the plot - get the name, get the waveform and plot it. '''
        
        (name, _) = self._view.get_metadata_info()  # Don't care about the metadata.
        waveform_data = self._client.waveform_get(name)['detail'][0]   # first waveform.
        
        # waveform_data is (name, points, rank) so:
        
        self._view.plot(name, waveform_data['samples'])
        