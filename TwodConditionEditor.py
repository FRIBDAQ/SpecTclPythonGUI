'''
   Provides an editor for two dimensional conditions like gates and bands.
   The idea is that you have an editable list in which x/y points can be  inserted
   2d gates need:
   *   A condition name.
   *   An X parameter
   *   A Y parameter.
   *   A list of points (settable minimum number of required points defaults to 3)
   
   
'''

from PyQt5.QtWidgets import (
    QLabel, QLineEdit, QPushButton, QWidget,
    QHBoxLayout, QVBoxLayout, QCheckBox
)
from PyQt5.QtGui import QDoubleValidator
from PyQt5.QtCore import pyqtSignal
from PyQt5.Qt import *


from editablelist import EditableList
from ParameterChooser import LabeledParameterChooser
from spectrumeditor import error
from parse import parse

class PointListEditor(QWidget):
    ''' This widget factors out editing 2d points from the
        various 2d contision edtiros (contours, bands, gamma
        contours and gamma bands.).   The shape of the widget
        is line edits for X/Y point coordinates and an editable
        list to hold the coordinates.  Coordinates are put in the
        list box in the form: "( {x}, {y})" which also allows
        us to use the parse method to pull them back out.
        The editable list add signal is internally absorbed into
        the _addpoint internal slot.  It is not intended that this
        be overridden.  It includes validation.
    Signals: None
    Public Slots: None  
    Attributes:
        x      - X value (for point)
        y      - Y value (for point)
        points - list of points, each point containing {'x':xxxx, 'y':yyyy}  
        
    Normally a class that includes this widget will 
    relay these attributes...or at least the points attribute.    
    '''
    def __init__(self, *args):
        super().__init__(*args)
        #  |                                       |
        #  | X: [ entry ]     +------------------+ |
        #  | Y: [ entry ]     | Point list       | |
        #  |                  +------------------+ |
        #  |                                       |
        layout = QHBoxLayout()
        x     = QHBoxLayout()
        y     = QHBoxLayout()
        coord = QVBoxLayout()
        
        x.addWidget(QLabel('X ', self))
        self._x = QLineEdit('0.0', self)
        self._x.setValidator(QDoubleValidator())
        x.addWidget(self._x)
        coord.addLayout(x)
        
        y.addWidget(QLabel("Y ", self))
        self._y = QLineEdit('0.0', self)
        self._y.setValidator(QDoubleValidator())
        y.addWidget(self._y)
        coord.addLayout(y)
        coord.addStretch(1)
        layout.addLayout(coord)
        
        self._points =  EditableList('Points', self)
        layout.addWidget(self._points)
        
        self.setLayout(layout)
        
        # Internally catch the Add signal from the editable list
        # IF all goes well it will call the addpoint slot.
        
        self._points.add.connect(self._addpoint)
    # Implement attributes:
    
    def x(self):
        try:
            return float(self._x.text())
        except:
            return None      # Float conversion failed.
    def setX(self, value):
        self._x.setText(f'{value}')
    
    def y(self):
        try:
            return float(self._y.text())
        except:
            return None
    def setY(self, value):
        self._y.setText(f'{value}')
        
    def points(self):
        text_list = self._points.list()
        result = list()
        
        for item in text_list:
            parsed = parse("({}, {})", item)
            result.append({'x': parsed[0], 'y': parsed[1]})
        return result
    def setPoints(self, pts):
        items = list()
        for pt in pts:
            x = pt['x']
            y = pt['y']
            items.append(f'({x}, {y})')
        self._points.setList(items)    
    # internal slots:
    
    def _addpoint(self):
        x = self.x()
        y = self.y()
        if x is None or y is None:
            return         # Need both x and y.
        
        self._points.appendItem(f'({x}, {y})')    
