''' This module implements a frame that contains 
    Two enumerated type selectors laid out horizontally.
    The left most of these contains selector from the list of 
    spectrum types supported by this application while the right 
    side contiains a selector from the list of channel typse supported by
    this application.  By application I mean the server.

    The normal use is to instantiate this widget then pass a client
    object to load

    Attributes:
    *   selectedSpectrumType - the currently selected spectrum type
       specified as a capabilities.SpectrumTypes enumerator.
    *  selectedSpectrumTypeString - the string used to label the currently
       selected spectrum type.
    *  selectedChannelType - the currently selected channel type;
       specified as a capabilities.ChannelTypes enumerated object.
    *  selectedChannelTypeString - the string used to label the currently
       selected channel type.
    Signals: 
    *  spectrumtypeChanged - The currently selected spectrum type has changed.
        The new specctrum type enum value is passed to the slot. Note that
        the name attribute of that value provides the text string.
    *  channelTypeChanged  - The currently selected channel type has changed.
       as with the spectrumTypeChanged signal, the currently selected
       channel type enum is passed to the slot.
'''

import capabilities as cap
import rustogramer_client
from EnumeratedTypeSelector import TypeSelector
from enum import Enum

from PyQt5.QtCore import (
    pyqtSignal
)
from PyQt5.QtWidgets import (QFrame, QGridLayout, QLabel, 
    QApplication, QMainWindow
)

class TypeFrame(QFrame):
    spectrumTypeChanged = pyqtSignal(Enum)
    channelTypeChanged  = pyqtSignal(Enum)

    def __init__(self, *args):
        super().__init__(*args)
        self.setFrameShape(QFrame.StyledPanel)
        layout = QGridLayout(self)
        
        stype_label = QLabel('SpectrumType')
        self.spectrumType = TypeSelector(self)
        self.spectrumType.selected.connect(self.stype_changed)
        ctype_label = QLabel('ChannelType')
        self.channelType  = TypeSelector(self)
        self.channelType.selected.connect(self.ctype_changed)

        layout.addWidget(stype_label, 0, 0)
        layout.addWidget(self.spectrumType, 1, 0)
        layout.addWidget(ctype_label, 0, 1)
        layout.addWidget(self.channelType, 1,1)

        self.setLayout(layout)

    ''' 
      load the spectrum type and channel type widgets with the
      types supported by the server.  We don't assume that capabilities.set_client
      has been called yet...that's a cheap function anyway since it just sets
      internal data; so if we're wrong there's no cost to it.

      Parmaeters: client - a rustogramer_client.rustogramer object
    '''
    def load(self, client):
        cap.set_client(client)
        stypes = cap.get_supported_spectrumTypes()
        self.spectrumType.clear()
        for  t in stypes :
            self.spectrumType.addItem(t.name, t)

        ctypes = cap.get_supported_channelTypes()
        self.channelType.clear()
        for t in ctypes :
            self.channelType.addItem(t.name, t)

    ''' Support for selectedSpectrumType/TypeString Properties: '''

    def selectedSpectrumType(self):
        return self.spectrumType.selectedType()
    def setSelectedSpectrumType(self, t):
        self.spectrumType.setSelectedType(t)

    def selectedSpectrumTypeString(self):
        return self.spectrumType.selectedText()
    def setSelectedSpectrumTypeString(self, txt):
        self.spectrumType.setSelectedText(txt)

    ''' Support for selectedChannelType/TypeString properties: '''
    
    def selectedChannelType(self):
        return self.channelType.selectedType()
    def setSelectedChannelType(self, t):
        self.channelType.setSelectedType(t)
    def selectedChannelTypeString(self):
        return self.channelType.selectedText()
    def setSeletedChannelTypeString(self, t):
        self.channelType.setSelectedText(t)
    
    # My slots which just relay the signal to my signals:

    def stype_changed(self, s, t):
        self.spectrumTypeChanged.emit(t)
    def ctype_changed(self, s, t):
        self.channelTypeChanged.emit(t)


# Test code.  host and port are for a running histogram server.

def selc(v):
    print("Changed:", v, v.name)

def test_widget(host, port):
    client = rustogramer_client.rustogramer({'host': host, 'port': port})
    app = QApplication([])
    main = QMainWindow()
    sel = TypeFrame(main)
    sel.load(client)
    main.setCentralWidget(sel)
    sel.spectrumTypeChanged.connect(selc)
    sel.channelTypeChanged.connect(selc)
    if cap.has_1d():    #Amost surely does but....
        sel.setSelectedSpectrumType(cap.SpectrumTypes.Oned)

    main.show()
    app.exec()

