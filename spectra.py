'''  This module provides the spectrum widget.  The Spectrum widget looks like this:

+--------------------------------+
|   Spectrum editor              |
+--------------------------------+
|  spectrum list                 |
+--------------------------------+

*   Where spectrum editor is an instance of spectrumeditor.Editor
*   Where spectrum list is an instance of SpectrumList.SpectrumList


'''

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QFrame,
    QApplication, QMainWindow, QSizePolicy, QMessageBox
)

from SpectrumList import (SpectrumList, SpectrumModel)
from spectrumeditor import Editor
from capabilities import set_client as set_cap_client
from ParameterChooser import update_model as load_parameters
from gatelist import common_condition_model
from  rustogramer_client import rustogramer as RClient
from rustogramer_client import RustogramerException
_client = None

def set_client(c):
    ''' Set the client used to interact with the server
    '''
    global _client
    _client = c


class SpectrumWidget(QWidget):
    def __init__(self, *args):
        global _client
        super().__init__(*args)

        
        load_parameters(_client)

        # assumption is that set_client has been called

        set_cap_client(_client)

        # two frames in a vbox layout in the widget, the top frame
        # contains the editor, the bottom the spectrum list.abs
        
        layout = QVBoxLayout()
        
        self._editor = Editor(self)
        self._editor.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        layout.addWidget(self._editor)

        
        self._listing = SpectrumList(self)
        layout.addWidget(self._listing)

        self._spectrumListModel = SpectrumModel()
        self._listing.getList().setModel(self._spectrumListModel)
        self._listing.getList().horizontalHeader().setModel(self._spectrumListModel)
        self._spectrumListModel.load_spectra(_client)


        self.setLayout(layout)

        # Connect to be able to update the view:

        self._editor.new_spectrum.connect(self._add_to_listing)
        self._editor.spectrum_deleted.connect(self._remove_from_listing)
        self._editor.clear_selected.connect(self._clear_selected)
        self._editor.clear_all.connect(self._clear_all)
        self._editor.delete_selected.connect(self._delete_selected)
        self._editor.gate_selected.connect(self._gate_selected)
        self._editor.ungate_selected.connect(self._ungate_selected)
        self._editor.load.connect(self._load_spectrum)

        self._listing.filter_signal.connect(self._filter_list)
        self._listing.clear_signal.connect(self._clear_filter)
        
        self._listing.getList().reload.connect(self._reload_spectrum)
        self._listing.getList().update.connect(self._update_spectrum)

    def _add_to_listing(self, new_name):
        # Get the definition:

        sdef = _client.spectrum_list(new_name)
        sdef = sdef ['detail']
        if len(sdef) == 1:
            self._spectrumListModel.addSpectrum(sdef[0])
    def _remove_from_listing(self, old_name):
        self._spectrumListModel.removeSpectrum(old_name)

    def _filter_list(self, mask):
        global _client
        self._spectrumListModel.load_spectra(_client, mask)
        common_condition_model.load(_client)

    def _clear_filter(self):
        global _client
        self._listing.setMask("*")
        self._filter_list("*")

    # internal slots:

    def _clear_selected(self):
        # Clear seleted spectra:

        spectra = self._listing.getSelectedSpectra()
        for name in spectra:
            _client.spectrum_clear(name)
    def _clear_all(self):
        # Clear all spectra

        _client.spectrum_clear('*')
    def _delete_selected(self):
        # Upon confirmation, delete selected spectra:
        spectra = self._listing.getSelectedSpectra()
        if len(spectra) == 0:
            return
        spectrum_list = ', '.join(spectra)
        dlg = QMessageBox(
            QMessageBox.Warning, 'Confirm',
            f'Are you sure you want to delete the spectra: {spectrum_list} ?',
            QMessageBox.Yes | QMessageBox.No, self
        )
        if dlg.exec() == QMessageBox.Yes:
            for s in spectra:
                _client.spectrum_delete(s)
                self._remove_from_listing(s)
    def _gate_selected(self):
        global _client
        spectra = self._listing.getSelectedSpectra()
        gate    = self._editor.selected_gate()
        if len(spectra) == 0 or gate.isspace():
            return   
        for spectrum in spectra:
            _client.apply_gate(gate, spectrum)
        # Update the list:
        self._spectrumListModel.load_spectra(_client, self._listing.mask())
    def _ungate_selected(self):
        global _client
        spectra = self._listing.getSelectedSpectra()
        if len(spectra) == 0:
            return               # So we don't need to regen list.
        for spectrum in spectra:
            _client.ungate_spectrum(spectrum)
        self._spectrumListModel.load_spectra(_client, self._listing.mask())
    def _load_spectrum(self):
        #  Load the single selected spectrum into the editor.

        # There must be exactly one spectum selected:

        selected = self._listing.getSelectedDefinitions()
        if not len(selected) == 1:
            dlg = QMessageBox(
                QMessageBox.Warning, 'Single selection required',
                'You must select exactly one spectrum from the list to load the editor',
                QMessageBox.Ok
            )
            dlg.exec()
            return
        spectrum = selected[0]
        self._editor.load_editor(spectrum)
    
    def _update_spectrum(self, row):
        
        
        # Handle update clicks.  the spectsrum definition
        # is read and the binning updated from the table values.
        # Note this destroys and re-creates the table.
        
        try:
            newdef = self._spectrumListModel.getRow(row)
        except:
            QMessageBox.warning(self, 'Bad axis specifications',
                'One of the axis specifications is not numeric fix that and click update again.'
            )
            return
        print(f'replacing {row}')
        print("with ", newdef)
        # what we do is very spectrum type dependent but we will
        # need to delete the old specturm:
        
        name = newdef[0]
        type = newdef[1]
        olddef = _client.spectrum_list(name)['detail']
        print("Old definition", olddef)
        chtype = self._editor.channeltype_string()
        try:
            if type == '1':
                _client.spectrum_delete(name)
                _client.spectrum_create1d(name, newdef[2], newdef[3], newdef[4], newdef[5], chtype)
            elif type == '2':
                _client.spectrum_delete(name)
                _client.spectrum_create2d(name, newdef[2], newdef[6], 
                    newdef[3], newdef[4], newdef[5], newdef[7], newdef[8], newdef[9], chtype
                )
            elif type == 'g1':
                # Construct the parameters list - strip leading/trailing whitespace, just in case.
                parameters = newdef[2].split(',')
                parameters = [x.strip() for x in parameters]
                
                _client.spectrum_delete(name)
                _client.spectrum_createg1(name, parameters, newdef[3], newdef[4], newdef[5], chtype)
            elif type == 'g2':
                # There's really only one parameters list even though it shows as x and y:
            
                
                _client.spectrum_delete(name)
                _client.spectrum_createg2(name, parameters,
                    newdef[3], newdef[4], newdef[5], newdef[7], newdef[8], newdef[9], chtype)
            elif type == 'gd':
                parameters = newdef[2].split(',')
                xpars = [x.strip() for x in parameters]
                parameters = newdef[6].split(',')
                ypars = [x.strip() for x in parameters]
                
                _client.spectrum_delete(name)
                _client.spectrum_creategd(name, xpars, ypars,
                    newdef[3], newdef[4], newdef[5], newdef[7], newdef[8], newdef[9], chtype
                )
            elif type == 's':
                parameters = newdef[2].split(',')
                parameters = [x.strip() for x in parameters]
                
                _client.spectrum_delete(name)
                _client.spectrum_createsummary(name, parameters, newdef[7], newdef[8], newdef[9], chtype)
            elif type == 'm2':
                parameters = newdef[2].split(',')
                xpars = [x.strip() for x in parameters]
                parameters = newdef[6].split(',')
                ypars = [x.strip() for x in parameters]
                
                _client.spectrum_delete(name)
                _client.spectrum_create2dsum(name, xpars, ypars, 
                    newdef[3], newdef[4], newdef[5], newdef[7], newdef[8], newdef[9], chtype
                )
            else:
                # Unsupported...just reload what it is now.
                self._reload_spectrum(row)
        except RustogramerException as e:
            QMessageBox.warning(
                self, 'Unable to replace spectrum',
                f'{e}  Original spectrum may have been deleted'
            )
            self._filter_list(self._listing.mask())    # So the spectrum vanishes if it did.
            return     # In  case more code is added below.
        # Try to apply any old gate to the new spectrum
        
        if newdef[10] is not None:
            try:
                _client.apply_gate(newdef[10], name)
            except RustogramerException as  e:
                QMessageBox.warning(
                    self, 'Unable to regate spectrum',
                    f'Unable to re-establish gate on {name}: {e}, {name} will be ungated.'
                )
                self._filter_list(self._listing.mask())
                
                # IF there's more codee, can continue.
        
    def _reload_spectrum(self, row):
        current = self._spectrumListModel.getRow(row)
        
        # Get the name of the spectrum ask for its properties and then load it back into that row:
        
        name = current[0]
        info = _client.spectrum_list(name)['detail']
        
        # It's remotely possible (multi clients) the spectrum was deleted - in which update
        # since the whole world could have shifted beneath us:
        
        if len(info) == 0:
            self._filter_list(self._listing.mask())   
        else:
            self._spectrumListModel.replaceRow(row, info[0])
        
    
    def editor(self):
        return self._editor



def test(host, port):
    ''' Exercise this module host.
     *  host = host running a server.
     *  port = port on which that server is listening for connections.
     '''
    set_client(RClient({'host': host, 'port': port}))
    app = QApplication([])

    c   = QMainWindow()
    view = SpectrumWidget(c)
    c.setCentralWidget(view)

    c.show()
    app.exec()

# For test with debugger:

if __name__ == '__main__':
    test('localhost', 8000)