class TwodConditionEditor(QWidget):
    '''
        Signals:
           commit - Create/replace the condition.
        Slots:
            validate - Called from the Create/Replace button's clicked signal. If
                -   There's a condition name.
                -   There's an x parameter.
                -   There's a Y parameter
                -   There are at lesat the minimum required points
                commit is emitted.
                If any of these conditions is not met, an error is popped up.
            addpoint - Add an x/y poiunt to the list.
        Attributes:
            name - name of the condition.
            xparam - name of the x parameter.
            yparam - name of the y parameter.
            points - list of points, each point containing {'x':xxxx, 'y':yyyy}  
            minpoints - Minimum allowed # of points     
    '''
    commit = pyqtSignal()
    def __init__(self, *args):
        super().__init__(*args)
        
        layout = QVBoxLayout()
        
        # Top is the condition name prompter:
        
        line1 = QHBoxLayout()
        line1.addWidget(QLabel('Name: ', self))
        self._name = QLineEdit(self)
        line1.addWidget(self._name)
        
        layout.addLayout(line1)
        
        #   Line 2 are the X/Y parameters:
        
        line2 = QHBoxLayout()
        line2.addWidget(QLabel('X param', self))
        self._xparam = LabeledParameterChooser(self)
        line2.addWidget(self._xparam)
        line2.addWidget(QLabel('Y param', self))
        self._yparam = LabeledParameterChooser(self)
        line2.addWidget(self._yparam)
        line2.addStretch(1)
        
        layout.addLayout(line2)
        
        # Line 3 is a point list editor.
        
        ptlist = QHBoxLayout()
        self._pointlist = PointListEditor(self)
        ptlist.addWidget(self._pointlist)
        ptlist.addStretch(1)
        layout.addLayout(ptlist)
        
        
        #  The create/replace is bottom.
        
        commit = QHBoxLayout()
        self._commit = QPushButton('Create/Replace', self)
        commit.addWidget(self._commit)
        commit.addStretch(1)
        
        layout.addLayout(commit)
        layout.addStretch(1)
        
        self.setLayout(layout)
        
        # Attribute initialization

        self._minpoints = 3        # Contour
        
        
        
        # Similarly the commit button goes to our validate slot
        
        self._commit.clicked.connect(self.validate)
    
    # Implement attributes:
    
    def name(self):
        return self._name.text()
    def setName(self, txt):
        self._name.setText(txt)
        
    def xparam(self):
        return self._xparam.parameter()
    def setXparam(self, name):
        self._xparam.setParameter(name)
        
    def yparam(self):
        return self._yparam.parameter()
    def setYparam(self, name):
        self._yparam.setParameter(name)
        
    def minpoints(self):
        return self._minpoints
    def setMinpoints(self, value):
        self._minpoints = value
    
    #   These attributes relay the points attribute from
    #   self._points.
    
    def points(self):
        return self._pointlist.points()
    def setPoints(self, pts):
        self._pointlist.setPoints(pts)
    
    # Public Methods:
    
    def clear(self):
        self.setName('')
        self.setXparam('')
        self.setYparam('')
        self.setPoints(list())
        self._pointlist.setX(0.0)
        self._pointlist.setY(0.0)
        
    
        
    #   slots...note that if derived classes want additional
    #  Validations they should perform the first before invoking
    #  super().validate()
    #
    def validate(self):
        if self._empty(self.name()):
            error("A condition name is required")
            return
        if self._empty(self.xparam()) or self._empty(self.yparam()):
            error('Both X and Y parameters are must be selected')
            return
        m = self.minpoints()
        if len(self.points()) < m:
            error(f'At least {m} points are required for this type of condition.')
            return
        self.commit.emit()
    
    #  Utilities
    def _empty(self, txt):
        return txt is None or txt == '' or txt.isspace()
        
        
