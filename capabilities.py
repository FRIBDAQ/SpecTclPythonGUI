''' This package contains code that
1.  Determines the program type (currently SpecTcl or Rustogramer)
2.  Provides capability information about the current program.
For example; rustogramer only implements a subset of the spectrum and
gate types that SpecTcl implements.  The application can ask questions like
'does the server program implement strip chart spectra?'

Normally this is used to disable/enable parts of the user interface appropriate
to the program.

To minimize the (expensive) interactions with the server, 
'''

from enum import Enum, auto
class Program(Enum) :
    @staticmethod
    def _generate_next_value(name, start, count, last_values) :
        return count+1
    
    Rustogramer = auto()
    SpecTcl = auto()
    Unknown = auto()    # Could not determine server type

server_program = None
major_version = None
minor_version = None
edit_level = None
combined_version = None # (major * 100 + minor)*1000 + editlevel
client = None

version_adjustments_made = False

def _make_combined_version(major, minor, edit):
    # Creates the full version as a single number that can be numerically compared e.g.
    # _make_combined_version(1,2,3) < make_combined_version(1,2, 4)
    #  major - the major version number
    #  minor - the minor version number
    #  edit  - the edit level
    #
    #  Note pre-release versions don't work!!!
    return (major*100 + minor)*1000 + edit
'''
   If the program is not known get it after that, return it:
   Note set_client must have been called.
'''
def get_program():
    #  Note pre release edit levels are treated as 0.
    global server_program
    global major_version
    global minor_version
    global edit_level
    global client
    global version_adjustments_made
    global combined_version
    
    if server_program is None:
        info = client.get_version()
        info = info['detail']
        major_version = int(info['major'])
        minor_version = int(info['minor'])
        try:
            edit_level = int(info['editlevel'])
        except:
            edit_level = 0                    # pre-releasegit 
        combined_version = _make_combined_version(major_version, minor_version, edit_level)
        #  Get the program name.. note version of SpecTcl may
        # not return a program_name key:

        if 'program_name' in info.keys():
            name = info['program_name']
        else:
            name = 'SpecTcl'

        
        # Compue the value of server_program

        if name == 'SpecTcl':
            server_program = Program.SpecTcl
        elif name == 'Rustogramer':
            server_program = Program.Rustogramer
        else:
            server_program = Program.Unknown

        if not version_adjustments_made:
            _adjust_for_version()
    return server_program


'''  This must be called first to provide a client object to the
     package:
'''

def set_client(client_obj): 
    global client
    client = client_obj

def get_client():
    global client
    return client

#  Spectrum Type capabilities:

class SpectrumTypes(Enum):
    @staticmethod
    def _generate_next_value(name, start, count, last_values) :
        return count+1
    
    Oned = auto()
    Twod = auto()
    Summary = auto()
    Gamma1D = auto()
    Gamma2D = auto()
    TwodSum = auto()
    GammaDeluxe = auto()
    Projection = auto()

    #   Not implemented in client API (yet)
    #  But SpecTcl has them :

    StripChart = auto()
    Bitmask    = auto()
    GammaSummary = auto()

# Supported by each type.  This is a map of sets
# OF types supported by both the API and the 
# server program indexed by server program.

supported_spectrum_types = {
    Program.Rustogramer: {
        SpectrumTypes.Oned, SpectrumTypes.Twod,
        SpectrumTypes.Summary, SpectrumTypes.Gamma1D,
        SpectrumTypes.Gamma2D, SpectrumTypes.TwodSum,
        SpectrumTypes.GammaDeluxe,
        SpectrumTypes.Projection
    },
    Program.SpecTcl: {
        SpectrumTypes.Oned, SpectrumTypes.Twod,
        SpectrumTypes.Summary, SpectrumTypes.Gamma1D,
        SpectrumTypes.Gamma2D, SpectrumTypes.TwodSum,
        SpectrumTypes.GammaDeluxe,
        SpectrumTypes.Projection,
        SpectrumTypes.GammaSummary,
        SpectrumTypes.Bitmask,
        SpectrumTypes.StripChart
    },
    Program.Unknown: {}
}

