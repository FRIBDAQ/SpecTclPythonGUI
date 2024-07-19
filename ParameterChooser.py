''' Provides a Parameter Chooser widget with a shared model.
  By shared model I mean that all instances of a parameter tree
  will contain the same tree of parameters.  This means we only have to
  turn the parameter names into a tree once and that's done it
  for all parameter choosers.

  This is done by constructing a ComboTree and replacing its model
  with our shared model.  loading the tree into any parameter chooser
  will therefore load it into all.

'''


from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtWidgets import (
    QApplication, QWidget,  QMainWindow, QWidget, QLabel, QPushButton,
    QHBoxLayout, QVBoxLayout, QTreeView, QAbstractItemView
)
from ComboTree import ComboTree
from rustogramer_client import rustogramer
import TreeMaker as tm

_parameter_model = QStandardItemModel()


#  These are shamelessly stolen from ParameterChooser and ComboTree:

# Given a standard item and subtree associated iwth it,
# Builds the rest of the tree on top of that item.
#  This is done recursively.
def _subtree(top, children):
    for child in children:
        child_item = QStandardItem(child)
        top.appendRow(child_item)
        if children[child]:    
            _subtree(child_item, children[child])


def update_model(client):
    global _parameter_model
    _parameter_model.clear()
    parameters = client.parameter_list()
    names = [x['name'] for x in parameters['detail']]
    names.sort()
    tree = tm.make_tree(names)
    for key in tree:
        top = QStandardItem(key)
        _subtree(top, tree[key])
        _parameter_model.appendRow(top)


class Chooser(ComboTree):
    def __init__(self, *args):
        global _parameter_view
        super().__init__(*args)
        self.setModel(_parameter_model)

        # If the model has data and the first item
        # has children, expand it in the view it for better sizing:

        top = _parameter_model.item(0,0)
        if top is not None:
            index = _parameter_model.indexFromItem(top)
            self.view().setExpanded(index, True)

        
        

    def load_parameters(self, client):
        self.clear()              # Don't accumulate
        parameters = client.parameter_list()
        names = []
        for parameter in  parameters['detail']:
            names.append(parameter['name'])
        names.sort()
        tree = tm.make_tree(names)
        self.load_tree(tree)


'''
 Megawidget that is a parameter chooser with a 
 label below indicatig which parameter is selected.
'''
class LabeledParameterChooser(QWidget):
    def __init__(self, *args):
        super().__init__(*args)
        layout = QVBoxLayout()
        self._chooser = Chooser(self)
        layout.addWidget(self._chooser)
        self._label = QLabel('', self)
        layout.addWidget(self._label)

        self._chooser.selected.connect(self._changelabel)

        self.setLayout(layout)
    def _changelabel(self, path):
        label = '.'.join(path)
        self._label.setText(label)

    def parameter(self):
        return self._label.text()
    def setParameter(self, text):
        self._label.setText(text)
    def model(self):
        # Return the parameter model.
        return self._chooser.model()

class ParameterTree(QTreeView):
    def __init__(self, *args):
        super().__init__(*args)
        self.setModel(_parameter_model)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setHeaderHidden(True)
    
    def selection(self):
        '''
          Returns a list of parameter names that are selected.
          Note that only terminal nodes can be selected in this scheme.
          
        '''
        selected_indices = self.selectedIndexes()
        selected_items = [self.model().itemFromIndex(x) for x in selected_indices]
        terminals = [x for x in selected_items if not x.hasChildren()]
        
        return [self._build_path(x) for x in terminals]

    def _build_path(self, x):
        # Given a terminal node - build the path to it 
        
        reversed_path = list()
        while x is not None:
            reversed_path.append(x.text())
            x = x.parent()
        reversed_path.reverse()    # Now it's from top to bottom:
        return '.'.join(reversed_path)    
        
#  Test - Make widget 1, connect to SpecTcl to load the model,
#  make widget 2... the two widgets should both list all parameters:

p=None

def sel(l):
    print("Selected: ", l)
    print("Parameter: ", '.'.join(l))

def new_index(i):
    global p
    print("Index ", i)
    print("That's ", p.current_item())
def test(host, port):
    global p
    client = rustogramer({'host': host, 'port': port})
    app = QApplication([])
    mw = QMainWindow()

    c = QWidget()
    l = QHBoxLayout()
    p1 = Chooser(c)
    p1.load_parameters(client)
    p1.selected.connect(sel)
    p = p1
    p1.currentIndexChanged.connect(new_index)
    l.addWidget(p1)
    p2 = Chooser(c)
    l.addWidget(p2)
    c.setLayout(l)


    mw.setCentralWidget(c)
    mw.show()
    app.exec()
    
def list_tree():
    print(tree_widget.selection())
def tree(host, port):
    global tree_widget
    client = rustogramer({'host': host, 'port': port})
    update_model(client)
    app = QApplication([])
    mw = QMainWindow()

    container = QWidget()
    layout = QVBoxLayout()
    
    tree_widget  = ParameterTree()
    layout.addWidget(tree_widget)
    button = QPushButton('List')
    layout.addWidget(button)
    container.setLayout(layout)
    
    button.clicked.connect(list_tree)
    
    mw.setCentralWidget(container)
    
    mw.show()
    app.exec()