'''
    This module provides a controller which will be used
    to connect the waveform view to the ReST client.
    It handles view signals and handles updating the view
'''
from PyQt5.QtGui import QStandardItemModel, QStandardItem
class WaveformController:
    def __init__(self, view, client):
        '''
            view - the WaveformViewTab instance to control
            client - the RestClient instance to use to get waveform data
        '''
        self._view = view
        self._client = client
        self._model = QStandardItemModel()
        
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
            self._model.appendRow(item)
        self._view.set_waveforms(self._model)
    
    def _waveform_selected(self, waveform_id):
        ''' Slot called when a waveform is selected in the view.
            waveform_id - the string id of the selected waveform.
        '''
        # Get the waveform data from the server:
        
        print("Waveform selected:", waveform_id)
    