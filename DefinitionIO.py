''' 
This module provides code to save/restore various definitions to an Sqlite3 database file.
One would create one of a DefinitionWriter or DefinitionReader object and then invoke the various
methods  on that to do the I/O.  The database files use the same schema as the SpecTcl
sqlite3 data store; See https://docs.nscl.msu.edu/daq/newsite/spectcldb/index.html

Note that while that schema supports storing more than one 'save set' in a single database file,
this capability is not used and when a database file is initialized, the save set created is 
called 'rustogramer_gui'. 
'''

import sqlite3
import time

save_set_name = 'rustogramer_gui'

class DefinitionWriter:
    ''' Writer for definitions.  Insantiating the writer creates the initial schema if
       needed.  Note that at present, we only create a single save set, see the 
       save_set_name variable.  Given that, creating one of these on a non empty 
       database file can result in undefined consequences.
       
       Note as well that while the SpecTcl data store includes scheme components to store
       e.g. runs and spectrum contents, we don't create those elements.
    '''
    def __init__(self, filename):
        self._sqlite = sqlite3.connect(filename)
        self._create_schema()
        self._saveid = self.open_saveset(save_set_name)
    def __del__(self):
        self._sqlite.close()
        
    def open_saveset(self, name):
        '''
        Opens a save set in the databse.  If the save set does not exist, it is created.
        Any definitions saved until the next open_saveset operation will be done on that
        saveset
        
        Parameters:
        *  name   - name of the saveset.
        
        Returns integer save-set id.
        
        '''
        
        cur = self._sqlite.execute('''
            SELECT id FROM save_sets WHERE name = ?
                             ''', (name,))
        id = cur.fetchone()
        if id is None:
            cur = self._sqlite.execute('INSERT INTO save_sets (name, timestamp) VALUES (?,?)', (name, time.time()))
            id = cur.lastrowid
            self._saveid = id
            self._sqlite.commit()
            return id
        else:
            self._saveid = id[0]
            return id[0]
        
    def save_parameter_definitions(self, defs):
        '''
        Save the parameter definitions into the current save set.  
        
        Parameters:
        * defs - parameter definitions as gotten from e.g. 
                 rustogramer_client.rustogramer.paramter_list()['detail']
        
        '''  
        
        # Note that I believe this creates a transaction that encapsulates all of the
        # INSERTs below but it's not clear from the docs.
        cur = self._sqlite.cursor()
        cur.executemany(f'''
            INSERT INTO parameter_defs (save_id, name, number, low, high, bins, units)
                VALUES({self._saveid}, :name, :id, :low, :hi, :bins, :units)
                        ''', defs)
        self._sqlite.commit()
    
    def save_spectrum_definitions(self, defs):
        '''
            Save the definitions of all spectra to the database file.  Note that since
            inserting a spectrum is not an atomic database operation,  everything is done
            in a transaction.  This implies the spectrum save is an all or nothing thing.
            
            *   defs - the specturm definitions from e.g. 
                rustogramer_client.rustogramer.spectrum_list()['detail']
            
            If the save fails, the exception raised is passed onward to the caller with the
            transation rolled back.
        '''   
        c = self._sqlite.cursor()
        # I want expclicit control over the transaction and I'm not sure when/what needs
        # committing if I just use the auto so we'll use a save point for that:
        
        c.execute('SAVEPOINT spectrum_save')
        try :
            for s in defs:
                self._save_specdef(c, s)
        except:
            #  If there are any errors rollback the save point and any
            #  tansaction and re-raise.
            c.execute('ROLLBACK TRANSACTION TO SAVEPOINT spectrum_save')
            c.execute('RELEASE SAVEPOINT spectrum_save')       # Save points are tricky this way.
            self._sqlite.rollback()
            raise
        # Success so commit:
        
        c.execute('RELEASE SAVEPOINT spectrum_save')
        self._sqlite.commit()
        
    def save_condition_definitions(self, defs):
        '''
        Save condition definitions to the database file.   See the discussion of transactions
        in save_spectrum_definitions above.
        
        *  defs - the defintitions to save. Results of e.g. 
            rustgrammer_client.rustogramer.condition_list()['detail']
            
        If the save fails, transactions are rolledback and the exception is re-raised to the caller.
        '''
        
        # It's important that we re-order that definitions so that we define dependent gates
        # Before they are needed:
        
        defs = self._fill_missing_condition_keys(defs)
        defs = self._reorder_conditions(defs)
        
        c = self._sqlite.cursor()
        c.execute('SAVEPOINT condition_save')    # See notes in save_spectrum_definitions.
        
        try:
            for condition in defs:
                self._save_condition(c, condition)
        except:
            c.execute('ROLLBACK TRANSACTION TO SAVEPOINT condition_save')
            c.execute('RELEASE SAVEPOINT condition_save')
            self._sqlite.rollback()
            raise
            
        c.execute('RELEASE SAVEPOINT condition_save')
        self._sqlite.commit()
    def save_gates(self, applications):
        '''
          I use Rustogramer parlance here - a condition in rustogramer
          is what SpecTcl calls a gate.  A gate application is what
          Rustogramer calls a gate.  A gate is a condition applied to
          a spectrum such that it only increments for events which
          make that condition true.
          
          This method writes the gates (applications) to the database.
          
          *  applications is the ['detail'] of the returned value
          from a successful call to
          rustogramer_client.rustogramer.apply_list
          This is a list of dicts with the fields:
             'spectrum' a spectrum name
             'gate'     a possibly null gate on that spectrum.
            If the value of the 'gate' is none, then the spectrum
            is ungated (in Rustogramer this can happen, in 
            SpecTcl all spectra are gated even if with a special
            'true' gate).
        '''
        # There will be some fancy subselecting done to 
        # get the gate id and spectrum id given their names as
        #  the gate_applications table is really just a join table
        #  Between spectrum_defs and gate_defs
        
        # Let's marshall the list of subsitutions:
        #  :saveid  - will be the current save set id.
        #  :specname - will be the name of the spectrum.
        #  :condname - will be the name of the condition 
        #
        #  There will only be entries for spectra that are 
        #  actually gated.
        #
        substitutions = list()
        for application in applications:
            if application['gate'] is not None:
                substitutions.append({
                    'saveid': self._saveid,
                    'specname': application['spectrum'],
                    'condname' : application['gate']
                })
        
        # We only need to do anything if there are applications:
        
        if len(substitutions) > 0:
            cursor = self._sqlite.cursor()
            cursor.executemany('''
                INSERT INTO gate_applications (spectrum_id, gate_id)
                    SELECT spectrum_defs.id AS spectrumid,
                           gate_defs.id     AS gateid FROM spectrum_defs
                    INNER JOIN gate_defs ON spectrum_defs.save_id = gate_defs.saveset_id
                    WHERE spectrum_defs.save_id = :saveid
                     AND  spectrum_defs.name   = :specname
                     AND  gate_defs.name       = :condname
            ''', substitutions)
            self._sqlite.commit()
    def save_variables(self, definitions):
        '''
        Saves the tree variable definitions/values to the database.
        
        definitions - is the ['detail'] that comes from 
        rustogramer_client.rustogramer.treevariable_list.  This is a list
        of dicts where each dict has the field:
          'name'  - the name of the variable.
          'value' - The current value (double) of the variable.
          'units' - The units of measure of the variable.
          
          Saving this stuff should be relatively straightforward.
        '''
        
        # Generate the substitutions:
        
        substitutions = list()
        for var in definitions:
            substitutions.append({
                'saveid':  self._saveid,
                'name'  : var['name'],
                'value' : var['value'],
                'units' : var['units']
            })
        
        if len(substitutions) > 0:
            cursor = self._sqlite.cursor()
            cursor.executemany('''
                    INSERT INTO  treevariables (save_id, name, value, units)
                       VALUES (:saveid, :name, :value, :units)
                ''', substitutions)
            self._sqlite.commit()
               
    # Private methods    
    def _create_schema(self):
        # Create the databas schema; again see 
        # https://docs.nscl.msu.edu/daq/newsite/spectcldb/index.html
        # 'Database schema' appendix.
        #  Note:  In this implementation we don't worry about making the
        #         indices.. that provides for fastest inserts (I think).
        #  Note:  This schema is pretty much assured to be correct since
        #         it's literally copy/pasted from the SpecTcl main/db/SpecTclDatabase.cpp  module
        #  Note:  Some tables have been added to spectrum definitions to make it possible
        #         to read back all spectrum types.  An issue was added to github.com/FRIBDAQ/SpecTcl 
        #         to bring these back into synch (#91).
        #  This method is rather lengthy but straightforward so I don't bother to break it up
        #
        
        cursor = self._sqlite.cursor()
        
        #  Table for savesets.
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS  save_sets 
                (id  INTEGER PRIMARY KEY,
                name TEXT UNIQUE,
                timestamp INTEGER)
                             ''')
        
        #  Table for parameter and metadata definitions.
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS parameter_defs
                (id      INTEGER PRIMARY KEY,                    
                save_id INTEGER NOT NULL,  -- foreign key to save_sets.id
                name    TEXT NOT NULL,
                number  INTEGER NOT NULL,
                low     REAL,
                high    REAL,
                bins    INTEGER,
                units   TEXT)
                                ''')
        
        # Tables for spectrum definitions
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS spectrum_defs
                (id      INTEGER PRIMARY KEY,
                save_id INTEGER NOT NULL,     -- Foreign key to save_sets.id
                name    TEXT NOT NULL,
                type    TEXT NOT NULL,
                datatype TEXT NOT NULL
            )
                             ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS axis_defs
            (
                id           INTEGER PRIMARY KEY,
                spectrum_id  INTEGER NOT NULL,  -- FK to spectrum_defs.id
                low          REAL NOT NULL,
                high         REAL NOT NULL,
                bins         INTEGER NOT NULL
            )
                             ''')
        #     Note this definition means that gd spectra can't be recovered.
        #     we really need spectrum_x_params and spetrum_y_params tables.
        #     That also means reworking the SpecTcl part of the equation.
        #     We'll generate those tables, and stock them with an issue in SpecTcl
        #     to fix.
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS spectrum_params   
            (   id          INTEGER PRIMARY KEY,          
                spectrum_id INTEGER NOT NULL,             
                parameter_id INTEGER NOT NULL             
            )
                            ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS spectrum_x_params   -- Rustogramer.
            (   id          INTEGER PRIMARY KEY,          
                spectrum_id INTEGER NOT NULL,             
                parameter_id INTEGER NOT NULL             
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS spectrum_y_params   -- Rustogramer.
            (   id          INTEGER PRIMARY KEY,          
                spectrum_id INTEGER NOT NULL,             
                parameter_id INTEGER NOT NULL             
            )
        ''')
        # Tables for condition (gate) definitions
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS gate_defs       
                (   id          INTEGER PRIMARY KEY,   
                    saveset_id  INTEGER NOT NULL,      
                    name        TEXT NOT NULL,         
                    type        TEXT NOT NULL          
                )
                             ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS gate_points  
            (   id          INTEGER PRIMARY KEY,   
                gate_id     INTEGER NOT NULL,      
                x           REAL,                  
                y           REAL                   
            )
                              ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS gate_parameters 
            (   id   INTEGER PRIMARY KEY,           
                parent_gate INTEGER NOT NULL,       
                parameter_id INTEGER NOT NULL       
            )
                             ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS component_gates       
                (                                            
                    id          INTEGER PRIMARY KEY,         
                    parent_gate INTEGER NOT NULL,           
                    child_gate  INTEGER NOT NULL            
                )
                            ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS gate_masks    
            (   id          INTEGER PRIMARY KEY,     
                parent_gate INTEGER NOT NULL,        
                mask        INTEGER NOT NULL         
            )
                             ''')
        
        # Join table defining which conditions are applied to which 
        # spectra.  You might think that a save set id is needed
        # as well but the spectrum_id and gate_id foreign keys
        # represent spectra and conditions that are
        # implicitly qualified by save set.
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS gate_applications (
                id                INTEGER PRIMARY KEY,  
                spectrum_id       INTEGER NOT NULL,     
                gate_id           INTEGER NOT NULL      
            )
        
                             ''')
        # Define tree variables (only used by SpecTcl).
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS treevariables (   
                id             INTEGER PRIMARY KEY,   
                save_id        INTEGER NOT NULL,      
                name           TEXT NOT NULL,         
                value          DOUBLE NOT NULL,       
                units          TEXT                   
            )
                             ''')
    def _save_specdef(self, cursor, d):
        # Given a database cursor 'cursor' and spectrum definition 'd', performs the
        # SQL to save that defintiion to file.  Note that it is best if there's a transaction
        # or savepoint active on the database so that the non-atomic save of the spectrum
        # becomes atomic over some timeline.
        
        # Write the root record and save it's id for foreign keys in the child records:
        
        cursor.execute('''INSERT INTO spectrum_defs 
            (save_id, name, type, datatype) 
            VALUES (:sid, :name, :type, :dtype)
        ''', 
        {
            'sid': self._saveid, 'name': d['name'], 'type': d['type'], 'dtype': d['chantype']
        })
        specid = cursor.lastrowid
        for axis in d['axes']:
            cursor.execute('''
                INSERT INTO axis_defs (spectrum_id, low, high, bins)
                    VALUES (:sid, :low, :high, :bins)
            ''', {
                'sid': specid, 'low': axis['low'], 'high': axis['high'], 'bins': axis['bins']
            }
        )
        #   Inserts are done  in a tricky way using a subselect that gets both the 
        #   spectrum id and parameter ids we have to do it in this tricky way because
        #   we can't mix VALUES and subselects on one INSERT Alternatives:
        #    Do an INSERT and an UPDATE
        #    Do a separate SELEC\T to get the parameter id from the name then do the insert
        #
        #  For non SQL fluent people.  the INSERT will insert as many rows as will match the
        #  query in the subselect.   The columns in parentheses will be inserted with values pulled 
        #  from the query in order:  spectrum_id stocked with the spectrum_defs.id value and
        #  parmaeter_id with parameter_defs.id
        #  
        #   The INNER JOIN joins the spectrum_defs table with the parameter_defs table wherever
        #   the save_id field on each matches (for the same save set id).
        #   The WHERE clause requires a match with the id of the spectrum we're saving,
        #           and a match for the parameter name as well as a match for our saveset.
        #    this should result in one match that will have our spectrum id, our saveset an the
        #    parameter id we're looking up for parameter name in that saveset.
        #
        for p in d['parameters']:
            cursor.execute('''
                INSERT INTO spectrum_params (spectrum_id, parameter_id)
                SELECT spectrum_defs.id AS spectrum_id, 
                        parameter_defs.id AS param_id FROM spectrum_defs 
                        INNER JOIN parameter_defs ON spectrum_defs.save_id = parameter_defs.save_id   
                    WHERE spectrum_defs.id = :specid 
                        AND parameter_defs.name = :paramname 
                        AND spectrum_defs.save_id = :saveid
            ''', {
                'specid': specid, 'paramname': p, 'saveid': self._saveid
            })
        # x parameters, same subselect trick, different target table:
        
        for p in d['xparameters']:
            cursor.execute('''
                INSERT INTO spectrum_x_params (spectrum_id, parameter_id)
                SELECT spectrum_defs.id AS spectrum_id, 
                        parameter_defs.id AS param_id FROM spectrum_defs 
                        INNER JOIN parameter_defs ON spectrum_defs.save_id = parameter_defs.save_id   
                    WHERE spectrum_defs.id = :specid 
                        AND parameter_defs.name = :paramname 
                        AND spectrum_defs.save_id = :saveid
            ''', {
                'specid': specid, 'paramname': p, 'saveid': self._saveid
            })
        
        # y parameters
        
        for p in d['yparameters']:
            cursor.execute('''
                INSERT INTO spectrum_y_params (spectrum_id, parameter_id)
                SELECT spectrum_defs.id AS spectrum_id, 
                        parameter_defs.id AS param_id FROM spectrum_defs 
                        INNER JOIN parameter_defs ON spectrum_defs.save_id = parameter_defs.save_id   
                    WHERE spectrum_defs.id = :specid 
                        AND parameter_defs.name = :paramname 
                        AND spectrum_defs.save_id = :saveid
            ''', {
                'specid': specid, 'paramname': p, 'saveid': self._saveid
            })
    def _fill_missing_condition_keys(self, definitions):
        #  This is needed because SpecTcl only fills in the needed keys not the full set of keys so:
        
        for cond in definitions:
            k = cond.keys()
            if 'gates' not in k:
                cond['gates'] = list()
            if 'parameters' not in k:
                cond['parameters']  = list()
            if 'points' not in k:
                cond['points'] = list()
            if 'low' in k:
                #   low/high also create points:
                cond['points'] = [{'x': cond['low'], 'y': 0.0}, {'x': cond['high'], 'y': 0.0}]

        return definitions
    def _reorder_conditions(self, definitions):
        #  Reorders the condition definitions so that if a condition is dependent on other
        #  conditions all of those will get written out before us.

        reordered = list()
        # Toss all conditions up into a map indexed by name:
        
        name_map = dict()
        for cond in definitions:
            cond['written'] = False       # Not yet written to file.
            name_map[cond['name']] = cond
        
        #  The work:
        
        for cond in definitions:
            name = cond['name']
            if not name_map[name]['written']:
                deps = self._enumerate_dependencies(cond, name_map)
                reordered.extend(deps)
                # Unlikely but possible that cond is in deps:
                
                if not name_map[name]['written']:
                    reordered.append(cond)
                    name_map[name]['written'] = True
             
        return reordered
    def _enumerate_dependencies(self, cond, name_map):
        #  Given a condition, provide an ordered list of dependencies
        #  that have not yet been 'written'  This is recursive
        #  as dependent conditions might, themselves have
        #  dependencies.
        #  NOTE:  The condition itself is not  in the returned list.
        result = list()
        for dep_name in cond['gates']:
            if not name_map[dep_name]['written']:
                dep = name_map[dep_name]
                deps = self._enumerate_dependencies(dep, name_map)
                result.extend(deps)
                # Unlikely but maybe written was set in dep:
                if not name_map[dep_name]['written']:
                    result.append(dep)
                    name_map[dep_name]['written'] = True
        return result
    
    def _save_condition(self, cursor, condition):
        #  Save a single condition to the database.  Since this is not atomic, the
        # caller shouild have a transaction going in the cursor.
        # It is also important that the conditions be ordered so that conditions
        # are defined prior to being needed by compound conditions.  This is the
        # calller's responsibility.
        
        # root record - and get the row id so we can connect child records to this:
        
        cursor.execute('''
                INSERT INTO gate_defs (saveset_id, name, type)
                    VALUES (:saveid, :name, :type)
            ''',
            {
                'saveid': self._saveid, 'name': condition['name'], 'type': condition['type']
                
            }
        )
        gateid = cursor.lastrowid
        
        #  If here are gate points, they need to be saved; We check the size because
        #  We can marshall all poinst up for an executemany:  
        
        if len(condition['points']) > 0:
            point_bindings = list()
            for p in condition['points']:    # Build the bindings for executemany.
                point_bindings.append(
                    {'gid': gateid, 'x': p['x'], 'y': p['y']}
                )
            cursor.executemany('''
                INSERT INTO gate_points (gate_id, x, y) VALUES (:gid, :x, :y)
                ''', point_bindings)
            
        
        # See spectrum creation for the trick we use with subselects and INSERT here.
        
        for pname in condition['parameters']:
            cursor.execute('''
                    INSERT INTO gate_parameters (parent_gate, parameter_id)
                    SELECT gate_defs.id AS gateid, parameter_defs.id FROM gate_defs
                    INNER JOIN parameter_defs 
                       ON gate_defs.saveset_id = parameter_defs.save_id
                    WHERE gate_defs.name = :gatename
                        AND gate_defs.saveset_id = :saveset
                        AND parameter_defs.name = :paramname
                ''',
                {
                    'gatename': condition['name'], 'saveset': self._saveid, 'paramname': pname
                }
            )
        # Can't really play the same trick with componet conditions because we'd need to match
        # both the gate name and dependent gate name in the root table so (sigh):
        
        for dependent_condition  in condition['gates']:
            cursor.execute('''
                SELECT id FROM gate_defs WHERE name = :name AND saveset_id = :sid
            ''', {
                'name' : dependent_condition, 'sid' : self._saveid
            })
            ids = cursor.fetchall()
            if len(ids)  != 1:
                raise LookupError(f'0 or more than one matches for {dependent_condition} in condition id lookup')
            id = ids[0][0]
            cursor.execute('''
                INSERT INTO component_gates (parent_gate, child_gate) 
                    VALUES (:gateid, :depid)
                ''', {
                    'gateid': gateid, 'depid': id
                }
            )
        # Now some special cases:
        #  if low/high are defined, then those are points with only the x axis meaningful:
        
        if 'low' in condition.keys() and 'points' not in condition.keys():
            low = condition['low']  
            high = condition['high']    # Can't have one without the other:
            
            point_bindings = (
                {'id': gateid, 'x': low, 'y': 0.0},
                {'id': gateid, 'x': high, 'y': 0.0}
            )
            cursor.executemany('''
                INSERT INTO gate_points  (gate_id, x, y) VALUES (:id, :x, :y)
            ''', point_bindings)
        
        # If there's a 'value' field, then it's a mask gate:
        
        if 'value' in condition.keys():
            cursor.execute('''
                    INSERT INTO gate_masks (parent_gate, mask)
                    VALUES (:id, :mask)
                ''', {
                  'id': gateid, 'mask': condition['value']  
                })
            
    
        
class DefinitionReader:
    '''
    This class reads definitions from a database file.  At present,
    we only support the single saveset defined in the global variable
    save_set_name.  However we do provide the open_save_set method
    to select a different save-set -- you should not consider this
    to be well supported.
    '''
    def __init__(self, filename):
        ''' 
            Connect to the saved data in the sqlite3 database 'filename'
            see DefinitionWriter's _create_schema method to see the
            expected database schema.
        '''
        self._sqlite = sqlite3.connect(filename)
        self._saveid = None
        self.open_save_set(save_set_name)
    def __del__(self):
        self._sqlite.close()
        
    def open_save_set(self, name):
        '''
        Make the saveset 'name' current.  If there is no such save set
        in the database, LookupError is raised.
        '''
        cursor = self._sqlite.cursor()
        cursor.execute('''
            SELECT id FROM save_sets WHERE name = :name
        ''', {'name' : name})
        matches = cursor.fetchall()
        if len(matches) != 1:
            raise LookupError(
                f"There were no (or more than one) matches to the save set {name}"
            )
        self._saveid = matches[0][0]
        
    def read_parameter_defs(self):
        '''
        Reads all of the parameter definitions from the current save set.
        returns a list of dicts each dict has the following keys:
        
        'name'    - Parameter name.
        'number'  - Parameter number.
        'low'     - Low value (if empty None)
        'high'    - High value (if empty None)
        'bins'    - Suggested axis binning.
        'units'   - Units of measure string (None if empty).
        
        '''
        
        # Query all parameter definitions for our saveset:
        
        cursor = self._sqlite.cursor()
        cursor.execute('''
            SELECT  name, number, low, high, bins, units FROM parameter_defs 
            WHERE save_id = :saveid
        ''', {'saveid': self._saveid})
        data = cursor.fetchall()
        
        # I think we got back a list of tuples where the elements of each tuple are, in order the
        # columns queried:
        
        result = list()
        for item in data:
            row = {
                'name': item[0],
                'number': item[1],
                'low': item[2],
                'high': item[3],
                'bins': item[4],
                'units': item[5]
            }
            # The empty items might look like '' not None.  Depends on the Sqlite3 package impl.
            if row['low'] == '':
                row['low'] = None
            if row['high'] == '':
                row['high'] = None
            if row['units'] == '':
                row['units'] = None
            result.append(row)
        return result
    def read_spectrum_defs(self):
        '''
        Produces a list of dicts where each dict is a spectrum definition pulled from the database.
        Each spectrum definition dict will have the following keys:
            'name'  - The spectrum name
            'type'  - The spectrum type string (e.g. '1').
            'datatype' - the channel data type (e.g. f64).
            'axes'  - array of dicts for the axes ('low', 'high', 'bins' for each axis)
            'xaxis' - If appropriate an Xaxis definition.
            'yaxis' - If appropriate a Y axis definition.
            'parameters' - The entire set of parameters
            'xparameters' - The set of X parameters.
            'yparameters' - the set of Y parameter names.
        
        We can get the name, type, and axes easily but I'm not SQLSmart enuough to get the parameters
        without separate queries.  I'll leave that to someone smarter than I.
        
        '''
        
        definition_dict = dict()             # Indexed by spectrum name:
        
        # Note the order by below is used to ensure we get axes in x/y order.
        
        cursor = self._sqlite.cursor()
        cursor.execute('''
            SELECT name, type, datatype, low, high, bins  FROM axis_defs
            LEFT JOIN  spectrum_defs 
               ON spectrum_defs.id = axis_defs.spectrum_id
            WHERE spectrum_defs.save_id = :saveset
            ORDER BY axis_defs.id
        ''', {'saveset' : self._saveid})   
        
        data = cursor.fetchall()
        
        # Build the initial dict with name, type, datatype, axes, xaxis and yaxis.  There are some
        # Funky special cases for axes:
        
        for spectrum in data:
            name = spectrum[0]
            axis = {
                    'low': spectrum[3],
                    'high' : spectrum[4],
                    'bins' : spectrum[5]
                }
            if not name in definition_dict.keys():
                # Initial occurrence of spectrum:
                
                
                sdef = {
                    'name': spectrum[0],
                    'type': spectrum[1],
                    'datatype': spectrum[2],
                    'axes': [axis,],
                    'xaxis': list(),
                    'yaxis': list(),
                    'parameters': list(),
                    'xparameters': list(),
                    'yparameters': list()
                }
                sdef['xaxis'] = axis   
                definition_dict[name] = sdef
            else:
                # Just need to fold in a second axis.
                
                definition_dict[name]['axes'].append(axis)
                definition_dict[name]['yaxis'] = axis   # Second is always Y.
                
                
        # Now fold in parameters  The first inner join associates the parameter ids
        # in spectrum_params with their names in the definition table
        # the second associates the spectrum id with the specturm name.
        
        cursor.execute('''
            SELECT spectrum_defs.name, parameter_defs.name FROM spectrum_params
            INNER JOIN parameter_defs ON spectrum_params.parameter_id = parameter_defs.id
            INNER JOIN spectrum_defs ON spectrum_params.spectrum_id = spectrum_defs.id
            WHERE spectrum_defs.save_id = :saveset
        ''', {'saveset': self._saveid})
        
        data = cursor.fetchall()
        for d in data:
            spname = d[0]
            pname  = d[1]
            definition_dict[spname]['parameters'].append(pname)
        
        # and X parameters - same as above but with the spectrum_x_params table:
        
        cursor.execute('''
            SELECT spectrum_defs.name, parameter_defs.name FROM spectrum_x_params
            INNER JOIN parameter_defs ON spectrum_x_params.parameter_id = parameter_defs.id
            INNER JOIN spectrum_defs ON spectrum_x_params.spectrum_id = spectrum_defs.id
            WHERE spectrum_defs.save_id = :saveset
        ''', {'saveset': self._saveid})
        
        data = cursor.fetchall()
        for d in data:
            spname = d[0]
            pname  = d[1]
            definition_dict[spname]['xparameters'].append(pname)
        
        # and Y parameters
        
        cursor.execute('''
            SELECT spectrum_defs.name, parameter_defs.name FROM spectrum_y_params
            INNER JOIN parameter_defs ON spectrum_y_params.parameter_id = parameter_defs.id
            INNER JOIN spectrum_defs ON spectrum_y_params.spectrum_id = spectrum_defs.id
            WHERE spectrum_defs.save_id = :saveset
        ''', {'saveset': self._saveid})
        
        data = cursor.fetchall()
        for d in data:
            spname = d[0]
            pname  = d[1]
            definition_dict[spname]['yparameters'].append(pname)
        
        return definition_dict.values()
    def read_condition_defs(self):
        '''
        Reads all condition definitions from file's open saveset and returns them as a 
        list of dicts.  Each dict will have the following keys:
          name - The name of the condition type.
          type - The type string of the condition type.
          points - list of (x,y) pairs that are the condition points for conditions that have points
                 This can be empty.
          parameters - List of parameters that are used by the condition
          dependencies - List of condition names this condition depends on.
          mask   - If the condition is a mask the value of this mask.
          
          Note that conditions are guaranteed to be in an order such that iterating over
          the list allows the conditions to be defined (e.g. dependent conditions before
          conditions that depend on them).   This is a natural consequence of the fact
          that the writer writes them in that order and, by ordering by primary key,
          we get them out of the database in that order.
          
          Unfortunately, the variability of condition definitions does not really allow us to make
          much use of fancy queries to reduce the number of queries needed to reconstruct
          a condition.  We are able to do the usual fancy things to turn ids into names
          for the parameters and dependent conditions.
        '''    
        result = list()
        cursor = self._sqlite.cursor()
        
        #  Get the root records:
        
        cursor.execute('''
            SELECT name, type, id FROM gate_defs 
            WHERE saveset_id = :saveid
            ORDER BY id ASC
        ''', {'saveid': self._saveid})
        
        roots = cursor.fetchall()
        
        # Now iterate over each root record doing the appropriate single shot joins
        # to get the child records.  If I were smart, I'd use the gate type to
        # minimize queries but that would mean propagating knowledge of those types
        # down to this level which I'm avoiding.
        
        for root in roots:
            name  = root[0]
            ctype = root[1]
            id    = root[2]
            #        Gate points.
            cursor.execute('''
                    SELECT x,y FROM gate_points
                    WHERE gate_id = :id
                    ORDER BY id ASC  
                ''', {'id': id})
            pts = cursor.fetchall() # [(x,y), (x,y)....]
            #         Parmeter names:
            cursor.execute('''
                SELECT name FROM parameter_defs
                INNER JOIN gate_parameters ON parameter_defs.id = gate_parameters.parameter_id
                WHERE parent_gate = :id
                ORDER BY gate_parameters.id ASC
            ''', {'id': id})
            pnames = [x[0] for x in cursor.fetchall()]
            
            #      Component condition names:
            
            cursor.execute('''
                SELECT name from gate_defs
                INNER JOIN component_gates ON component_gates.child_gate = gate_defs.id
                WHERE parent_gate = :id
                ORDER BY component_gates.id ASC
            ''', {'id': id})
            components = [x[0] for x in cursor.fetchall()]
            
            #  Mask:
            
            cursor.execute('''
                SELECT mask FROM gate_masks WHERE parent_gate = :id
            ''', {'id': id})
            mask = cursor.fetchall()
            
            definition = {
                'name' :name,
                'type' :ctype,
                'points': pts,
                'parameters' : pnames,
                'dependencies' : components
            }
            if len(mask) == 1:
                definition['mask'] = mask[0]
            else:
                definition['mask'] = None
            result.append(definition)
            
        return result
    def read_applications(self):
        '''
        Return a  list of dicts that describe which conditions are applied to which spectra.
        The dicts have the keys:
        spectrum - name of a spectrum.
        condition - Name of the condition applied to the spectrum.
        
        The list can be empty.
        '''
        
        cursor = self._sqlite.cursor()
        
        cursor.execute('''
            SELECT spectrum_defs.name, gate_defs.name FROM spectrum_defs
            INNER JOIN gate_applications on spectrum_id = spectrum_defs.id
            INNER JOIN gate_defs ON gate_defs.id = gate_applications.gate_id
            WHERE spectrum_defs.save_id = :saveid
        ''', {'saveid': self._saveid})
        
        data = cursor.fetchall()
        
        return [{'spectrum': x[0], 'condition': x[1]} for x in data]
    
