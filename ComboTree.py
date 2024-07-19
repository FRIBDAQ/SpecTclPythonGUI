''' This package provides a combobox which displays choices as a tree.
    The tree items, when selected will send the itemselected singal
    and pass, as an argument a list which contains the path of the item.
    e.g. suppose the item:

    a +
      -> b +
           > c (this item)
    is selected, the signal will send the list:
    ['a', 'b', 'c']
 
    This code is based loosely on an example described in:

    https://stackoverflow.com/questions/27172160/how-to-implement-a-tree-based-qcombobox

    Several modifications, however:

    *  A specialized QTreeView is used to actually supply the
       mouse button release events that are transformed into a signal
    *  The model is included with the TreeComboBox so that users
    can:
        -   Load the full tree from the representation created by TreeMaker
        -   Users can ask the box to clear the tree.

    These are the use cases I can see for the application.
'''
from PyQt5.QtCore import *
from PyQt5.QtWidgets import (
    QComboBox, QTreeView, 
    QApplication, QFrame
)
from PyQt5.QtGui import (
    QStandardItem, QStandardItemModel
)
import TreeMaker as tm

''' Specialized tree view that processes mouse button releases
    signal the path of the item selected as the 'chosen' custom signal.
'''
class TreeView(QTreeView):

    def __init__(self, parent=None):
        super().__init__(parent)
    
    
class ComboTree(QComboBox):
    selected = pyqtSignal(list)
    def __init__(self, *args):
        super().__init__(*args)

        # Set up the view:

        self.__skip_next_hide = False
        self._last_index = None
        tree_view = TreeView(self)
        tree_view.setFrameShape(QFrame.NoFrame)
        tree_view.setEditTriggers(tree_view.NoEditTriggers)
        tree_view.setAlternatingRowColors(True)
        tree_view.setSelectionBehavior(tree_view.SelectRows)
        tree_view.setWordWrap(True)
        tree_view.setAllColumnsShowFocus(True)
        tree_view.setHeaderHidden(True)
        self.setView(tree_view)
        self.SizeAdjustPolicy(QComboBox.AdjustToContents)

        self.view().viewport().installEventFilter(self)

        # set up the model:

        model = QStandardItemModel(self)
        self.setModel(model)

    ''' Clear the model and update the combobox: '''
    def clear(self):
        self.model().clear()

    ''' load a tree from the TreeMaker package '''
    def load_tree(self, tree):
        # At the top level we get each top level key and
        # then recursively get its children:
        model = self.model()
        for key in tree:
            top = QStandardItem(key)
            self._subtree(top, tree[key])
            model.appendRow(top)


    #   Internal methods:

    # Given a standard item and subtree associated iwth it,
    # Builds the rest of the tree on top of that item.
    #  This is done recursively.
    def _subtree(self, top, children):
        for child in children:
            child_item = QStandardItem(child)
            top.appendRow(child_item)
            if children[child]:    
                self._subtree(child_item, children[child])


    def showPopup(self):
        self.setRootModelIndex(QModelIndex())
        super().showPopup()

    def hidePopup(self):
        self.setRootModelIndex(self.view().currentIndex().parent())
        self.setCurrentIndex(self.view().currentIndex().row())
        if self.__skip_next_hide:
            self.__skip_next_hide = False
        else:
            super().hidePopup()

    def selectIndex(self, index):
        self.setRootModelIndex(index.parent())
        self.setCurrentIndex(index.row())

    def eventFilter(self, object, event):
        if event.type() == QEvent.MouseButtonPress and object is self.view().viewport():
            index = self.view().indexAt(event.pos())
            self.mouse(event)
            self.__skip_next_hide = not self.view().visualRect(index).contains(event.pos())
        return False
    def _path(self, idx):
        # Given a model index get its path:
        model = self.model()
        item = model.itemFromIndex(idx)
        result = []
        while item is not None:
            result.insert(0, item.text())
            item = item.parent()
        return result            

    #  Called when a mouse event hits...signal the selected item.
    # with its path.  Note that we only signal on terminal nodes.
    #
    def mouse(self, e):
        pos = e.pos()
        view = self.view()
        idx = view.indexAt(pos)
        model= self.model()
        if model is not None:
            self._lastIndex = idx
            if not model.itemFromIndex(idx).hasChildren():
                self.selected.emit(self._path(idx))
        super().mouseReleaseEvent(e)
    
    def _root_item(self, ):
        current = self.model().QModelIndex()
        p = current.parent()
        while p is not None:
            current = p
        return current

    def current_item(self):
        if self._last_index is not None:
            return self._path(self._lastIndex)
        else:
            return ""            

# Test functions:

def sel_slot(data):
    print("Selected: ", data)


# Low level test where we put some stuff in the model without using
# the convenience methods.

def test_lowlevel():
    app = QApplication([])
    combo = ComboTree()
    model = combo.model()
    parent_item = QStandardItem('Item 1')
    parent_item.appendRow(QStandardItem('Child'))
    model.appendRow(parent_item)
    model.appendRow(QStandardItem('Item 2'))

    combo.show()
    combo.selected.connect(sel_slot)

    app.exec()

# High level test where we load a tree:
    
def test_highlevel():
    tree_data = ['a', 'b.c', 'c.d.e.f', 'q', 'z.z']
    app = QApplication([])
    combo = ComboTree()
    combo.load_tree(tm.make_tree(tree_data))

    combo.show()
    combo.selected.connect(sel_slot)
    
    app.exec()