''' Top level GUI (Main program)
    the following program parameters are supported

    --host - host running rustogramer or SpecTcl - defaults to 'localost'
    --port - port on which the REST server is listening (defaults to 8000)
    --service - Defaults to None - service the REST server advertises
    --service_user - User the service is advertised under defaults to the name of the current user.

'''

from argparse import ArgumentParser
import OsServices
import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QWidget
)
from spectra import SpectrumWidget
import spectra
import argparse
import capabilities
import parametercontroller
import parameditor
import gatelist
import gates
from treevariable import TreeVariableView, common_treevariable_model
from treevariableController import TreeVariableController
from rustogramer_client import rustogramer as RestClient

import FileMenu
import DataSourceMenu
import FilterMenu
import SpectraMenu
import GateMenu
import HelpMenu
import bindings
import bindingscontroller
import waveformview, waveformcontroller


def _updateBindableSpectra(index):
    if index == bindings_tab_index:
        FileMenu.bindings_controller.updateValidSpectra()
        
def setup_menubar(win, client):
    '''
    Sets up the menubar and the menus in it:
    File, "Data Source", Filters[If SpecTcl], Gate, Help
    
    Note as well, that the contents of some menus will depend on the 
    program capabilties as well.
    
    Parameters:
    * win - Must be the application main window.
    * client -  is the client object through which we make REST requests of the server.
    '''
    # Our menu objects need to be global:
    
    global file_menu_object
    global data_source_menu_object
    global filter_menu_object
    global spectra_menu_object
    global gate_menu_object
    global help_menu_object
    
    menubar = win.menuBar()
    file_menu = menubar.addMenu('&File')
    file_menu_object = FileMenu.FileMenu(file_menu, client, win)
    
    data_source_menu = menubar.addMenu('Data &Source')
    data_source_menu_object = DataSourceMenu.DataSourceMenu(data_source_menu, client, win)
    
    if capabilities.get_program() == capabilities.Program.SpecTcl:
        filter_menu = menubar.addMenu('Filters')
        filter_menu_object = FilterMenu.FilterMenu(filter_menu, client, win, data_source_menu_object)
    spectrum_menu = menubar.addMenu("&Spectra")
    spectra_menu_object = SpectraMenu.SpectraMenu(spectrum_menu, client, win, file_menu_object)
    
    gate_menu = menubar.addMenu("&Gate")
    gate_menu_object = GateMenu.Gate(gate_menu, client, win, spectra_menu_object)
    
    
    help_menu = menubar.addMenu("&Help")
    help_menu_object = HelpMenu.Help(help_menu)

# Per issue #152 style the tabs so the selected one is more visible
#  see:   
# #  https://doc.qt.io/qt-5/stylesheet-examples.html#customizing-qtabwidget-and-qtabbar
# and:
#  https://doc.qt.io/qtforpython-6/overviews/stylesheet-examples.html
def setTabStyle(app):
    app.setStyleSheet('''
QTabWidget::pane { /* The tab widget frame */
    border-top: 2px solid #C2C7CB;
}

QTabWidget::tab-bar {
    left: 5px; /* move to the right by 5px */
}

/* Style the tab using the tab sub-control. Note that
    it reads QTabBar _not_ QTabWidget */
QTabBar::tab {
    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                stop: 0 #E1E1E1, stop: 0.4 #DDDDDD,
                                stop: 0.5 #D8D8D8, stop: 1.0 #D3D3D3);
    border: 2px solid #C4C4C3;
    border-bottom-color: #C2C7CB; /* same as the pane color */
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    min-width: 8ex;
    padding: 2px;
}

QTabBar::tab:selected, QTabBar::tab:hover {
    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                stop: 0 #fafafa, stop: 0.4 #f4f4f4,
                                stop: 0.5 #e7e7e7, stop: 1.0 #fafafa);
}

QTabBar::tab:selected {
    border-color: #9B9B9B;
    border-bottom-color: #C2C7CB; /* same as pane color */
}

QTabBar::tab:!selected {
    margin-top: 2px; /* make non-selected tabs look smaller */
}

/* make use of negative margins for overlapping tabs */
QTabBar::tab:selected {
    /* expand/overlap to the left and right by 4px */
    margin-left: -4px;
    margin-right: -4px;
}

QTabBar::tab:first:selected {
    margin-left: 0; /* the first selected tab has nothing to overlap with on the left */
}

QTabBar::tab:last:selected {
    margin-right: 0; /* the last selected tab has nothing to overlap with on the right */
}

QTabBar::tab:only-one {
    margin: 0; /* if there is only one tab, we don't want overlapping margins */
}
''')
    
