'''
  This module has the controller for the bindings UI.  It is expected to
  instantiate a BindingsGroupTab  and any other dialogs that will want to pop up
  by attaching to appropriate signals in that megawidget.
  
  We also will have some methods to load binding groups in from some external
  as well as a method to fetch out the bindings list to the some external entity.
  
  This is needed to support saving and restoring bindings groups from file.
  
  The model part of the MVC is loaded as internal data to the view from the underlying actual model:
  the server and spectrum sets held by the specstrumset.SpecTrumSet objects.
'''

from spectrumset import UpdateValidNames, ValidNames, SpectrumSet
from bindings import *
from SpectrumList import SpectrumModel
from bindingeditor import promptNewBindingList, editBindingList

from PyQt5.QtWidgets import QMessageBox



class BindingsController:
  '''
    See the module documentation.
    Important methods:
    
    - loadBindingGroups - loads the binding groups from some external source
    - fetchGroups       - Fetches bindings so they can be saved somewhere.
  '''
  def __init__(self, client, view):
      '''  client is a rustogrammer client object
              It will be used to:
              1. maintain the spectrumlist.
              2. execute bind operations in the server.
            view - is the view object it must conform to the interfaces in the
                  BindingGroupTab api.
      '''
      self._view = view
      self._client = client
      self._bindinglists = list()  # list of SpectrumSet Each is a dict of name, desc, and spectrumset.
      self._spectrumList = SpectrumModel()
      
      self._updateValidSpectra()
      
  
      # Connect to the view actions:
      
      self._view.new.connect(self._createNew)
      self._view.edit.connect(self._editExisting)
      self._view.load.connect(self._bindgroup)
      self._view.add.connect(self._addgroup)
      self._view.save.connect(self._saveoncurrent)
      self._view.saveas.connect(self._savenew)
      self._view.bindall.connect(self._bindall)
      self._view.update.connect(self._updateValidSpectra)
      
      #  Public methods.
      
  def loadBindingGroups(self, groups):
    ''' 
      Load the binding groups from some external source.
      The form of each group in the iterable parameter _groups_ is
      a dict containing:
      name:   - name of the binding group.
      description - Description of the binding group.
      spectra - Spectra in the binding group.
      
      We'll convert spectra into a SpectrumSet and silently discard any with 
      invalid spectra.. thus we do an _update first to have the most current
      set of bindings.
    '''
    
    self._bindinglists = list()
    self._updateValidSpectra()
    for group in groups:
      try:
        self._bindinglists.append(self._dictToList(group))
      except:
        pass                        # non fatal, just drop that set.            
    self._fixBindings() 
    self._updateView()

  def fetchGroups(self) :
    '''
        Result is a list of dicts as per loadBindingsGroup
    '''
    return self._groupsToDicts()


  def updateValidSpectra(self):

    self._updateValidSpectra()
    
  #  Private methods

  # signal handlers.

  def _updateValidSpectra(self):
    # Using the client, get the list of spectra into our spectrum list model
    # fetch the names into the valid spectrum names of spectrumset
    
    
    self._spectrumList.load_spectra(self._client)
    UpdateValidNames(self._spectrumList.getNames())
    self._fixBindings()
    self._updateView()
    
  
    
  def _createNew(self):
    # Pop up an editor dialog... with no  initial binding.  Accepting results in
    # a new binding.      

    
    new = promptNewBindingList(self._view, self._spectrumList.getNames())
    if new is not None:
      # new is a bindings dict... add it to our bindings list and 
      # update the view:
      self._bindinglists.append(self._dictToList(new))
      self._updateView()

  def _editExisting(self):
      #  Edit the currently selected binding no-op if nothing is selected.
      
      current = self._view.selectedBinding()
      if len(current) == 1:
        current = current[0]
        modified = editBindingList(self._view, ValidNames(), current)
        if modified is not None:
          # Might replace _or_ be a new one.
          
          self._addOrModifyBinding(modified)
          self._updateView()
        
  def _bindgroup(self):
      # Load the selected binding group into the server's spectrum memory,
      # first clearing the present bindings:
      
      self._client.unbind_all()
      self._addgroup()                   # Append selected bindings to nothing 
      
  def _addgroup(self):
      # If possible adds the selected bindings to those in the server's shared 
      # spectrum memory:
      
      sel = self._view.selectedBinding()
      if len(sel) == 1:
          sel = sel[0]
          try :
            self._client.sbind_spectra(sel['spectra'])
            self._view.setLoaded(sel['name'], sel['description'])
          except:
            QMessageBox.warning(
              self._view, 
              '''Unable to bind all of the spectra in the binding list. 
  Might not be enough shared memory''')

  def _saveoncurrent(self):
    #  Save the currently loaded bindings over the selected bindset. 
    
    sel = self._view.selectedBinding()
    if len(sel) == 1:
      sel = sel[0]
      bindings = self._client.sbind_list()['detail']
      sel['spectra'] = [x['name'] for x in bindings]  
      self._addOrModifyBinding(sel)
      self._updateView()

  def _savenew(self):
    # Save current bindings as a new one:
    
    bound = [x['name'] for x in self._client.sbind_list()['detail']]
    binding = {'name' :'', 'description' :'', 'spectra':bound}
    modified = editBindingList(self._view, ValidNames(), binding)
    if modified is not None:
      self._addOrModifyBinding(modified)
      self._updateView()

  def _bindall(self):
    # BInd all spectra:
    
    self._client.unbind_all()
    self._client.sbind_all()

  
    
  ########################### 
  #  Utilities

  def _updateView(self):
    # Update the binding lists in the view so that they match whats in our
    # internal list.  We do this by forming the list of dicts and then 
    # invoking setBindingsGroups in the view:
    
    d = self._groupsToDicts()
    self._view.setBindingGroups(d) 
    

  def _groupsToDicts(self):
    # convert the bindings groups to dicts:
    
    grps = []
    for bg in self._bindinglists :
      grps.append(self._setToDict(bg))
    return grps
  def _setToDict(self, s):
    return {'name' : s.getname(), 
              'description': s.getdescription(), 
              'spectra':s.getspectra()
      }
  def _dictToList(self, d):
    # Convert a dict to a spectrum list - returns None if the dict is not valid.
    
    result = SpectrumSet(d['name'], d['description'])
    try:
      result.add(d['spectra'])
    except:
      result = None
    return result
    
    
  def _addOrModifyBinding(self, modified):
    # Given a binding, either replaces an existing one _or_
    # if there is no existing one, appends it to the bindings list.
    
    i = 0 
    replaced = False
    while i < len(self._bindinglists):
      if self._bindinglists[i].getname() == modified['name']:
        self._bindinglists[i]  = self._dictToList(modified)
        replaced = True
        break
      else:
        i += 1
    if not replaced:
      self._bindinglists.append(self._dictToList(modified))

  def _fixBindings(self):
    #  Normally called after the list of spectra have been updated.
    #  For now, removes binding sets that are invalid because
    #  their spectra have been yanked.
    #  TODO:  Instead, maybe(?) remove just the invalid spectra.
    
    bad_indexes = list()            # list of invalid indices
    i = 0
    while i < len(self._bindinglists):
      if len(self._bindinglists[i].validate()) > 0:
        bad_indexes.append(i)
      i += 1
    bad_indexes.sort(reverse=True)
    for i in bad_indexes:
      self._bindiglists.pop(i)
      
      
      
    
