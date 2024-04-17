from SerializableObject import SerializableObject
from TypeCode import TypeCode
from Spectrum import Spectrum
import ApplicationSerializer
import ParameterTypes
import datetime

class SpectralData(SerializableObject):
    def __init__(self, type):
        """
        Description:
            Initializes this instance
        Arguments:
            type (int)    The type of spectral data, see TypeCodes
                          class.
        Return:
            (int) the value
        """
        SerializableObject.__init__(self, type)
        self.__startTime=datetime.datetime.utcnow()
        self.__status=ParameterTypes.DeviceStatus.Idle
        self.__input=1
        self.__group=1
        self.__spectrum=Spectrum()

    def update(self, startT=None, spec=None, status=None, input=None, group=None):
        """
        Description:
            Updates the spectral data contents
        Arguments:
            startT (datetime)    The start time
            spec (Spectrum)    The spectrum
            status (int)    The status
            input (int)    The input
            group (int)    The group
        Return:
            None
        """
        if not (startT is None):
            self.__startTime = startT
        if not (spec is None):
            self.__spectrum = spec
        if not (status is None):
            self.__status = int(status)
        if not (input is None):
            self.__input = int(input)
        if not (group is None):
            self.__group = int(group)

    def getStartTime(self):
        """
        Description:
            Gets the acquisition start time
        Arguments:
            none
        Return:
            (DateTime) the value
        """
        return self.__startTime
    def getGroup(self):
        """
        Description:
            Gets the memory group
        Arguments:
            none
        Return:
            (int) the value
        """
        return self.__group
    def getInput(self):
        """
        Description:
            Gets the input number
        Arguments:
            none
        Return:
            (int) the value
        """
        return self.__input
    def getStatus(self):
        """
        Description:
            Gets the input status
        Arguments:
            none
        Return:
            (int) the value see ParameterTypes.DeviceStatus class
        """
        return self.__status
    def getSpectrum(self):
        """
        Description:
            Gets the spectrum
        Arguments:
            none
        Return:
            (Spectrum) the value
        """
        return self.__spectrum
    def getDataSize(self):
        """
        Description:
            Gets the size in bytes of data to serialize
        Arguments:
            none
        Return:
            (int) the value
        """
        return self.__spectrum.getSize() + 4 + 4 + 8
    def serializeData(self, stream):
        """
        Description:
            Serializes all data contained in this instance into
            a stream
        Arguments:
            stream (in, char [])    The stream to append to
        Returns:
            char[]    The stream containing the results
        """
        stream += ApplicationSerializer.ApplicationSerializer.serialize(self.__startTime)
        stream += ApplicationSerializer.ApplicationSerializer.serialize(int(self.__status), objTypeCode=TypeCode.Int)
        stream += ApplicationSerializer.ApplicationSerializer.serialize(self.__input, objTypeCode=TypeCode.Short)
        stream += ApplicationSerializer.ApplicationSerializer.serialize(self.__group, objTypeCode=TypeCode.Short)
        stream += self.__spectrum.serialize()
        return stream
    def deserializeData(self, stream):
        """
        Description:
            Deserializes all data contained in this instace into
            a stream
        Arguments:
            stream (in, char [])    The stream to append to
        Returns:
            char[]    The stream minus the deserialized data
        """
        [self.__startTime, stream] = ApplicationSerializer.ApplicationSerializer.deserialize(stream, TypeCode.DateTime) 
        [self.__status, stream] = ApplicationSerializer.ApplicationSerializer.deserialize(stream, TypeCode.Int) 
        [self.__input, stream] = ApplicationSerializer.ApplicationSerializer.deserialize(stream, TypeCode.Short) 
        [self.__group, stream] = ApplicationSerializer.ApplicationSerializer.deserialize(stream, TypeCode.Short) 
        return self.__spectrum.deserialize(stream)
        
