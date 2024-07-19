from PyQt5.QtWidgets import (
    QTabWidget, QWidget, 
    QApplication, QMainWindow
)
from PyQt5.QtCore import pyqtSignal

import TrueFalseConditionEditor
import CompoundConditionEditor
import NotConditionEditor
import SliceConditionEditor
import TwodConditionEditor
import MaskGateEditor
from capabilities import (
    ConditionTypes, get_supported_condition_types, set_client, get_client
)
from rustogramer_client import rustogramer as rc, RustogramerException 
from spectrumeditor import error
from gatelist import common_condition_model

''' This module provides a tabbed widget that is the gate editing part of
    the Gate tab.  As with the spectrum editor, each supported gate type.
    The key  driver is a set of widgets and controllers associated with them
    that are used to edit each gate type.  There is alwso some capabilities query
    magic used to supress tabs for editor views that are not suported.
    
    What drives all of this is a map keyed by condition type with values
    that are n-tuples containing:
    *  The tab label for that gate type
    *  The class for that gate type's editor view.
    *  The class for that gate type's editor controller.
    
    
'''

#   gate controller types:

class GateController:          # Base class
    ''' Ultimate base class for controllers that make gates (conditions)
       Views used by this controller base class must:
       - provide a commit signal that is emitted when it's time to make the gate.
       - provide a name attribute that returns the proposed conditio name.
       
       Concrete subclasses must implement
       create(name) - to create the actual gate...all error handling and signalling is done by us.
       
    '''
    def __init__(self, view, client, editor):
        self._view = view
        self._client = client
        self._editor = editor
        self._view.commit.connect(self._create)            
    
    def _create(self):
        name = self._view.name()
        if name == '' or name.isspace():
            return
        try:
            self.create(name)
            self._view.clear()
        except RustogramerException as e:
            error(f'Failed to create condition: {name}: {e}')
            return
        
        # success if we got here so:
        
        self._editor.signal_removal(name)    # in case this is a replace.
        self._editor.signal_added(name)
        self._view.setName('')               # Clear the gate name on success.
    
    def create(self, name):
        pass                                 # Derived classes must override.
    
    
class ConstantGateController(GateController):
    # Base class for  T and F gates.
    def __init__(self, view, client, editor):
        super().__init__(view, client, editor)
        
    
    def create(self, name):
        type = self._view.gate_type()
    
        if type:
            self._client.condition_make_true(name)
        else:
            self._client.condition_make_false(name)
    
class TrueGateController(ConstantGateController):
    def __init__(self, view, client, editor):
        super().__init__(view, client, editor)
        view.setGate_type(True)
        
        
    
class FalseGateController(ConstantGateController):
    def __init__(self, view, client, editor):
        super().__init__(view, client, editor)
        view.setGate_type(False)


class CompoundGateController(GateController):
    # Base class for And/Or gates, concrete derivations
    # must implement make_gate
    # We'll haul the dependencies from the view.
    #
    def __init__(self, view, client, editor):
        super().__init__(view, client, editor)
    
    def create(self, name): 
        self.make_gate(name, self._view.dependencies())
    
class AndGateController(CompoundGateController):
    def __init__(self, view, client, editor):
        super().__init__(view, client, editor)
    def make_gate(self, name, dependencies):
        self._client.condition_make_and(name, dependencies)

class OrGateController(CompoundGateController):
    def __init__(self, view, client, editor):
        super().__init__(view, client, editor)
    def make_gate(self, name, dependencies):
        self._client.condition_make_or(name, dependencies)
            

class NotGateController(GateController):
    def __init__(self, view, client, editor):  
        super().__init__(view, client, editor)
    
    def create(self, name):
        self._client.condition_make_not(name, self._view.condition())
        
    

class SliceGateController(GateController):
    def __init__(self, view, client, editor):
        super().__init__(view, client, editor)
    def create(self, name):
        self._client.condition_make_slice(
            name, self._view.parameter(), self._view.low(), self._view.high()
        )
        
    

class ContourController(GateController):
    def __init__(self, view, client, editor):
        super().__init__(view, client, editor)
        view.setMinpoints(3)    # Contours need 3 pts.
    def create(self, name):
        self._client.condition_make_contour(
            name, self._view.xparam(), self._view.yparam(), self._view.points()
        )
        
    

class BandController(GateController):
    def __init__(self, view, client, editor):
        super().__init__(view, client, editor)
        view.setMinpoints(2)     # Bands only need two points.
    def create(self, name):
        self._client.condition_make_band(
            name, self._view.xparam(), self._view.yparam(), self._view.points()
        )
        
    

class GammaContourController(GateController):
    def __init__(self, view, client, editor):
        super().__init__(view, client, editor)
        view.setMinpoints(3)
        view.appendarray.connect(self._appendarray)
    def create(self, name):
        self._client.condition_make_gamma_contour(
            name,  self._view.parameters(), self._view.points()
        )
    def _appendarray(self, pattern):
        param_descs = self._client.parameter_list(pattern)['detail']
        names = [x['name'] for x in param_descs]
        names.sort()
        for name in names:
            self._view.appendParameter(name)
        
   

class GammaBandController(GateController):
    def __init__(self, view, client, editor):
        super().__init__(view, client, editor)
        view.setMinpoints(2)
        view.appendarray.connect(self._appendarray)
    def create(self, name):
        self._client.condition_make_gamma_band(
            name,  self._view.parameters(), self._view.points()
        )
    def _appendarray(self, pattern):
        param_descs = self._client.parameter_list(pattern)['detail']
        names = [x['name'] for x in param_descs]
        names.sort()
        for name in names:
            self._view.appendParameter(name)
    

