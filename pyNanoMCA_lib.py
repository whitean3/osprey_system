# -*- coding: utf-8 -*-
"""
File:           pyNanoMCA_lib.py
Description:    Cross-platform communication library for the Labzy/Yantel nanoMCA.
Creator:        Joshua A. Handley (2022)


The labZY Device is a slave device while the host is a master device.
- Therefore, the master initiates the communication by sending a command.
- Subsequent commands are sent by the host only after a complete and valid response has been received from the labZY Device or a time-out interval has been reached.
- The time-out interval should be equal or greater than five seconds.

There are only two commands to access data and to control the labZY Device.
- The FPGA spectral data (spectrum) and the FPGA registers are accessed as memory data at specific addresses.
- Each memory location is organized and accessed as a 16-bit word.
    - Each 16-bit word consists of two bytes and two words comprise a long word.
    - Bytes representing words and long words, and words representing long words are stored in the memory in a Little-Endian order.
- The host sends and receives the data as a sequence of bytes.
    - The first byte in the sequence is designated as zero byte (BYTE[0]) followed by bytes whose order is incrementally numbered.
    - Bytes are sent in order that follows the Little-Endian rule when the bytes represent words or long words.
- The data is read or written in words starting at an initial address IADR or IADW respectively.
    - This address is specified in the commands sent by the host to the labZY Device.
    - An AutoIncrement bit is a part of the address information send by the host.
        - If the AutoIncrement bit in the address field of the command is set to one, then the data address will be incremented automatically after each word reading/writing.
        - The start address is the initial address specified by the host.
        - When reading data and the AutoIncrement bit is zero then the data will be read from the same initial address if the number of words to be read is greater than one.
        - When more than one word is to be written with the AutoIncrement bit set to zero then the data at the specified address will be overwritten until the last data word send by the host is written.
    - The host commands also include the number of bytes to be read or written to the FPGA memory - TNBR or TNBW respectively.

Copyright (c) 2022 ACT. All rights reserved.

***********************************************************************************************
*** See the Execution/Diagnostics section (end of file) to see example usage of the library ***
***********************************************************************************************
"""
#=== IMPORTS ============================================================================================

# Standard libs
import time
import struct
from enum import IntEnum
import decimal
from decimal import Decimal
from collections import OrderedDict
from typing import Optional, Union, Tuple, Any, List, OrderedDict as OrderedDictType

# Serial
# `pip install pyserial`
import serial
import serial.tools.list_ports

# Logging
import logging

# nanoMCA structures
import pyNanoMCA_Registers as Registers

# Histogram support
histogramSupport = False
try:
    #import asciiHistogram_lib as histogram
    import printHistogram_lib as histogram
    histogramSupport = True
except ImportError:
    histogram = None
    pass

#========================================================================================================
#=== CONFIGURATION (User Configurable) ==================================================================

# Logging / Output
outputPrefix                    = "nanoMCA Lib:"
outputPrefixPadding             = 15
outputDebug                     = False
outputTrace                     = False

# Diagnostics (when executing this file directly)
diagnostics_DeviceIndex         = 0
diagnostics_AcquireSpectrum     = False
diagnostics_LiveTime_sec        = 5
diagnostics_Histogram_enabled   = True
diagnostics_Histogram_bins      = 48
diagnostics_Histogram_height    = 10
diagnostics_Write_CSVs          = False


#========================================================================================================
#=== GLOBALS ============================================================================================

# Version information
versionLib      = "1.0.0"

# Decimals
decimal.getcontext().rounding = decimal.ROUND_HALF_UP
decimal.getcontext().prec = 6

# Logging
if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        #format='%(asctime)s [%(levelname)s]:  %(message)s',
        format='[%(levelname)s]:  %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    _logger = logging.getLogger('nanoMCA_lib')
else:
    _logger = logging.getLogger('Main.nanoMCA')


#========================================================================================================
#=== ENUMERATIONS =======================================================================================

class Enums:

    class CountingTimePreset(IntEnum):
        Continuous = 0
        LiveTime = 1
        RealTime = 2

    class Polarity(IntEnum):
        Negative = -1
        Unknown = 0
        Positive = 1

    class InputPolarityMode(IntEnum):
        Negative = -1
        Automatic = 0
        Positive = 1


#========================================================================================================
#=== LISTS ==============================================================================================

class Lists:

    CoarseGainOptions: OrderedDictType[float, Tuple[int, int, int, int, int]] = OrderedDict(
        {
            # Gain: MUL0, MUL1, MUL2, MUL3, MUL4
            # Gain: 1.41, 2.00, 1.19, 4.00, 16.0
            0.00:   (0, 0, 0, 0, 0),
            1.19:   (0, 0, 1, 0, 0),
            1.41:   (1, 0, 0, 0, 0),
            2.00:   (0, 1, 0, 0, 0),
            2.60:   (1, 0, 1, 0, 0),
            3.19:   (0, 1, 1, 0, 0),
            3.41:   (1, 1, 0, 0, 0),
            4.00:   (0, 0, 0, 1, 0),
            4.60:   (1, 1, 1, 0, 0),
            5.19:   (0, 0, 1, 1, 0),
            5.41:   (1, 0, 0, 1, 0),
            6.00:   (0, 1, 0, 1, 0),
            6.60:   (1, 0, 1, 1, 0),
            7.19:   (0, 1, 1, 1, 0),
            7.41:   (1, 1, 0, 1, 0),
            8.60:   (1, 1, 1, 1, 0),
            16.00:  (0, 0, 0, 0, 1),
            17.19:  (0, 0, 1, 0, 1),
            17.41:  (1, 0, 0, 0, 1),
            18.00:  (0, 1, 0, 0, 1),
            18.60:  (1, 0, 1, 0, 1),
            19.19:  (0, 1, 1, 0, 1),
            19.41:  (1, 1, 0, 0, 1),
            20.00:  (0, 0, 0, 1, 1),
            20.60:  (1, 1, 1, 0, 1),
            21.19:  (0, 0, 1, 1, 1),
            21.41:  (1, 0, 0, 1, 1),
            22.00:  (0, 1, 0, 1, 1),
            22.60:  (1, 0, 1, 1, 1),
            23.19:  (0, 1, 1, 1, 1),
            23.41:  (1, 1, 0, 1, 1),
            24.60:  (1, 1, 1, 1, 1)
        }
    )


