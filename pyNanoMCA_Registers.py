# -*- coding: utf-8 -*-
"""
File:           pyNanoMCA_Structures.py
Description:    Structure definitions for the nanoMCA registers.
Creator:        Joshua A. Handley (2022)

Copyright (c) 2022 ACT. All rights reserved.
"""
#=== IMPORTS ===========================================================================================

# Standard libs
from enum import IntEnum
from typing import List, Dict, Tuple, Union
from ctypes import LittleEndianStructure, c_int16, c_uint16, c_uint32, c_int32


#=======================================================================================================
#=== CONVERSIONS =======================================================================================

def TOOL_to_DeviceModel(tool: int) -> str:
    if tool == 0:
        return "nanoXRS"
    elif tool == 1:
        return "nanoMCA"
    elif tool == 2:
        return "nanoDPP"
    else:
        raise NotImplementedError("TOOL value not yet implemented")


def ADCR_to_ADCResolution_bits(adcr: int) -> int:
    if adcr == 0:
        return 16
    elif adcr == 1:
        return 15
    elif adcr == 2:
        return 14
    elif adcr == 3:
        return 12
    else:
        raise NotImplementedError("ADCR value not yet implemented")


def ADFR_to_ADCF_MHz(adfr: int) -> float:
    if adfr == 0:
        return 80.0
    elif adfr == 1:
        return 100.0
    else:
        raise NotImplementedError("ADFR value not yet implemented")


def IPOL_to_InputPolarity(ipol: int) -> int:
    if ipol == 0:
        return -1
    elif ipol == 1:
        return 1
    else:
        raise NotImplementedError("IPOL value not yet implemented")


#=======================================================================================================
#=== MICRO DATA ========================================================================================

class MicroData(LittleEndianStructure):
    """
    The MICRO Data is a set of eight words that are transmitted as part of the labZY Device response to the host READ COMMAND.
    WORD[4] (BYTE [8,9]) through WORD[11] (BYTE [22,23]) in the response represent the MICRO Data.
    The Micro Data is read only data and represent constant or volatile values.
    The volatile values may change between consecutive readings.
    """

    _fields_ = [
        ("Firmware_Version", c_uint16, 16),
        ("Serial_Number", c_uint16, 16),
        ("Reserved1", c_uint16, 16),
        ("Reserved2", c_uint16, 16),
        ("Input_D_SlowADC", c_uint16, 16),
        ("Reserved3", c_uint16, 16),
        ("Temperature_C", c_int16, 16),
        ("Reserved4", c_uint16, 16)
    ]


#=======================================================================================================
#=== REGISTERS =========================================================================================

class RegisterNumber(IntEnum):
    TRVD = 0,
    ADCO = 1,
    SSRT = 2,
    SSFT = 3,
    FSRT = 4,
    FSFT = 5,
    STCB = 8,
    LTCB = 9,
    STCA = 10,
    LTCA = 11,
    AMPO = 12,
    FDGD = 13,
    INHW = 14,
    HINF = 15,
    CTRS = 16,
    FAGN = 17,
    CAGN = 18,
    PZRO = 19,
    NORM = 20,
    DATE = 22,
    TIME = 23,
    TVFD = 24,
    TVTD = 25,
    TVCT = 26,
    TVRL = 27,
    TVRR = 28,
    SBLR = 30,
    FBLR = 31,
    SPKT = 32,
    PINH = 33,
    STHR = 34,
    FTHR = 36,
    SBGT = 38,
    SEXT = 39,
    FEXT = 40,
    DTEX = 41,
    PRTM = 42,
    PDCN = 44,
    ICRC = 45,
    ICRR = 46,
    ICRL = 47,
    SPNE = 48,
    SNNE = 50,
    FPNE = 52,
    FNNE = 54,
    ERTC = 56,
    ELTC = 58,
    ERTF = 60,
    ELTF = 61,
    ETCA = 62,
    ETCB = 62,
    FPGV = 63,
    LBLH = 64,
    RBLH = 65,
    LBRH = 66,
    RBRH = 67,
    DIND = 68,
    COWW = 69,
    STOD = 70


class RegisterNames:
    
    ByNumber: Dict[RegisterNumber, str] = {
        RegisterNumber.TRVD : "Trace Viewer Data",
        RegisterNumber.ADCO : "ADC Offset",
        RegisterNumber.SSRT : "Slow Shaper Rise Time",
        RegisterNumber.SSFT : "Slow Shaper Flat Top",
        RegisterNumber.FSRT : "Fast Shaper Rise Time",
        RegisterNumber.FSFT : "Fast Shaper Flat Top",
        RegisterNumber.STCB : "Short Time Constant B",
        RegisterNumber.LTCB : "Long Time Constant B",
        RegisterNumber.STCA : "Short Time Constant A",
        RegisterNumber.LTCA : "Long Time Constant A",
        RegisterNumber.AMPO : "Amplifier Offset",
        RegisterNumber.FDGD : "Fast Discriminator Guard",
        RegisterNumber.INHW : "Input C Inhibit Width",
        RegisterNumber.HINF : "Hardware Info",
        RegisterNumber.CTRS : "Control and Status",
        RegisterNumber.FAGN : "Fine Analog Gain",
        RegisterNumber.CAGN : "Coarse Analog Gain",
        RegisterNumber.PZRO : "Pole-Zero",
        RegisterNumber.NORM : "Normalization Factor",
        RegisterNumber.DATE : "Scratch Pad",
        RegisterNumber.TIME : "Scratch Pad",
        RegisterNumber.TVFD : "Trace Viewer Sampling Frequency Divider",
        RegisterNumber.TVTD : "Trace Viewer Pre-Trigger Delay",
        RegisterNumber.TVCT : "Trace Viewer Control",
        RegisterNumber.TVRL : "Trace Viewer ROI Left",
        RegisterNumber.TVRR : "Trace Viewer ROI Right",
        RegisterNumber.SBLR : "Slow Shaper Base-Line Restorer Time Constant",
        RegisterNumber.FBLR : "Fast Shaper Base-Line Restorer Time Constant",
        RegisterNumber.SPKT : "Slow Shaper Peaking Time",
        RegisterNumber.PINH : "Slow Shaper Peak Inhibit Time",
        RegisterNumber.STHR : "Slow Shaper Noise Threshold",
        RegisterNumber.FTHR : "Fast Shaper Noise Threshold",
        RegisterNumber.SBGT : "Slow Base-Line Restorer Gate",
        RegisterNumber.SEXT : "Slow Discriminator Extension",
        RegisterNumber.FEXT : "Fast Discriminator Extension",
        RegisterNumber.DTEX : "Dead Time Extension",
        RegisterNumber.PRTM : "Preset Time",
        RegisterNumber.PDCN : "Peak Detector Count",
        RegisterNumber.ICRC : "Incoming Count",
        RegisterNumber.ICRR : "ICR Real Time",
        RegisterNumber.ICRL : "ICR Live Time",
        RegisterNumber.SPNE : "Slow Shaper Positive Noise Estimation",
        RegisterNumber.SNNE : "Slow Shaper Negative Noise Estimation",
        RegisterNumber.FPNE : "Fast Shaper Positive Noise Estimation",
        RegisterNumber.FNNE : "Fast Shaper Negative Noise Estimation",
        RegisterNumber.ERTC : "Elapsed Real Time Coarse",
        RegisterNumber.ELTC : "Elapsed Live Time Coarse",
        RegisterNumber.ERTF : "Elapsed Real Time Fine",
        RegisterNumber.ELTF : "Elapsed Live Time Fine",
        RegisterNumber.ETCA : "Expected Primary Exponential Time Constant A",
        RegisterNumber.ETCB : "Expected Primary Exponential Time Constant B",
        RegisterNumber.FPGV : "FPGA Design Version Number",
        RegisterNumber.LBLH : "Left Boundary of the Stabilizer Peak Left-Hand Side ROI",
        RegisterNumber.RBLH : "Right Boundary of the Stabilizer Peak Left-Hand Side ROI",
        RegisterNumber.LBRH : "Left Boundary of the Stabilizer Peak Right-Hand Side ROI",
        RegisterNumber.RBRH : "Right Boundary of the Stabilizer Peak Right-Hand Side ROI",
        RegisterNumber.DIND : "Delay of the Logic Signal at Input D",
        RegisterNumber.COWW : "Coincidence/Anti-Coincidence Window Width",
        RegisterNumber.STOD : "Pulse-Height Storage Delay"
}


