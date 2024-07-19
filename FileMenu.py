from PyQt5.QtWidgets import (
    QAction, QDialog, QDialogButtonBox, QVBoxLayout, QHBoxLayout, QRadioButton, QFileDialog,
    QLabel, QCheckBox, QPushButton, QTextEdit
)
from PyQt5.QtCore import QObject
from PyQt5.Qt import Qt
import capabilities
from spectrumeditor import confirm, error
import SpectrumList
import os
from  rustogramer_client import RustogramerException
import DefinitionIO

class FileMenu(QObject):
    ''' 
       Implements the file menu... init will instantiate it and
       connect us to the action signals which we will process.
    
        Note that the lifetime of this object must be program lifetime.
    '''
    def __init__(self, menu, client, *args):
        '''
        Note that deriving us from QObject allows us to own children.
          *   menu - The File QMenu object.
          *   client - the REST client.
        '''
        super().__init__(*args)
        program = capabilities.get_program()
        self._program = program   
        self._menu = menu
        self._client = client
        
        # We need to retain ownership of our actions:
        
        self._save = QAction('Save...', self)
        self._save.triggered.connect(self._save_definitions)
        self._menu.addAction(self._save)
        
        # Only for SpecTcl:
        
        if program == capabilities.Program.SpecTcl:
            self._save_treevars = QAction('Save Treevariables...', self)
            self._menu.addAction(self._save_treevars)
            self._save_treevars.triggered.connect(self._save_vars)
            
        self._save_spectra = QAction('Save spectrum contents...', self)
        self._save_spectra.triggered.connect(self.saveSpectra)
        self._menu.addAction(self._save_spectra)
        
        self._menu.addSeparator()
        
        self._load = QAction('Load...', self)
        self._load.triggered.connect(self._load_definitions)
        self._menu.addAction(self._load)
        
        self._read_spectrum = QAction('Read Spectrum contents...', self)
        self._menu.addAction(self._read_spectrum)
        self._read_spectrum.triggered.connect(self.read_spectrum_file)
        
        # SpecTcl supports sourcing a Tcl script:
        
        if program == capabilities.Program.SpecTcl:
            
            self._source  = QAction('Source Tcl Script...', self)
            self._source.triggered.connect(self._execute_script)
            self._menu.addAction(self._source)
            
        # We'll add exit:
        
        self._menu.addSeparator()
        
        # we can stop the histogramer if it's rustogramer:
        
        
        self._exit = QAction('Exit', self)
        self._exit.triggered.connect(self._exitGui)
        self._exit = self._menu.addAction(self._exit)
        
        if program == capabilities.Program.Rustogramer:
            self._kill = QAction('Stop Histogramer')
            self._menu.addAction(self._kill)
            self._kill.triggered.connect(self._exitHistogramerAndSelf)
        
    def _save_definitions(self):
        #  Prompt for the file and defer the actual save to the 
        #  DefintionIO module.
        
        file = self. _getSqliteFilename()
        if file == ('',''):
            return
        filename = self._genfilename(file)
        
        # If the file exists, delete it:
        
        try:
            os.remove(filename)
        except:
            pass
        saver = DefinitionIO.DefinitionWriter(filename)
        
        try:
        
        # Save the parameters:
        
            parameter_defs = self._client.parameter_list()['detail']
            saver.save_parameter_definitions(parameter_defs)
            
            # Spectrum definitions:
            
            spectrum_defs = self._client.spectrum_list()['detail']
            saver.save_spectrum_definitions(spectrum_defs)
            
            #  Conditions:
            
            condition_defs = self._client.condition_list()['detail']
            saver.save_condition_definitions(condition_defs)
            
            gate_defs = self._client.apply_list()['detail']
            saver.save_gates(gate_defs)
            
            # SpecTcl has variables:
            
            if self._program == capabilities.Program.SpecTcl:
                var_defs = self._client.treevariable_list()['detail']
                saver.save_variables(var_defs)
        except Exception as  e:
            error(f'Failed to write {filename}: {e}')
            
        
    def _save_vars(self):
        #  Save only the tree variables to a database file
        file = self._getSqliteFilename()
        if file == ('',''):
            return
        filename = self._genfilename(file)
        
        # If the file exists, delete it:
        
        try:
            os.remove(filename)
        except:
            pass
        try:
            writer = DefinitionIO.DefinitionWriter(filename)
            vars = self._client.treevariable_list()['detail']
            writer.save_variables(vars)
        except Exception as e:
            error(f'Failed to write tree variables to {filename} : {e}')
        
    def saveSpectra(self):
        '''
          Prompt for a set of spectra to save and save them.  This is public so that
          it is accessible to the spectrum menu.
        '''
        
        namePrompter = SpectrumSaveDialog(self._menu)
        if namePrompter.exec():
            names = namePrompter.selectedSpectra()
            format = namePrompter.format()
            
            wdir = os.getcwd()
            if format == 'json':
                default_ext = 'Json (*.json);;Text (*.txt)'
            elif format == 'ascii':
                default_ext = 'Spectrum (*.spec);;Text (*.txt)'
            elif format == 'binary':
                default_ext = 'Binary (*.bin);; Any (*.*)'
            else:
                default_ext = 'spec'
            if len(names) > 0:
                name = QFileDialog.getSaveFileName(
                    self._menu, 'Spectrum File', wdir, default_ext, default_ext)
                if not name == ('', ''):
                    filename  = self._genfilename(name)
                    
                    try:
                        self._client.spectrum_write(filename, format, names)
                    except RustogramerException as e:
                        error(f'Failed to save spectra to {filename} : {e}')
        
    def _load_definitions(self):
        #  Load definitions from a database file:
        
        file = self._getExistingSqliteFilename()
        if file[0] == '':
            return
        filename = self._genfilename(file)
        reader = DefinitionIO.DefinitionReader(filename)
        
        #  Read the parameters from the database and restore them (not so simple actually):
        
        parameters = reader.read_parameter_defs()
        self._update_parameters(parameters)
        
        spectra = reader.read_spectrum_defs()
        # There are several things they may want to do with existing spectra:
        # figure them out:
        if len(spectra) > 0:
            existing_dialog = DupSpectrumDialog(self._menu)
            choice = existing_dialog.exec()
            existing = set()               # Will be existing indexed by name:
            existing_spectra = self._client.spectrum_list()['detail']
            if choice == 1:
                # Existing is an empty set after we delete everything:
                for spectrum in existing_spectra:
                    self._client.spectrum_delete(spectrum['name'])
            elif choice == 2 or choice == 3:
                # Need the existing spectrum names set:
                for spectrum in existing_spectra:
                    existing.add(spectrum['name'])
            else:
                pass
            self._restore_spectra(choice, spectra, existing)
        
        conditions = reader.read_condition_defs()
        for condition in conditions:
            self._recreate_condition(condition)
            
            
        applications = reader.read_applications()
        self._restore_gate_applications(applications)
        
        # Simplest is to unbind all and rebind all:
        
        self._client.unbind_all()
        self._client.sbind_all()
        
        
        
    def read_spectrum_file(self):
        '''
           Prompt for how and which file to read spectra from...and do it.
           This is public so it can be re-used by SpectraMenu.
        '''
        dlg = ReadSpectraOptionsDialog(self._menu)
        response = dlg.exec()
        if not response:
            return
        snapshot = dlg.snapshot()
        replace  = dlg.replace()
        bind     = dlg.bind()
        format   = dlg.format()
        #  Prompt for a filename:
        
        file = QFileDialog.getOpenFileName(
            self._menu,  'Spectrum Filename', os.getcwd(),
            f'{format} files (*.{format})'
        )
        if file[0] == '':
            return
        filename = self._genfilename(file)
        try:
            self._client.spectrum_read(filename, format, 
                {'snapshot': snapshot, 'replace': replace, 'bind': bind}
            )
        except Exception as e:
            error(f"Failed to read spectrum file {filename}: {e}")
    def _execute_script(self):
        #  Run a script in the interpreter of the server.  We support a twp ways to do this:
        #  1.  Run a scrsipt file.
        #  2.  Edit a script (which can include loading a file).
        
        #  Figure out the mode:
        
        prompt = EditOrLoad(self._menu)
        how = prompt.exec()
        if how == 0:
            return             # Canceled
        elif how == 1:
            self._source_file()
        else:
            self._edit_script()
        
    def _exitGui(self):
        #  Make sure the user is certain and if so, exit:
        if confirm('Are you sure you want to exit the GUI (note the histogramer will continue to run)', self._menu):
            exit()
            
    def _exitHistogramerAndSelf(self):
        if confirm('Are you sure you want to exit the GUI and the histogramer?', self._menu):
            self._client.kill_histogramer()
            exit()
    # utilities
    
    def _genfilename(self, dialog_name):
        return genFilename(dialog_name)
        
    def _getSqliteFilename(self):
          return  QFileDialog.getSaveFileName(
            self._menu, 'Definition File', os.getcwd(), 
            'Sqlite3 (*.sqlite)'
        )      
    def _getExistingSqliteFilename(self):
           return  QFileDialog.getOpenFileName(
            self._menu, 'Definition File', os.getcwd(), 
            'Sqlite3 (*.sqlite)'
        )        
    def _update_parameters(self, definitions):
        #  Takes a set of parameter definitions and does what's needed.
        # What's needed:
        #   If the parameter does not exist, first just create it.
        #   Then edit the parameter's properties to match what's in its new definition.
        
        existing_defs = self._client.parameter_list()['detail']
        existing_map = dict()
        for p in existing_defs:
            existing_map[p['name']] = p

        # Now we can run through the new definitions:
        
        names = existing_map.keys()
        for p in definitions:
            name = p['name']
            if not name in names:
                self._client.parameter_create(name, {})
            # Only pull the non null ones out:
            
            mods = dict()
            if p['low'] is not None:
                mods['low'] = p['low']
            if p['high'] is not None:
                mods['high'] = p['high']
            if p['units'] is not None:
                mods['units'] = ['units']
            
            if mods:
                # Dicts are true if non-empty:
                self._client.parameter_modify(name, mods)
    def _restore_spectra(self, dupchoice, spectra, existing):
        #  dupchoice - selection from the DupSpectrumDialog   
        #  spectra   - Description of spectra to restore.
        #  existing  - Set of existing spectrum names.
        
        for spectrum in spectra:
            if spectrum['name'] in existing:
                if dupchoice == 2:          # Replace
                    self._client.spectrum_delete(spectrum['name'])
                else:
                    # Else is ok because existing is empty if dupchoice is 1 so
                    # Choice must be 3 (keep existing).
                    continue            # Do nothing with that definition.
            # At this point we can create the spectrum:
            
            self._create_spectrum(spectrum)
    def _create_spectrum(self, definition):
        
        # Create a spectrum given its definition;  how depends on type:
        
        name = definition ['name']
        stype = definition['type']
        dtype = definition['datatype']
        
        
        # If interchanging spectra between SpecTcl <--> Rustogramer we may need to 
        # massage the data type:
        
        if capabilities.DataTypeStringsToChannelTypes[dtype] not in \
            capabilities.get_supported_channelTypes():
            dtype = capabilities.ChannelTypesToDataTypeStrings[
                capabilities.get_default_channelType()]
        
        
        if stype == '1':
            self._client.spectrum_create1d(
                name, definition['xparameters'][0], 
                definition['xaxis']['low'], definition['xaxis']['high'], definition['xaxis']['bins'],
                dtype
            )
        elif stype == '2':
            self._client.spectrum_create2d(
                name, definition['xparameters'][0], definition['yparameters'][0],
                definition['xaxis']['low'], definition['xaxis']['high'], definition['xaxis']['bins'],
                definition['yaxis']['low'], definition['yaxis']['high'], definition['yaxis']['bins'],
                dtype
            )
        elif stype == 'g1':
            self._client.spectrum_createg1(
                name, definition['parameters'],
                definition['xaxis']['low'], definition['xaxis']['high'], definition['xaxis']['bins'],
                dtype
            )
        elif stype == 'g2':
            self._client.spectrum_createg2(
                name, definition['parameters'],
                definition['xaxis']['low'], definition['xaxis']['high'], definition['xaxis']['bins'],
                definition['yaxis']['low'], definition['yaxis']['high'], definition['yaxis']['bins'],
                dtype
            )
        elif stype == 'gd':
            self._client.spectrum_creategd(
                name, definition['xparameters'], definition['yparameters'],
                definition['xaxis']['low'], definition['xaxis']['high'], definition['xaxis']['bins'],
                definition['yaxis']['low'], definition['yaxis']['high'], definition['yaxis']['bins'],
                dtype
            )
        elif stype == 's':
            # Axis definition...if there's a y axis we use it otherwise the X
            # That may be a SpecTcl Rustogramer difference:
            if definition['yaxis'] is not None and len(definition['yaxis']) != 0:
                axis = definition['yaxis']
            else:
                axis = definition['xaxis']
            self._client.spectrum_createsummary(
                name, definition['parameters'],
                axis['low'], axis['high'], axis['bins'],
                dtype
            )
        elif stype == 'm2':
            # If there's no y parameters, then every other parameter in x/y is 
            # x,y
            if definition['yparameters'] is None:
                xparams =list()
                yparams = list()
                p  = iter(definition['parameters'])
                for x in p:
                    xparams.append(x)
                    yparams.append(next(p))
            else:
                xparams = definition['xparameters']
                yparams = definition['yparameters']
            self._client.spectruM_create2dsum(
                name, xparams, yparams,
                definition['xaxis']['low'], definition['xaxis']['high'], definition['xaxis']['bins'],
                definition['yaxis']['low'], definition['yaxis']['high'], definition['yaxis']['bins'],
                dtype
            )
        elif stype == 'S':
            self._client.spectrum_createstripchart(
                name, definition['xparameters'][0], definition['yparameters'][1],
                definition['xaxis']['low'], definition['xaxis']['high'], definition['xaxis']['bins'],
                definition['yaxis']['low'], definition['yaxis']['high'], definition['yaxis']['bins'],
                dtype
            )
        elif stype == 'b':
            self._client.spectrum_createbitmask(
                name, definition['xparameters'][0],
                definition['xaxis']['low'], definition['xaxis']['high'], definition['xaxis']['bins'],
                dtype
            )
        elif stype == 'gs':
            print(' gamma summary def looks like: ', definition)
        else:
            error(f'Specturm if type {stype} is not supported at this time.')
    
    def _recreate_condition(self, cond):
        # Re create a condition in the server:
        # JUst return if the condition type is not supported by our histogramer:
        
        
        cname = cond['name']
        ctype = cond['type']
        
        if not capabilities.has_condition_type(capabilities.ConditionTypeNamesToType[ctype]):
            return
        
        if ctype == 'T':
            self._client.condition_make_true(cname)
        elif ctype == 'F':
            self._client.condition_make_false(cname)
        elif ctype == '-':
            self._client.condition_make_not(cname, cond['dependencies'][0])
        elif ctype == '*':
            self._client.condition_make_and(cname, cond['dependencies'])
        elif ctype == '+':
            self._client.condition_make_or(cname, cond['dependencies'])
        elif ctype == 's':
            self._client.condition_make_slice(
                cname, cond['parameters'][0], 
                cond['points'][0][0], cond['points'][1][0]
            ) 
        elif ctype== 'c':
            self._client.condition_make_contour(
                cname, cond['parameters'][0], cond['parameters'][1],
                [{'x': x[0], 'y': x[1]} for x in cond['points']]
            )
        elif ctype== 'b':
            self._client.condition_make_band(
                cname, cond['parameters'][0], cond['parameters'][1],
                [{'x': x[0], 'y': x[1]} for x in cond['points']]
            )
        elif ctype =='gs':
            self._client.condition_make_gamma_slice(
                cname, cond['parameters'],
                cond['points'][0][0], cond['points'][1][0]
            )
        elif ctype == 'gc':
            self._client.conditino_make_gamma_contour(
                cname, cond['parameters'],
                [{'x': x[0], 'y': x[1]} for x in cond['points']]
            )
        elif ctype == 'gb':
            self._client.condition_make_gamma_band(
                cname, cond['parameters'],
                [{'x': x[0], 'y': x[1]} for x in cond['points']]
            )
        elif ctype == 'em':
            self._client.condition_make_mask_equal(
                cname, cond['parameters'][0], cond['mask']
            )
        elif ctype == 'am':
            self._client.condition_make_mask_and(
                cname, cond['parameters'][0], cond['mask']
            )
        elif ctype =='nm':
            self._client.condition_make_mask_nand(
                cname, cond['parameters'][0], cond['mask']
            )
        else:
            error(f'Gate type {ctype} is not supported.')
    
    def _restore_gate_applications(self, apps):
        # Restore the gate applications.  Doing this in a separate
        # method makes handling the cancel from the ExistingApplcationsDialog eaiser.
        
        current = self._get_current_applications()
        if len(current) > 0:
            dlg = ExistingApplicationsDialog()
            response = dlg.exec()
            if response == 0:
                return                # Cancel.
            elif response == 1:
                names =  [x['spectrum'] for x in current]
                self._client.ungate_spectrum(names)
            else:
                pass                          # Should be 2.
        # make the applications:
        
        for app in apps:
            self._client.apply_gate(app['condition'], app['spectrum'])
    def _get_current_applications(self):
        # This is hidden in a method because there's some actual massaging in both Rustogramer
        # and SpecTcl needed to make the actual list of spectra with gates applied:
        
        apps = self._client.apply_list()['detail']
        #
        #  SpecTcl has no ungated spectra.. the special true gates '-Ungated-' or '-TRUE-' is applied to
        #  What rustogramer would call ungated spectra
        #
        apps = [x for x in apps 
                if (x['gate'] is not None) and (x['gate'] != '-Ungated-') and (x['gate'] != '-TRUE-')]
        print(apps)
        return apps
    def _source_file(self):
        file = QFileDialog.getOpenFileName(
            self._menu, "Choose Script File", os.getcwd(), 
            "Tcl File (*.tcl *.tk);;All files (*.*)", 
            "Tcl File (*.tcl *.tk)"
        )
        if file[0] == '':
            return             # Canceled file selection.
        filename = self._genfilename(file)
        try:
            with open(filename, 'r') as f:
                script = f.read()
                self._client.execute_tcl(script)
        except Exception as e:
            error(f'Executing script file {filename} : {e}')
    def _edit_script(self):
        editor = ScriptEditor(self._menu)
        if editor.exec():
            script = editor.text()
            self._client.execute_tcl(script)
