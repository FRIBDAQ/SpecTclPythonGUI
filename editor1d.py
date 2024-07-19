''' This module provides a megawidget (oneDEditor) that edits/creates
a 1d spectrum.  In addition to the spectrum type,
a 1d spectrum has:
   *   a name.
   *   a parameter
   *   a single axis definition.

 Therefore the followinng properties are provided:
  *  name - the spetrum the spectrujm name.
  *  parameter(readonly) - the currently selected parameter.
  *  low  - Axis low limit.
  *  high - axis high limit.
  *  bins - Axis bins.
  *  array - User wants an  'array' of spectra made.

  Note that if a parameter is specified and has the
  low/high/bins recommendations, these should be loaded
  into the axis properties by the client.

  The following signals are provided:

    *  nameChanged - the name of the spectrum has changed.
    *  parameterSelected - the parameter of the spectrum
        has been selected.
    *  axisModified - the axis has been modified.
    *  commit - The user pushed the create/modify button.

    The following slot is provided:

    *  update_parameters - the parameters loaded into the e paramter
    selector should be updated from the server program.
    This should be passed a rustogramer client object.

    nameChanged Signal - this signal provides the current text
    of the spectrum name.  If the spectrum is already an
    existing spectrum, the program shouild fill in the
    remaining properties (parameter name and axis definition) of
    that spectrum).

    parameterSelected Signal - this signal provides the current textual
    name of the parameter.  The client should load the axis
    definition of the spectrum with any recommended axis
    spefication associated with that parameter or leave the
    axis definition unchanged, if there is none.  Note that
    if the spectrum is created the axis definition _may_ he
    associated with the parameter for future use.

    axisModified Signal - a dict is passed to the slot that
    contains the following keys:  'low', 'hi' and 'bins'
    with obvious contents.  Since the axis entries are 
    comboboxes, none of these will be None.

    '''



from axisdef import AxisInput
from ParameterChooser import Chooser as ParameterChooser
from PyQt5.QtWidgets import (
    QLineEdit, QWidget, QHBoxLayout, QVBoxLayout, QLabel,
    QApplication, QMainWindow, QPushButton, QCheckBox,
    QMessageBox
)
from PyQt5.QtCore import pyqtSignal, Qt
from rustogramer_client import rustogramer as cl

class oneDEditor(QWidget):
    nameChanged = pyqtSignal(str)
    parameterSelected = pyqtSignal(str)
    axisModified = pyqtSignal(dict)
    commit = pyqtSignal()

    def __init__(self, *args):
        super().__init__(*args)

        layout = QVBoxLayout()
        
        # The top horizontal line names the spectrum and provides
        # an option to make an array:

        line1 = QHBoxLayout()

        line1.addWidget(QLabel('Name:', self))
        self.sname  = QLineEdit(self)
        line1.addWidget(self.sname)
        self.is_array = QCheckBox('Array?', self)
        line1.addWidget(self.is_array)
        line1.addStretch(1)               # Tight back to left.
        layout.addLayout(line1)
        
        # Next the parameter chooser and axis on line 2:
        
        line2 = QHBoxLayout()
        pchooser = QVBoxLayout()
        
        pchooser.addWidget(QLabel('Parameter', self))
        self.pchooser = ParameterChooser(self)
        pchooser.addWidget(self.pchooser)
        self.chosen_param = QLabel('')
        pchooser.addWidget(self.chosen_param)
        line2.addLayout(pchooser)
        
       

        axisl = QLabel('X Axis:', self)
        self.axis = AxisInput(self)
        axis_layout = QVBoxLayout()
        axis_layout.addWidget(axisl)
        axis_layout.addWidget(self.axis)
        line2.addLayout(axis_layout)
        line2.addStretch(1)            # Left justified.
        layout.addLayout(line2)

        line3 = QHBoxLayout()
        c = QPushButton('Create/Replace')
        line3.addWidget(c)
        line3.addStretch(1)
        
        layout.addLayout(line3)
        layout.addStretch(1)
        
        self.setLayout(layout)


        # Connect internal signals to slots:

        self.sname.textChanged.connect(self.nameTextChanged)
        self.pchooser.selected.connect(self.parameterChanged)
        self.axis.lowChanged.connect(self.axisChanged)
        self.axis.highChanged.connect(self.axisChanged)
        self.axis.binsChanged.connect(self.axisChanged)
        c.pressed.connect(self.make_spectrum)

    # Attribute getter/setter methods.

    def name(self):
        return self.sname.text()
    def setName(self, text):
        self.sname.setText(text)
    def parameter(self):
        return self.chosen_param.text()
    def setParameter(self, p):
        # Caller is responsible for ensuring this is is a legal name
        self.chosen_param.setText(p)

    def low(self):
        return self.axis.low()
    def setLow(self, value):
        self.axis.setLow(value)

    def high(self):
        return self.axis.high()
    def setHigh(self, value):
        self.axis.setHigh(value)
    
    def bins(self):
        return self.axis.bins()
    def setBins(self, value):
        self.axis.setBins(value)

    def array(self):
        return self.is_array.checkState() == Qt.Checked
    def setArray(self, value):
        if value :
            state = Qt.checked
        else:
            state = Qt.Unchecked
        self.is_array.setCheckState(state)


    # Define slot methods:

    def nameTextChanged(self, new_name):
        self.nameChanged.emit(new_name)
    

    def parameterChanged(self, new_path):
        # We turn the new_path, a list of path
        # elements into a full parameter name:

        path = '.'.join(new_path)
        self.chosen_param.setText(path)
        self.parameterSelected.emit(path)

    def axisChanged(self, value):
        # Marshall the dict:

        axis_def = {
            'low'  : self.axis.low(),
            'hi' : self.axis.high(),
            'bins' : self.axis.bins()
        }
        self.axisModified.emit(axis_def)
    
    def make_spectrum(self):
        self.commit.emit()

    def update_parameters(self, client):
        self.pchooser.load_parameters(client)