#=======================================================================================================
#=== STRUCTURES ========================================================================================
# NOTE: Fields are defined as LSB-first

class Structures:

    class CustomStructure(LittleEndianStructure):
        class Info:
            Address: int = 0x8000 + 0
            Span: int = 1
        Info = Info()

        def Fields(self) -> List[Tuple[str, Union[c_uint16, c_uint32, c_int32], int]]:
            return self._fields_

    # Register #0
    class TRVD(CustomStructure):
        """
        This register is the output of a FIFO register.
        When this register is read, the address auto-increment bit in the command address field must be set to 0.
        The FIFO dept is 512 words (1024 bytes).
        The even number of words are the signal data (signed), sequentially from left to right (time progression).
        The odd number of words contain the digital traces data in the lower byte.
        The upper byte of the odd words should be ignored.
        Referring to the trace viewer of the labZY-MCA software, Bit 0 of the odd words is the upper (FLLD) trace, bit 7 is the lowest (ROI) trace.
        Each pair of adjacent even-odd words represent the data at the same clock sample.
        """
        def __init__(self):
            self.Info.Address = 0x8000 + 0
            self.Info.Span = 1
            super().__init__()
        _fields_ = [
            ("FIFO", c_uint16, 16)
        ]

    # Register #1
    class ADCO(CustomStructure):
        """
        ADCO: Bits 15-0; Unsigned; Defines the output offset of the ADC.
        Refer to the documentation of labZY Tools and labZY-MCA software.
        Range: 0 to 32000
        Default: 8000
        Dependency: User defined
        """
        def __init__(self):
            self.Info.Address = 0x8000 + 1
            self.Info.Span = 1
            super().__init__()
        _fields_ = [
            ("ADC_Offset", c_uint16, 16)
        ]

    # Register #2
    class SSRT(CustomStructure):
        """
        SSRT: Bits 10-0; Unsigned; Defines the number of consecutive samples in the rise time of the slow shaper.
        The length of the rise time in the time domain is the product of SSRT and TCLK: SSRT*TCLK
        Range: 1 to 2047
        Default: 240
        Dependency: User defined
        Not Connected: Bits 15-11
        """
        def __init__(self):
            self.Info.Address = 0x8000 + 2
            self.Info.Span = 1
            super().__init__()
        _fields_ = [
            ("Slow_Shaper_Rise_Time", c_uint16, 11),
            ("NC", c_uint16, 5),
        ]

    # Register #3
    class SSFT(CustomStructure):
        """
        SSFT: Bits 7-0; Unsigned; Defines the number of consecutive samples in the flat top of the slow shaper.
        The length of the flat top in the time domain is the product of SSFT and TCLK: SSFT*TCLK
        Range: 1 to 255
        Default: 1
        Dependency: User defined
        Not Connected: Bits 15-8
        """
        def __init__(self):
            self.Info.Address = 0x8000 + 3
            self.Info.Span = 1
            super().__init__()
        _fields_ = [
            ("Slow_Shaper_Flat_Top", c_uint16, 8),
            ("NC", c_uint16, 8),
        ]

    # Register #4
    class FSRT(CustomStructure):
        """
        FSRT: Bits 9-0; Unsigned; Defines the number of consecutive samples in the rise time of the fast shaper.
        The length of the rise time in the time domain is the product of FSRT and TCLK: FSRT*TCLK
        Range: 1 to 1023
        Default: 16
        Dependency: User defined
        Not Connected: Bits 15-10
        """
        def __init__(self):
            self.Info.Address = 0x8000 + 4
            self.Info.Span = 1
            super().__init__()
        _fields_ = [
            ("Fast_Shaper_Rise_Time", c_uint16, 10),
            ("NC", c_uint16, 6),
        ]

    # Register #5
    class FSFT(CustomStructure):
        """
        FSFT: Bits 7-0; Unsigned; Defines the number of consecutive samples in the flat top of the fast shaper.
        The length of the flat top in the time domain is the product of FSFT and TCLK: FSFT*TCLK
        Range: 1 to 255
        Default: 1
        Dependency: User defined
        Not Connected: Bits 15-8
        """
        def __init__(self):
            self.Info.Address = 0x8000 + 5
            self.Info.Span = 1
            super().__init__()
        _fields_ = [
            ("Fast_Shaper_Flat_Top", c_uint16, 8),
            ("NC", c_uint16, 8),
        ]

    # Register #8
    class STCB(CustomStructure):
        """
        STCB: Bits 7-0; Unsigned; Defines the secondary unfolding time-constant of the built-in preamplifier (nanoMCA-SP) or the secondary unfolding time-constant of the exponential pulses directly fed to input B (nanoMCA or nanoDPP).
        The unfolding time constant in the time domain is approximately equal to STCB*TCLK/8
        Range: 1 to 255
        Default: 16
        Dependency: User defined
        Not Connected: Bits 15-8
        """
        def __init__(self):
            self.Info.Address = 0x8000 + 8
            self.Info.Span = 1
            super().__init__()
        _fields_ = [
            ("Short_Time_Constant_B", c_uint16, 8),
            ("NC", c_uint16, 8),
        ]

    # Register #9
    class LTCB(CustomStructure):
        """
        LTCB: Bits 12-0; Unsigned; Defines the primary unfolding time-constant of the built-in preamplifier (nanoMCA-SP) or the primary unfolding time-constant of the exponential pulses directly fed to input B (nanoMCA or nanoDPP).
        The unfolding time constant in the time domain is approximately equal to LTCB*TCLK/8
        Range: 1 to 8191
        Default: 2000
        Dependency: User defined
        Not Connected: Bits 15-13
        """
        def __init__(self):
            self.Info.Address = 0x8000 + 9
            self.Info.Span = 1
            super().__init__()
        _fields_ = [
            ("Long_Time_Constant_B", c_uint16, 13),
            ("NC", c_uint16, 3),
        ]

    # Register #10
    class STCA(CustomStructure):
        """
        STCA: Bits 7-0; Unsigned; Defines the secondary unfolding time-constant of the built-in amplifier at input A (nanoMCA, nanoMCA-SP, nanoXRS) or the secondary unfolding time-constant of the exponential pulses directly fed to input A (nanoDPP).
        The unfolding time constant in the time domain is approximately equal to STCA*TCLK/8
        Range: 1 to 255
        Default: 32
        Dependency: User defined
        Not Connected: Bits 15-8
        """
        def __init__(self):
            self.Info.Address = 0x8000 + 10
            self.Info.Span = 1
            super().__init__()
        _fields_ = [
            ("Short_Time_Constant_A", c_uint16, 8),
            ("NC", c_uint16, 8),
        ]

    # Register #11
    class LTCA(CustomStructure):
        """
        LTCA: Bits 12-0; Unsigned; Defines the primary unfolding time-constant of the built-in amplifier at input A (nanoMCA, nanoMCA-SP, nanoXRS) or the primary unfolding time-constant of the exponential pulses directly fed to input A (nanoDPP).
        The unfolding time constant in the time domain is approximately equal to LTCA*TCLK/8
        Range: 1 to 8191
        Default: 4000
        Dependency: User defined
        Not Connected: Bits 15-13
        """
        def __init__(self):
            self.Info.Address = 0x8000 + 11
            self.Info.Span = 1
            super().__init__()
        _fields_ = [
            ("Long_Time_Constant_A", c_uint16, 13),
            ("NC", c_uint16, 3),
        ]

    # Register #12
    class AMPO(CustomStructure):
        """
        AMPO: Bits 15-0; Unsigned; Defines the offset of the analog signal at the input of the ADC.
        If the amplifier input is set to positive, then the offset at the ADC input changes proportionally to the AMPO value.
        If the amplifier input is set to negative, then the offset at the ADC input changes inversely to AMPO value.
        It is recommended that AMPO is adjusted automatically by setting bit AOFS = 1.
        For given ADC offset ADCO, AMPO can be adjusted manually so that the baseline of the ADC signal is approximately zero - refer to the www.labzy.com video "Adjusting the Amplifier Offset of nanoMCA tools ".
        Range: 0 to 65535
        Default: 32768
        Dependency: Ignored if bit AOFS = 1 (Register 16).
        """
        def __init__(self):
            self.Info.Address = 0x8000 + 12
            self.Info.Span = 1
            super().__init__()
        _fields_ = [
            ("Amplifier_Offset", c_uint16, 16)
        ]

    # Register #13
    class FDGD(CustomStructure):
        """
        FDGD: Bits 7-0; Unsigned; Defines the minimum width of the fast discriminator considered to be pile-up free.
        When the fast discriminator width is longer than the width specified by this register a pile-up condition in the fast channel is indicated causing a pile-up rejection of the corresponding pulse in the slow channel.
        This technique effectively reduces the resolving time of the pile-up rejector.
        However, such pile-up rejection can only be applied when the fast shaper pulses exhibit virtually no tailing.
        To disable the pileup rejection based on the fast discriminator width, set FDGD = 255 (0xFF).
        The width of the Fast Discriminator Guard in the time domain is given by FDGD*TCLK
        Range: 1 to 255
        Default: 255
        Dependency: User defined
        Not Connected: Bits 15-8
        """
        def __init__(self):
            self.Info.Address = 0x8000 + 13
            self.Info.Span = 1
            super().__init__()
        _fields_ = [
            ("Fast_Discriminator_Guard", c_uint16, 8),
            ("NC", c_uint16, 8),
        ]

    # Register #14
    class INHW(CustomStructure):
        """
        INHW: Bits 13-0; Unsigned; Defines the width of the internal inhibit signal triggered by Input C, INHW is in microseconds.
        If INHW is less than the width of the Input C signal, Input C functions as the inhibit signal.
        Range: 0 to 10000
        Default: 10
        Dependency: User defined

        ACPL: Bit 14; When ACPL=1, the active polarity of the inhibit signal is determined automatically, assuming the average inhibit time is shorter than the non-inhibit time.
        When ACPL=0 the active polarity of the inhibit signal is determined by the state of the CPOL bit.
        Default: 1
        Dependency: User defined

        CPOL: Bit 15; When ACPL = 0, this bit is rw and determines the active polarity of the inhibit signal at Input C.
        When CPOL=0, the active polarity of the inhibit signal at Input C is logic LOW.
        When CPOL=1, the active polarity of the inhibit signal is logic HIGH.
        When ACPL=1 this bit is rr and indicates the automatically determined active polarity of the inhibit signal at Input C.
        When reading CPOL=0, the active polarity of the inhibit signal at Input C is determined to be logic LOW.
        When CPOL=1, the active polarity of the inhibit signal is determined to be logic HIGH.
        Default: rr
        Dependency: User defined or ACPL bit.
        """
        def __init__(self):
            self.Info.Address = 0x8000 + 14
            self.Info.Span = 1
            super().__init__()
        _fields_ = [
            ("Input_C_Inhibit_Width", c_uint16, 14),
            ("ACPL", c_uint16, 1),
            ("CPOL", c_uint16, 1),
        ]

    # Register #15
    class HINF(CustomStructure):
        """
        ADCR: Bits 1-0; Unsigned; ADC resolution in bits:
            16 bit ADC - ADCR=0;
            15 bit ADC - ADCR=1;
            14 bit ADC - ADCR=2;
            12 bit ADC - ADCR=3;

        ADFR: Bits 3-2; Unsigned; ADC sampling frequency (ADCF):
            ADCF=80MHz - ADFR=0;
            ADCF=100MHz - ADFR=1;
            Future Use - ADFR=2;
            Future Use - ADFR=3;

        SIZE: Bits 11-8; Unsigned; Reports the number of hard size channels (fixed length of the hardware spectrum).
        The total number of channels is equal to 2^SIZE

        TOOL: Bits 15-22; Unsigned; Reports the labZY tool:
            TOOL=0 - nanoXRS
            TOOL=1 - nanoMCA, nanoMCA-SP
            TOOL=2 - nanoDPP
            TOOL=all others - Future Use
        """
        def __init__(self):
            self.Info.Address = 0x8000 + 15
            self.Info.Span = 1
            super().__init__()

        _fields_ = [
            ("ADCR", c_uint16, 2),
            ("ADFR", c_uint16, 2),
            ("NC", c_uint16, 4),
            ("SIZE", c_uint16, 4),
            ("TOOL", c_uint16, 4),
        ]

    # Register #16
    class CTRS(CustomStructure):
        """
        ACQE: Bit 0; Controls Spectrum Acquisition.
        Write: Spectrum acquisition is enabled by writing ACQE = 1
        Note: Spectrum acquisition will not be enabled if the preset time is reached by the timers.
        Spectrum acquisition is disabled by writing ACQE = 0.
        Read: ACQE = 1 when the spectrum acquisition is in progress, ACQE = 0 when the spectrum acquisition is stopped either manually or by the timers when the preset time is reached.
        Default at Power On: Acquisition Disabled
        Dependency: User defined or timers.

        TMRE: Bit 1; Enables/Disables Timers.
        Write: Time counting is enabled by writing TMRE = 1
        Note: Time counting will not be enabled if the preset time is reached by the timers.
        Time counting is disabled by writing TMRE = 0.
        Read: TMRE = 1 when time counting is in progress, TMRE = 0 when the time counting is stopped, either manually or by the timers when the preset time is reached.
        Default at Power On: Time Counting is Disabled
        Dependency: User defined or timers.

        TMRR: Bit 2; Reset Timers.
        Write: Reset timers to zero count by writing TMRR = 1,
        No effect on timers count when writing TMRR = 0.
        Read: TMRR= 0 always.
        Dependency: User defined.

        LRTM: Bit 3; Determines the type of the preset time.
        Live Time - LRTM = 1
        Real Time - LRTM = 0
        Default: 1
        Dependency: User defined.

        SPCR: Bits 5-4; Reset Spectrum Content.
        Write: Reset channel counts to zero when writing SPCR = 2,
        No effect on channel counts when writing any other values.
        Read: SPCR = 1 always.
        Dependency: User defined.

        AOFS: Bit 8; Amplifier Offset Control.
        Automatic - AOFS = 1
        Manual - AOFS = 0
        Default: 1
        Recommended: 1
        Dependency: User defined.

        PLSR: Bit 9; Digital Pulser Control.
        Disable Digital Pulser - PLSR = 1
        Enable Digital Pulser - PLSR = 0
        Default: 1
        Dependency: User defined.

        DPOL: Bit 13; Input D active logic level control.
        Active logic LOW - DPOL = 0
        Active logic HIGH - DPOL = 1
        Default: 0
        Dependency: User defined.

        DFUN: Bit 14; Input D function.
        Slow ADC analog input - DFUN = 1
        Logic signal input - DFUN = 0
        Default: 1
        Dependency: User defined.

        TRVR: Bit 15; Trace Viewer Status Bit.
        Trace Viewer Data is Not Ready - TRVR=0
        Data is Ready for Download - TRVR=1
        """
        def __init__(self):
            self.Info.Address = 0x8000 + 16
            self.Info.Span = 1
            super().__init__()
        _pack_ = 1
        _fields_ = [
            ("ACQE", c_uint16, 1),
            ("TMRE", c_uint16, 1),
            ("TMRR", c_uint16, 1),
            ("LRTM", c_uint16, 1),
            ("SPCR", c_uint16, 2),
            ("NC_1", c_uint16, 2),
            ("AOFS", c_uint16, 1),
            ("PLSR", c_uint16, 1),
            ("NC_2", c_uint16, 3),
            ("DPOL", c_uint16, 1),
            ("DFUN", c_uint16, 1),
            ("TRVR", c_uint16, 1)
        ]

    # Register #17
    class FAGN(CustomStructure):
        """
        FAGN: Bits 15-0; Unsigned; Defines the fine gain (Fine Gain) of the builtin amplifier.
        Fine Gain = 1.2 - FAGN/327675
        Range: 0 to 65535
        Default: 65535
        Dependency: User defined
        """
        def __init__(self):
            self.Info.Address = 0x8000 + 17
            self.Info.Span = 1
            super().__init__()
        _fields_ = [
            ("Fine_Analog_Gain", c_uint16, 16)
        ]

    # Register #18
    class CAGN(CustomStructure):
        """
        MUL0 to MUL4:
            nanoMCA and nanoMCA-SP:
                Coarse Gain = 1.41MUL0+2.00MUL1+1.19MUL2+4.00MUL3+16.00MUL4
            nanoXRS and nanoDPP:
                Coarse Gain = 1.41MUL0+2.00MUL1
            All tools:
                Total Gain = Coarse Gain* Fine Gain
        Dependency: User defined

        AIPL: Bit 13; When AIPL = 1, the polarity of the active input signal is determined automatically.
        When AIPL = 0, the polarity of the active input signal is determined by the state of the IPOL bit.
        Default: 1
        Dependency: User defined

        ISEL: Bit 14; Analog Input Select.
        Input A is active when ISEL = 0
        Input B is active when ISEL = 1
        Default: 0
        Dependency: User defined.

        IPOL: Bit 15; When AIPL = 0, this bit is rw and determines the signal polarity the active analog input (A or B).
        When IPOL=0, the polarity of the analog signal is negative
        When IPOL=1, the polarity of the analog signal is positive.
        When AIPL=1, this bit is rr and indicates the automatically determined active polarity of the analog signal at active analog input (A or B).
        Default: rr
        Dependency: User defined or AIPL bit (Register 18).
        """
        def __init__(self):
            self.Info.Address = 0x8000 + 18
            self.Info.Span = 1
            super().__init__()
        _fields_ = [
            ("MUL0", c_uint16, 1),
            ("MUL1", c_uint16, 1),
            ("MUL2", c_uint16, 1),
            ("MUL3", c_uint16, 1),
            ("MUL4", c_uint16, 1),
            ("NC", c_uint16, 8),
            ("AIPL", c_uint16, 1),
            ("ISEL", c_uint16, 1),
            ("IPOL", c_uint16, 1)
        ]

    # Register #19
    class PZRO(CustomStructure):
        """
        PZRO: Bits 11-0; Unsigned; Defines the attenuation factor of the pole-zero compensating circuit.
        Larger numbers of PZRO compensate for relatively shorter time constants.
        Smaller numbers of PZRO compensate for longer time constant.
        Set PZRO=0 for signals from reset type preamplifiers.
        Range: 0 to 4095
        Default: 0
        Applicable: Input A of nanoMCA and nanoMCA-SP only.
        Dependency: User defined

        APZO: Bit 15; Control for automatic Pole-Zero adjustment.
        Not implemented at the time of writing this document.
        Applicable: nanoMCA and nanoMCA-SP only.
        Not Connected: Bits 14-12
        """
        def __init__(self):
            self.Info.Address = 0x8000 + 19
            self.Info.Span = 1
            super().__init__()
        _fields_ = [
            ("PZRO", c_uint16, 12),
            ("NC", c_uint16, 3),
            ("APZO", c_uint16, 1)
        ]

    # Register #20
    class NORM(CustomStructure):
        """
        NORM: Bits 13-0; Unsigned; Defines the normalization factor used to scale down the pulse-height measurement so that a predefined range of the ADC digitized signal fits within the hard spectrum size.
        Range: 0 to 214-1
        Dependency: User defined or automatically calculated depending on the rise time of the digitally shaped pulse.
        For triangular pulse shape and default ADC offset:
            NORM = 40960*SSRT/2SIZE
        For hard size spectrum of 16k channels:
            NORM = 2.5*SSRT (Register 2)

        ** In register #21, not used:
        ANRM: Bit 31; This bit has no effect on the hardware.
        It only indicates to the software to automatically calculate NORM as function of SSRT.

        FNRM: Bit 30; This bit has no effect on the hardware.
        It only indicates to the software to fine calculate NORM using time constant dependency.
        """
        def __init__(self):
            self.Info.Address = 0x8000 + 20
            self.Info.Span = 1
            super().__init__()
        _fields_ = [
            ("Normalization_Factor", c_uint16, 14),
            ("NC", c_uint16, 2),
        ]

    # Register #22
    class DATE(CustomStructure):
        """
        DATE: Bits 15-0; This register neither controls nor depends on the hardware.
        It can be used as a non-volatile storage.
        The labZY-MCA software stores the Start Date of the spectrum acquisition.
        Dependency: User defined
        """
        def __init__(self):
            self.Info.Address = 0x8000 + 22
            self.Info.Span = 1
            super().__init__()
        _fields_ = [
            ("Scratch", c_uint16, 16)
        ]

    # Register #23
    class TIME(CustomStructure):
        """
        TIME: Bits 15-0; This register neither controls nor depends on the hardware.
        It can be used as a non-volatile storage.
        The labZY-MCA software stores the Start Time of the spectrum acquisition.
        Dependency: User defined
        """
        def __init__(self):
            self.Info.Address = 0x8000 + 23
            self.Info.Span = 1
            super().__init__()
        _fields_ = [
            ("Scratch", c_uint16, 16)
        ]

    # Register #24
    class TVFD(CustomStructure):
        """
        TVFD: Bits 15-0; Unsigned; Defines the trace viewer sampling frequency divider.
        The trace viewer sampling frequency (TVSF) is:
            TVSF = ADCF / (TVFD + 1)
        Range: 0 to 65535
        Default: 0
        Dependency: User defined
        """
        def __init__(self):
            self.Info.Address = 0x8000 + 24
            self.Info.Span = 1
            super().__init__()
        _fields_ = [
            ("Trace_Viewer_Sampling_Frequency_Divider", c_uint16, 16)
        ]

    # Register #25
    class TVTD(CustomStructure):
        """
        TVTD: Bits 7-0; Unsigned; Defines the number of the samples captured by the trace viewer before the active edge of the trace viewer trigger.
        Range: 0 to 255
        Default: 0
        Dependency: User defined
        Not Connected: Bits 15-8
        """
        def __init__(self):
            self.Info.Address = 0x8000 + 25
            self.Info.Span = 1
            super().__init__()
        _fields_ = [
            ("Trace_Viewer_PreTrigger_Delay", c_uint16, 8),
            ("NC", c_uint16, 8)
        ]

    # Register #26
    class TVCT(CustomStructure):
        """
        TVIS: Bits 1-0; Unsigned; Selects the digital signal fed to the input of the trace viewer.
        SLOW (shaper) - TVIS=0
        FAST (shaper) - TVIS=1
        ADC - TVIS=2
        AUX (Slow Shaper) - TVIS=3
        Range: 0 to 3
        Default: 0

        TVDC: Bit 2; Auxiliary trigger source selector.
        See TVTS description.
        Default: 0

        TVTS: Bits 5-3; Unsigned; Selects the trigger source of the trace viewer.
        FLLD - TVTS=0
        SLLD - TVTS=1
        PKDT - TVTS=2
        STORE - TVTS=3
        PUR - TVTS=4
        INHIBIT - TVTS=5, TVDC=0
        INPUT C - TVTS=6, TVDC=0
        COINC _W - TVTS=5, TVDC=1
        INPUT D - TVTS=6, TVDC=1
        ROI - TVTS=7
        Default: 0

        TVTE: Bit 6; Trigger edge selector.
        LOW to HIGH - TVTE=0
        HIGH to LOW - TVTE=1
        Default: 0

        TVSG: Bits 11-8; Unsigned; Gain control of the trace viewer digital signal when the input is fed by the slow shaper (TVIS=0).
        Trace Viewer Input = (Slow shaper digital signal)/2TVSG
        Range: 0 to 15
        Default: 0

        TVFG: Bits 11-8; Unsigned; Gain control of the trace viewer digital signal when the input is fed by the fast shaper (TVIS=1).
        Trace Viewer Input = (Fast shaper digital signal)/2TVFG
        Range: 0 to 15
        Default: 0
        """
        def __init__(self):
            self.Info.Address = 0x8000 + 26
            self.Info.Span = 1
            super().__init__()
        _fields_ = [
            ("TVIS", c_uint16, 2),
            ("TVDC", c_uint16, 1),
            ("TVTS", c_uint16, 3),
            ("TVTE", c_uint16, 1),
            ("NC", c_uint16, 1),
            ("TVSG", c_uint16, 4),
            ("TVFG", c_uint16, 4),
        ]

    # Register #27
    class TVRL(CustomStructure):
        """
        TVRL: Bits 15-0; Unsigned; The number of the channel corresponding to the left boundary of an ROI of the hard size spectrum.
        Pulses whose amplitudes fall within the ROI will trigger the trace viewer when TVTS=7.
        Range: 0 to 16383
        Default: 0
        Dependency: User defined
        """
        def __init__(self):
            self.Info.Address = 0x8000 + 27
            self.Info.Span = 1
            super().__init__()
        _fields_ = [
            ("Trace_Viewer_ROI_Left", c_uint16, 16)
        ]

    # Register #28
    class TVRR(CustomStructure):
        """
        TVRR: Bits 15-0; Unsigned; The number of the channel corresponding to the right boundary of an ROI of the hard size spectrum.
        Pulses whose amplitudes fall within the ROI will trigger the trace viewer when TVTS=7.
        Range: 0 to 16383
        Default: 0
        Dependency: User defined
        """
        def __init__(self):
            self.Info.Address = 0x8000 + 28
            self.Info.Span = 1
            super().__init__()
        _fields_ = [
            ("Trace_Viewer_ROI_Right", c_uint16, 16)
        ]

    # Register #30
    class SBLR(CustomStructure):
        """
        SBLR: Bits 9-0; Unsigned; Defines the time constant of a gated first-order high-pass filter used as a base-line restorer of the slow shaper.
        The time constant in the time domain is proportional to the product of SBLR and TCLK: Time Constant = 256*SBLR*TCLK
        Range: 1 to 1023
        Default: 500
        Dependency: User defined
        Not Connected: Bits 15-10
        """
        def __init__(self):
            self.Info.Address = 0x8000 + 30
            self.Info.Span = 1
            super().__init__()
        _fields_ = [
            ("SBLR", c_uint16, 10),
            ("NC", c_uint16, 6)
        ]

    # Register #31
    class FBLR(CustomStructure):
        """
        FBLR: Bits 7-0; Unsigned; Defines the time constant of a gated first-order high-pass filter used as a base-line restorer of the fast shaper.
        The time constant in the time domain is proportional to the product of FBLR and TCLK: Time Constant = 256*FBLR*TCLK
        Range: 1 to 255
        Default: 100
        Dependency: User defined
        Not Connected: Bits 15-8
        """
        def __init__(self):
            self.Info.Address = 0x8000 + 31
            self.Info.Span = 1
            super().__init__()
        _fields_ = [
            ("FBLR", c_uint16, 8),
            ("NC", c_uint16, 8)
        ]

    # Register #32
    class SPKT(CustomStructure):
        """
        SPKT: Bits 15-0; Unsigned; The number of consecutive samples from the beginning of the slow pulse shape to the moment of peak detection.
        SPKT is function of the slow shaper parameters.
        SPKT = SSRT+SSFT+SSRT/32
        Range: Depends on the ranges of SSRT and SSFT
        Default: Calculated from the defaults of SSRT and SSFT
        Dependency: SSRT (Register 2) and SSFT (Register 3).
        """
        def __init__(self):
            self.Info.Address = 0x8000 + 32
            self.Info.Span = 1
            super().__init__()
        _fields_ = [
            ("Slow_Shaper_Peaking_Time", c_uint16, 16)
        ]

    # Register #33
    class PINH(CustomStructure):
        """
        PINH: Bits 15-0; Unsigned; The number of consecutive samples from the peak detection until the next allowed peak detection.
        PINH is function of the slow shaper parameters.
        PINH = SSRT- 4, but not less than zero.
        Range: Depends on the range of SSRT
        Default: Calculated from the default of SSRT
        Dependency: SSRT (Register 2)
        """
        def __init__(self):
            self.Info.Address = 0x8000 + 33
            self.Info.Span = 1
            super().__init__()
        _fields_ = [
            ("Slow_Shaper_Peak_Inhibit_Time", c_uint16, 16)
        ]

    # Register #34-35
    class STHR(CustomStructure):
        """
        STHR: Bits 31-0; Signed; The threshold of the slow shaper noise discriminator.
        STHR is set as a function of the desired threshold expressed as a channel number of the hard size spectrum and the normalization factor NORM.
        When set to a negative number, the threshold is set automatically by the hardware.
        STHR = (Threshold Channel Number)*NORM - manual threshold
        STHR = -1 - automatic threshold
        Range: -1 to (2^31) - 1
        Default: -1
        Dependency: User defined and NORM (Register 20, 21)
        """
        def __init__(self):
            self.Info.Address = 0x8000 + 34
            self.Info.Span = 2
            super().__init__()
        _fields_ = [
            ("Slow_Threshold", c_int32, 32)
        ]

    # Register #36-37
    class FTHR(CustomStructure):
        """
        FTHR: Bits 31-0; Signed; The threshold of the fast shaper noise discriminator.
        FTHR is set as a function of the desired threshold expressed as a channel number of the hard size spectrum and FSRT and the SIZE.
        When set to a negative number, the threshold is set automatically by the hardware.
        Manual setting:
            FTHR = (Threshold Channel Number)* 40960*FSRT/2SIZE
            FTHR = -1 - automatic threshold
        Range: -1 to (2^31) - 1
        Default: -1
        Dependency: User defined, FSRT (Register 4) and SIZE (Register 15).
        """
        def __init__(self):
            self.Info.Address = 0x8000 + 36
            self.Info.Span = 2
            super().__init__()
        _fields_ = [
            ("Fast_Threshold", c_uint32, 32)
        ]

    # Register #38
    class SBGT(CustomStructure):
        """
        SBGT: Bits 15-0; Unsigned; Extension of the fast discriminator signal with number of consecutive samples for which the slow base-line restorer is gated off.
        SBGT = 2*SSRT
        Range: Depends on the range of SSRT
        Default: Calculated from the default of SSRT
        Dependency: SSRT (Register 2)
        """
        def __init__(self):
            self.Info.Address = 0x8000 + 38
            self.Info.Span = 1
            super().__init__()
        _fields_ = [
            ("Slow_Baseline_Restorer_Gate", c_uint16, 16)
        ]

    # Register #39
    class SEXT(CustomStructure):
        """
        SEXT: Bits 9-0; Unsigned; Extension of the slow shaper noise discriminator signal with specified number of clock periods.
        The extension length in the time domain is given as:
            Extension = SEXT*TCLK
        Range: 0 to 1023
        Default: SEXT = SSRT/10 + 4
        Recommended: SEXT = SSRT/10 + 4
        Dependency: User defined or SSRT (Register 2).
        Not Connected: Bits 15-10
        """
        def __init__(self):
            self.Info.Address = 0x8000 + 39
            self.Info.Span = 1
            super().__init__()
        _fields_ = [
            ("Slow_Discriminator_Extension", c_uint16, 10),
            ("NC", c_uint16, 6)
        ]

    # Register #40
    class FEXT(CustomStructure):
        """
        FEXT: Bits 7-0; Unsigned; Extension of the fast shaper noise discriminator signal with specified number of clock periods.
        The extension length in the time domain is given as:
            Extension = FEXT*TCLK
        Range: 0 to 255
        Default: FEXT = FSRT/10 + 4
        Recommended: FEXT = FSRT/10 + 4
        Dependency: User defined or FSRT (Register 4).
        Not Connected: Bits 15-8
        """
        def __init__(self):
            self.Info.Address = 0x8000 + 40
            self.Info.Span = 1
            super().__init__()
        _fields_ = [
            ("Fast_Discriminator_Extension", c_uint16, 8),
            ("NC", c_uint16, 8)
        ]

    # Register #41
    class DTEX(CustomStructure):
        """
        DTEX: Bits 12-0; Unsigned; Extension of the fast discriminator signal with specified number of clock periods.
        DTEX depends on FSRT, FSFT and SPKT
        DTEX = 2* SPKT - (2*FSRT + FSFT)
        Range: 0 to 1023
        Default: DTEX = 2* SPKT - (2*FSRT + FSFT)
        Dependency: FSRT (Register 4), FSFT (Register 5), SPKT (Register 32).
        Not Connected: Bits 15-13
        """
        def __init__(self):
            self.Info.Address = 0x8000 + 41
            self.Info.Span = 1
            super().__init__()
        _fields_ = [
            ("DeadTime_Extension", c_uint16, 13),
            ("NC", c_uint16, 3)
        ]

    # Register #42-43
    class PRTM(CustomStructure):
        """
        PRTM: Bits 31-0; Unsigned; The preset acquisition time in seconds.
        Bit LRTM determines if the preset time is live time or real time.
        Set to zero to disable timer control of the spectrum acquisition.
        Range: 0 to (2^32) - 1
        Default: 0
        Dependency: User defined
        """
        def __init__(self):
            self.Info.Address = 0x8000 + 42
            self.Info.Span = 2
            super().__init__()
        _fields_ = [
            ("Preset_Time", c_uint32, 32)
        ]

    # Register #44
    class PDCN(CustomStructure):
        """
        PDCN: Bits 15-0; Unsigned; Number of counts peak detected, pile-up free, and stored in the MCA memory in a time interval ICRR.

        Throughput Count Rate = PDCN/ICRR

        Range: 0 to (2^16) - 1
        Dependency: Read only
        """
        def __init__(self):
            self.Info.Address = 0x8000 + 44
            self.Info.Span = 1
            super().__init__()
        _fields_ = [
            ("Peak_Detector_Count", c_uint16, 16)
        ]

    # Register #45
    class ICRC(CustomStructure):
        """
        ICRC: Bits 15-0; Unsigned; Number of counts of the fast discriminator in a time interval ICRL.

        True Incoming Count Rate = ICRC/ICRL

        Range: 0 to 216 -1
        Dependency: Read only
        Unsigned Word representing the number of counts of the fast discriminator in the interval of real time given in REGISTER 46.
        True incoming rate is calculated by dividing REG 45 by REG 47.
        """
        def __init__(self):
            self.Info.Address = 0x8000 + 45
            self.Info.Span = 1
            super().__init__()
        _fields_ = [
            ("Peak_Detector_Count", c_uint16, 16)
        ]

    # Register #46
    class ICRR(CustomStructure):
        """
        ICRR: Bits 15-0; Unsigned; ICR Real time ticks.
        ICR Real Time [seconds] = ICRR * 2048 * TCLK
        Range: 0 to (2^16) - 1
        Dependency: Read only
        """
        def __init__(self):
            self.Info.Address = 0x8000 + 46
            self.Info.Span = 1
            super().__init__()
        _fields_ = [
            ("ICR_Real_Time", c_uint16, 16)
        ]

    # Register #47
    class ICRL(CustomStructure):
        """
        ICRL: Bits 15-0; Unsigned; ICR Live time ticks.
        ICR Live Time [seconds] = ICRL * 2048 * TCLK
        Range: 0 to (2^16) - 1
        Dependency: Read only
        """
        def __init__(self):
            self.Info.Address = 0x8000 + 47
            self.Info.Span = 1
            super().__init__()
        _fields_ = [
            ("ICR_Live_Time", c_uint16, 16)
        ]

    # Register #48-49
    class SPNE(CustomStructure):
        """
        SPNE: Bits 31-0; Unsigned; The estimated threshold of the slow shaper noise based on positive noise samples only.
        The channel number of the hard size spectrum corresponding to the estimated noise threshold can be obtained by dividing the SPNE by the normalization factor NORM.
        Threshold Channel Number = SPNE/NORM
        Range: 0 to (2^32) - 1
        """
        def __init__(self):
            self.Info.Address = 0x8000 + 48
            self.Info.Span = 2
            super().__init__()
        _fields_ = [
            ("Slow_Shaper_Positive_Noise_Estimation", c_uint32, 32)
        ]

    # Register #50-51
    class SNNE(CustomStructure):
        """
        SNNE: Bits 31-0; Unsigned; The estimated threshold of the slow shaper noise based on negative noise samples only.
        The channel number of the hard size spectrum corresponding to the estimated noise threshold can be obtained by dividing the SNNE by the normalization factor NORM.
        Threshold Channel Number = SNNE/NORM
        Range: 0 to (2^32) - 1
        """
        def __init__(self):
            self.Info.Address = 0x8000 + 50
            self.Info.Span = 2
            super().__init__()
        _fields_ = [
            ("Slow_Shaper_Negative_Noise_Estimation", c_uint32, 32)
        ]

    # Register #52-53
    class FPNE(CustomStructure):
        """
        FPNE: Bits 31-0; Unsigned; The estimated threshold of the fast shaper noise based on positive noise samples only.
        The channel number of the hard size spectrum corresponding to the estimated noise threshold can be obtained by dividing the FPNE by the normalization factor NORM.
        Threshold Channel Number = FPNE/NORM
        Range: 0 to (2^32) - 1
        """
        def __init__(self):
            self.Info.Address = 0x8000 + 52
            self.Info.Span = 2
            super().__init__()
        _fields_ = [
            ("Fast_Shaper_Positive_Noise_Estimation", c_uint32, 32)
        ]

    # Register #54-55
    class FNNE(CustomStructure):
        """
        FNNE: Bits 31-0; Unsigned; The estimated threshold of the fast shaper noise based on negative noise samples only.
        The channel number of the hard size spectrum corresponding to the estimated noise threshold can be obtained by dividing the FNNE by the normalization factor NORM.
        Threshold Channel Number = FNNE/NORM
        Range: 0 to (2^32) - 1
        """
        def __init__(self):
            self.Info.Address = 0x8000 + 54
            self.Info.Span = 2
            super().__init__()
        _fields_ = [
            ("Fast_Shaper_Negative_Noise_Estimation", c_uint32, 32)
        ]

    # Register #56-57
    class ERTC(CustomStructure):
        """
        ERTC: Bits 31-0; Unsigned; The elapsed real time in increments of 10ms.
        The elapsed real time can be calculated with resolution of 200ns using ERTC and ERTF (Register 60).
        Elapsed Real Time [s] = 0.01*ERTC + 0.0000002*ERTF
        Range: 0 to (2^32) - 1
        """
        def __init__(self):
            self.Info.Address = 0x8000 + 56
            self.Info.Span = 2
            super().__init__()
        _fields_ = [
            ("Elapsed_Real_Time_Coarse", c_uint32, 32)
        ]

    # Register #58-59
    class ELTC(CustomStructure):
        """
        ELTC: Bits 31-0; Unsigned; The elapsed live time in increments of 10ms.
        The elapsed live time can be calculated with resolution of 200ns using ELTC and ELTF (Register 61).
        Elapsed Live Time [s] = 0.01*ELTC + 0.0000002*ELTF
        Range: 0 to (2^32) - 1
        """
        def __init__(self):
            self.Info.Address = 0x8000 + 58
            self.Info.Span = 2
            super().__init__()
        _fields_ = [
            ("Elapsed_Live_Time_Coarse", c_uint32, 32)
        ]

    # Register #60
    class ERTF(CustomStructure):
        """
        ERTF: Bits 15-0; Unsigned; The elapsed real time in increments of 200ns in the range of 0 to 10ms.
        The elapsed real time can be calculated with resolution of 200ns using ERTF and ERTC (Register 56, 57).
        Elapsed Real Time [s] = 0.01*ERTC + 0.0000002*ERTF
        Range: 0 to 49999
        """
        def __init__(self):
            self.Info.Address = 0x8000 + 60
            self.Info.Span = 1
            super().__init__()
        _fields_ = [
            ("Elapsed_Real_Time_Fine", c_uint16, 16)
        ]

    # Register #61
    class ELTF(CustomStructure):
        """
        ELTF: Bits 15-0; Unsigned; The elapsed live time in increments of 200ns in the range of 0 to 10ms.
        The elapsed live time can be calculated with resolution of 200ns using ELTF and ELTC (Register 58, 59).
        Elapsed Live Time [s] = 0.01*ELTC + 0.0000002*ELTF
        Range: 0 to 49999
        """
        def __init__(self):
            self.Info.Address = 0x8000 + 61
            self.Info.Span = 1
            super().__init__()
        _fields_ = [
            ("Elapsed_Live_Time_Fine", c_uint16, 16)
        ]

    # Register #62
    class ETCA(CustomStructure):
        """
        ETCA: Bits 3-0; Unsigned; Determines the expected Primary Exponential Time Constant at Input A of the labZY tools.
        This parameter is part of the FPGA design and is specified in the file name of the FPGA design.
        Expected Time Constant Input A = 2ETCA*TCLK
        Range: 0 to 15
        """
        def __init__(self):
            self.Info.Address = 0x8000 + 62
            self.Info.Span = 1
            super().__init__()
        _fields_ = [
            ("ETCA", c_uint16, 4),
            ("ETCB", c_uint16, 4),
            ("NC", c_uint16, 8)
        ]

    # Register #62
    class ETCB(CustomStructure):
        """
        ETCB: Bits 7-4; Unsigned; Determines the expected Primary Exponential Time Constant at Input A of the labZY tools.
        This parameter is part of the FPGA design and is specified in the file name of the FPGA design.
        Expected Time Constant Input B = 2ETCB*TCLK
        Range: 0 to 15
        """
        def __init__(self):
            self.Info.Address = 0x8000 + 62
            self.Info.Span = 1
            super().__init__()
        _fields_ = [
            ("ETCA", c_uint16, 4),
            ("ETCB", c_uint16, 4),
            ("NC", c_uint16, 8)
        ]

    # Register #63
    class FPGV(CustomStructure):
        """
        FPGV: Bits 15-0; Unsigned; Specifies the version number of the FPGA design loaded into the labZY tool.
        FPGA Version = FPGV/10
        Range: 0 to 65535
        """
        def __init__(self):
            self.Info.Address = 0x8000 + 63
            self.Info.Span = 1
            super().__init__()
        _fields_ = [
            ("FPGA_Version_Number", c_uint16, 16)
        ]

    # Register #64
    class LBLH(CustomStructure):
        """
        LBLH: Bits 13-0; Unsigned; Channel number of the hard size spectrum corresponding to the left boundary of the stabilizer peak left-hand side ROI.
        Range: 0 to 16383

        ENST: Bit 15; When ENST = 1 the gain stabilizer is enabled.
        When ENST= 0 the gain stabilizer is disabled.
        """
        def __init__(self):
            self.Info.Address = 0x8000 + 64
            self.Info.Span = 1
            super().__init__()
        _fields_ = [
            ("LBLH", c_uint16, 14),
            ("NC", c_uint16, 1),
            ("ENST", c_uint16, 1)
        ]

    # Register #65
    class RBLH(CustomStructure):
        """
        RBLH: Bits 13-0; Unsigned; Channel number of the hard size spectrum corresponding to the right boundary of the stabilizer peak left-hand side ROI.
        Range: 0 to 16383
        """
        def __init__(self):
            self.Info.Address = 0x8000 + 65
            self.Info.Span = 1
            super().__init__()
        _fields_ = [
            ("RBLH", c_uint16, 14),
            ("NC", c_uint16, 2)
        ]

    # Register #66
    class LBRH(CustomStructure):
        """
        LBRH: Bits 13-0; Unsigned; Channel number of the hard size spectrum corresponding to the left boundary of the stabilizer peak right-hand side ROI.
        Range: 0 to 16383
        """
        def __init__(self):
            self.Info.Address = 0x8000 + 66
            self.Info.Span = 1
            super().__init__()
        _fields_ = [
            ("LBRH", c_uint16, 14),
            ("NC", c_uint16, 2)
        ]

    # Register #67
    class RBRH(CustomStructure):
        """
        RBRH: Bits 13-0; Unsigned; Channel number of the hard size spectrum corresponding to the right boundary of the stabilizer peak righthand side ROI.
        Range: 0 to 16383
        """
        def __init__(self):
            self.Info.Address = 0x8000 + 67
            self.Info.Span = 1
            super().__init__()
        _fields_ = [
            ("RBRH", c_uint16, 14),
            ("NC", c_uint16, 2)
        ]

    # Register #68
    class DIND(CustomStructure):
        """
        DIND: Bits 11-0; Unsigned; Specifies the delay of the logic signal at the Input D when Input D is configured as logic signal input used for coincidence/anti-coincidence.
        Not applicable for nanoXRS.
        In the time domain, the width of the coincidence/anti-coincidence window  is:
            Input D Delay = DIND*TCLK
        Range: 0 to 4095
        """
        def __init__(self):
            self.Info.Address = 0x8000 + 68
            self.Info.Span = 1
            super().__init__()
        _fields_ = [
            ("Delay_of_the_Logic_Signal_at_Input_D", c_uint16, 12),
            ("NC", c_uint16, 4)
        ]

    # Register #69
    class COWW(CustomStructure):
        """
        COWW: Bits 11-0; Unsigned; Specifies the width coincidence/anticoincidence window.
        Not applicable for nanoXRS.
        In the time domain, the width of the coincidence/anti-coincidence window is:
            Window Width = COWW*TCLK
        Range: 0 to 4095

        ANTI: Bit 14; When ANTI = 0, the internally generated window is a coincidence window.
        When ANTI = 1, the internally generated window is an anti-coincidence window.
        If DIRD = 0 then ANTI must also be set to 0.
        Not applicable for nanoXRS.

        DIRD: Bit 15; When DIRD = 1, the internal window generator is enabled with window width specified by COWW.
        When DIRD = 0, the gain window generator is disabled and the width of the Input D logic signal is the width of the coincidence window.
        Not applicable for nanoXRS.
        """
        def __init__(self):
            self.Info.Address = 0x8000 + 69
            self.Info.Span = 1
            super().__init__()
        _fields_ = [
            ("CoincidenceWindow_Width", c_uint16, 12),
            ("NC", c_uint16, 2),
            ("ANTI", c_uint16, 1),
            ("DIRD", c_uint16, 1),
        ]

    # Register #70
    class STOD(CustomStructure):
        """
        STOD: Bits 11-0; Unsigned; Specifies the delay of pulse height storage and the peak-detect signal.
        The delayed peak-detect signal is used as coincidence/anti-coincidence signal.
        Not applicable for nanoXRS.
        In the time domain the width of the storage delay is:
            Storage Delay = STOD*TCLK
        Range: 0 to 4095
        """
        def __init__(self):
            self.Info.Address = 0x8000 + 70
            self.Info.Span = 1
            super().__init__()
        _fields_ = [
            ("PulseHeight_Storage_Delay", c_uint16, 12),
            ("NC", c_uint16, 4)
        ]
