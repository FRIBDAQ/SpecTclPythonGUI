''' 
This model contains a class that acts as the controller for the treevariable view.
'''
from treevariable import (common_treevariable_model)
from spectrumeditor import error
import fnmatch


class TreeVariableController:
    ''' 
        This is a controller for the TreeVariableView.  It connects to all of
        the signals the view emits and interacts with both the view and the
        model (the server program) to perform the actions requested by the
        view.
        
        This class has no public methods.  Once the event loop is running,
        it is fully autonomous.
    '''
    def __init__(self, view, client):
        '''
           view - the TreeVariableView object we're the controller form.
           client - The client object (rustogramer_client.rustogramer) that we use
              to communicate with the model (server).'
            
        '''
        self._view = view
        self._client = client
        
        # Let's also cache the view's components to save some time:
        
        self._selector = view.selector()
        self._table    = view.table()
        
        view.append.connect(self._append)
        view.replace.connect(self._replace)
        view.remove.connect(self._remove)
        view.load.connect(self._load)
        view.set.connect(self._set)
    
    def _append(self):
        if self._selector.array():
            element = self._selected()['name']
            path =  element.split('.')
            array = path[0:-1]
            if len(array) > 0:
                pattern = '.'.join(array) + '.*'
                for variable in self._client.treevariable_list()['detail']:
                    if fnmatch.fnmatch(variable['name'], pattern):
                        self._table.append(variable)
        else:
            self._table.append(self._selected())
    def _replace(self):
        selection = self._table.selection()
        if len(selection) == 1:
            row = selection[0]['row']
            self._table.replace(row, self._selected())
    def _remove(self):
        sel = self._table.selection()
        rows = [x['row'] for x in sel]
        rows.sort(reverse=True)
        for row in rows:
            self._table.remove(row)
    def _load(self):
        selection = self._table.selection()
        data = self._client.treevariable_list()['detail']    # Load current data from server.
        for item in selection:
            name = item['name']
            info = self._find_def(name, data)
            if info is not None:
                self._table.replace(item['row'], info)
    def _set(self):
        data = self._get_vars_to_set()
        for var in data:
            self._client.treevariable_set(var['name'], var['value'], var['units'])
            common_treevariable_model.set_definition(var)
    
    # Utiltities:
    
    def _selected(self):
        return  self._selector.definition()
    def _find_def(self, name, data):
        for item in data:
            if name == item['name']:
                return item
        return None
    def _get_vars_to_set(self):
        # Figure out which variables to set and to which values.
        # This is slightly complicated if array is checked:
        #  - it is possible that there's more than one selected item that
        #    that matches the array pattern.
        #  - it is further possible that the values requested will differ.  In that case,
        #    this is noted and an error popup will be done noting that this variable array will
        #    not be set.
    
        result = list()
        
        #  First get the selection list.
        
        selected = self._table.selection()
        if self._selector.array():
            selected = self._apply_array(selected)
        result = self._resolve_duplicates(selected)
        
        # Ok nw we have the set of definitions that describe the settings to make:
        # With any duplicates either coalesced or removed if they are inconsistent.
        
        return result
    def _apply_array(self, selection):
        # Given that the names should be turned into patterns, apply
        # return a new list of settings to make which have the arry check applied:
        
        result = list()
        for var in selection:
            name = var['name']
            pattern_list = name.split('.')
            pattern = '.'.join(pattern_list[0:-1]) + '.*'
            matches = common_treevariable_model.get_matching_definitions(pattern)
            for match in matches:
                # All units and values for any single match shoulid come from the base item.
                result.append({
                    'name':match['name'], 'value':var['value'], 'units':var['units']
                })
        return result
    def _resolve_duplicates(self, defs):
        # Given a set of definitions resolve the potential duplicates:
        # If there are duplicates with the same value/unit pairs Simple
        # Get rid of the 'second'.  If there is a mismatch in value/units,
        # Mark that to be the case and get rid of the second.
        # Once all this is done, indicate the set of duplicates in a popup error.
        # That lists the 'bad' duplciates.  The good values are returned.
        # This is all done by consdtructing a dict indexed on name
        # values are the definition with the added 'ok' field that is ok if there're no
        # inconsistent duplicates.
        
        dupcatcher = dict()
        for info in defs:
            name = info['name']
            if  name  not in dupcatcher.keys():
                # First (only?) time:
                
                dupcatcher[name] = info
                dupcatcher[name]['ok'] = True
            else:
                # is this version consistent? If so just don't add, otherwise,
                # set the 'ok' value to False.
                
                if info['value'] != dupcatcher[name]['value'] or info['units'] != dupcatcher[name]['units']:
                    dupcatcher[name]['ok'] = False
        
        # Bad names:
        
        bad_names = [dupcatcher[x]['name'] for x in dupcatcher.keys() if not dupcatcher[x]['ok']]
        if len(bad_names) > 0:
            error(f"The following settings are inconsistent in value and/or units and won't be altered {bad_names}")
            
        result = [dupcatcher[x] for x in dupcatcher.keys() if dupcatcher[x]['ok']]
        
        return result

#----------------------------------------------------------------------------
# Test code:

if __name__ == '__main__':
    from rustogramer_client import rustogramer as rcl
    from PyQt5.QtWidgets import (QApplication, QMainWindow)
    from treevariable import TreeVariableView
    
    client = rcl({'host': 'localhost', 'port':8000})
    common_treevariable_model.load(client)
    
    app = QApplication([])
    win = QMainWindow()
    
    wid = TreeVariableView()
    ctl = TreeVariableController(wid, client)
    
    win.setCentralWidget(wid)
    win.show()
    app.exec()
    
    