class SpectrumSaveDialog(QDialog):
    '''
    This class provides:
    *   A standard way to select spectra.
    *   A selection of formats with which to save the spectra (appropriate to the server)
    *   Buttons for Ok and Cancel.
    *  Selectors to get the selected spectra and the format name.
    '''
    def __init__(self, *args):
        super().__init__(*args)
        layout = QVBoxLayout()
        
        self._selection = SpectrumList.SpectrumSelector(capabilities.get_client(), self)
        layout.addWidget(self._selection)
        
        #  Radio boxes for formats:
        
        formats = capabilities.get_supported_spectrum_format_strings()
        radio_layout = QHBoxLayout()
        
        self._formats = []
        for (i, format) in enumerate(formats):
            button = QRadioButton(format, self)
            self._formats.append(button)
            radio_layout.addWidget(button)

    
        if len(self._formats) > 0:
            self._formats[0].setChecked(True)   # Default is first format.
        
        layout.addLayout(radio_layout)
        
        # The buttons at the bottom of the dialog:
        
        self._buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        self._buttonBox.accepted.connect(self.accept)
        self._buttonBox.rejected.connect(self.reject)
        
        layout.addWidget(self._buttonBox)
        
        self.setLayout(layout)
        

    
    def selectedSpectra(self):
        return self._selection.selected()
    def format(self):
        result = None    # In case we have an unknown.
        
        for format in self._formats:
            if format.isChecked():
                result = format.text()
                return result
        
        return result
        
        

