'''
    The Gates widget in this package is the widge for the GUI's gate tab.
    At the top it contains the gate editor tabbed widget while at the bottom, the
    filteredgates.FilteredConditions.  Normally, no signals escape this module from either
    widget.  We are aware of the client and thus can update both the parameter
    and the condition models as needed.
'''

from PyQt5.QtWidgets import(
    QWidget, QVBoxLayout
)
from PyQt5.QtCore import pyqtSignal, QObject

import conditionEditor
import filteredgates
from spectrumeditor import error
from gatelist import common_condition_model    # Condition model.
import ParameterChooser
from rustogramer_client import RustogramerException
class Gates(QWidget):
    '''
    Widget that is what belongs in the Gates tab of the GUI.
    Signals:
        update_gates  - The conditions model must be updated.
        update_params - The parameter omdel must be updated.
        select        - The selected conditions changed.
        clear         - The pattern for the gates list was cleared.
        load          - Load a single selected condition into the appropriate editor and
                        select it.
        delete_selected - Delete all selected conditions
        delete_displayed- Delete all conditions in the list.
        condition_removed - A named condition was deleted from the server
        condition_added - A named condition was added to the server
        NOTE: typically, condition_removed and condition_added come in pairs
              with condition_removed and then immediately following a condition_added both
              with the same name.
    Slots:
        validate_load - Called when the load button is clicked to ensure that
            load can be emitted.  If  overriding this to add validations, call super().validate_load()
            last to ensure the signal does not get emitted prematurely.
        select_changed    - Called when the gate selection has changed.  The current selection is 
                    marshalled and our select is emitted with that selection as a a parameter
        del_selected - marshall the selected items for he delete_selected signals.
    Attributes:
        gatelist - (readonly) returns the filtered gate list widget.
        editor   - (readonly) returns the editor widget.
        actions  - (readonly) returns the GateActionView above the table.
        NOTE: In general you don't need to connect to any signals in these widgets,
              they get filtered and relayed through our signals.
    '''
    update_gates = pyqtSignal()
    update_params= pyqtSignal()              # TODO - not yet signalled!!!!
    select      = pyqtSignal(list)
    clear       = pyqtSignal()
    load        = pyqtSignal(dict)
    delete_selected = pyqtSignal(list)
    delete_displayed = pyqtSignal(list)
    condition_removed = pyqtSignal(str)
    condition_added   = pyqtSignal(str)
    
    def __init__(self, *args):
        super().__init__(*args)
        
        # -- Layout the controls:
        
        layout = QVBoxLayout()
        
        # Top line is a condition editor:
        
        self._editor = conditionEditor.ConditionEditor(self)
        layout.addWidget(self._editor)
        
        # Second row down is the GateActionView:
        
        self._actions = filteredgates.GateActionView(self)
        layout.addWidget(self._actions)
        
        # Finally the  list itself:
        
        self._list = filteredgates.FilteredConditions(self)
        layout.addWidget(self._list)
        
        self.setLayout(layout)
        
        #  Direct signal relays:
        
        self._list.update.connect(self.update_gates)
        self._list.clear.connect(self.clear)
        self._editor.condition_removed.connect(self.condition_removed)
        self._editor.condition_added.connect(self.condition_added)
        
        # Signals that connect to slots which may or may not emit our signals:
        
        self._list.select.connect(self.select_changed)
        self._actions.loadeditor.connect(self.validate_load)
        self._actions.delselected.connect(self.del_selected)
        self._actions.delall.connect(self._deleteall)
    
    # Slots:
    
    def select_changed(self):
        '''  invoked when the list sends a select signal.  All we do is
            get the selection and pass it on to our own select signal:
        '''
        selection = self._list.selection()
        self.select.emit(selection)
        
    def validate_load(self):
        '''
        Determine if the load signal can be emitted.  This is the
        case if there is exactly one selection.  
        
        '''
        selection = self._list.selection()
        if len(selection) == 1:
            self.load.emit(selection[0])
        else:
            error("The 'Load Editor' button requires exactly one condition be selected from the list")
    def del_selected(self):
        '''
        This slot is invoked when the delete selected button is clicked on the
        action widget.  We pull the list of selected items from the condition
        list element and emit it via our delete_selected signal:
        '''
        items = [x['name'] for x in self._list.selection()]
        self.delete_selected.emit(items)
    
    # Non-public slots:
    
    def _deleteall(self):
        # Get the contents of the list and emit them with the delete_displayed signal:
        items = [x['name'] for x in self._list.contents()]
        self.delete_displayed.emit(items)
    
    #  Implement attributes:
    def gatelist(self):
        return self._list
    def editor(self):
        return self._editor
    def actions(self):
        return self._actions
    
