from SpectralData import SpectralData
from TypeCode import TypeCode
from Exceptions import UnsupportedCompressionException
import ApplicationSerializer
import ParameterTypes
from sys import version_info
if version_info[0] >= 3:
    long = int

class PhaData(SpectralData):
    """
    Description:
        An instance of this class is used to encapsulate all data related
        to Pha data such as spectrum, real time, live time, computational
        value.
    """
    def __init__(self):
        """
        Description:
            This method will initialize the instance
        Arguments:
            None
        Returns:
            None
        """
        SpectralData.__init__(self, TypeCode.PhaData)
        self.__liveTime = 0
        self.__realTime = 0
        self.__compValue = 0

    def update(self, elive=None, ereal=None, ecomp=None, startT=None, spec=None, status=None, input=None, group=None):
        """
        Description:
            Updates the PHA data contents
        Arguments:
            elive (long)    The elapsed live
            ereal (long)    The elapsed real
            ecomp (long)    The elapsed comp preset
            startT (datetime)    The start time
            spec (Spectrum)    The spectrum
            status (int)    The status
            input (int)    The input
            group (int)    The group
        Return:
            None
        """
        if not (elive is None):
            self.__liveTime = long(elive)
        if not (ereal is None):
            self.__realTime = long(ereal)
        if not (ecomp is None):
            self.__compValue = long(ecomp)
        SpectralData.update(self, startT, spec, status, input, group)

    def getLiveTime(self):
        """
        Description:
            This method will return the live time (uS)
        Arguments:
            None
        Returns:
            (double) The value
        """
        return self.__liveTime
    def getRealTime(self):
        """
        Description:
            This method will return the real time (uS)
        Arguments:
            None
        Returns:
            (double) The value
        """
        return self.__realTime
    def getComputationalValue(self):
        """
        Description:
            This method will return the computational
            value provided computational preset is enabled
        Arguments:
            None
        Returns:
            (Long) The value
        """
        return self.__compValue
    def getDataSize(self):
        """
        Description:
            Gets the size in bytes of data to serialize
        Arguments:
            none
        Return:
            (int) the value
        """
        return SpectralData.getDataSize(self) + 3*8
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
        stream += ApplicationSerializer.ApplicationSerializer.serialize(long(self.__liveTime), objTypeCode=TypeCode.Long)
        stream += ApplicationSerializer.ApplicationSerializer.serialize(long(self.__realTime), objTypeCode=TypeCode.Long)
        stream += ApplicationSerializer.ApplicationSerializer.serialize(long(self.__compValue), objTypeCode=TypeCode.Long)
        stream = SpectralData.serializeData(self, stream)
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
        [self.__liveTime, stream] = ApplicationSerializer.ApplicationSerializer.deserialize(stream, TypeCode.Long)
        [self.__realTime, stream] = ApplicationSerializer.ApplicationSerializer.deserialize(stream, TypeCode.Long)
        [self.__compValue, stream] = ApplicationSerializer.ApplicationSerializer.deserialize(stream, TypeCode.Long)
        return SpectralData.deserializeData(self, stream)