# This dialog is used to get how to handle spectra read in.  There are three choices:
#  -   Delete all first.
#  -   Replace any duplicates.
#  -   Keep the duplicates as is.
#
#  Instantiate this dialog then its exec method will
#  return one of:
#    - 1  - Delete all
#    - 2  - Replace duplicates.
#    - 3  - Keep duplicates.
#    - 0  - The dialog was cancelled you should not recover the spectra.
#        
class DupSpectrumDialog(QDialog):
    def __init__(self, *args):
        super().__init__(*args)
        layout = QVBoxLayout()
        
        # At the top is the explanatory text.
        
        self._explanation = QLabel(self)
        self._explanation.setWordWrap(True)
        self._explanation.setText(" \
You are about to recover spectrum definitions from a file.  It is possible there are already \
spectra defined with the same names as this in the file.  Decide what you want to do with \
existing spectra:")
        layout.addWidget(self._explanation)
        
        # Second row is an hbox layout that has the radio buttons.  The
        # initial value is delete all spectra first.
        
        radios = QHBoxLayout()
        self._deleteall = QRadioButton('Delete all existing', self)
        self._deleteall.setChecked(True)
        radios.addWidget(self._deleteall)
        
        self._deletedups = QRadioButton("Ovewrite existing defs", self)
        radios.addWidget(self._deletedups)
        
        self._keepdups = QRadioButton("Don't re-define duplicates", self)
        radios.addWidget(self._keepdups)
        
        layout.addLayout(radios)
        
        # Now the dialog buttons:
        
        self._buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        self._buttonBox.accepted.connect(self.accept)
        self._buttonBox.rejected.connect(self.reject)
        
        layout.addWidget(self._buttonBox)
        
        self.setLayout(layout)
    
    def exec(self):
        # Override the exec - after the base class finishes interrogate the radios
        # to decide what to return:
        
        if super().exec():
            if self._deleteall.isChecked():
                return 1
            if self._deletedups.isChecked():
                return 2
            if self._keepdups.isChecked():
                return 3
            # Should not land here but...
            
            return 0      # Treat it like  a cancel.
        else:
            return 0      #  Canacel

