'''
Provides the help menu for the program.  When setting the version  update the
version string below.
'''

from PyQt5.QtWidgets import (
    QDialog, QAction, QDialogButtonBox, QTextEdit,
    QVBoxLayout
)
from PyQt5.QtCore import QSize
from PyQt5 import Qt

version = "0.1"
qt_source_code_link = "https://wiki.qt.io/Building_Qt_5_from_Git#Getting_the_source_code"
rustogramer_git = "https://github.com/FRIBDAQ/rustogrammer"

qt_version_string = Qt.PYQT_VERSION_STR

about_text = f'''
<p>
  RestGui provides a ReST client to control histogram servers like
  SpecTcl and Rustogramer.
</p>
<p>
  Verion: {version}
</p>
<p>
  RestGui makes use of PyQt5 which, in turn makes use of Qt {qt_version_string}
  We use the open source license of Qt and thus must also provide a means to 
  download source code for Qt, as well as the source code for this program.
  
  Qt source code can be found at <br/>
  <a href='{qt_source_code_link}' > {qt_source_code_link} </a>
</p>
<p>
  This project is in the restclients/python directory of the rustogramer project at:
  <a href='{rustogramer_git}'>{rustogramer_git}</a>

</p>
<p>
  Author:  Ron Fox<br/>
           Facility for Rare Isotope Beams<br/>
           Michigan State University.<br/>

</p>
'''

class Help:
    def __init__(self, menu):
        self._menu = menu
        self._about = QAction('About...')
        self._about.triggered.connect(self._display_help)
        self._menu.addAction(self._about)
    def _display_help(self):
        dlg = About(self._menu)
        dlg.exec()
        
class About(QDialog):
    def __init__(self, *args):
        super().__init__(*args)
    
        
        layout = QVBoxLayout()
        self._about= QTextEdit(self)
        self._about.setHtml(about_text)
        self._about.setReadOnly(True)
        layout.addWidget(self._about)
        
        # The button s just have dismiss:
        
        self._buttonBox = QDialogButtonBox(QDialogButtonBox.Close, self)
        self._buttonBox.rejected.connect(self.reject)
        
        layout.addWidget(self._buttonBox)
        
        self.setLayout(layout)
        self.setMinimumSize(QSize(600, 400))
        self.setWindowTitle('About ReSTGUI')