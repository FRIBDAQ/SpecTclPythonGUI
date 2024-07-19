'''
Proivides the Gate class which defines and implements the Gate menu items.
'''

from PyQt5.QtWidgets import(
    QAction, QDialog, QDialogButtonBox, QAbstractItemView, QPushButton,
    QVBoxLayout
)
from PyQt5.QtCore import pyqtSignal
from gatelist import ConditionList, common_condition_model
from conditionEditor import ConditionEditor
class Gate():
    def __init__(self, menu, client, main, spectra):
        '''
          menu - the menu we populate
          client- a client to the server we're interacting with
          main- THe main window.
          spectra- The handler for the Spectra menu..so we can use the apply_gate method
                  from that object
        '''
        
        self._menu = menu
        self._client = client
        self._win = main
        self._spectra = spectra
        
        self._create = QAction('Create...')
        self._create.triggered.connect(self._create_gates)
        self._menu.addAction(self._create)
        
        self._apply = QAction('Apply...')
        self._apply.triggered.connect(self._spectra.apply_gate)
        self._menu.addAction(self._apply)
        
        self._menu.addSeparator()
        
        self._delete = QAction('Delete...')
        self._delete.triggered.connect(self._delete_gates)
        self._menu.addAction(self._delete)
        
    def _create_gates(self):
        dlg = ConditionCreationDialog(self._menu)
        dlg.exec()
        
    def _delete_gates(self):
        dlg = GateListPrompter(self._menu)
        dlg.refresh.connect(self._refresh_gates)
        if dlg.exec():
            for condition in dlg.conditions():
                self._client.condition_delete(condition)
    
    
    def _refresh_gates(self):
        common_condition_model.load(self._client)
    

class GateListPrompter(QDialog):
    refresh = pyqtSignal()
    def __init__(self, *args):
        super().__init__(*args)
        
        layout = QVBoxLayout()
        
        self._conditions = ConditionList(self)
        self._conditions.setSelectionMode(QAbstractItemView.ExtendedSelection)
        layout.addWidget(self._conditions)
        
        self._refresh = QPushButton('Refresh List',self)
        layout.addWidget(self._refresh)
        self._refresh.clicked.connect(self.refresh)
        
        self._buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        self._buttonBox.accepted.connect(self.accept)
        self._buttonBox.rejected.connect(self.reject)
        
        layout.addWidget(self._buttonBox)
        
        self.setLayout(layout)
        
    def conditions(self):
        # Return the set of selected gates:
        
        selected_indices = self._conditions.selectedIndexes()
        result = list()
        for index in selected_indices:
            model = index.model()
            item = model.itemFromIndex(index)
            result.append(item.text())
            
        return result
    
class ConditionCreationDialog(QDialog):
    def __init__(self, *args):
        super().__init__(*args)
        layout = QVBoxLayout()
        
        self._editor = ConditionEditor(self)
        layout.addWidget(self._editor)
        
        self._buttonBox = QDialogButtonBox(QDialogButtonBox.Ok,  self)
        self._buttonBox.accepted.connect(self.accept)
        
        layout.addWidget(self._buttonBox)
        
        self.setLayout(layout)