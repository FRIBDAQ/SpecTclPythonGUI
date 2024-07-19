''' This file implements the controller for the parameter editor.
   it is connected to the various signals in the editor to 
   provide so-called business logic for the editor, that connects it to 
   actions requested of the server.
'''
import ParameterChooser
import parameditor
import spectrumeditor
from rustogramer_client import RustogramerException
from ParameterChooser import update_model
from PyQt5.QtWidgets import (QApplication, QMainWindow, QMessageBox, QDialog)
class ParameterController:
    ''' Slots:
        * new_row  - add the current parameter as a new row.
        * replace_row - Replace the 'current' row with the parameter.
        * load     - Load selected rows with updated server info.
        * set_params - set selected rows as new parameter metadata.
        * change_spectra - Change relevant spectra so that new axes
                      definitions from parameter metadata will be used.
    '''
    def __init__(self, view, client, spectrum_view):

        #  Save the view and client to support signal handling.
        #

        self._view = view
        self._client = client
        self._spectrum_view = spectrum_view

        #  Connect to the view's signals:

        view.newRow.connect(self.new_row)
        view.replaceRow.connect(self.replace_row)
        view.remove.connect(self.remove_selected)
        view.reload.connect(self.refresh_parameters)
        view.loadclicked.connect(self.load)
        view.setclicked.connect(self.set_params)
        view.changeclicked.connect(self.change_spectra)
    
    # slots:

    def new_row(self):
        info = self._get_parameter_metadata()
        
        if info is not None:
            self._view.table().add_row(
                info['name'], info['low'], info['hi'], info['bins'],
                info['units']
            )
            
    def replace_row(self):
        row = self._view.table().currentRow()
        if row == -1:
            return               # No current row.
        info = self._get_parameter_metadata()
        self._view.table().set_row(
            row,
            info['name'], info['low'], info['hi'], info['bins'],
            info['units']
        )
    def load(self):
        rows = self._view.table().selected_rows()
        for row in rows:
            name = self._view.table().get_row(row)['name']
            info = self._get_metadata(name)
            if info is not None:
                self._view.table().set_row(
                    row,
                    info['name'], info['low'], info['hi'], info['bins'],
                    info['units']
            )
    def remove_selected(self):
        table = self._view.table()
        # Sort descending so removing does not change indices:
        remove_rows = table.selected_rows()
        remove_rows.sort(reverse=True)
        for r in remove_rows:
            table.delete_row(r)

        
    def refresh_parameters(self):
        update_model(self._client)

    def set_params(self):
        #  Note we need to worry about 'arrays'.
        for row in self._view.table().selected_rows():
            info = self._view.table().get_row(row)
            names = self._make_names(info['name'])
            for name in names :
                self._client.parameter_modify(name, info)

    def change_spectra(self):
        # We need to make a list of spectra to be modified so we
        # can ask the user which ones to change.

        modified_list = self._get_spectra_to_modify()
        for item in modified_list:
            self._modify_spectrum(item)


    # utilities:

    def _get_parameter_metadata(self):
        # We don't worry about multiple matches but we do worry
        # about no matches - returning None.
        name = self._view.parameter()
        
        if name is None or (name == '') or name.isspace():
            return None
        return self._get_metadata(name)
        
    def _get_metadata(self, name):
        reply = self._client.parameter_list(name)
        if len(reply['detail']) == 0:
            return None
        return reply['detail'][0]
    def _make_names(self, template):
        #  Either return the name or the array based on this
        #  template if array is checked:

        if self._view.array():
            pattern_path =  (template.split('.')[:-1])
            pattern_path.append('*')
            pattern = '.'.join(pattern_path)
            
            results = self._client.parameter_list(pattern)['detail']
            return [x['name'] for x in results]

        else:
            return [template]
    def _get_spectra_to_modify(self):
        # Let's save the parameter defs once so we don't need to 
        # get it for each parameter. Note the spectrum model could be filtered
        # so we can't use it:

        self._spectrum_defs = self._client.spectrum_list('*')['detail']

        # Given the Change button was clicked, this returns a list of dicts.
        # Each dict contains: a modified specrum definition for that spectrum.
        # for a spectrum to change and the final state of the spectrum.
        # The user has been prompted to accept/reject individual items on that
        # list, and the list is therefore filtered by the user's acceptance.
        result = []
        # First make the list of all spectra that can be modified:

        for r in self._view.table().selected_rows():
            row = self._view.table().get_row(r)
            modify_these = self._get_proposed_modifications_for_row(row)
            result.extend(modify_these)


        # Resolve duplicates - it's possible in wildcarding to get one
        # parameter to modify an x axis and another to modify the y axis.
        # In this case we take all differences from the original spectrum.

        result = self._resolve_duplicates(result)

        # Sort spectra alphabetically by name for the user.

        result = sorted(result, key = lambda x: x['name']) 

        # Some spectra can't actually be resized in this way - e.g. bitmask
        # spectra - it does not make sense to care about the parameter metadata:

        result = self._remove_unsupported_types(result)


        if len(result) == 0:
            return []               #  no spectra to change.

        # some spectra need adjustment e.g. g2 spectra - we'll propagete
        # the xaxis -> the y axis since it does not show x parametres.
        # Do this before filtering so the user can adjust again if desired.
        #
        result = self.adjust_defs_for_type(result)

        # Filter by the user's acceptance.

        result = self._filter_list(result)

        
        return result

    def _get_proposed_modifications_for_row(self, row):
        # For a row in the parameter list table, return a list of the spectra
        #  see get_spectra_to_modify for the contents of list elements.
        # that could be modified for that parameter (take into account the 
        # array check box).
        result = []
        for parameter in self._make_names(row['name']):
            result.extend(self._get_proposed_modifications_for_parameter(parameter, row))

        return result
    def _get_proposed_modifications_for_parameter(self, name, row):
        # Given exactly 1 parameter, determine the list of modifications
        # that can be done for that parameter.
        mods = []
        for spectrum in self._spectrum_defs:


            # We have to hoke up xparameters for gs spectrum types;

            if spectrum['type'] == 'gs':
                xparams = list()
                for x in spectrum['xparameters']:
                    xparams = xparams + x.split()
            else:
                xparams = spectrum['xparameters']

            if name in xparams or name in spectrum['yparameters']:
                mod = spectrum
                if name in spectrum['xparameters']:
                    mod['xaxis']['low'] = row['low']
                    mod['xaxis']['high']= row['high']
                    mod['xaxis']['bins']= row['bins']
                if name in spectrum['yparameters']:
                    mod['yaxis']['low'] = row['low']
                    mod['yaxis']['high']= row['high']
                    mod['yaxis']['bins']= row['bins']
                mods.append(mod)

        return mods
    def _resolve_duplicates(self, mods):
        #  If there are duplicates resolve those by merging both mods.

        d = dict()                     # simplest way to find dicts:
        for mod in mods:
            if mod['name'] in d.keys():
                name = mod['name']
                if mod['xaxis'] is not None:
                    if not mod['xaxis']['low'] == d[name]['xaxis']['low']:
                        d[name]['xaxis']['low'] = mod['xaxis']['low']
                    if not mod['xaxis']['high'] == d[name]['xaxis']['high']:
                        d[name]['xaxis']['high'] = mod['xaxis']['high']
                    if not mod['xaxis']['bins'] == d[name]['xaxis']['bins']:
                        d[name]['xaxis']['bins'] = mod['xaxis']['bins']
                if mod['yaxis'] is not None:
                    if not mod['yaxis']['low'] == d[name]['yaxis']['low']:
                        d[name]['yaxis']['low'] = mod['yaxis']['low']
                    if not mod['yaxis']['high'] == d[name]['yaxis']['high']:
                        d[name]['yaxis']['high'] = mod['yaxis']['high']
                    if not mod['yaxis']['bins'] == d[name]['yaxis']['bins']:
                        d[name]['yaxis']['bins'] = mod['yaxis']['bins']
                    
            else:
                d[mod['name']] = mod  # not duplicate

        return [d[x] for x in d.keys()]
    def _filter_list(self, defs):
        # Be nice ... if there's only one change figure that they don't
        # need the whole big dialog:

        if len(defs) == 1:
            name = defs[0]['name']
            if spectrumeditor.confirm(f'If you click Ok, {name} will be replaced', self._view):
                return defs
            else:
                return list()
        else:
            dlg = parameditor.ConfirmSpectra(self._view)
            dlg.getTable().load(defs)
            if dlg.exec() == QDialog.Accepted:
                return dlg.getTable().acceptedSpectra()
            else:
                return list()
    def adjust_defs_for_type(self, deflist):
        result = list()
        for sdef in deflist:
            if sdef['type'] == 'g2':
                sdef['yaxis'] = sdef['xaxis']
            result.append(sdef)

        return result
    def _modify_spectrum(self, sdef):
        # Given a new definition of an existing spectrum, delete/re-create
        # accoring to the spectrum definition.

        try:
            self._client.spectrum_delete(sdef['name'])
            self._spectrum_view.editor().spectrum_removed(sdef['name'])
        except RustogramerException as e:
            spectrumeditor.error(f'Unable to delete spectrum {sdef["name"]}: {e}')
            return
        # What we do depends on the spectrum type; sadly buster's python has
        # no match statement:

        try:
            if sdef['type'] == '1':
                self._client.spectrum_create1d(
                    sdef['name'], sdef['xparameters'][0],
                    sdef['xaxis']['low'],
                    sdef['xaxis']['high'],
                    sdef['xaxis']['bins'],
                    sdef['chantype']
                )
            elif sdef['type'] == '2':
                self._client.spectrum_create2d(
                    sdef['name'], 
                    sdef['xparameters'][0], sdef['yparameters'][0],
                    sdef['xaxis']['low'],
                    sdef['xaxis']['high'],
                    sdef['xaxis']['bins'],
                    sdef['yaxis']['low'],
                    sdef['yaxis']['high'],
                    sdef['yaxis']['bins'],
                    sdef['chantype']
                )
            elif sdef['type'] == 's':
                self._client.spectrum_createsummary(
                    sdef['name'],
                    sdef['xparameters'],
                    sdef['xaxis']['low'],    # Winds up in the x axis.
                    sdef['xaxis']['high'],
                    sdef['xaxis']['bins'],
                    sdef['chantype']
                )
            elif sdef['type'] == 'g1':
                self._client.spectrum_createg1(
                    sdef['name'],
                    sdef['xparameters'],
                    sdef['xaxis']['low'],  
                    sdef['xaxis']['high'],
                    sdef['xaxis']['bins'],
                    sdef['chantype']
                )
            elif sdef['type'] == 'g2':
                self._client.spectrum_createg2(
                    sdef['name'], sdef['xparameters'],
                    sdef['xaxis']['low'],  
                    sdef['xaxis']['high'],
                    sdef['xaxis']['bins'],
                    sdef['yaxis']['low'],  
                    sdef['yaxis']['high'],
                    sdef['yaxis']['bins'],
                    sdef['chantype']
                )
            elif sdef['type'] == 'gd':
                self._client.spectrum_creategd(
                    sdef['name'], 
                    sdef['xparameters'], sdef['yparameters'],
                    sdef['xaxis']['low'],  
                    sdef['xaxis']['high'],
                    sdef['xaxis']['bins'],
                    sdef['yaxis']['low'],  
                    sdef['yaxis']['high'],
                    sdef['yaxis']['bins'],
                    sdef['chantype']
                )
            elif sdef['type'] == 'm2':
                self._client.spectrum_create2dsum(
                    sdef['name'],
                    sdef['xparameters'], sdef['yparameters'],
                    sdef['xaxis']['low'],  
                    sdef['xaxis']['high'],
                    sdef['xaxis']['bins'],
                    sdef['yaxis']['low'],  
                    sdef['yaxis']['high'],
                    sdef['yaxis']['bins'],
                    sdef['chantype']
                )
            elif sdef['type'] == 'S':
                self._client.spectrum_createstripchart(
                    sdef['name'],
                    sdef['xparameters'][0], sdef['yparameters'][0],
                    sdef['xaxis']['low'],
                    sdef['xaxis']['high'],
                    sdef['xaxis']['bins'],
                    sdef['chantype']
                )
            elif sdef['type'] == 'gs':
                # we have a list of strings of parameters we need to make a list of lists:

                params = [x.split() for x in sdef['xparameters']]
                self._client.spectrum_creategammasummary(
                    sdef['name'],
                    params,
                    sdef['xaxis']['low'],
                    sdef['xaxis']['high'],
                    sdef['xaxis']['bins'],
                    sdef['chantype']
                )
                                                         
            else:
                spectrumeditor.error(f'Unsupported spectrum type: {sdef["type"]}')
                return
            self._spectrum_view.editor().spectrum_added(sdef['name'])
        except RustogramerException as e:
            spectrumeditor.error(f'Failed to create {sdef["name"]}: {e}')
            return
        try:
            self._client.sbind_list([sdef['name']])
        except RustogramerException as e:
            spectrumeditor.error(f'Failed to bind {sdef["name"]} to display memory but it was created: {e}')

    def _remove_unsupported_types(self, defs):
        return [x for x in defs if x['type'] != 'b']

#-------------------- Testing -----------------------------

if __name__ == '__main__':
    client = rustogramer_client.rustogramer({'host': 'localhost', 'port':8000})

    app = QApplication([])
    win = QMainWindow()

    ParameterChooser.update_model(client)

    view = parameditor.ParameterEditor()
    win.setCentralWidget(view)
    controller = ParameterController(view, client)
    win.show()
    app.exec()