def _has_stype(type_sel):
    global supported_spectrum_types
    server = get_program() 
    return type_sel in supported_spectrum_types[server]

def has_1d():
    return _has_stype(SpectrumTypes.Oned)
def has_2d():
    return _has_stype(SpectrumTypes.Twod)
def has_summary():
    return _has_stype(SpectrumTypes.Summary)
def has_gamma1d():
    return _has_stype(SpectrumTypes.Gamma1D)
def has_gamma2d():
    return _has_stype(SpectrumTypes.Gamma2D)
def has_twod_sum():
    return _has_stype(SpectrumTypes.TwodSum)
def has_pgamma():
    return _has_stype(SpectrumTypes.GammaDeluxe)
def has_stripchart():
    return _has_stype(SpectrumTypes.StripChart)
def has_bitmask():
    return _has_stype(SpectrumTypes.Bitmask)
def has_projection():
    return _has_stype(SpectrumTypes.Projection)
def has_gamma_summary():
    return _has_stype(SpectrumTypes.GammaSummary)
def get_supported_spectrumTypes():
    global supported_spectrum_types
    server_program = get_program()
    return supported_spectrum_types[server_program]
def has_waveforms():
    ''' Return true if the server prorgram supports the waveform
        requests.  This is true if the version is greater than or equal to
        7.0-003 and the program is SpecTcl.
    '''
    server = get_program()
    return server == Program.SpecTcl and combined_version >= _make_combined_version(7,0,3)


#Spectrum data types supported:

class ChannelTypes(Enum):
    Double = auto()
    Long = auto()
    Short = auto()
    Byte = auto()

DataTypeStringsToChannelTypes = {
    'byte': ChannelTypes.Byte,
    'short': ChannelTypes.Short,
    'long' : ChannelTypes.Long,
    'f64'  : ChannelTypes.Double
}
ChannelTypesToDataTypeStrings = {
    ChannelTypes.Byte : 'byte',
    ChannelTypes.Short : 'short',
    ChannelTypes.Long : 'long',
    ChannelTypes.Double : 'f64'
}

supported_channel_types = {
    Program.Rustogramer : {
        ChannelTypes.Double
    },
    Program.SpecTcl : {
        ChannelTypes.Long, ChannelTypes.Short, ChannelTypes.Byte
    },
    Program.Unknown: {}
}

def _has_channel_type(data_type) :
    global supported_channel_types
    return data_type in supported_channel_types[get_program()]

def has_double_channels():
    return _has_channel_type(ChannelTypes.Double)
def has_long_channels():
    return _has_channel_type(ChannelTypes.Long)
def has_short_channels():
    return _has_channel_type(ChannelTypes.Short)
def has_byte_channels():
    return _has_channel_type(ChannelTypes.Byte)
def get_supported_channelTypes():
    global supported_channel_types
    program = get_program()
    return supported_channel_types[program]

def get_default_channelType():
    program = get_program()
    if program == Program.SpecTcl:
        return ChannelTypes.Long
    elif program == Program.Rustogramer:
        return ChannelTypes.Double
    else:
        return ChannelTypes.Long     # Should not be here.

class ConditionTypes(Enum):
    And = auto()
    Band = auto()
    Contour = auto()
    FalseCondition = auto()     # False is a reserved word.
    GammaBand = auto()          # Only in SpecTcl.
    GammaContour = auto()
    GammaSlice  = auto()
    Not = auto()
    Or = auto()
    Slice = auto()
    TrueCondition = auto()
    MaskEqual = auto()           # SpecTclOnly.
    MaskAnd = auto()             # SpecTclOnly.
    MaskNand = auto()          # SpecTclOnly.
    C2Band   = auto()          # SpecTl only.

