'''  This module contains a shared model for and listing of conditions.
 Conditions can be applied to a spectrum to gate its increements.
'''

from PyQt5.QtWidgets import (
    QTableView,  QListView, QComboBox,
    QApplication, QMainWindow
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import (QStandardItem, QStandardItemModel)

class ConditionModel(QStandardItemModel):
    ''' This model contains the gates for e.g. gate tables.
      The model is tabular in nature and has the following columns:
      * 0 - The gate name.
      * 1 - The gate type string.
      * 2 - Any dependent gates (None if there are no dependent gates for this
          type) otherwise a comma separated string list.
      * 3 - THe parameters the gate depends on or again None if there are no
             dependend parameters for this gate. A comma separated stringlist
      * 4 - points  If the gate has points this is the list of x/y points in the
            gate.  This is a comma separated string list of the form (x1,y1), ...
      * 5 - limits if the gates have limits, this is  a string of the form
            low, high
    '''
    def __init__(self, *args):
        super().__init__(*args)
        self._colheadings = [
            'Name', 'Type', 'Gates', 'Parameters', 'Points', 'Limits', 'Mask'
        ]
    def load(self, client, pattern = '*'):
        data = client.condition_list(pattern)['detail']
        self.clear() 
        for condition in data:
            self._add_condition(condition)
        pass
    def headerData(self, col, orient, role):
        if role == Qt.DisplayRole:
            if orient == Qt.Horizontal:
                return self._colheadings[col]
            else:
                return None

    def _add_condition(self, c):
        name = QStandardItem(c['name'])
        type_string = QStandardItem(c['type'])
        gates = QStandardItem(self._get_string_list(c, 'gates'))
        parameters = QStandardItem(self._get_string_list(c, 'parameters'))
        points     = QStandardItem(self._get_points(c))
        limits     = QStandardItem(self._get_limits(c))
        mask      = QStandardItem(self._get_mask(c))
        self.appendRow([name, type_string, gates, parameters, points, limits, mask])
    def _get_field(self, item, key):
        #  If there is no field, None is returned, else the contents
        # of that field are returned...irregardless of type
        if key in item.keys():
            return item[key]
        else:
            return None
    def _get_string_list(self, c, key):
        # Return an item that is a string list:

        result = self._get_field(c, key)
        if result is not None:
            result = ', '.join(result)
        return result
    def _get_points(self, c):
        # Return the string for points or None if needed:
        result = self._get_field(c, 'points')
        if result is not None:
            result_strings = []
            for p in result:
                x = p['x']
                y = p['y']
                result_strings.append(f'({x}, {y})')
            result = ', '.join(result_strings)
    
        return result
    def _get_mask(self, c):
        mask =  self._get_field(c, 'value')
        if mask is not None:
            mask = f'{mask}'
        return mask
    def _get_limits(self, c):
        # Return the approprate limits string. Note that
        # low implies a high:

        low = self._get_field(c, 'low')
        if low is None:
            return None
        else :
            high = c['high']     # Low implies a high.
            return f'{low}, {high}'
    
common_condition_model = ConditionModel()   # So all gate things look the same.

''' We provide the following GUI elements;
    ConditionChooser  - Combobox stocked with the set of condition names defined.
    ConditionList     - A list box containng names of conditions.
    ConditionTable    - A table of conditions and their characteristics.

    These all make use of common_condition_model, so updating that model
    updates the contents of all of these.
'''

class ConditionChooser(QComboBox):
    def __init__(self, *args):
        global common_condition_model
        super().__init__(*args)
        self.setModel(common_condition_model)
        self.setModelColumn(0)

class ConditionList(QListView):
    def __init__(self, *args):
        global common_condition_model
        super().__init__(*args)
        self.setModel(common_condition_model)
        self.setModelColumn(0)

class ConditionTable(QTableView):
    def __init__(self, *args):
        global common_condition_model
        super().__init__(*args)
        self.setModel(common_condition_model)
