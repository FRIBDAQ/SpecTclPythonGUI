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
    global _SpectrumNames
    print('updating validnames: ', names)
    _SpectrumNames= {x : x for x in names}
    

def ValidNames() :
    global _SpectrumNames
    return _SpectrumNames
class SpectrumSet :
    ''' 
        Container class for a spectrum set.
    '''
    def __init__(self, name, description=None):
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
           Remove a single spectrum from the set. Raises 'ValueError' if spectrum
           is not in the list.
        '''
        self.spectra.remove(spectrum)

    def validate(self):
        ''' Return a list of spectra that are not valid
        
        '''
        
        result = []
        for spectrum in self.spectra:
            if not spectrum in _SpectrumNames:
                result.append(spectrum)
        
        return result
    
    def getname(self) :
        ''' Return name of the set: '''
        return self.name
    def getdescription(self):
        ''' Return the description  cuold be None if not set. '''
        
        return self.description
    def getspectra(self):
        ''' Returns the spectrum in the list '''
        return self.spectra
    def apply(self, function, extra_arg = None) :
        ''' 
          Applies a function to each element of the spectrum list
          
          function - the function to apply
          extra_arg - extra argument to hand the function.
          
          The function is called function(extra_arg, name) e.g.
        '''
        for name in self.spectra:
            function(extra_arg, name)
    
    #----------------------------------------------------------------------
    #  Unit tests.
    #---------------------------------------------------------------------
    
import unittest
class TestSpectrumSet(unittest.TestCase):
    def setUp(self):
        global _SpectrumNames
        _SpectrumNames = dict()
        self.applyList = ['spec1', 'spec2', 'spec3', 'spec4']
        self.fnresult = []
    def tearDown(self):
        pass
        
    def test_valid_names_1(self) :
        
        self.assertEqual({}, _SpectrumNames)
    def test_valid_names_2(self):
        
        UpdateValidNames(['a', 'b', 'c']) 
        self.assertEqual({'a': 'a', 'b': 'b', 'c': 'c'}, _SpectrumNames)

    def test_create_0(self):
        
        listing = SpectrumSet('aname')
        self.assertEqual('aname', listing.name)    
        self.assertIsNone(listing.description)
        self.assertEqual([], listing.spectra)
    def test_create_1(self):
        
        listing = SpectrumSet('aname', 'list description')
        self.assertEqual('aname', listing.name)    
        self.assertEqual('list description', listing.description)
        self.assertEqual([], listing.spectra)
        
    def test_add_1(self):
        
        listing = SpectrumSet('aname')
        UpdateValidNames(['spec1'])
        listing.add(['spec1'])
        self.assertEqual(['spec1'], listing.spectra)
    
    def test_add_2(self):
        listing = SpectrumSet('aname')
        self.assertRaises(KeyError, SpectrumSet.add, self, 'junk')
        
    def test_remove_1(self):
        s = ['spec1', 'spec2', 'spec3', 'spec4']
        UpdateValidNames(s)
        listing = SpectrumSet('aname')
        listing.add(s)
        listing.remove('spec3')
        self.assertEqual(['spec1', 'spec2', 'spec4'], listing.spectra)
    def test_remove_2(self):
        s = ['spec1', 'spec2', 'spec3', 'spec4']
        UpdateValidNames(s)
        listing = SpectrumSet('aname')
        listing.add(s)
        self.assertRaises(ValueError, SpectrumSet.remove, listing, 'junk')    # no op.
    
    def test_getname_1(self):
        listing = SpectrumSet('aname')
        self.assertEqual('aname', listing.getname())        
    def test_getdescription_1(self):
        self.assertIsNone(SpectrumSet('aname').getdescription())
    def test_getdescription_2(self):
        self.assertEqual('this is something', SpectrumSet('aname', 'this is something').getdescription())
    def test_getspectra_1(self):
        listing = SpectrumSet('aname')
        self.assertEqual([], listing.getspectra())
    def test_getspectra_2(self):
        listing = SpectrumSet('aname')
        s = ['spec1', 'spec2', 'spec3', 'spec4']
        UpdateValidNames(s)
        listing.add(s)
        self.assertEqual(s, listing.getspectra())   
    
    def apply_function(self, name):
        self.fnresult.append(name)
        
    def test_apply_1(self):
        listing = SpectrumSet('aname')
        listing.apply(TestSpectrumSet.apply_function, self)
        self.assertEqual([], self.fnresult)
    def test_apply_2(self):
        listing = SpectrumSet('aname')
        s = ['spec1', 'spec2', 'spec3', 'spec4']
        UpdateValidNames(s)
        listing.add(s)
        listing.apply(TestSpectrumSet.apply_function, self)
        self.assertEqual(s, self.fnresult)
        
    def test_valid_1(self):
        self.assertEqual([], ValidNames())
    def test_valid_1(self) :
        s = ['spec1', 'spec2', 'spec3', 'spec4']
        UpdateValidNames(s)
        self.assertEqual(s, [x for x in ValidNames().keys()])
        
if __name__ == '__main__':
    unittest.main()