# Dialog to determine how existing gate applications are to be handled.
#  Instantiating and invoking exec returns:
#    1  - Kill all existing applications.
#    2  - Retain any existing applications not overwritten.
#    0  - User cancelled don't restore the aplications.
class ExistingApplicationsDialog(QDialog): 
    def __init__(self, *args):
        super().__init__(*args)
        layout = QVBoxLayout()
        
        self._explanation = QLabel(self)
        self._explanation.setText(" \
Choose how existing gate applications will be handled.   If you check the \
box below, all existing gate applications will be removed before restoring \
the applications in the file.  If you leave the box unchecked, \
existing gate applications that are not overidden from the file will remain \
        ")
        self._explanation.setWordWrap(True)
        layout.addWidget(self._explanation)
        
        self._killfirst = QCheckBox('Kill existing gate applications', self)
        layout.addWidget(self._killfirst)
        
        # Now the dialog buttons:
        
        self._buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        self._buttonBox.accepted.connect(self.accept)
        self._buttonBox.rejected.connect(self.reject)
        
        layout.addWidget(self._buttonBox)
        
        self.setLayout(layout)
        
    def exec(self):                  # Override:
        if super().exec():
            if self._killfirst.checkState() == Qt.Checked:
                return 1
            else:
                return 2
        else:
            return 0 