#=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
#=-= DEVICE CLASS -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-

class NanoMCA:

    # Vars
    Device: Optional[serial.Serial] = None
    Connected: bool = False
    SerialNumber: int = 0
    DeviceModel: str = ""
    TCLK_us: float = 0
    InputPolarity: Enums.Polarity = Enums.Polarity.Unknown
    NormalizationFactor: int = 0

    # CONNECTION

    def Connect(self, index: int, method: str = 'usb', baudrate: int = 921600) -> bool:
        """
        Connect to a nanoMCA using the provided method.

        :param index: The index of the device to connect to, in order of device listing
        :param method: The method to use to connect. Options: ['usb']
        :param baudrate: The baudrate to use for the connection. Varies by device firmware, specifically v30.19=460800, v30.20=921600, ... Default 921600
        :return: True, if successfully connected.
        """
        ConsolePrintDebug("[Function: Connect(method: '" + method + "', baudrate: " + str(baudrate) + ")]")

        # Disconnect?
        self.Disconnect()

        try:
            # Get list of connected devices
            COMPorts = serial.tools.list_ports.comports()
            connectedDevices = []
            for c in sorted(COMPorts):
                if c.vid is not None and c.vid == 1027:
                    if c.pid is not None and c.pid == 24597:
                        connectedDevices.append(c.device)
            if len(connectedDevices) == 0:
                ConsolePrintError("Failed to connect to nanoMCA! No connected devices identified.")
                return False
            elif len(connectedDevices) > 1:
                ConsolePrint("Identified {} connected nanoMCA devices".format(len(connectedDevices)))

            # Try opening port
            ConsolePrint("Connecting to nanoMCA #{} @ '{}'...".format(index, connectedDevices[index]))
            self.Device = serial.Serial(port=connectedDevices[index], baudrate=baudrate, rtscts=True, timeout=5.0, write_timeout=5.0)
            self.Connected = True

            # Get information
            self.SerialNumber = self.GetParameter_SerialNumber()
            self.DeviceModel = self.GetParameter_DeviceModel()
            self.TCLK_us = self.GetParameter_TCLK_us()
            self.InputPolarity = self.GetInputPolarity()
            self.NormalizationFactor = self.ReadRegister(Registers.RegisterNumber.NORM).Normalization_Factor

            # Success
            ConsolePrint("Connected! (SN#{})".format(self.SerialNumber))
            return True

        except serial.SerialException as ex:
            ConsolePrintError("Failed to connect to nanoMCA! Reason: " + str(ex))
            return False
        except Exception as ex:
            ConsolePrintError("Exception connecting to nanoMCA!", ex)
            return False

    def Disconnect(self):
        """
        Disconnect from the nanoMCA.

        :return: True, if successfully disconnected.
        """
        ConsolePrintDebug("[Function: Disconnect()]")

        # Try to disconnect
        try:
            # Connected?
            if self.Device is not None:
                # Close connection
                self.Device.close()
                ConsolePrint("Disconnected (SN#{})".format(self.SerialNumber))

            # Clear vars
            self.Device = None
            self.Connected = False
            self.DeviceModel = ""
            self.TCLK_us = 0
            self.InputPolarity = Enums.Polarity.Unknown
            self.NormalizationFactor = 0

            # Success
            return True

        except Exception as ex:
            ConsolePrintError("Exception disconnecting nanoMCA!", ex)
            return False

    # READING / WRITING REGISTERS

    def RawRead(self, startAddress: int, numWords_ToRead: int, autoIncrement: bool = True) -> Optional[Tuple[Registers.MicroData, Union[int, List]]]:
        try:
            # Connected?
            if self.Device is None or not self.Device.isOpen() or not self.Connected:
                ConsolePrintError("Failed to read from device! Device not connected.")
                return None

            # Generate packet contents
            numBytes_ReadCommand = 11  # Number of bytes in total packet, including checksum
            bits_UpperUnused = f"{0:09b}"
            bits_AutoIncrement = "1" if autoIncrement else "0"
            bits_IADR = f"{startAddress:022b}"
            bits_Data = bits_UpperUnused + bits_AutoIncrement + bits_IADR

            # Start building request packet (without checksum)
            pktLE_NoChksum = bytearray(struct.pack(
                '<HHLH',                # Format
                100,                    # Command code: Read (100)
                numBytes_ReadCommand,   # Number of bytes in the read command including the check sum byte
                int(bits_Data, 2),      # Data
                numWords_ToRead * 2     # The number of FPGA data bytes to be read (twice the number of FPGA data words to be read). TNBR must be an even number.
            ))

            # Calculate checksum
            # The content of the check sum byte is obtained in two steps:
            #   - First, a byte sum is calculated by adding all bytes in the command/response excluding the check sum byte.
            #     In the byte sum calculation the bytes are treated as unsigned numbers and the overflow is ignored.
            #   - Secondly, all bits of the obtained byte sum are inverted and the result is incremented by 2 ignoring the overflow.
            pktChkSum = sum(pktLE_NoChksum) & 255
            pktChkSum = (~pktChkSum + 2) & 255

            # Finalize request packet
            pktLE = pktLE_NoChksum.copy()
            pktLE.append(pktChkSum)

            # Send request packet
            if outputTrace:
                print("[Read TX LE] " + bytes(pktLE_NoChksum).hex(sep=' ', bytes_per_sep=2) + " // {:02x}".format(pktChkSum))
            self.Device.write(pktLE)

            # Read response
            respLE = self.Device.read(24 + (numWords_ToRead * 2) + 1)
            if respLE is None:
                ConsolePrintError("Failed to read from device! No response.")
                return None
            if outputTrace:
                respLE_Hex = respLE[:-1].hex(sep=' ', bytes_per_sep=2) + " // {:02x}".format(respLE[-1]) + " (Len: {})".format(len(respLE))
                print("[Read RX LE] " + respLE_Hex)

            # Verify checksum
            calcChkSum = sum(respLE[:-1]) & 255
            calcChkSum = (~calcChkSum + 2) & 255
            if respLE[-1] != calcChkSum:
                ConsolePrintError("Failed to read from device! Checksum invalid.")
                return None

            # Unpack data
            respBE = struct.unpack(
                '<HHL8H' + ('H' if (numWords_ToRead == 1) else ("{:.0f}".format(numWords_ToRead / 2) + 'L')) + 'B',
                respLE
            )
            if outputTrace:
                print("[Read RX BE] " + str(respBE[:-1]) + " // {:02x}".format(respBE[-1]))

            # Validate response
            resp_ResponseCode = respBE[0]
            if resp_ResponseCode != 100:
                ConsolePrintError("Failed to read from device! Invalid response code returned.")
                return None
            resp_Length = respBE[1]
            if resp_Length != len(respLE):
                ConsolePrintError("Failed to read from device! Invalid response length.")
                return None
            resp_AddressBits = respBE[2]
            if format(resp_AddressBits, 'b').zfill(32) != bits_Data:
                ConsolePrintError("Failed to read from device! Address bits mismatch.")
                return None

            # Parse data
            resp_MicroData = Registers.MicroData.from_buffer_copy(respLE[8:24])
            if numWords_ToRead <= 2:
                resp_FPGAData = respBE[11]
            else:
                resp_FPGAData = respBE[11:-1]

            # Ok
            return resp_MicroData, resp_FPGAData
        except Exception as ex:
            ConsolePrintError("Exception reading from device!", ex)
            return None

    def RawWriteBytes(self, startAddress: int, dataBytes: bytearray) -> bool:
        try:
            # Connected?
            if self.Device is None or not self.Device.isOpen() or not self.Connected:
                ConsolePrintError("Failed to write to device! Device not connected.")
                return False

            # Generate packet contents
            numBytes_WriteCommand = 9 + len(dataBytes)  # Number of bytes in total packet, including checksum
            bits_UpperUnused = f"{0:08b}"
            bits_WriteBit = "1"
            bits_AutoIncrement = "1"
            bits_IADW = f"{startAddress:022b}"  # FPGA Address of the first data word to be written.
            bits_PacketInfo = bits_UpperUnused + bits_WriteBit + bits_AutoIncrement + bits_IADW

            # Start building request packet (without checksum)
            pktLE_NoChksum = bytearray(struct.pack(
                '<HHL',  # Format
                110,  # Command code: Write (110)
                numBytes_WriteCommand,  # Number of bytes in the write command including the check sum byte
                int(bits_PacketInfo, 2),  # Data
            ))
            pktLE_NoChksum = pktLE_NoChksum + dataBytes

            # Calculate checksum
            # The content of the check sum byte is obtained in two steps:
            #   - First, a byte sum is calculated by adding all bytes in the command/response excluding the check sum byte.
            #     In the byte sum calculation the bytes are treated as unsigned numbers and the overflow is ignored.
            #   - Secondly, all bits of the obtained byte sum are inverted and the result is incremented by 2 ignoring the overflow.
            pktChkSum = sum(pktLE_NoChksum) & 255
            pktChkSum = (~pktChkSum + 2) & 255

            # Finalize request packet
            pktLE = pktLE_NoChksum.copy()
            pktLE.append(pktChkSum)

            # Send request packet
            if outputTrace:
                pktLE_Hex = bytes(pktLE_NoChksum).hex(sep=' ', bytes_per_sep=2) + " // {:02x}".format(pktChkSum)
                print("[Write TX LE] " + pktLE_Hex)
            self.Device.write(pktLE)

            # Read response
            respLE = self.Device.read(9)
            if outputTrace:
                print("[Write RX LE] " + respLE[:-1].hex(sep=' ', bytes_per_sep=2) + " // {:02x}".format(respLE[-1]) + " (Len: {})".format(len(respLE)))

            # Verify checksum
            calcChkSum = sum(respLE[:-1]) & 255
            calcChkSum = (~calcChkSum + 2) & 255
            if respLE[-1] != calcChkSum:
                ConsolePrintError("Failed to write to device! Checksum invalid.")
                return False

            # Unpack data
            respBE = struct.unpack('<HHLB', respLE)
            if outputTrace:
                print("[RX BE] " + str(respBE[:-1]) + " [Chksum: {:02x}]".format(respBE[-1]))

            # Parse and validate response
            resp_ResponseCode = respBE[0]
            if resp_ResponseCode != 110:
                ConsolePrintError("Failed to write to device! Invalid response code returned.")
                return False
            resp_Length = respBE[1]
            if resp_Length != len(respLE):
                ConsolePrintError("Failed to write to device! Invalid response length.")
                return False
            resp_AddressBits = respBE[2]
            if format(resp_AddressBits, 'b').zfill(32) != bits_PacketInfo:
                ConsolePrintError("Failed to write to device! Address bits mismatch.")
                return False

            # Ok
            return True
        except Exception as ex:
            ConsolePrintError("Exception writing to device!", ex)
            return False

    def ReadRegister(self, register: Registers.RegisterNumber) -> Optional[Registers.Structures.CustomStructure]:
        try:
            # Connected?
            if self.Device is None or not self.Device.isOpen() or not self.Connected:
                ConsolePrintError("Failed to read register from device! Device not connected.")
                return None

            # Get structure
            s = getattr(Registers.Structures, register.name, None)

            # Got structure?
            if s is None:
                raise NotImplementedError("The register '" + register.name + "' is not yet implemented.")
            s = s()

            # Read register
            regTuple = self.RawRead(s.Info.Address, s.Info.Span, s.Info.Span > 1)

            # Got data?
            if regTuple is None:
                # (Error already printed by read function)
                return None
            val = regTuple[1]

            # Populate structure
            s = getattr(Registers.Structures, register.name, None)
            s = s.from_buffer_copy(val.to_bytes(2 * s.Info.Span, 'little'))
            return s

        except Exception as ex:
            ConsolePrintError("Exception reading & processing register '{}'!".format(register.name), ex)
            return None

    def WriteRegister(self, newRegister: Registers.Structures.CustomStructure) -> bool:
        # There are 128 registers located at addresses 0x8000 to 0x807F.
        # The address 0x8000 is the base address.
        # Registers are numbered sequentially from 0 to 127.

        try:
            # Connected?
            if self.Device is None or not self.Device.isOpen() or not self.Connected:
                ConsolePrintError("Failed to write register to device! Device not connected.")
                return False

            # Write register
            newRegister: Any = newRegister
            return self.RawWriteBytes(newRegister.Info.Address, bytearray(newRegister))

        except Exception as ex:
            ConsolePrintError("Exception writing register #{}!".format(newRegister.Info.Address), ex)
            return False

    # COMMON PARAMETERS

    def GetMicroData(self) -> Registers.MicroData:
        mData, _ = self.RawRead(Registers.Structures.CTRS.Info.Address, 1)
        return mData

    def GetParameter_SerialNumber(self) -> int:
        return self.GetMicroData().Serial_Number

    def GetParameter_DeviceModel(self) -> str:
        devModel = Registers.TOOL_to_DeviceModel(self.ReadRegister(Registers.RegisterNumber.HINF).TOOL)
        if not devModel.startswith("nanoMCA"):
            raise NotImplementedError("Other devices not yet implemented")
        return devModel

    def GetParameter_TCLK_us(self) -> float:
        return 1.0 / Registers.ADFR_to_ADCF_MHz(self.ReadRegister(Registers.RegisterNumber.HINF).ADFR)

    # INPUT POLARITY

    def GetInputPolarity(self) -> Enums.Polarity:
        """
        Get the signal input polarity.

        :return: The signal input polarity, or Unknown if error occurred.
        """
        try:
            return Enums.Polarity(Registers.IPOL_to_InputPolarity(self.ReadRegister(Registers.RegisterNumber.CAGN).IPOL))

        except Exception as ex:
            ConsolePrintError("Exception getting input polarity!", ex)
            return Enums.Polarity.Unknown

    def SetInputPolarity(self, polarityMode: Enums.InputPolarityMode) -> bool:
        """
        Set the signal input polarity.

        :param polarityMode: The input polarity.
        :return: True, if the parameter was successfully set.
        """
        ConsolePrint("[Function: SetInputPolarity({})]".format(polarityMode)) if outputDebug else None
        try:
            # Read current gain register
            regCAGN = self.ReadRegister(Registers.RegisterNumber.CAGN)

            # Set input polarity mode
            if polarityMode.Automatic:
                regCAGN.AIPL = 1
            elif polarityMode.Positive:
                regCAGN.AIPL = 0
                regCAGN.IPOL = 1
            elif polarityMode.Negative:
                regCAGN.AIPL = 0
                regCAGN.IPOL = 0

            # Update register
            return self.WriteRegister(regCAGN)

        except Exception as ex:
            ConsolePrintError("Exception setting input polarity!", ex)
            return False

    # SHAPING

    def SetSlowShaper_RiseTime(self, riseTime_us: float) -> bool:
        """
        Set the slow shaper's rise time, in us.

        :param riseTime_us: The rise time, in microseconds (resolution 0.0001 us).
        :return: True, if the parameter was successfully set.
        """
        ConsolePrint("[Function: SetSlowShaper_RiseTime({})]".format(riseTime_us)) if outputDebug else None

        try:
            # Read and set register
            reg = self.ReadRegister(Registers.RegisterNumber.SSRT)
            reg.Slow_Shaper_Rise_Time = int(round(riseTime_us / self.TCLK_us, 0))
            if not self.WriteRegister(reg):
                ConsolePrintError("Failed to set slow shaper rise time! SSRT setting failed.")
                return False

            # Ok
            return True
        except Exception as ex:
            ConsolePrintError("Exception setting slow shaper rise time!", ex)
            return False

    def SetSlowShaper_FlatTop(self, flatTop_us: float) -> bool:
        """
        Set the slow shaper's rise time, in us.

        :param flatTop_us: The flat top, in microseconds (resolution 0.0001 us).
        :return: True, if the parameter was successfully set.
        """
        ConsolePrint("[Function: SetSlowShaper_FlatTop({})]".format(flatTop_us)) if outputDebug else None

        try:
            # Read and set register
            reg = self.ReadRegister(Registers.RegisterNumber.SSFT)
            reg.Slow_Shaper_Flat_Top = int(round(flatTop_us / self.TCLK_us, 0))
            if not self.WriteRegister(reg):
                ConsolePrintError("Failed to set slow shaper flat top! SSFT setting failed.")
                return False

            # Ok
            return True
        except Exception as ex:
            ConsolePrintError("Exception setting slow shaper flat top!", ex)
            return False

    def SetSlowShaper_BLR(self, blrResponse_us: float) -> bool:
        """
        Set the slow shaper's baseline restore time constant.

        :param blrResponse_us: The baseline restore response, in microseconds.
        :return: True, if the parameter was successfully set.
        """
        ConsolePrint("[Function: SetSlowShaper_BLR({})]".format(blrResponse_us)) if outputDebug else None

        try:
            # Calculate constant
            calcSBLR = int(round(blrResponse_us / (256.0 * self.TCLK_us), 0))

            # Read and set register
            reg = self.ReadRegister(Registers.RegisterNumber.SBLR)
            reg.SBLR = calcSBLR
            if not self.WriteRegister(reg):
                ConsolePrintError("Failed to set slow shaper BLR! SBLR setting failed.")
                return False

            # Ok
            return True
        except Exception as ex:
            ConsolePrintError("Exception setting slow shaper BLR!", ex)
            return False

    def SetFastShaper_RiseTime(self, riseTime_us: float) -> bool:
        """
        Set the fast shaper's rise time, in us.

        :param riseTime_us: The rise time, in microseconds (resolution 0.0001 us).
        :return: True, if the parameter was successfully set.
        """
        ConsolePrint("[Function: SetFastShaper_RiseTime({})]".format(riseTime_us)) if outputDebug else None

        try:
            # Read and set register
            reg = self.ReadRegister(Registers.RegisterNumber.FSRT)
            reg.Fast_Shaper_Rise_Time = int(round(riseTime_us / self.TCLK_us, 0))
            if not self.WriteRegister(reg):
                ConsolePrintError("Failed to set fast shaper rise time! FSRT setting failed.")
                return False

            # Ok
            return True
        except Exception as ex:
            ConsolePrintError("Exception setting fast shaper rise time!", ex)
            return False

    def SetFastShaper_FlatTop(self, flatTop_us: float) -> bool:
        """
        Set the fast shaper's rise time, in us.

        :param flatTop_us: The flat top, in microseconds (resolution 0.0001 us).
        :return: True, if the parameter was successfully set.
        """
        ConsolePrint("[Function: SetFastShaper_FlatTop({})]".format(flatTop_us)) if outputDebug else None

        try:
            # Read and set register
            reg = self.ReadRegister(Registers.RegisterNumber.FSFT)
            reg.Fast_Shaper_Flat_Top = int(round(flatTop_us / self.TCLK_us, 0))
            if not self.WriteRegister(reg):
                ConsolePrintError("Failed to set fast shaper flat top! FSFT setting failed.")
                return False

            # Ok
            return True
        except Exception as ex:
            ConsolePrintError("Exception setting fast shaper flat top!", ex)
            return False

    def SetFastShaper_BLR(self, blrResponse_us: float) -> bool:
        """
        Set the fast shaper's baseline restore time constant.

        :param blrResponse_us: The baseline restore response, in microseconds.
        :return: True, if the parameter was successfully set.
        """
        ConsolePrint("[Function: SetFastShaper_BLR({})]".format(blrResponse_us)) if outputDebug else None

        try:
            # Calculate constant
            calcFBLR = int(round(blrResponse_us / (256.0 * self.TCLK_us), 0))

            # Read and set register
            reg = self.ReadRegister(Registers.RegisterNumber.FBLR)
            reg.FBLR = calcFBLR
            if not self.WriteRegister(reg):
                ConsolePrintError("Failed to set fast shaper BLR! FBLR setting failed.")
                return False

            # Ok
            return True
        except Exception as ex:
            ConsolePrintError("Exception setting fast shaper BLR!", ex)
            return False

    def SetUnfoldingTimeB_Short_ns(self, unfoldingTime_ns: float) -> bool:
        """
        Set the short unfolding time for input B, in nanoseconds.

        :param unfoldingTime_ns: The unfolding time, in **nanoseconds** (unlike the long time constant).
        :return: True, if the parameter was successfully set.
        """
        ConsolePrint("[Function: SetUnfoldingTimeB_Short_ns({})]".format(unfoldingTime_ns)) if outputDebug else None

        try:
            # Calculate constant
            calcSTCB = int(round(((unfoldingTime_ns / 1000.0) * 8.0) / self.TCLK_us, 0))

            # Read and set register
            reg = self.ReadRegister(Registers.RegisterNumber.STCB)
            reg.Short_Time_Constant_B = calcSTCB
            if not self.WriteRegister(reg):
                ConsolePrintError("Failed to set short unfolding time B! STCB setting failed.")
                return False

            # Ok
            return True
        except Exception as ex:
            ConsolePrintError("Exception setting short unfolding time B!", ex)
            return False

    def SetUnfoldingTimeB_Long_us(self, unfoldingTime_us: float) -> bool:
        """
        Set the long unfolding time for input B, in microseconds.

        :param unfoldingTime_us: The unfolding time, in microseconds.
        :return: True, if the parameter was successfully set.
        """
        ConsolePrint("[Function: SetUnfoldingTimeB_Long_us({})]".format(unfoldingTime_us)) if outputDebug else None

        try:
            # Calculate constant
            calcLTCB = int(round((unfoldingTime_us * 8.0) / self.TCLK_us, 0))

            # Read and set register
            reg = self.ReadRegister(Registers.RegisterNumber.LTCB)
            reg.Long_Time_Constant_B = calcLTCB
            if not self.WriteRegister(reg):
                ConsolePrintError("Failed to set long unfolding time B! LTCB setting failed.")
                return False

            # Ok
            return True
        except Exception as ex:
            ConsolePrintError("Exception setting long unfolding time B!", ex)
            return False

    # DIGITAL PULSER

    def SetDigitalPulser(self, pulserEnabled: bool) -> bool:
        """
        Enable or disable the digital pulser.

        :param pulserEnabled: True to enable the digital pulser.
        :return: True, if the parameter was successfully set.
        """
        ConsolePrint("[Function: SetDigitalPulser({})]".format(pulserEnabled)) if outputDebug else None
        try:
            # Read current gain register
            regCAGN = self.ReadRegister(Registers.RegisterNumber.CAGN)

            # Enable/disable the digital pulser
            # NOTE: 0 to enable, 1 to disable
            regCAGN.PLSR = 0 if pulserEnabled else 1

            # Update register
            return self.WriteRegister(regCAGN)

        except Exception as ex:
            ConsolePrintError("Exception enabling/disabling digital pulser!", ex)
            return False

    # PRESETS

    def GetPreset_Time(self) -> Optional[float]:
        """
        Get the preset time.

        :return: The preset time, else None if error
        """
        ConsolePrint("[Function: GetPreset_Time()]") if outputDebug else None

        try:
            # Get preset time
            return self.ReadRegister(Registers.RegisterNumber.PRTM).Preset_Time / 100.0
        except Exception as ex:
            ConsolePrintError("Exception getting preset time!", ex)
            return False

    def SetPreset_Time(self, presetMode: Enums.CountingTimePreset, presetTime_sec: float = 0) -> bool:
        """
        Set a preset time.

        :param presetMode: The preset counting time mode to use for the acquisition.
        :param presetTime_sec: The preset time, in seconds (resolution 0.01 sec). Set to zero for continuous acquisition.
        :return: True, if the preset time was successfully set
        """
        ConsolePrint("[Function: SetPresetTime({}, {})]".format(presetMode.name, presetTime_sec)) if outputDebug else None

        try:
            # Read CTRS
            regCTRS = self.ReadRegister(Registers.RegisterNumber.CTRS)

            # Modify preset type
            regCTRS.LRTM = 1 if presetMode == Enums.CountingTimePreset.LiveTime else 0

            # Set preset type
            if not self.WriteRegister(regCTRS):
                ConsolePrintError("Failed to set preset time! CTRS setting failed.")
                return False

            # Set preset time
            regPRTM = Registers.Structures.PRTM()
            regPRTM.Preset_Time = int(round(presetTime_sec * 100.0, 0)) if presetMode != Enums.CountingTimePreset.Continuous else 0
            if not self.WriteRegister(regPRTM):
                ConsolePrintError("Failed to set preset time! PRTM setting failed.")
                return False

            # Ok
            return True
        except Exception as ex:
            ConsolePrintError("Exception setting preset time!", ex)
            return False

    # GAINS

    def GetGain_Coarse(self) -> Optional[Decimal]:
        try:
            # CoarseGain = 1.41 * MUL0 + 2.00 * MUL1 + 1.19 * MUL2 + 4.00 * MUL3 + 16.00 * MUL4
            coarseReg = self.ReadRegister(Registers.RegisterNumber.CAGN)
            return round(Decimal(1.41 * coarseReg.MUL0 + 2.00 * coarseReg.MUL1 + 1.19 * coarseReg.MUL2 + 4.00 * coarseReg.MUL3 + 16.00 * coarseReg.MUL4), 2)

        except Exception as ex:
            ConsolePrintError("Exception getting coarse gain!", ex)
            return None

    def GetGain_Fine(self) -> Optional[Decimal]:
        try:
            # Fine Gain = 1.2 - FAGN/327675
            fineReg = self.ReadRegister(Registers.RegisterNumber.FAGN)
            return round(Decimal(1.2 - (fineReg.Fine_Analog_Gain / 327675.0)), 5)

        except Exception as ex:
            ConsolePrintError("Exception getting fine gain!", ex)
            return None

    def SetGain_Coarse(self, newGain: float) -> bool:
        """
        Set new coarse gain.

        :param newGain: New gain (adjusted to match within range of x0.0-24.6, see `Lists.CoarseGainOptions`)
        :return: True, if successfully set.
        """
        ConsolePrint("[Function: SetGain_Coarse({})]".format(newGain)) if outputDebug else None
        try:
            # CoarseGain = 1.41 * MUL0 + 2.00 * MUL1 + 1.19 * MUL2 + 4.00 * MUL3 + 16.00 * MUL4

            # Get closest gain match
            actualGain = 0
            actualGainSwitches = (0, 0, 0, 0, 0)
            if 0 <= newGain <= list(Lists.CoarseGainOptions.keys())[-1]:
                for k in Lists.CoarseGainOptions.keys():
                    if (k - 0.001 <= newGain) and (k + 0.001 >= newGain):
                        actualGain = k
                        actualGainSwitches = Lists.CoarseGainOptions[k]
            elif newGain < 0:
                actualGain = 0
                actualGainSwitches = (0, 0, 0, 0, 0)
            else:
                actualGain = list(Lists.CoarseGainOptions.keys())[-1]
                actualGainSwitches = (1, 1, 1, 1, 1)

            # Write to log
            ConsolePrint("Setting coarse gain to x{:.2f}".format(actualGain))

            # Read current gain register
            regCAGN = self.ReadRegister(Registers.RegisterNumber.CAGN)

            # Set new switches
            regCAGN.MUL0 = actualGainSwitches[0]
            regCAGN.MUL1 = actualGainSwitches[1]
            regCAGN.MUL2 = actualGainSwitches[2]
            regCAGN.MUL3 = actualGainSwitches[3]
            regCAGN.MUL4 = actualGainSwitches[4]

            # Update register
            return self.WriteRegister(regCAGN)

        except Exception as ex:
            ConsolePrintError("Exception setting coarse gain!", ex)
            return False

    def SetGain_Fine(self, newGain: float) -> bool:
        """
        Set new fine gain.

        :param newGain: New gain (limit x1.0-1.2)
        :return: True, if successfully set.
        """
        ConsolePrint("[Function: SetGain_Fine({})]".format(newGain)) if outputDebug else None
        try:
            # Fine Gain = 1.2 - FAGN/327675

            # Bound the gain to x1-1.2
            actualGain = min(max(1.0, newGain), 1.2)

            # Write to log
            ConsolePrint("Setting fine gain to x{:.5f}".format(actualGain))

            # Read current gain register
            regFAGN = self.ReadRegister(Registers.RegisterNumber.FAGN)

            # Set new gain
            regFAGN.Fine_Analog_Gain = int(round((1.2 - actualGain) * 327675.0, 0))

            # Update register
            return self.WriteRegister(regFAGN)

        except Exception as ex:
            ConsolePrintError("Exception setting fine gain!", ex)
            return False

    # CONTROL

    def Acquisition_Start(self) -> bool:
        """
        Start acquiring.

        :return: True, if the acquisition was successfully started
        """
        ConsolePrint("[Function: Acquisition_Start()]") if outputDebug else None

        try:
            # Read CTRS
            regCTRS = self.ReadRegister(Registers.RegisterNumber.CTRS)

            # Set acquire flag
            regCTRS.ACQE = 1

            # Enable timers
            regCTRS.TMRE = 1

            # Update register
            if not self.WriteRegister(regCTRS):
                ConsolePrintError("Failed to start acquisition! CTRS setting failed.")
                return False

            # Ok
            return True
        except Exception as ex:
            ConsolePrintError("Exception starting acquisition!", ex)
            return False

    def Acquisition_Stop(self) -> bool:
        """
        Stop acquiring.

        :return: True, if the acquisition was successfully stopped
        """
        ConsolePrint("[Function: Acquisition_Stop()]") if outputDebug else None

        try:
            # Read CTRS
            regCTRS = self.ReadRegister(Registers.RegisterNumber.CTRS)

            # Set acquire flag
            regCTRS.ACQE = 0

            # Stop timers
            regCTRS.TMRE = 0

            # Update register
            if not self.WriteRegister(regCTRS):
                ConsolePrintError("Failed to stop acquisition! CTRS setting failed.")
                return False

            # Ok
            return True
        except Exception as ex:
            ConsolePrintError("Exception stopping acquisition!", ex)
            return False

    def Acquisition_Clear(self) -> bool:
        """
        Clear acquisition.

        :return: True, if the acquisition was successfully cleared
        """
        ConsolePrint("[Function: Acquisition_Clear()]") if outputDebug else None

        try:
            # Read CTRS
            regCTRS = self.ReadRegister(Registers.RegisterNumber.CTRS)

            # Set clear flags
            regCTRS.TMRR = 1
            regCTRS.SPCR = 2

            # Update register
            if not self.WriteRegister(regCTRS):
                ConsolePrintError("Failed to clear acquisition! CTRS setting failed.")
                return False

            # Ok
            return True
        except Exception as ex:
            ConsolePrintError("Exception clearing acquisition!", ex)
            return False

    # STATUS

    def IsAcquiring(self) -> bool:
        """
        Checks if the device is currently acquiring data.

        :return: True, if the device is currently acquiring data
        """
        try:
            # Read CTRS
            regCTRS = self.ReadRegister(Registers.RegisterNumber.CTRS)

            # Return status
            return regCTRS.ACQE == 1

        except Exception as ex:
            ConsolePrintError("Exception checking acquisition status!", ex)
            return False

    # MEASUREMENT DATA

    def GetMeasurement_LiveTime(self) -> Optional[float]:
        """
        Gets the current acquisition live time, in seconds.

        :return: The value, else None if error
        """
        try:
            # Elapsed Live Time [s] = 0.01*ELTC + 0.0000002*ELTF
            valELTC = self.ReadRegister(Registers.RegisterNumber.ELTC).Elapsed_Live_Time_Coarse
            valELTF = self.ReadRegister(Registers.RegisterNumber.ELTF).Elapsed_Live_Time_Fine
            return (0.01 * valELTC) + (0.0000002 * valELTF)

        except Exception as ex:
            ConsolePrintError("Exception getting live time!", ex)
            return None

    def GetMeasurement_RealTime(self) -> Optional[float]:
        """
        Gets the current acquisition real time, in seconds.

        :return: The value, else None if error
        """
        try:
            # Elapsed Real Time [s] = 0.01*ERTC + 0.0000002*ERTF
            valERTC = self.ReadRegister(Registers.RegisterNumber.ERTC).Elapsed_Real_Time_Coarse
            valERTF = self.ReadRegister(Registers.RegisterNumber.ERTF).Elapsed_Real_Time_Fine
            return (0.01 * valERTC) + (0.0000002 * valERTF)

        except Exception as ex:
            ConsolePrintError("Exception getting real time!", ex)
            return None

    def GetMeasurement_CountRate_ICR(self) -> Optional[float]:
        """
        Gets the current, true incoming count rate, in CPS.

        :return: The value, else None if error
        """
        try:
            valICRC = self.ReadRegister(Registers.RegisterNumber.ICRC).Peak_Detector_Count
            valICRL = self.ReadRegister(Registers.RegisterNumber.ICRL).ICR_Live_Time
            return valICRC / (valICRL * 2048 * (self.TCLK_us / 1e6))

        except Exception as ex:
            ConsolePrintError("Exception getting ICR!", ex)
            return None

    def GetMeasurement_CountRate_Throughput(self) -> Optional[float]:
        """
        Gets the current throughput counting rate, in CPS.

        :return: The value, else None if error
        """
        try:
            valPDCN = self.ReadRegister(Registers.RegisterNumber.PDCN).Peak_Detector_Count
            valICRR = self.ReadRegister(Registers.RegisterNumber.ICRR).ICR_Real_Time
            return valPDCN / (valICRR * 2048 * (self.TCLK_us / 1e6))

        except Exception as ex:
            ConsolePrintError("Exception getting throughput count rate!", ex)
            return None

    def GetMeasurement_PHA(self) -> Optional[List[int]]:
        """
        Gets the current PHA spectrum.

        :return: The spectrum, else None if error
        """
        try:
            # Read-out full 16384 channel spectrum, in 4096 channel slices (2 words/ch)
            spec = []
            for i in range(4):
                _, chans = self.RawRead(i * 2 * 4096, 2 * 4096)
                spec.extend(chans)
            return spec

        except Exception as ex:
            ConsolePrintError("Exception getting PHA spectrum!", ex)
            return None


