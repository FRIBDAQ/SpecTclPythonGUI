'''
This module contains code to process the entries in the data source menu.
The following menu items are present:

Oneline - Take data from NSCLDAQ (SpecTcl only).
File    - Take data from an event/parameter file.
Pipe    - Take data from a program via a pipe (SpecTcl only).
-----
List of Runs - Take data from a list of run. (cluster file) - SpecTcl later than version 5.13-(???)
Filter File - Take data from a filter file. (SpecTcl only).
-----
Detach - Detach from the data source.
Abort Cluster File (SpecTcl only later than 5.13-xxx)

'''
from PyQt5.QtWidgets import (
    QAction, QFileDialog, QDialog, QDialogButtonBox, QRadioButton, QPushButton,
    QLabel, QWidget, QLineEdit,
    QVBoxLayout, QHBoxLayout
)
from PyQt5.QtCore import QObject

import os

import capabilities
from spectrumeditor import error, confirm
from editablelist import EditableList


class DataSourceMenu(QObject):
    def __init__(self, menu, client, gui, *args):
        super().__init__(*args)
        
        # Fill in the items in the menu:
        
        program = capabilities.get_program()
        
        # Simplify program comparisons:
        
        spectcl = capabilities.Program.SpecTcl
        rustogramer = capabilities.Program.Rustogramer
        # Save our internal data:
        
        self._program = program 
        self._menu = menu
        self._client = client
        self._ui     = gui
        
        self._warnedAboutFilters = False
        
        #  Add the menu items appropriate to the server:
        
        if program == spectcl:
            self._online = QAction('Online...', self)
            self._online.triggered.connect(self._attach_online)
            self._menu.addAction(self._online)
        
        self._file = QAction('File...', self)
        self._file.triggered.connect(self._read_event_file)
        self._menu.addAction(self._file)
        
        if program == spectcl:
            self._pipe = QAction('Pipe...', self)
            self._pipe.triggered.connect(self._attach_pipe)
            self._menu.addAction(self._pipe)
        
        # This list of stuff is all SpecTcl at this time.
        
        if program == spectcl:
            self._menu.addSeparator()

            if capabilities.has_rest_runlist():
                self._cluster = QAction('Cluster file...', self)
                self._cluster.triggered.connect(self._attach_cluster)
                self._menu.addAction(self._cluster)
                
            self._filter = QAction('Filter file...', self)
            self._filter.triggered.connect(self.attach_filter)
            self._menu.addAction(self._filter)
        
        self._menu.addSeparator()
        
        self._detach = QAction('Detach')
        self._detach.triggered.connect(self._detach_source)
        self._menu.addAction(self._detach)
        
        if program == spectcl:
            if capabilities.has_rest_runlist():   # Part of runlist functionality.
                self._abortlist = QAction('Abort Cluster File')
                self._abortlist.triggered.connect(self._stop_cluster)
                self._menu.addAction(self._abortlist)
                                   
        
    
    def _attach_cluster(self):
        pass
    def _stop_cluster(self):
        pass
    def _read_event_file(self):
        #  Prompt for an event file and 
        # Figure out the possible event file formats:
        
        formats = list()
        if capabilities.can_read_raw_events():
            formats.append('Raw (*.evt)')
        if capabilities.can_read_parfiles():
            formats.append('Parameterized (*.par)')
        
        if len(formats) == 0:
            error('The histogramer has no supported event file formats')
            return
        
        filters = ';;'.join(formats)
        
        file = QFileDialog.getOpenFileName(
            self._menu, 'Choose event file', os.getcwd(), filters, formats[0]
        )
        filename = file[0]
        if filename == '':                  # Cancelled out of file choice.
            return
        try:
            self._client.attach_source('file', filename)
            if self._isRawFile(filename, file[1]):
                # Need to set ringformat:
                format_prompt = FormatPrompter(self._menu)
                ringlevel = format_prompt.exec()
                if ringlevel > 0:
                    self._client.ringformat_set(ringlevel)
                else:
                    return                              # canceled.
            else:
                self._client.ringformat_set(12)         # Parameter files are ring 12.
            
            # Start analysis:
            
            self._client.start_analysis()
        except Exception as e:
            error(f'Unable to analyze data from file {filename} : {e}')
    
    def _detach_source(self):
        #  This is only slightly complicated;  For histogramers that 
        #  dont' have a rest detach request we use an attach to /dev/null -- which
        #  implicitly assumes they run in an unix environment (e.g. SpecTcl):
        # Must stop but we don't know if it's running:
        
        try:
            self._client.stop_analysis()
        except:
            pass
        try:
            if capabilities.can_rest_detach():
                self._client.detach_source()
            else:
                self._client.attach_source('file', '/dev/null')
        except Exception as e:
            error(f"Unable to detach because: {e}")
    
    def _attach_online(self):
        #  We need:
        #   The ringselector 
        #   Ring URL
        #   Format of data (ring format).
        #  We get that from OnlinePrompter:
        
        prompter = OnlinePrompter(self._menu)
        if prompter.exec():
        
            #  Fish waht we need from the prompter:
        
            url = prompter.ring()
            helper = prompter.ringselector()
            format = prompter.format()
            
            # Build the source string:
            
            source = f'{helper} --source={url} --sample=PHYSICS_EVENT --non-blocking'
            try:
                self._client.attach_source('pipe', source)
                self._client.ringformat_set(format)
                self._client.start_analysis()
            except Exception as e:
                error(f'Unable to attach online source {url} using {helper}: {e}')
     
    def _attach_pipe(self):
        # Handler attaching an arbitrary pipe as a data source.
        
        prompter = PipePrompter(self._menu)
        if prompter.exec():
            source = prompter.source()
            format = prompter.format()
            try:
                self._client.attach_source('pipe', source)   
                self._client.ringformat_set(format)
                self._client.start_analysis()
            except Exception as e:
                error(f'Unable to start {source} as pipe data source: {e}')
                
    def attach_filter(self):
        '''  Attach a filter file.  This is a public entry so
             the filter menu can use it as well for Filter->Read Filter File...s
        '''
        #  If we've never warned about needing a special event processor do it now
        # and marked that we warned:'''
        
        if not self._warnedAboutFilters:
            self._warnedAboutFilters = True
            if not confirm("\
Reading filter files requires that you have set up a filter event processor. \
If you have not done that your analysis of a filter file will fail.  If you ar sure \
this SpecTcl has properly set up to analyze filter files, you can click 'Yes' below \
If not click 'No' to do something else \
"):
                return
        # Prompt for the filter file:
        
        file = QFileDialog.getOpenFileName(
            self._menu,
            'Filter file to process?', os.getcwd(),
            'Filter files (*.flt);;All files (*)', 'Filter files (*.flt)'
        )
        filename = file [0]
        if filename != '':
            try:
                self._client.attach_source('file', filename, 'filter')
                self._client.start_analysis()
            except Exception as e:
                error("Unable to process filter file {file}: {e}")    
                return              # Simplifies adding code beyond this.
            
        
               
    def _isRawFile(self, filename, filter):
        # Figure out if the filename is a raw event file:
        
        parts = os.path.splitext(filename)
        print(parts)
        return parts[1] == '.evt'
    
    

