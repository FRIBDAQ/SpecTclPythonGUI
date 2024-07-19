'''
  This module provides a bit mask selector.  It's 32 checkbuttons
  labeled above.  

  Signals:
  -  changed - the bitmask changed.
  Attributes:
     mask  - get/set the bitmask.
'''

from PyQt5.QtWidgets import (
    QLabel, QCheckBox, QVBoxLayout, QGridLayout, QWidget,
    QApplication, QMainWindow
)
from PyQt5.QtCore import pyqtSignal, Qt


class BitMask(QWidget):
    changed = pyqtSignal()
    def __init__(self, *args):
        super().__init__(*args)
        self._checkboxes = []
        layout = QGridLayout()

        for bit in range(32):
            bitbox = QVBoxLayout()
            bitbox.addWidget(QLabel(f'{bit:02d}', self), Qt.AlignBottom)
            box = QCheckBox(self)
            bitbox.addWidget(box, Qt.AlignTop)
            self._checkboxes.append(box)
            layout.addLayout(bitbox, 0, 32-bit)
            box.stateChanged.connect(self._changed)

        self.setLayout(layout)
    # Need this to throw away the state parameter.
    def _changed(self, ignored):
        self.changed.emit()
    
    def mask(self):
        result = 0
        for (i, box) in enumerate(self._checkboxes):
            if box.checkState() == Qt.Checked:
                result = result | (1 << i)
        return result
    def setMask(self, value):
        for (i, box) in enumerate(self._checkboxes):
            if (value & (1 << i))  != 0:
                box.setCheckState(Qt.Checked)
            else:
                box.setCheckState(Qt.Unchecked)

#-------------------------- testing -------------------------
def mask():
    m = w.mask()
    print(f'{m:08x}')
if __name__ == '__main__':
    app = QApplication([])
    c   = QMainWindow()
    
    w = BitMask()
    w.changed.connect(mask)
    w.setMask(0x0102030405060708)
    c.setCentralWidget(w)


    c.show()
    app.exec()