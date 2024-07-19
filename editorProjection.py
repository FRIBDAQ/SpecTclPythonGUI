'''  
    This module will provides a projection definition editor.
    Projection spectra take an existing 2d spectrum and create a
    projection of the spectrum onto a specific axis.  Optionally,
    the projection can be:
    *  A snapthot, in which case it will not be incremented in future events.
    *  Within a named contour in which case the resulting spectrum will only be
       composed of counts within the contour on the parent spectrum and, if not a
       snapshot only increment when the contour gate is true.
    Therefore the editor will look something like:

    +-----------------------------------------------+
    |  Name [ Line edit                           ] |
    |    Project:            [ ] snapshot           |
    | +-------------------+  [ ] in contour         |
    | |  2d spectrum list |  +--------------------+ |
    | +-------------------+  |  contour list      | |
    |   [direction]          +--------------------| |
    |                [  Create/replace ]            |
    +-----------------------------------------------+

    Note:  The contour list is only usable if in contour is checked otherwise,
        it is disabled:

    Signals:
       *    spectrumChosen - A spectrum was selected from the combobox
               Normally, the controller will load the contour list with the
               visible contours on that spectrum in response to this signal.
       *    commit - Create/replace was clicked.
    Attributes:
        * name - spectrum name.
        * spectrum - selected spectrum
        * snapshot - snapshot checkbutton state.
        * contour  - contour checkbutton state
        * contour_name - name of contour (valid only if contour() is True)  
        * direction - Projection direction
    Public methods:
        * setSpectra - provide the list of spectra for the spectrum combobox.
        * setContours - Provide a list of contours for the spectrum combobox.
       
'''

from PyQt5.QtWidgets import (
    QLabel, QLineEdit, QComboBox, QCheckBox, QPushButton,
    QVBoxLayout,  QHBoxLayout,
    QApplication, QMainWindow
)
from PyQt5.QtCore import pyqtSignal
from PyQt5.Qt import *

from direction import DirectionChooser

class ProjectionEditor(QLabel):
    commit         = pyqtSignal()
    spectrumChosen = pyqtSignal(str)
    def __init__(self, *args):
        super().__init__(*args)

        # Layout the megawidget:
        
        layout = QVBoxLayout()        #  It's all a vertical w HBox rows.

        # The spectrum name:
        
        row1 = QHBoxLayout()
        row1.addWidget(QLabel('Name', self))
        self._name = QLineEdit(self)
        row1.addWidget(self._name)
        layout.addLayout(row1)

        # The Spectrum selector:
        
        row2 = QHBoxLayout()
        
        s_layout = QVBoxLayout()
        s_layout.addWidget(QLabel('Spectrum:', self))
        self._spectrum = QComboBox(self)
        s_layout.addWidget(self._spectrum)
        row2.addLayout(s_layout)

        # Snapshot?
        
        self._snapshot = QCheckBox('Snapshot', self)
        row2.addWidget(self._snapshot)

        # Direction

        self._direction = DirectionChooser()
        row2.addWidget(self._direction)

        # Contour?

        c_layout = QVBoxLayout()
        self._incontour = QCheckBox('contour', self)
        self._contour   = QComboBox(self)
        self._contour.setDisabled(True)
        c_layout.addWidget(self._incontour)
        c_layout.addWidget(self._contour)
        row2.addLayout(c_layout)
        
        layout.addLayout(row2)

        # Create replace button:

        commit = QHBoxLayout()

        self._commit = QPushButton('Create/Replace')
        commit.addWidget(self._commit)
        commit.addStretch(1)
        
        layout.addLayout(commit)
        layout.addStretch(1)

        self.setLayout(layout)

        # Internally handled signals:

        self._incontour.clicked.connect(self._contourToggled)
        self._spectrum.activated.connect(self._relaySpectrumSelected)

        # Export commit -> commit

        self._commit.clicked.connect(self.commit)

    #   Implement attribute getters/setters.

    def name(self):
        return self._name.text()
    def setName(self, new_name):
        self._name.setText(new_name)

    def spectrum(self):
        return self._spectrum.currentText()
    def setSpectrum(self, new_name):
        index = self._spectrum.findText(new_name)
        if index >= 0:
            self._spectrum.setCurrentIndex(index)
        else:
            raise KeyError(f'No such spectrum: {new_name}')

    def snapshot(self):
        return self._snapshot.checkState == Qt.Checked
    def setSnapshot(self, value):
        if value:
            self._snapshot.setCheckState(Qt.Checked)
        else:
            self._snapshot.setCheckstate(Qt.Unchecked)
            

    def contour(self):
        return self._incontour.checkState() == Qt.Checked
    def setContour(self, value):
        if value:
            self._incontour.setCheckState(Qt.Checked)
        else:
            self._incontour.setCheckstate(Qt.Unchecked)
    
    def contour_name(self):
        return self._contour.currentText()
    def setContour_name(self, name):
        index = self._contour.findText(name)
        if index >= 0:
            self._contour.setCurrentIndex(index)
        else:
            raise KeyError(f'No such contour: {name}')
    
    def direction(self):
        return self._direction.selection()
    def setDirection(self, direction):
        self._direction.setSelection(direction)
    #   Implement public methods.

    def setSpectra(self, spectrum_names):
        self._setComboBoxContents(self._spectrum, spectrum_names)
    def setContours(self, contour_names):
        self._setComboBoxContents(self._contour, contour_names)

    #   Internal signal handlers:

    def _contourToggled(self):
        # Enable/disable the contour widget depending on the toggle state:

        if self._incontour.checkState() == Qt.Checked:
            self._contour.setDisabled(False)
        else:
            self._contour.setDisabled(True)
    def _relaySpectrumSelected(self, index):
        self.spectrumChosen.emit(self._spectrum.currentText())

    #  Utilties: 

    def _clearComboBox(self, box):
        while box.count() > 0:
            box.removeItem(0)

    def _setComboBoxContents(self, box, items):
        # Set combobox values to a set of items:

        self._clearComboBox(box)
        box.addItems(items)
        
#---------------------- test code ---------------------------

def _spectrum_selected(name):
    print(f'{name} was selected -loading some contours')
    w.setContours(['a', 'b'])

w = None
if __name__ == '__main__':
    app = QApplication([])
    c   = QMainWindow()
    
    w   = ProjectionEditor()
    w.setSpectra(['1','2', '3'])
    w.spectrumChosen.connect(_spectrum_selected)
    c.setCentralWidget(w)

    c.show()
    app.exec()

        
        