#  A widget for selecting the RingFormat:

class RingFormat(QWidget):  
    _format_versions = [10, 11, 12]
    def __init__(self, *args):
        super().__init__(*args)
        formats = QHBoxLayout()
        self._formats = list()
        for version in self._format_versions:
            fmt = QRadioButton(f'NSCLDAQ-{version}', self)
            self._formats.append(fmt)
            formats.addWidget(fmt)
            
        #  Default to the most recent format:
        
        self._formats[-1].setChecked(True)    
        self.setLayout(formats)
    #  Attributes:
    
    def setFormat(self, level):
        for (i, version) in enumerate(self._format_versions):
            if level == version:
                self._formats[i].setChecked(True)
                return
        raise IndexError(f'Unrecognized format level {level}')
    def format(self):
        for (i, version) in enumerate(self._format_versions):
            if self._formats[i].isChecked():
                return version
            
        raise AssertionError("No radio buttons are checked!!")
class FormatPrompter(QDialog):
    #  Provides a prompter dialog for the ring format.
    #  exec returns:
    #   0     - User cancelled.
    #   otherwise the major version of the NSCLDAQ format to use (e.g 11).
    _format_versions = [10, 11, 12]
    def __init__(self, *args):
        super().__init__(*args)
        layout = QVBoxLayout()
        layout.addWidget(QLabel('Select Ring Item format:', self))
        #  Top is a row of formats NSCLDAQ 10-12.
        
            
        self._format = RingFormat(self)
        layout.addWidget(self._format)
        
        #  Now the button box:
        
        self._buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        self._buttonBox.accepted.connect(self.accept)
        self._buttonBox.rejected.connect(self.reject)
        
        layout.addWidget(self._buttonBox)
        
        self.setLayout(layout)
    
    def exec(self):
        if super().exec():
            return self._format.format()
        else:
            return 0                       # Cancel.

