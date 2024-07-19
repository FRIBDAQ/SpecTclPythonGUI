'''
This module provide a mechanism to group spectra in to sets.  To this module, 
there are a set of spectrum names which can be udpated by the client. 
A spectrum set is a list of names from the list of valid names.
Spectrum sets have the following capabilities:

-  Spectrum sets have names and an optional description which can be set or retrieved.
-  Spectra can be added.
-  Spectra can be removed.
-  The list of spectrum names can be fetched.
-  A list of spectrum names that are no longer in the (recently updated) spectrum list
can be retrieved.


'''

# the list of valid spectrum names is a hash for easy, fast lookup.
_SpectrumNames = {}

def UpdateValidNames(names) :
    '''
        sets a new set of valid spectrum names.  I imagine this is gotten via
        interactions with  the histogrammer REsT server.
        
        names - an interable that contains the valid names.
        
        The resulting dict will have as key values the key.  Really this is just so
        we can do in operations quickly on cases where there are 1000's of spectra
        (think Gamma Group).
        
    '''
    _SpectrumNames= {x : x for x in names}
    
    
class SpectrumSet :
    ''' 
        Container class for a spectrum set.
    '''
    def __init(self, name, description=None):
        '''
          Create the spectrum set - The resulting set will be
          empty.
          
          name - name of the set
          description - set description (optional).
        '''
        self.name = name
        self.description = description
        self.spectra = []
    
    def add(self, spectra):
            '''
             Add spectra to the list.  If a proposed spectrum is not
             in the _SpectumNames list, no spectra are added and a
             'KeyError' is raised.
             
             spectra - iterable containing the spectrum names to add
             
             Up to the client to ensure that spectra  have no duplicates.
            '''
            #   Make a validated list -- this comprehension will raise
            #  KeyError for a bad spectrum.
            
            spectra = [_SpectrumNames[x]  for x in spectra]
            self.spectra.extend(spectra)
    
    def remove(self, spectrum):
        '''
           Remove a single spectrum from the set.
        '''
        this.spectra.remove(spectrum)

    def validate(self):
        ''' Return a list of spectra that are not valid
        
        '''
        
        result = []
        for spectrum in this.spectra:
            if not spectrum in _SpectrumNames:
                result.append(spectrum)
        
        return result
    
    def name(self) :
        ''' Return name of the set: '''
        return self.name
    def description(self):
        ''' Return the description  cuold be None if not set. '''
        
        return self.description
    def spectra(self):
        ''' Returns the spectrum in the list '''
        return self.spectra
    def apply(self, function, extra_arg = None) :
        ''' 
          Applies a function to each element of the spectrum list
          
          function - the function to apply
          extra_arg - extra argument to hand the function.
          
          The function is called function(name, extra_arg) e.g.
        '''
        for name in self.spectra:
            function(name, extra_arg)
    