# Test the UI:
client = None
editor = None


def default(value, default=0):
    if value is None:
        value = default
    return value
    
# Catch parameterSelected signal. If there's no spectrum name, 
# load the name from the parameter:

def loadName(param):
    global editor
    global client
    current_name = editor.name()
    if current_name is None or len(current_name) == 0:
        editor.setName(param)
    # Regardless if the parameter has metadata load that into the axis definition:

    param_info = client.parameter_list(param)['detail'][0]
    editor.setLow(default(param_info['low']))
    editor.setHigh(default(param_info['hi']))
    editor.setBins(default(param_info['bins'], 512))

# A real one would test for and delete an existing 
# spectrum with that name.

def confirm(question):
    dlg = QMessageBox(QMessageBox.Warning, 'Confirm?', 
                    question,
                    QMessageBox.Yes | QMessageBox.No, editor
                )
    dlg = dlg.exec()
    return dlg == QMessageBox.Yes

def gen_name(sname, pname):
    spath = sname.split('.')
    if len(spath) > 1:
        spath = spath[0:-1]
    ppath = pname.split('.')
    spath.append(ppath[-1])
    return '.'.join(spath)



# given a parameter name patter, get a list of matching names:

def param_names(pattern):
    global client
    defs = client.parameter_list(pattern)['detail']
    result =  [x['name'] for x in defs]
    result.sort()
    return result
    

#  If any of the spectra are defined, prompt to proceed or not with their
#  replacement:
#   - Assume there's at least one name
#   - Assume all names can be generated by replacing the last path element with *
#
def proceed(names) :
    global client
    template_name = names[0]  #assume there's at least one
    pattern = template_name.split('.')[0:-1]
    pattern.append('*')
    pattern = '.'.join(pattern)

    defs = client.spectrum_list(pattern)['detail']
    existing_names = [x['name'] for x in defs]

    duplicate_names = [x for x in names if x in existing_names]
    if len(duplicate_names) > 0 :
        c = confirm(f'These spectra already exist {duplicate_names} continuing will replace them, do you want to continue?')
        if c:
            for s in duplicate_names:
                client.spectrum_delete(s)    # Delete the dups so we can replace.
        return c
    else:
        return True                       # no confirmations needed.


#Make an 'array' of spectra.  This is done if the tail of the parameter, replaced
# by * produces several parameter names.  The generated spectra:
#  - All have the same axis definition.
#  - If the spectrum name in the dialog has a period in it, the last part of
#    the name is replaced by the last part of the each parameter name e.g.
#     spectrum.00 with parameters p.0, 0.1, p.2 gives spectrum.0, spectrum.1, spectrum.2
#    if there is no period, the suffix is appended, e.g. spectrum with the
#    same parameters gives spectrum.0, spectrum.1, spectrum.2 as before.
#
def make_spectrum_array(sname, param):

    #  Get the list of parameter names to use:

    param_base = '.'.join(param.split('.')[0:-1])
    param_pattern = param_base + '.*'
    parameters    = param_names(param_pattern)
    # Generate the spectrum names:

    spectrum_names = [gen_name(sname, x) for x in parameters]
    if proceed(spectrum_names):
        low = editor.low()
        high = editor.high()
        bins = editor.bins()

        for sname, pname in  zip(spectrum_names, parameters):
            client.spectrum_create1d(sname, pname, low, high, bins)
        
        client.sbind_spectra(spectrum_names)
        editor.set_name('')

# Respond to the create/replace button:

def create():
    global editor
    global client

    
    sname = editor.name()
    param = editor.parameter()
    # Preconditions to making a spectrum; there must be a spectrum and parameter
    # name.
    if sname is not None and len(sname) > 0 and param is not None and len(param) > 0:
        if not editor.array():
            if len(client.spectrum_list(sname)['detail']) > 0:
                if not confirm(f'{sname} already exists replace it?'):
                    return

                # Delete the existing spectrum

                client.spectrum_delete(sname)
            # Create what is now guaranteed to be a new spectrum.
            low   = editor.low()
            high  = editor.high()
            bins  = editor.bins()
            client.spectrum_create1d(sname, param, low, high, bins)
            client.sbind_spectra([sname])
            editor.setName('')
        else:
            make_spectrum_array(sname, param)
           

def test(host, port):
    global client
    global editor
    app = QApplication(['editor1d-test'])
    c = QMainWindow()

    editor = oneDEditor(c)
    c.setCentralWidget(editor)
    client = cl({'host': host, 'port': port})
    editor.update_parameters(client)
    editor.commit.connect(create)
    editor.parameterSelected.connect(loadName)

    c.show()
    app.exec()

      