PORTMAN_PORT=30000

parsed_args = argparse.ArgumentParser(
    prog='Gui.py',
    description='User interface GUI for SpecTcl and rustogramer programs',
    epilog ='If --service and --port are provided, --service overrides.  If --service is not provided, --port is used.'
)
parsed_args.add_argument('-H', '--host', 
    default='localhost', action='store', help='Host on which the histogram program is running'
)
parsed_args.add_argument('-p', '--port', 
    default=8000, action='store', help='Port on which the histogramer REST server is listening for connections defaults to "8000"'
)
parsed_args.add_argument('-s', '--service', default=None, action='store', help='Service the REST server advertises defaults to None')
parsed_args.add_argument('-u', '--service-user', default=OsServices.getlogin(), action='store', help=f'Username the REST server advertises under defaults to "{OsServices.getlogin()}"')

args = parsed_args.parse_args()

client_args = {'host' : args.host, 'port':args.port, 'pmanport': PORTMAN_PORT}
print(client_args)
if args.service is not None:
    client_args['service'] = args.service
    client_args['user']    = args.service_user
    

client = RestClient(client_args)
spectra.set_client(client)
capabilities.set_client(client)
gatelist.common_condition_model.load(client)


#  Build the GUI:

app = QApplication(sys.argv)
main = QMainWindow()

# Style sheet to make the selected tabs stand out more:

setTabStyle(app)

tab_num = 0
tabs = QTabWidget()
spectrum_view = spectra.SpectrumWidget()
tabs.addTab(spectrum_view,'Spectra')         
tab_num += 1

param_view= parameditor.ParameterEditor()
tabs.addTab(param_view, 'Parameters')       
tab_num += 1
param_controller = parametercontroller.ParameterController(
    param_view, client, spectrum_view
)

if capabilities.get_program() == capabilities.Program.SpecTcl:
    common_treevariable_model.load(client)
    var_view = TreeVariableView()
    var_controller = TreeVariableController(var_view, client)
    tabs.addTab(var_view, 'Variables')
    tab_num += 1
condition_view = gates.Gates()
condition_controller = gates.Controller(condition_view, client)
tabs.addTab(condition_view, 'Gates')
tab_num += 1

#  The new tab to handle spectrum binding sets:
bindings_view = bindings.BindingGroupTab()
FileMenu.bindings_controller = bindingscontroller.BindingsController(client, bindings_view)
tabs.addTab(bindings_view, 'BindSets')
bindings_tab_index = tab_num
tabs.currentChanged.connect(_updateBindableSpectra)
tab_num += 1 

# If the server suports waveforms add a tab with the waveform view:

if capabilities.has_waveforms():
    wave_form_view = waveformview.WaveformViewTab()
    wave_form_controller = waveformcontroller.WaveformController(
        wave_form_view, client
    )                               # hook the controller and view together.
    tabs.addTab(wave_form_view, 'Waveforms')
    waveform_view_tab_index = tab_num
    tab_num += 1

# if you add tabs, be sure to update tab_num so that, if necessary a tab can save its tab number.
#  Note that the tab number below are capability dependent.

# We want to update the available spectra when this tab is selectged:




main.setCentralWidget(tabs)

# 

setup_menubar(main, client)

main.show()
app.exec()
 