class  Controller:
    '''
    This controller mediates between the signals the Gates widget emits and actions
    done in the server.  It should be instantiated along with the Gate widget as that's
    just a view in the MVC architecture where we are a controller and the model is the
    server state.
    '''
    def __init__(self, view, client):
        '''
           view - A Gates widget object that we are the controller of.
           client - a REST client to the server.
        '''
        
        #  Save our internal state:
        
        self._view = view
        self._client = client
        
        #  Connect singnals to our handlers:
    
        view.update_gates.connect(self._update)
        view.update_params.connect(self._pupdate)
        view.clear.connect(self._clear)
        view.load.connect(self._load)
        view.delete_selected.connect(self._delete_list)
        view.delete_displayed.connect(self._delete_list)
        
        # For now, condition_removed and condition_added just update
        # Later we may want a more targeted approach:
        
        # Need them both because deletion is possible with creation.
        
        view.condition_removed.connect(self._update)
        view.condition_added.connect(self._update)
    # Slots   
    
    def _update(self):
        # note that the mask might have changed so the filtered gates model might need to
        # get modified too - do this first:
        mask = self._view.gatelist().filter()
        filteredgates.filtered_gate_model.setFilterWildcard(mask)
        common_condition_model.load(self._client)
        
    def _pupdate(self):
        #  Update the full parameter name model.
        
        ParameterChooser.update_model(self._client)   
        
    def _clear(self): 
        #  Clear the pattern back to * and update:
        
        self._view.gatelist().setFilter('*')
        self._update()
        
    def _load(self, condition):
        # Load the appropriate editor and select its tab
        
        type_string = condition['type']
        self._view.editor().selectTab(type_string)
        eview = self._view.editor().getView(type_string)
        
        # How a view is loaded depends on the type however they all have the name attribute:
        
    
        if type_string == 's':
            eview.setParameter(condition['parameters'][0])
            eview.setLow(condition['low'])
            eview.setHigh(condition['high'])
        elif type_string == 'c' or type_string == 'b':  # Contour and Band are the same view:
            eview.setXparam(condition['parameters'][0])
            eview.setYparam(condition['parameters'][1])
            eview.setPoints(condition['points'])
        elif type_string == '*' or type_string == '+':   # And, Or are the same view:
            eview.setDependencies(condition['gates']) 
        elif type_string ==  '-':
            eview.setCondition(condition['gates'][0])
        elif type_string == 'gc' or type_string == 'gb':
            eview.setParameters(condition['parameters'])
            eview.setPoints(condition['points'])
        elif type_string == 'gs':
            eview.setParameters(condition['parameters'])
            eview.setLow(condition['low'])
            eview.setHigh(condition['high']) 
        elif type_string in ['em', 'am', 'nm']:
            eview.setParameter(condition['parameters'][0])
            eview.setMask(condition['mask'])
        elif type_string == 'T' or type_string == 'F':
            pass                                  # Placeholder because this is a legal type:
        else:
            error(f'Load for condition type {type_string} is not supported')
            return
        eview.setName(condition['name'])       # Success is assured at this oint.
        
    def _delete_list(self, names):
        # Deletes a list of conditions by name:
        
        for condition in names:
            try:
                self._client.condition_delete(condition)
                self._view.editor().signal_removal(condition)
            except RustogramerException as e:
                error(f'Unable to remove condition {condition} : {e} - prior conditions in the selected list were deleted')
                return
        
        
        
#-----------------------------------------------------------------
# Test code:

if __name__ == '__main__':
    from rustogramer_client import rustogramer as rc
       
    from capabilities import set_client 
    
    from PyQt5.QtWidgets import (
        QApplication, QMainWindow
    )
    
    client = rc({'host': 'localhost', 'port':8000})
    set_client(client)
    common_condition_model.load(client)
    ParameterChooser.update_model(client)
    
    app = QApplication([])
    win = QMainWindow()
    
    wid = Gates()
    
    win.setCentralWidget(wid)
    win.show()
    app.exec()
    