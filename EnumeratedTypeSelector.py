''' This module provides a spectrum type selector.
The user is assumed to have stocked it with a list of
spectrum type names and corresponding capabilities.SpectrumTypes
The signal 'selected' is emitted when a spectrum type is selected
from the list and the slot is provided with the corresponding
spectrum type Enum as well as the type name (which can be used to
title other UI elements e.g. a labeled framo for editing spectra of
type type).

Attributes:
  selectedType - The current selected enum.
  selectedText - The currently selected
'''

from PyQt5.QtWidgets import (
    QTableView, QMainWindow, QComboBox, QApplication
)
from PyQt5.QtCore import *
from enum import Enum
from capabilities import SpectrumTypes, ChannelTypes

class TypeSelector(QComboBox):
    selected = pyqtSignal(str, Enum)
    def __init__(self, parent = None):
        super().__init__(parent)
        self.setEditable(False)
        self.currentIndexChanged.connect(self.select_type)
    '''
       Override for add item that forces you to provide user data
       which normally is a SpectrumTypes value
       e.g. box.addItem('1-d', SpectrumTypes.Oned)
    '''
    def addItem(self, text, value):
        super().addItem(text, value)

    def select_type(self, index):
        sptype = self.currentData()
        text = self.currentText()
        self.selected.emit(text, sptype)
    
    def selectedType(self):
        return self.currentData()
    def setSelectedType(self, d):
        index = self.findData(d)
        if index != -1 :
            self.setCurrentIndex(index)
        else:
            raise KeyError
    def selectedText(self):
        return self.currentText()
    def setSelectedText(self, txt):
        index = self.findText(txt)
        if index != -1:
            self.setCurrentIndex(index)
        else:
            raise KeyError

### Test code:

def sel_handler(type_str, type_val):
    print("Selected: ", type_str, type_val)

#  Test with spectrum types:

def teststypes():
    app = QApplication(['test'])
    win = QMainWindow()
    list = TypeSelector()
    list.addItem('1d', SpectrumTypes.Oned)
    list.addItem('2d', SpectrumTypes.Twod)
    list.addItem('Projection', SpectrumTypes.Projection)
    win.setCentralWidget(list)
    list.selected.connect(sel_handler)
    win.show()
    app.exec()

# test with channel types:
def testctypes():
    app = QApplication(['test'])
    win = QMainWindow()
    list = TypeSelector()
    list.addItem('Double', ChannelTypes.Double)
    list.addItem('Long (32)', ChannelTypes.Long)
    list.addItem('Short (16)', ChannelTypes.Short)
    win.setCentralWidget(list)
    list.selected.connect(sel_handler)
    win.show()
    app.exec()
