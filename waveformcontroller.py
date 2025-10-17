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
        self._metadatamodel = QStandardItemModel()
        
        # Connect view signals to slots:
        self._view.waveform_selected.connect(
            self._waveform_selected
        )
        
        # Load the waveform list:
        self._load_waveform_list()
    
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
    