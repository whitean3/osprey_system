import datetime
import struct
import sys
import time
import Parameter
import Command
import PhaData
import McsData
import DlfcData
import CounterData
import RegionOfInterest
import ParameterAttributes
import ListData
import Spectrum
import SCAdefinitions
import SCAbuffer
import DigitalOscilloscopeData
from TypeCode import TypeCode
from Exceptions import SerializationException
from MetaData import MetaData
from SerializableObject import SerializableObject

if sys.version_info >= (3, 0):
    long = int

class Uint64(object):
    def __init__(self, val):
        self.value = long(val)
        self.uint64 = True

def convertToLocalDate(val):
    """
    Description:
        This method will convert the value received from the lynx, which
        is a Win32 FILETIME struct, into a localized Python date/time
    Arguments:
        val    (in, double or long) The value to convert
    Returns:
        (datetime) The converted value
    """
    _FILETIME_null_date = datetime.datetime(1601, 1, 1, 0, 0, 0)
    import sys
    if sys.version_info >= (3, 0):
        timestamp = int(val)
    else:
        timestamp = long(val)
    val= _FILETIME_null_date + datetime.timedelta(microseconds=timestamp/10) - datetime.timedelta(seconds=time.timezone)
    #if (1==time.daylight):
    #    val += datetime.timedelta(seconds=3600)
    return val


def convertToLynxDate(dt):
    """
    Description:
        This method will convert the argument to a Lynx date/time value
    Arguments:
        dt    (in, datetime) The value to convert
    Returns:
        (long) The converted value
    """
    from datetime import datetime, timedelta, tzinfo
    from calendar import timegm


    ZERO = timedelta(0)
    HOUR = timedelta(hours=1)


    class UTC(tzinfo):
        """UTC"""
        def utcoffset(self, dt):
            return ZERO

        def tzname(self, dt):
            return "UTC"

        def dst(self, dt):
            return ZERO


    utc = UTC()
    EPOCH_AS_FILETIME = 116444736000000000  # January 1, 1970 as MS file time
    HUNDREDS_OF_NANOSECONDS = 10000000

    if (dt.tzinfo is None) or (dt.tzinfo.utcoffset(dt) is None):
        dt = dt.replace(tzinfo=utc)
    ft = EPOCH_AS_FILETIME + (timegm(dt.timetuple()) * HUNDREDS_OF_NANOSECONDS)
    return ft + (dt.microsecond * 10)

                        