ConditionTypeNamesToType = {
    '*': ConditionTypes.And,
    'b': ConditionTypes.Band,
    'c': ConditionTypes.Contour,
    'F': ConditionTypes.FalseCondition,
    'gb': ConditionTypes.GammaBand,
    'gc': ConditionTypes.GammaContour,
    '-' : ConditionTypes.Not,
    '+' : ConditionTypes.Or,
    's' : ConditionTypes.Slice,
    'T' : ConditionTypes.TrueCondition,
    'em': ConditionTypes.MaskEqual,
    'am': ConditionTypes.MaskAnd,
    'nm': ConditionTypes.MaskNand,
    
}

supported_condition_types = {
    Program.Rustogramer : {
        ConditionTypes.And, ConditionTypes.Band, ConditionTypes.Contour, 
        ConditionTypes.FalseCondition, ConditionTypes.GammaContour,
        ConditionTypes.GammaSlice,
        ConditionTypes.Not, ConditionTypes.Or, ConditionTypes.Slice,
        ConditionTypes.TrueCondition
    },
    Program.SpecTcl : {
        ConditionTypes.And, ConditionTypes.Band, ConditionTypes.Contour, 
        ConditionTypes.FalseCondition, ConditionTypes.GammaContour,
        ConditionTypes.GammaBand, ConditionTypes.GammaSlice,
        ConditionTypes.Not, ConditionTypes.Or, ConditionTypes.Slice,
        ConditionTypes.TrueCondition,
        ConditionTypes.GammaBand, ConditionTypes.MaskEqual, ConditionTypes.MaskAnd,
        ConditionTypes.MaskNand, 
        ConditionTypes.C2Band
    },
    Program.Unknown: {}
}
def has_condition_type(selector):
    global supported_condition_types
    program = get_program()
    return selector in supported_condition_types[program]

def has_condition_name(name):
    if name not in ConditionTypeNamesToType.keys():  # supports stupid tests.
        return False
    type = ConditionTypeNamesToType[name]
    return has_condition_type(tpe)

def get_supported_condition_types():
    global supported_condition_types
    program = get_program()
    return supported_condition_types[program]

supported_spectrum_format_strings = {
    Program.Rustogramer : ['json', 'ascii'],
    Program.SpecTcl: ['ascii',  'binary'],
    Program.Unknown: []
}
# SpecTcl version 5.13-xxx
# and later support JSON 




def get_supported_spectrum_format_strings():
    global supported_spectum_format_strings
    program = get_program()
    return supported_spectrum_format_strings[program]

def has_rest_runlist():
    ''' 
        True if the program can be asked to process a list of runs (cluster file) via REST:
    '''

    return (get_program() == Program.SpecTcl) and (combined_version >= _make_combined_version(5,14,0))
    

def can_read_raw_events():
    ''' Return TRUE if .evt files can be read. '''
    program = get_program()
    return program == Program.SpecTcl      # SpecTcl can but not rustogramer.

def can_read_parfiles():
    ''' Return true if .par files can be read '''
    program = get_program()
    return program == Program.Rustogramer or \
        (program == Program.SpecTcl and combined_version >= _make_combined_version(5, 13, 10))

def can_rest_detach():
    # The /attach/detach rest request exists.
    
    return get_program() == Program.Rustogramer
        

# Make capability adjusments for version:
# This will wind up looking like a cluster f**k most likely 
# as capabilities are added over time:
def _adjust_for_version():
    
    #   SpecTcl 5.13-013 adds support for JSON spectrum I/O:
    
    if server_program == Program.SpecTcl:
        if combined_version >= _make_combined_version(5, 13, 13):
            supported_spectrum_format_strings[Program.SpecTcl].append('json')
            
        # Version 5.14-xxx adds support for FRIBPipe filters.
        if combined_version >= _make_combined_version(5,14,0):
            spectcl_filter_formats.append("FRIBPipe")
            

#
#  Issue #172 - support both xdr and FRIBPipe filter file formats:
#  Note:  This is only for SpecTcl as there is no support for filters
#        in rustogramer:

spectcl_filter_formats = ["xdr"]

def supported_filter_formats():
    '''  Return a list of the supported filter file formats.
         If not SpecTcl, we return an empty string otherwise
         spectcl_filter_formats
    '''
    program = get_program()
    if program == Program.SpecTcl:
        return spectcl_filter_formats
    else: 
        return []