# A dialog that allows users to select how spectra are read from file.  Has a bunch of checkboxes
# and a radio button set for formats:
# that turn on/off options.  The options are:
#  snapshot - Spectra read in won't be incremented by future events.
#  replace  - If the spectrum exists alread it will be replaced.
#  bind     - Spectra get bound into the display memory
#  
#  Default have snapshot and bind checked but replace not.
#
#  Formats depend on the server capabilities and are chosen from the 
#  set:
#    json - supported by SpecTcl and rustogramer data files are in JSON format
#    ascii - Supported by SpecTcl and rustogramer - old SpecTcl ASCII format.
#    binary - only supported by SpecTcl - SMAUG binary format from Betty days.
#
class ReadSpectraOptionsDialog(QDialog):
    def __init__(self, *args):
        super().__init__(*args)
        
        layout = QVBoxLayout()
        
        # Top is a vertical set of save options:
        
        layout.addWidget(QLabel('Save options:', self))
        self._snapshot = QCheckBox('Save as snapshots', self)
        self._snapshot.setCheckState(Qt.Checked)
        layout.addWidget(self._snapshot)
        
        self._replace = QCheckBox('Replace spectra with same names', self)
        layout.addWidget(self._replace)
        
        self._bind = QCheckBox('Bind to display memory', self)
        self._bind.setCheckState(Qt.Checked)
        layout.addWidget(self._bind)
        
        layout.addWidget(QLabel('File format:'))
        
        formats = QHBoxLayout()
        self._formats = list()
        for fmt in capabilities.get_supported_spectrum_format_strings():
            fmtwidget = QRadioButton(fmt, self)
            self._formats.append(fmtwidget)
            formats.addWidget(fmtwidget)
        if len(self._formats) > 0:
            self._formats[0].setChecked(True)
        
        layout.addLayout(formats)
        
        # Now the dialog buttons:
        
        self._buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        self._buttonBox.accepted.connect(self.accept)
        self._buttonBox.rejected.connect(self.reject)
        
        layout.addWidget(self._buttonBox)
        
        self.setLayout(layout)
    
    # Selectors to get the state of the box (e.g. after exec returns):
    
    def snapshot(self):
        return self._snapshot.checkState() == Qt.Checked
    def replace(self):
        return self._replace.checkState() == Qt.Checked
    def bind(self):
        return self._bind.checkState() == Qt.Checked
    
    def format(self):
        for fmt in self._formats:
            if fmt.isChecked():
                return fmt.text()
        return None