class ApplicationSerializer:    
    """
    Description:
        This is a utility class that will perform all of
        the application serialization.  Note: This class will
        handle all of the endian transformations.  Therefore,
        the consumer layer, Device class instance, will always
        return the correct data representation.
    """    
    def getTypeCode(obj):
        """
        Description:
            Returns the Lynx type code used to describe
            the data type of the argument
        Arguments:
            obj    (in, any)    The data
        Exceptions:
            SerializationException.
        Return:
            int    The type code see TypeCode class
        """
        if (None == obj):
            return TypeCode.Null
        elif(isinstance(obj, bool)):
            return TypeCode.Bool
        elif (isinstance(obj, int)) :
            return TypeCode.Uint
        elif(isinstance(obj, float)):
            return TypeCode.Double        
        elif(isinstance(obj, str)):
            return TypeCode.String
        elif(isinstance(obj, datetime.datetime)):
            return TypeCode.DateTime
        elif(isinstance(obj, SerializableObject)):
            return obj.getType()
        elif(hasattr(obj, 'uint64')):
            return TypeCode.Long
        elif(hasattr(obj, 'getType')):
            return obj.getType()
        else:
            if sys.version_info < (3, 0):
                if isinstance(obj, long):
                    return TypeCode.Long

            raise SerializationException("Type not supported: %s" % type(obj))
    getTypeCode = staticmethod(getTypeCode)
    
    def getTypeSize(obj):
        """
        Description:
            Returns the number of bytes that are used
            to contain all of the data within the object
        Arguments:
            obj    (in, any)    The data
        Exceptions:
            SerializationException.            
        Return:
            int    The size in bytes
        """
        if (None == obj):
            return 0
        elif(isinstance(obj, bool)):
            return 1
        elif (isinstance(obj, int)) :
            return 4
        elif(isinstance(obj, float)):
            return 8        
        elif(isinstance(obj, str)):
            return len(obj.encode('utf_16_le'))
        elif(isinstance(obj, datetime.datetime)):
            return 8
        elif(isinstance(obj, SerializableObject)):
            return int(obj.getSize())
        elif(hasattr(obj, 'uint64')):
            return 8
        elif(hasattr(obj, 'getSize')):
            return obj.getSize()
        else:
            if sys.version_info < (3, 0):
                if isinstance(obj, long):
                    return 8
            raise SerializationException('Type not supported: %s'%type(obj))
        
    getTypeSize = staticmethod(getTypeSize)
    
    def serialize(obj, stream=b'', writeMeta=False, objTypeCode=None):
        """
        History:
            This method serializes the data contained
            in this instance into the stream
        Arguments:
            obj         (in, any) The data to serialize
            stream      (in, char[]) The stream to append to
            writeMeta   (in, bool) Flag to indicate metadata should be written
                        before the data value is written.  This is optional.
                        If not supplied, no metadata is written
            objTypeCode (in, int) The type code of the obj parameter.  See
                        the TypeCode class.  This is optional.  If not
                        supplied, the type is dynamically determined.
        Exceptions:
            SerializationException.
        Return:
            stream    (char []) The stream containing the information plus
                                the additional stream data specified as via
                                the method argument='stream'
        """        
        if (writeMeta):
            metaData = MetaData(ApplicationSerializer.getTypeCode(obj), ApplicationSerializer.getTypeSize(obj))
            stream += metaData.serialize()
            
        if (None == obj): pass
        elif(isinstance(obj, bool) or (objTypeCode == TypeCode.Bool)):
            if (obj is True) :
                stream += struct.pack("B", 1)
            else:
                stream += struct.pack("B", 0)
        elif ((objTypeCode == TypeCode.Byte)) :
            stream += struct.pack("b", obj)
        elif ((objTypeCode == TypeCode.Ubyte)) :
            stream += struct.pack("B", obj)
        elif ((objTypeCode == TypeCode.Short) or (objTypeCode == TypeCode.Ushort)) :
            stream += struct.pack("<h", obj)
        elif objTypeCode == TypeCode.Uint :
            import ctypes
            stream += struct.pack("<I", ctypes.c_uint32(obj).value)
        elif((objTypeCode == TypeCode.Long) or (objTypeCode == TypeCode.Ulong)):
            import ctypes
            stream += struct.pack("<q", ctypes.c_uint64(obj).value)
        elif(objTypeCode == TypeCode.Float):
            stream += struct.pack("<f", obj)    
        elif (isinstance(obj, int) or (objTypeCode == TypeCode.Int)):
            stream += struct.pack("<i", obj)
        elif(hasattr(obj, 'uint64')):
            stream += struct.pack("<q", obj.value)
        elif(isinstance(obj, float) or (objTypeCode == TypeCode.Double)):
            stream += struct.pack("<d", obj)        
        elif(isinstance(obj, str) or (objTypeCode == TypeCode.String)):
            if (writeMeta is False):
                length = len(obj.encode('utf_16_le'))
                stream += struct.pack("<i", length)            
            stream += obj.encode('utf_16_le')
            #stream += struct.pack("%ds"%length, obj.encode('utf-16'))
        elif(isinstance(obj, datetime.datetime) or (objTypeCode == TypeCode.DateTime)):
            tmp = convertToLynxDate(obj)
            stream += struct.pack("<q", tmp)
        elif(isinstance(obj, SerializableObject)):
            stream += obj.serialize()
        elif(hasattr(obj, 'serialize')):
            stream += obj.serialize()
        elif(TypeCode.Null == type): pass  
        else:
            if sys.version_info < (3, 0):
                if isinstance(obj, long):
                    stream += struct.pack("<q", obj)
                    return stream

            raise SerializationException('Type not supported: %s'%type(obj))          
        return stream          
    serialize = staticmethod(serialize)
    
    def deserialize(stream, type=TypeCode.Unknown, size=0):
        """
        History:
            This method deserializes the data contained
            in the stream and returns it to the user
        Arguments:                    
            stream    (in, out, char[]) The stream to receive the data
            type      (in, int) The data type.  See TypeCode class
            size      (in, optional, int) The size of the data. Used only for strings
        Exceptions:
            SerializationException.
        Return:
            [any, char[]] [The deserialized instance, The stream minus the deserialized data]
        """
        if (TypeCode.Int == type):
            data=struct.unpack("<i", stream[0:4])[0]
            stream = stream[4:]            
        elif(TypeCode.Uint == type):
            data=struct.unpack("<I", stream[0:4])[0]
            stream = stream[4:]  
        elif(TypeCode.Long == type):
            data = struct.unpack("<q", stream[0:8])[0]
            stream = stream[8:]  
        elif(TypeCode.Ulong == type):
            data = struct.unpack("<Q", stream[0:8])[0]
            stream = stream[8:]  
        elif(TypeCode.Short == type):
            data = struct.unpack("<h", stream[0:2])[0]
            stream = stream[2:]   
        elif(TypeCode.Ushort == type):
            data = struct.unpack("<H", stream[0:2])[0]
            stream = stream[2:]   
        elif (TypeCode.Byte == type) :
            data = struct.unpack("<b", stream[0:1])[0]
            stream = stream[1:] 
        elif (TypeCode.Ubyte == type) :
            data = struct.unpack("<B", stream[0:1])[0]
            stream = stream[1:]   
        elif(TypeCode.Float == type):
            data = struct.unpack("<f", stream[0:4])[0]
            stream = stream[4:]    
        elif(TypeCode.Double == type):
            data = struct.unpack("<d", stream[0:8])[0]
            stream = stream[8:]         
        elif(TypeCode.Bool == type):
            data = struct.unpack('<B', stream[0:1])[0]
            if (0 == data):
                data = False
            else:
                data = True
            stream = stream[1:]
        elif(TypeCode.Null == type):            
            data = None
        elif(TypeCode.String == type):
            if (size > 0):
                length = size
            else:
                length = struct.unpack("<i", stream[0:4])[0]
                stream = stream[4:]
            data = stream[0:length]
            data = data.decode('utf-16')
            stream = stream[length:]
        elif(TypeCode.DateTime == type):
            ft = struct.unpack("<q", stream[0:8]) 
            data = convertToLocalDate(ft[0])
            stream = stream[8:]  
        elif(TypeCode.SCAdefinitionData == type):
            data = SCAdefinitions.SCAdefinitions()
            stream = data.deserialize(stream)
        elif(TypeCode.SCAbufferData == type):
            data = SCAbuffer.SCAbuffer()
            stream = data.deserialize(stream)
        elif(TypeCode.CommandData == type):
            data = Command.Command()
            stream = data.deserialize(stream)
        elif(TypeCode.ParameterData == type):
            data = Parameter.Parameter()
            stream = data.deserialize(stream)
        elif(TypeCode.PhaData == type):
            data = PhaData.PhaData()
            stream = data.deserialize(stream)
        elif(TypeCode.McsData == type):
            data = McsData.McsData()
            stream = data.deserialize(stream)
        elif(TypeCode.DlfcData == type):
            data = DlfcData.DlfcData()
            stream = data.deserialize(stream)
        elif(TypeCode.CounterData == type):
            data = CounterData.CounterData()
            stream = data.deserialize(stream)
        elif(TypeCode.RegionOfInterestData == type):
            data = RegionOfInterest.RegionOfInterest()
            stream = data.deserialize(stream)
        elif(TypeCode.ParameterMetaData == type):
            data = ParameterAttributes.ParameterAttributes()
            stream = data.deserialize(stream)
        elif(TypeCode.ListData == type):
            data = ListData.ListData()
            stream = data.deserialize(stream)
        elif(TypeCode.TlistData == type):
            data = ListData.TlistData()
            stream = data.deserialize(stream)
        elif(TypeCode.SpectralData == type):
            data = Spectrum.Spectrum()
            stream = data.deserialize(stream)
        elif(TypeCode.DsoData == type):
            data = DigitalOscilloscopeData.DigitalOscilloscopeData()
            stream = data.deserialize(stream)
        elif(TypeCode.Unknown == type):
            #Punt and assume there is metadata in the stream
            metaData = MetaData()
            stream = metaData.deserialize(stream)
            return ApplicationSerializer.deserialize(stream, metaData.getDataType(), metaData.getDataSize())
        elif(TypeCode.Blob == type):
            # This is a BLOB
            return [stream, stream]
        else:
            raise SerializationException('Type not supported, Canberra Type Code: %d'%type)
        return [data, stream]
    deserialize = staticmethod(deserialize)