class Gamma2DEditor(QWidget):
    ''' Gamma 2d editors; have a name list an arbitrary list of
    parameters and a point list.  They can share a common
    editor widget which only needs to be told how many points
    are minimally required for the condition (3 for a contour, 
    2 for a band):
    
    Signals:
        appendarray - Help me by appending an array of params that match the
                    wild card.
        commmit - A valid condition can be accepted.
    Slots:
        validate - Called when the Create/Replace button is 
            clicked.  Must determine if a valid condition is in the
            editor and emit commit if so.   See the validate method
            for a description of the validations performed.  Note
            that if overriding this slot, typically you should first
            do your own validation _then_ invoke super().validate()
            if your validations pass, so that commit is properly signalled.
    Attributes:
        name -   Name of the condition.
        parameters - List of parameters to check
        points     - List of point dicts in the editor {'x': x, 'y':y}
                     
    '''
    commit = pyqtSignal()
    appendarray = pyqtSignal(str)
    def __init__(self, *args):
        super().__init__(*args)
        
        layout = QVBoxLayout()
        
        # Top is the name prompter:
        
        row1 = QHBoxLayout();
        row1.addWidget(QLabel('Name: ', self))
        self._name = QLineEdit(self)
        row1.addWidget(self._name)
        layout.addLayout(row1)
        
        # Next is the parameter chooser and editable list
        # of parameter names:
        
        row2 = QHBoxLayout()
        
        params = QVBoxLayout()
        self._parameter = LabeledParameterChooser(self)
        params.addWidget(self._parameter)
        self._array = QCheckBox('Array', self)
        params.addWidget(self._array)
        params.addStretch(1)
        
        row2.addLayout(params)
        self._parameters = EditableList('parameters', self)
        row2.addWidget(self._parameters)
        row2.addStretch(1)
        layout.addLayout(row2)
        
        # Point list:
        
        row3 = QHBoxLayout()
        self._points = PointListEditor(self)
        row3.addWidget(self._points)
        row3.addStretch(1)
        layout.addLayout(row3)
        
        # Confirmer:
        
        row4 = QHBoxLayout()
        self._accept = QPushButton("Create/Replace")
        row4.addWidget(self._accept)
        row4.addStretch(1)
        layout.addLayout(row4)
        
        layout.addStretch(1)
        
        self.setLayout(layout)
        
        #  Default minpoints value:
        
        self._minpoints = 3     # For contour.
        
        # Internal signal handling:
        
        self._accept.clicked.connect(self.validate)
        self._parameters.add.connect(self._addparameter)
    
    # Attributes:
    
    def name(self):
        return self._name.text()
    def setName(self, name):
        self._name.setText(name)
    
    def parameters(self):
        return self._parameters.list()
    def setParameters(self, param_list):
        self._parameters.setList(param_list)

    def points(self):
        return self._points.points()
    def setPoints(self, pts):
        self._points.setPoints(pts)
    
    def minpoints(self):
        return self._minpoints
    def setMinpoints(self, value):
        self._minpoints = value
    
    #  Public methods:
    
    def clear(self):
        self.setName('')
        self.setParameters(list())
        self.setPoints(list())
        self._points.setX(0.0)
        self._points.setY(0.0)
    
    # Append parameter
    
    def appendParameter(self, name):
        self._parameters.appendItem(name)
        
    # Slots:
    
    def validate(self):
        '''
          Ensure that we have a valid gate before emittiung
          commit:
          *   There must be a condition name.
          *   There must be at least two parameters.
          *   There must be at leat minpoints points.
          If any of these is not the case, an error dialog
          is posted and commit is _not_ emitted.
          If all of these are satisfied, commit is emitted.
          
        '''
        n = self.name()
        if n == '' or n.isspace():
            error('A condition name is required')
            return
        if len(self.parameters()) < 2:
            error('2d gamma conditions require at least two parameters')
            return
        m = self.minpoints()
        if len(self.points()) < m:
            error(f'At least {m} points must be accepted.')
            return
        #  All validations passed so:
        self.commit.emit()
        
    # Private methods:
    
    def _addparameter(self):
        
        name = self._parameter.parameter()
        if name == '' or name.isspace():
            return
        if self._arrayChecked() :
            name_list = name.split('.')
            
            name_list = name_list[:-1]
            name_pattern = '.'.join(name_list) + '.*'
            self.appendarray.emit(name_pattern)
        else:
            self._parameters.appendItem(name)
    
    def _arrayChecked(self):
        if self._array.checkState() ==  Qt.Checked:
            return True
        else: 
            return False      
    
    
    
        
        
    
#----------------- Test code ---------------------


def newgate():
    print("New gate accepted:")
    print("  name", wid.name())
    print("  xpar", wid.xparam())
    print("  ypar", wid.yparam())
    print("  pts ", wid.points())

def ggate():
    print("Gamma gate accepted:")
    print("   namne", gwid.name())
    print("   params", gwid.parameters())
    print("   pts   ", gwid.points())
if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication, QMainWindow
    from rustogramer_client import rustogramer as rc
    from ParameterChooser import update_model
    client = rc({'host': 'localhost', 'port': 8000})
    update_model(client)
    
    app = QApplication([])
    win = QMainWindow()
    
    top = QWidget()
    layout = QHBoxLayout()
    wid = TwodConditionEditor()
    wid.commit.connect(newgate)
    layout.addWidget(wid)
    
    gwid = Gamma2DEditor()
    gwid.commit.connect(ggate)
    layout.addWidget(gwid)
    
    top.setLayout(layout)
    
    win.setCentralWidget(top)
    win.show()
    app.exec()
        
        
        