class EditOrLoad(QDialog):
    #  Prompt for how to load a script  into interpreter:
    #  1 - Just run a file.
    #  2 - Run a simple editor to prepare a script (including based on a file).
    #  0 - Cancelled out.
    #
    def __init__(self, *args):
        super().__init__(*args)
        
        #  Just a pair of radio buttons and the standard button box:
        
        layout = QVBoxLayout()
        
        self._file = QRadioButton("Load Script From File", self)
        self._file.setChecked(True)
        layout.addWidget(self._file)
        
        self._edit = QRadioButton("Edit a script and run it", self)
        layout.addWidget(self._edit)
        
        # Now the dialog buttons:
        
        self._buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        self._buttonBox.accepted.connect(self.accept)
        self._buttonBox.rejected.connect(self.reject)
        
        layout.addWidget(self._buttonBox)
        self.setLayout(layout)
    
    def exec(self):
        if super().exec():
            if self._file.isChecked():
                return 1
            if self._edit.isChecked():
                return 2
            else:
                return 0             # shouldn ot happen!!
        else:
            return 0     
    
class ScriptEditor(QDialog):
    # Dirt simple Script editor for to prepare a script to be edited for execution.
    #
    # Layout:
    # +----------------------------------------------------------------------+
    # |  [  Insert ... ]          [ Save ...]    [ Clear]                    |
    # |  [              QTextEdit with script  ]                             |
    # |  [ Ok ]  [Cancel ]                                                   |
    # +----------------------------------------------------------------------+
    #
    #  The buttons:
    #  *  Insert - prompts for a script file to edit and loads it at the cursor.
    #  *  Save - Prompts for a file to which to save the contents of the QTextEit.
    #  *  Clear - Clears all of the text in the QTextWidget.
    #  *  Ok    - User is ready to execute the script in the server.
    #  *  Cancel - User wants to give it all up as a bad job.
    #
    #  Attributes:
    #    text - Get/Set text in the textwidget.
    def __init__(self, *args):
        super().__init__(*args)
        
        layout = QVBoxLayout()
        
        # Horizontal strip of buttons at the top of the dialog:
        
        buttons = QHBoxLayout()
        self._load = QPushButton('Insert...', self)
        buttons.addWidget(self._load)
        
        self._save = QPushButton('Save...', self)
        buttons.addWidget(self._save)
        
        self._clear = QPushButton('Clear', self)
        buttons.addWidget(self._clear)
        
        layout.addLayout(buttons)
        
        # Editor:
        
        self._editor = QTextEdit(self)
        self._editor.setAcceptRichText(False)
        self._editor.setLineWrapMode(QTextEdit.NoWrap)
        layout.addWidget(self._editor)
        
        
        self._buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        self._buttonBox.accepted.connect(self.accept)
        self._buttonBox.rejected.connect(self.reject)
        
        layout.addWidget(self._buttonBox)
        self.setLayout(layout)
        
        # Hook the button to internal slots:
        
        self._load.clicked.connect(self.loadFile)
        self._save.clicked.connect(self.saveFile)
        self._clear.clicked.connect(self.clear)
        
    # Attributes:
    
    def text(self):
        return self._editor.toPlainText()
    def setText(self, text):
        self._editor.setPlainText(text)    
    
    # Slots:
    
    def loadFile(self):
        #  Load  file at the cursor.
        
        file =   file = QFileDialog.getOpenFileName(
            self, "Choose Script File", os.getcwd(), 
            "Tcl File (*.tcl *.tk);;All files (*.*)", 
            "Tcl File (*.tcl *.tk)"
        )
        if file[0] == '':
            return             # Canceled file selection.
        filename = genFilename(file)
        try:
            with open(filename, 'r') as f:
                script = f.read()
        except Exception as e:
            error(f'Unable to load {filename}: {e}')
            return
        
        cursor = self._editor.textCursor()
        cursor.insertText(script)
        
    def saveFile(self):
        # Save the contents of the editor:
        
        file = QFileDialog.getSaveFileName(
            self, 'Save script in...',
            "Tcl Script (*.tcl);; Tk Script (*.tk);; All Files (*.*)",
            "Tcl Script (*.tcl)"
        )
        if file[0] =='':
            return
        filename = genFilename(file)
        
        try:
            with open(filename, 'w') as f:
                f.write(self.text())
        except Exception as e:
            error(f'Failed to save script to {filename}: {e}')
            
    def clear(self):
        # Clear the text editor.
         
        self._editor.setText('')   
        
       
def genFilename(dialog_name):
    # Generate he filename from what comes back from QFileDialog:
        name = dialog_name[0]
        # IF this has an extension we're golden - that's the case if splitext[1] has a period.
        # otherwise we need to glue on the default extension.
        
        parts = os.path.splitext(name)
        if '.' in parts[1]:
            name = name.strip(') ')
            return name
        else:
            filter = dialog_name[1].split('(')[1]
            ext = filter.strip('*) ')
            # Trim off the * and trailing )
            
            return name + ext
        
        