class GSliceController(GateController):
    def __init__(self, view, client, editor):
        super().__init__(view, client, editor)
        view.appendarray.connect(self._appendarray)
    def create(self, name):
        self._client.condition_make_gamma_slice(
            name, self._view.parameters(), self._view.low(), self._view.high()
        )
    def _appendarray(self, pattern):
        param_descs = self._client.parameter_list(pattern)['detail']
        names = [x['name'] for x in param_descs]
        names.sort()
        for name in names:
            self._view.appendParameter(name)
    

class MaskEqualController(GateController):
    def __init__(self, view, client, editor):
        super().__init__(view, client, editor)
    def create(self, name):
        self._client.condition_make_mask_equal(name, self._view.parameter(), self._view.mask())
        

class MaskAndController(GateController):
    def __init__(self, view, client, editor):
        super().__init__(view, client, editor)
    def create(self, name):
        self._client.condition_make_mask_and(name, self._view.parameter(), self._view.mask())
        
    
class MaskNandController(GateController):
    def __init__(self, view, client, editor):
        super().__init__(view, client, editor)
    def create(self, name):
        self._client.condition_make_mask_nand(name, self._view.parameter(), self._view.mask())
        
        
_condition_table = {
    ConditionTypes.Slice: ('Slice', SliceConditionEditor.EditorView, SliceGateController),
    ConditionTypes.Contour: ("Contour", TwodConditionEditor.TwodConditionEditor, ContourController),
    ConditionTypes.And: ("And", CompoundConditionEditor.EditorView, AndGateController),
    ConditionTypes.Or: ("Or", CompoundConditionEditor.EditorView, OrGateController),
    ConditionTypes.Not: ("Not", NotConditionEditor.EditorView, NotGateController),
    ConditionTypes.Band: ("Band", TwodConditionEditor.TwodConditionEditor, BandController),
    ConditionTypes.GammaContour: ("G Contour", TwodConditionEditor.Gamma2DEditor, GammaContourController),
    ConditionTypes.GammaBand: ('G Band', TwodConditionEditor.Gamma2DEditor, GammaBandController),
    ConditionTypes.GammaSlice: ('G Slice', SliceConditionEditor.GammaEditorView, GSliceController),
    ConditionTypes.MaskEqual: ('Mask==', MaskGateEditor.View, MaskEqualController),
    ConditionTypes.MaskAnd: ("Mask *", MaskGateEditor.View, MaskAndController),
    ConditionTypes.MaskNand: ("Mask -*", MaskGateEditor.View, MaskNandController),
    ConditionTypes.FalseCondition: ('False', 
        TrueFalseConditionEditor.TrueFalseView,  FalseGateController
    ),
    ConditionTypes.TrueCondition: ('True', 
        TrueFalseConditionEditor.TrueFalseView, TrueGateController
    )
}

#  This is a table of condition type strings to tab label strings. It must be
#  kept synchonrized with the _condition_table above:

_type_to_label_table = {
    's' : 'Slice',
    'c' : "Contour",
    '*' : "And",
    '+' : "Or",
    '-' : "Not",
    'b' : "Band",
    'gc': "G Contour", 
    'gb': 'G Band',
    'gs': 'G Slice',
    'em': 'Mask==',
    'am': "Mask *",
    'nm': "Mask -*",
    'F' : 'False', 
    'T' : 'True', 
}
class ConditionEditor(QTabWidget):
    
    '''This provides the tabbed widget and stocks it with tabs that are germane to the
       server program.   This module aslo includes 'controller' classes, instances of which
       are created and used to handle events/signals from the editor views that are in each tab
       to actually do the stuff needed to the model (server program) to create/modify gates.
    '''
    condition_removed = pyqtSignal(str)
    condition_added   = pyqtSignal(str)
    def __init__(self, *args):
        super().__init__(*args)
        client = get_client()
        self._client = client
        supported_conditions = get_supported_condition_types()
        self._controllers = dict()
        self._views       = dict()

        for  ctype in _condition_table.keys():
            if ctype in supported_conditions:
                (label, viewclass, controllerclass) = _condition_table[ctype]
                widget = viewclass(self)
                controller = controllerclass(widget, client, self)
                self._controllers[label] = controller
                self._views[label] = widget
                self.addTab(widget, label)
    #  Utilities the controller might need.
    
    def signal_removal(self, name):
        # For now update the model:
        self.condition_removed.emit(name)
    def signal_added(self, name):
        # This is always called after signal_removal so we don't do anything in test mode.
        self.condition_added.emit(name)
        
    def getController(self, type_string):
        return self._controllers[_type_to_label_table[type_string]]
    def getView(self, type_string):
        return self._views[_type_to_label_table[type_string]]
    def selectTab(self, type_string):
        widget = self.getView(type_string)
        tab_no = self.indexOf(widget)
        self.setCurrentIndex(tab_no)

if __name__ == '__main__':
        from ParameterChooser import update_model
        
        set_client(rc({'host':'localhost', 'port':8000}))
        update_model(get_client())
        common_condition_model.load(get_client())
        app = QApplication([])
        win = QMainWindow()
        wid = ConditionEditor()
        
        win.setCentralWidget(wid)
        win.show()
        app.exec()
        
        