class OnlinePrompter(QDialog):
    # Prompt for what's needed to attach online:
    
    def __init__(self, *args):
        super().__init__(*args)
        
        # Figure out the helper string... use $DAQBIN if not defined
        # we'll give up:
        
        daqbin = os.getenv('DAQBIN')
        if daqbin is None:
            helper = ''
        else:
            helper = os.path.join(daqbin, 'ringselector')
        
        layout = QVBoxLayout()
        
        # At the top is the ringURL:
        
        ringurl = QHBoxLayout()
        self._url = QLineEdit(self)
        ringurl.addWidget(self._url)
        ringurl.addWidget(QLabel('Ring Buffer URL', self))
        
        layout.addLayout(ringurl)
        
        # Next is the helper with a Browse button.
        
        helper_layout = QHBoxLayout()
        self._helper = QLineEdit(helper, self)
        helper_layout.addWidget(self._helper)
        self._browse = QPushButton('Browse...', self)
        helper_layout.addWidget(self._browse)
        
        layout.addLayout(helper_layout)
        
        #  Next down is the ring format chooser:
        
        layout.addWidget(QLabel('ring format:', self))
        self._format = RingFormat(self)
        layout.addWidget(self._format)
        
        # Finally the dialog button box:
        
        self._buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        self._buttonBox.accepted.connect(self.accept)
        self._buttonBox.rejected.connect(self.reject)
        
        layout.addWidget(self._buttonBox)
        
        self.setLayout(layout)
        
        # Handle internal signals:
        
        self._browse.clicked.connect(self.browse_helper)
    
    #  Attribute implementations:
    
    def ring(self):
        return self._url.text()
    def setRing(self, url):
        self._url.setText(url)
    
    def ringselector(self):
        return self._helper.text()
    def setRingselector(self, helper):
        self._helper.setText(helper)
    
    def format(self):
        return self._format.format()
    def setFormat(self, level):
        self._format.setFormat(level)
        
    # slots:
    
    def browse_helper(self):
        #  Slot to browser for a helper file:
        #  We just use QFileDialog.getOpenFileName:
        
        filename = QFileDialog.getOpenFileName(
            self, "Select Helper program", os.getcwd(), "All Files (*)", "All Files (*)"
        )
        if filename[0] != '' :
            self._helper.setText(filename[0])
            
class PipePrompter(QDialog):
    def __init__(self, *args):
        super().__init__(*args)
        
        layout = QVBoxLayout()
        
        # At the top we have the program/browse button:
        
        program = QHBoxLayout()
        program.addWidget(QLabel("Program: ", self))
        self._program = QLineEdit(self)
        program.addWidget(self._program)
        self._browse = QPushButton('Browse...')
        program.addWidget(self._browse)
        
        layout.addLayout(program)
        
        # Next we have the mechanism for adding parameters:
        
        
        parameters = QHBoxLayout()
        self._parameter = QLineEdit(self)
        parameters.addWidget(self._parameter)
        self._parameters = EditableList("Parameters", self)
        parameters.addWidget(self._parameters)
        
        layout.addLayout(parameters)
        
        # Now the ring format:
        
        self._format = RingFormat(self)
        layout.addWidget(self._format)
        
        # Finally the dialog button box:
        
        self._buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        self._buttonBox.accepted.connect(self.accept)
        self._buttonBox.rejected.connect(self.reject)
        
        layout.addWidget(self._buttonBox)
        
        
        self.setLayout(layout)
        
        # Internal signal handling:
        
        self._browse.clicked.connect(self.browse_program)
        self._parameters.add.connect(self.add_parameter)
        
    # Attributes:
    #   source - the full data source specification.
    #   format - The format of the ring items.
    
    def source(self):
        program =self._program.text()
        parameter_list = self._parameters.list()
        parameters = ' '.join(parameter_list)
        
        return program + ' ' + parameters

    def setSource(self, program):
        #  THis may not be a completely faithful rendering:
        
        # Split the string at whitepsace:
        
        program_list = program.split()
        
        # Load the first element into the program line edit and the
        # rest of the elements into the list box:
        
        self._program.setText(program_list[0])
        self._parameters.setList(program_list[1:])
    
    def format(self):
        return self._format.format()
    def setFormat(self, level):
        self._format.setFormat(format)
    
    #   Slots:
    
    def browse_program(self):
        file = QFileDialog.getOpenFileName(
            self, 'Choose program', os.getcwd(),
            'All Files (*)', 'All files (*)'
        )
        filename = file[0]
        if filename != '':
            self._program.setText(filename)
    def add_parameter(self):
        parameter = self._parameter.text()
        self._parameters.appendItem(parameter)