# =============================================================================================================
# === Logging =================================================================================================

def ConsolePrint(message):
    global _logger
    _logger.info(message)


def ConsolePrintDebug(message):
    global _logger
    _logger.debug(message)


def ConsolePrintError(message, exception=None):
    global _logger

    if exception is not None:
        _logger.exception(message)
    else:
        _logger.error(message)


#========================================================================================================
#=== EXECUTION / DIAGNOSTICS ============================================================================
#========================================================================================================

# Library file executed directly?
if __name__ == '__main__':

    # Run diagnostic test...
    ConsolePrint("=========================================")
    ConsolePrint("========  n a n o M C A   L i b  ========")
    ConsolePrint("========  D I A G N O S T I C S  ========")
    ConsolePrint("=========================================")

    # Print the version information
    ConsolePrint("Library Version : v " + versionLib)
    ConsolePrint("                 =-=-=                   ")

    # Create new nanoMCA instance
    n = NanoMCA()

    # Attempt to connect to the device
    if n.Connect(index=diagnostics_DeviceIndex):

        # Get micro data
        microData = n.GetMicroData()

        # Print info: General
        ConsolePrint("================ GENERAL INFO ===========")
        ConsolePrint("{0:<22}: {1}".format("Device model", n.DeviceModel))
        ConsolePrint("{0:<22}: {1}".format("Serial number", microData.Serial_Number))
        ConsolePrint("{0:<22}: {1}".format("Firmware version", microData.Firmware_Version))
        ConsolePrint("{0:<22}: {1}".format("FPGA version", n.ReadRegister(Registers.RegisterNumber.FPGV).FPGA_Version_Number / 100))
        ConsolePrint("{0:<22}: {1} °C".format("Temperature", microData.Temperature_C))

        # Print info: Shaping (Slow)
        ConsolePrint("================= SHAPING INFO ==========")
        ConsolePrint("{0:<22}: {1}".format("ADC offset", n.ReadRegister(Registers.RegisterNumber.ADCO).ADC_Offset))
        v = n.ReadRegister(Registers.RegisterNumber.SSRT).Slow_Shaper_Rise_Time
        ConsolePrint("{0:<22}: {1:<11} ({2:.4f} uS)".format("Slow shaper RiseTime", str(v) + " samples", v * n.TCLK_us))
        v = n.ReadRegister(Registers.RegisterNumber.SSFT).Slow_Shaper_Flat_Top
        ConsolePrint("{0:<22}: {1:<11} ({2:.4f} uS)".format("Slow shaper FlatTop", str(v) + " samples", v * n.TCLK_us))
        v = n.ReadRegister(Registers.RegisterNumber.SBLR).SBLR
        ConsolePrint("{0:<22}: {1:<11} ({2:.2f} uS)".format("Slow shaper BLR", v, 256 * v * n.TCLK_us))

        # Print info: Shaping (Fast)
        v = n.ReadRegister(Registers.RegisterNumber.FSRT).Fast_Shaper_Rise_Time
        ConsolePrint("{0:<22}: {1:<11} ({2:.4f} uS)".format("Fast shaper RiseTime", str(v) + " samples", v * n.TCLK_us))
        v = n.ReadRegister(Registers.RegisterNumber.FSFT).Fast_Shaper_Flat_Top
        ConsolePrint("{0:<22}: {1:<11} ({2:.4f} uS)".format("Fast shaper FlatTop", str(v) + " samples", v * n.TCLK_us))
        v = n.ReadRegister(Registers.RegisterNumber.FBLR).FBLR
        ConsolePrint("{0:<22}: {1:<11} ({2:.2f} uS)".format("Fast shaper BLR", v, 256 * v * n.TCLK_us))

        # Print info: Amplifier
        ConsolePrint("================ AMPLIFIER INFO =========")
        coarseGain = n.GetGain_Coarse()
        fineGain = n.GetGain_Fine()
        ConsolePrint("{0:<22}: {1}".format("Input polarity", n.InputPolarity.name))
        ConsolePrint("{0:<22}: x {1:.2f}".format("Coarse gain", coarseGain))
        ConsolePrint("{0:<22}: x {1:.5f}".format("Fine gain", fineGain))
        ConsolePrint("{0:<22}: x {1:.5f}".format("Total gain", (coarseGain * fineGain) if coarseGain != 0 else fineGain))

        ConsolePrint("=========================================")

        # Acquisition test?
        if diagnostics_AcquireSpectrum:

            # Set preset time
            ConsolePrint("Acquire for " + str(diagnostics_LiveTime_sec) + " seconds (Preset live time)...")
            success = n.SetPreset_Time(presetMode=Enums.CountingTimePreset.LiveTime, presetTime_sec=diagnostics_LiveTime_sec)

            # Clear acquisition
            success = n.Acquisition_Clear() if success else None

            # Start acquisition
            success = n.Acquisition_Start() if success else None

            # Wait for acquisition to complete
            waitTime_sec = 0
            while n.IsAcquiring():
                time.sleep(1)
                waitTime_sec += 1
                ConsolePrint("... Elapsed time: " + str(waitTime_sec) + " sec")
            ConsolePrint("Acquisition complete!")

            ConsolePrint("                 =-=-=                   ")

            # Get data
            icr = n.GetMeasurement_CountRate_ICR()
            throughput = n.GetMeasurement_CountRate_Throughput()
            liveTime = n.GetMeasurement_LiveTime()
            realTime = n.GetMeasurement_RealTime()
            spectrum = n.GetMeasurement_PHA()

            # Print acquisition info
            ConsolePrint("{0:<22}: {1:.3f} s".format("Actual live time", liveTime))
            ConsolePrint("{0:<22}: {1:.3f} s".format("Actual real time", realTime))
            ConsolePrint("{0:<22}: {1:.3f} cps".format("True ICR", icr))
            ConsolePrint("{0:<22}: {1:.3f} cps".format("Throughput", throughput))
            ConsolePrint("{0:<22}: {1:.3f} %".format("Dead-time", ((1.0 - (throughput/icr)) * 100.0) if icr != 0 else 0))

            ConsolePrint("=========================================")

            # Histogram?
            if histogramSupport and diagnostics_Histogram_enabled:
                ConsolePrint("Acquired spectrum:")
                # Print histogram
                histogram.Print_Histogram(spectrum, bincount=diagnostics_Histogram_bins, height=diagnostics_Histogram_height, markerChar='*')

        # Done
        ConsolePrint("=========================================")
        ConsolePrint("Diagnostics COMPLETE!")
        n.Disconnect()

    else:

        ConsolePrint("Unable to connect to nanoMCA! Check connection and settings.")

    # End of diagnostics
    ConsolePrint("Exiting...")
