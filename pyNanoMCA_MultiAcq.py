# -*- coding: utf-8 -*-
"""
File:           pyNanoMCA_MultiAcq.py
Description:    Acquire from multiple Labzy/Yantel nanoMCAs simultaneously and store the data.
Creator:        Joshua A. Handley (2022)

Copyright (c) 2022 ACT. All rights reserved.

TODO: Check energy to channel when quad >0
TODO: Store spectra to separate files, by serial?

"""
#=== IMPORTS ===============================================================================================================

# Standard libs
import os
import sys
import time
import math
import datetime
import asyncio
import decimal
from collections import OrderedDict
from typing import Optional, Union, IO, Dict, List, OrderedDict as OrderedDictType


# Logging
import logging

# nanoMCA library
import pyNanoMCA_lib as Lib


#===========================================================================================================================
#=== STRUCTURES ============================================================================================================

class DetectorConfiguration:
    Name: str = ""
    CoordX: float = 0.0
    CoordY: float = 0.0
    GainTotal: float = 1.000
    ECalQuad: float = 0.0
    ECalSlope: float = 1.0
    ECalOffset: float = 0.0

    def __init__(self, name, coordX, coordY, gainTotal, eCalQuad, eCalSlope, eCalOffset):
        self.Name = name
        self.CoordX = coordX
        self.CoordY = coordY
        self.GainTotal = gainTotal
        self.ECalQuad = eCalQuad
        self.ECalSlope = eCalSlope
        self.ECalOffset = eCalOffset


#===========================================================================================================================
#=== CONFIGURATION (User Configurable) =====================================================================================

# Configuration
config_Setup                = {
    "Shaping": {
        "input"             : "B+",
        "slowRiseTime_us"   : 2.0,
        "slowFlatTop_us"    : 1.75,
        "slowBLR_us"        : 100.0,
        "fastRiseTime_us"   : 0.0625,
        "fastFlatTop_us"    : 0.0750,
        "fastBLR_us"        : 80.0,
        "shortTC_ns"        : 30.0,
        "longTC_us"         : 1.0,
        "pulser"            : False,
        "coincidence"       : False
    },
    "Detectors": [
        {
            16512: DetectorConfiguration(
                name="Detector #1",
                coordX=10.0,
                coordY=10.0,
                gainTotal=1.000,
                eCalQuad=0.0,
                eCalSlope=0.1252,
                eCalOffset=7.7887
            )
        },
        {
            16513: DetectorConfiguration(
                name="Detector #2",
                coordX=0.0,
                coordY=0.0,
                gainTotal=1.000,
                eCalQuad=0.0,
                eCalSlope=0.0903,
                eCalOffset=1.5958
            )
        },
        {
            16516: DetectorConfiguration(
                name="Detector #3",
                coordX=0.0,
                coordY=10.0,
                gainTotal=1.000,
                eCalQuad=0.0,
                eCalSlope=0.1176,
                eCalOffset=-6.4517
            )
        },
        {
            16517: DetectorConfiguration(
                name="Detector #4",
                coordX=10.0,
                coordY=0.0,
                gainTotal=1.000,
                eCalQuad=0.0,
                eCalSlope=0.1658,
                eCalOffset=5.2941
            )
        },
        {
            16518: DetectorConfiguration(
                name="Detector #5",
                coordX=10.0,
                coordY=0.0,
                gainTotal=1.000,
                eCalQuad=0.0,
                eCalSlope=0.1145,
                eCalOffset=2.5189
            )
        },
        {
            16519: DetectorConfiguration(
                name="Detector #6",
                coordX=10.0,
                coordY=0.0,
                gainTotal=1.000,
                eCalQuad=0.0,
                eCalSlope=0.1333,
                eCalOffset=-.6999
            )
        },
        {
            16520: DetectorConfiguration(
                name="Detector #7",
                coordX=10.0,
                coordY=0.0,
                gainTotal=1.000,
                eCalQuad=0.0,
                eCalSlope=0.0672,
                eCalOffset=4.7667
            )
        },
        {
            16521: DetectorConfiguration(
                name="Detector #8",
                coordX=10.0,
                coordY=0.0,
                gainTotal=1.000,
                eCalQuad=0.0,
                eCalSlope=0.0872,
                eCalOffset=3.3882
            )
        }
    ],
    "Measurement": {
        "liveTime_sec"      : 1.0,
        "roiEnergyLeft"     : 560,
        "roiEnergyRight"    : 760,
        "doAnalysis"        : True,
        "doLocalization"    : False,
        "store"             : True,
        "storeAs"           : "CSV",
        "storeDirectory"    : "Measurements/",
        "storeLiveTimes"    : False,
        "storeRealTimes"    : False,
        "storeICRs"         : True,
        "storeROIs"         : True,
        "storeSpectra"      : True,
        "zeroCompression"   : False
    }
}

# Logging / Output
outputPrefix                = "Main:"
outputPrefixPadding         = 15
outputVerbose               = False


#===========================================================================================================================
#=== GLOBALS ===============================================================================================================

# -- Version information
versionScript = "1.0.0"

# -- Detector vars
Devices: Optional[OrderedDictType[int, Lib.NanoMCA]] = None
DetectorConfig: Optional[OrderedDictType[int, DetectorConfiguration]] = None
ShapingInfo: Optional[Dict[str, Union[str, int, float, bool]]] = None
MeasurementInfo: Optional[Dict[str, Union[str, int, float, bool]]] = None

# -- Data vars
Data_LiveTimes: Optional[OrderedDictType[int, float]] = OrderedDict()
Data_RealTimes: Optional[OrderedDictType[int, float]] = OrderedDict()
Data_ICRs: Optional[OrderedDictType[int, int]] = OrderedDict()
Data_ROIs: Optional[OrderedDictType[int, int]] = OrderedDict()
Data_Spectra: Optional[OrderedDictType[int, List[int]]] = OrderedDict()

# -- Output vars
Output_CurrentDirectory = os.path.realpath(os.path.dirname(__file__))
Output_File: Optional[IO] = None
Output_File_Timestamp: Optional[str] = None

# -- Loop vars
loop_Main = None

# -- Decimals
decimal.getcontext().rounding = decimal.ROUND_HALF_UP
decimal.getcontext().prec = 6

# -- Status vars
status_Initialized = False
status_Configured = False
status_Fault = False

# -- Logging
logging.basicConfig(
    level=logging.INFO,
    #format='%(asctime)s [%(levelname)s]:  %(message)s',
    format='[%(levelname)s]:  %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
_logger = logging.getLogger('Main')


# ==========================================================================================================================
# === Loops ================================================================================================================

def Loop_PerformMeasurement(loop):

    global Devices
    global DetectorConfig
    global ShapingInfo
    global MeasurementInfo
    global status_Configured
    global status_Fault

    try:

        # Configuration required?
        if not status_Configured:

            # Configure all detectors
            success = True
            ConsolePrint("Configuring all detectors...")
            for sn in list(Devices.keys()):

                # Write to log
                ConsolePrint("Configuring detector '{}' (SN#{})...".format(DetectorConfig[sn].Name, sn))

                # Set input polarity
                if "+" in ShapingInfo['input']:
                    Devices[sn].SetInputPolarity(Lib.Enums.InputPolarityMode.Positive)
                else:
                    Devices[sn].SetInputPolarity(Lib.Enums.InputPolarityMode.Negative)

                # Set shaping (Slow)
                success = Devices[sn].SetSlowShaper_RiseTime(ShapingInfo['slowRiseTime_us']) if success else False
                success = Devices[sn].SetSlowShaper_FlatTop(ShapingInfo['slowFlatTop_us']) if success else False
                success = Devices[sn].SetSlowShaper_BLR(ShapingInfo['slowBLR_us']) if success else False

                # Set shaping (Fast)
                success = Devices[sn].SetFastShaper_RiseTime(ShapingInfo['fastRiseTime_us']) if success else False
                success = Devices[sn].SetFastShaper_FlatTop(ShapingInfo['fastFlatTop_us']) if success else False
                success = Devices[sn].SetFastShaper_BLR(ShapingInfo['fastBLR_us']) if success else False

                # Set unfolding time constants
                success = Devices[sn].SetUnfoldingTimeB_Short_ns(ShapingInfo['shortTC_ns']) if success else False
                success = Devices[sn].SetUnfoldingTimeB_Long_us(ShapingInfo['longTC_us']) if success else False

                # Set pulser
                success = Devices[sn].SetDigitalPulser(ShapingInfo['pulser']) if success else False

                # Set amplifier gains
                gainCoarse = 0
                if DetectorConfig[sn].GainTotal < 1.19:
                    gainCoarse = 0
                else:
                    for cg in list(Lib.Lists.CoarseGainOptions.keys()):
                        if (DetectorConfig[sn].GainTotal - cg) <= (cg * 0.2):
                            gainCoarse = cg
                            break
                gainFine = (DetectorConfig[sn].GainTotal / gainCoarse) if gainCoarse != 0 else DetectorConfig[sn].GainTotal
                success = Devices[sn].SetGain_Coarse(gainCoarse) if success else False
                success = Devices[sn].SetGain_Fine(gainFine) if success else False

                # Set preset time
                success = Devices[sn].SetPreset_Time(presetMode=Lib.Enums.CountingTimePreset.LiveTime, presetTime_sec=MeasurementInfo['liveTime_sec']) if success else False

                # Success?
                if not success:
                    ConsolePrintError("Failed to configure '{}' (SN#{})!".format(DetectorConfig[sn].Name, sn))
                    status_Fault = True
                    Cleanup()
                ConsolePrintDebug("         =-=-=")
            ConsolePrint("=========================================")

        # Start measuring on all detectors
        success = True
        ConsolePrintDebug("Acquire for {} seconds (Preset live time)...".format(MeasurementInfo['liveTime_sec']))
        for sn in list(Devices.keys()):

            # Clear acquisition
            success = Devices[sn].Acquisition_Clear() if success else None

            # Start acquisition
            success = Devices[sn].Acquisition_Start() if success else None

            # Failed to start?
            if not success:
                ConsolePrintError("Failed to start '{}' (SN#{})!".format(DetectorConfig[sn].Name, sn))
                status_Fault = True
                Cleanup()

        # All detectors configured and running
        status_Configured = True

        # Wait for all acquisitions to complete
        waitTime_sec = 0
        timeout = False
        while (not timeout) and all(d.IsAcquiring() for d in Devices.values()):
            time.sleep(0.1)
            waitTime_sec += 0.1
            if waitTime_sec > MeasurementInfo['liveTime_sec'] * 5.0:
                timeout = True
                break

        # No timeout?
        if timeout:
            ConsolePrintError("Timeout while waiting for all acquisitions to complete!")
            status_Fault = True
            Cleanup()

        # Acquisitions complete
        ConsolePrintDebug("Acquisitions complete!")
        ConsolePrintDebug("         =-=-=")

    except Exception as ex:
        ConsolePrintError("*** Exception during measurement loop! ***", exception=ex)
        status_Fault = True
        Cleanup()

    finally:
        # Call next coroutine
        loop.call_soon(Loop_Analyze, loop)


def Loop_Analyze(loop):

    global Devices
    global DetectorConfig
    global MeasurementInfo
    global Data_LiveTimes
    global Data_RealTimes
    global Data_ICRs
    global Data_ROIs
    global Data_Spectra
    global status_Fault

    try:

        # Enabled?
        if not MeasurementInfo['doAnalysis']:
            return

        # Get measurement data from all detectors
        ConsolePrint("Getting measurement data from all detectors...")
        for sn in list(Devices.keys()):

            # Write to log
            ConsolePrintDebug("Getting measurement data from detector '{}' (SN#{})...".format(DetectorConfig[sn].Name, sn))

            # Live time?
            if MeasurementInfo['storeLiveTimes']:
                Data_LiveTimes[sn] = Devices[sn].GetMeasurement_LiveTime()

            # Real time?
            if MeasurementInfo['storeRealTimes']:
                Data_RealTimes[sn] = Devices[sn].GetMeasurement_RealTime()

            # ICR?
            if MeasurementInfo['storeICRs']:
                Data_ICRs[sn] = Devices[sn].GetMeasurement_CountRate_ICR()

            # Spectrum?
            if MeasurementInfo['storeSpectra'] or MeasurementInfo['storeROIs']:
                Data_Spectra[sn] = Devices[sn].GetMeasurement_PHA()

            # ROIs?
            if MeasurementInfo['storeROIs']:
                if DetectorConfig[sn].ECalQuad != 0:
                    leftChannel = int(round(((-1.0 * DetectorConfig[sn].ECalSlope) + math.sqrt((DetectorConfig[sn].ECalSlope**2) - (4.0 * DetectorConfig[sn].ECalQuad * (DetectorConfig[sn].ECalOffset - MeasurementInfo['roiEnergyLeft'])))) / (2.0 * DetectorConfig[sn].ECalQuad), 0))
                    rightChannel = int(round(((-1.0 * DetectorConfig[sn].ECalSlope) + math.sqrt((DetectorConfig[sn].ECalSlope**2) - (4.0 * DetectorConfig[sn].ECalQuad * (DetectorConfig[sn].ECalOffset - MeasurementInfo['roiEnergyRight'])))) / (2.0 * DetectorConfig[sn].ECalQuad), 0))
                else:
                    leftChannel = int(round((MeasurementInfo['roiEnergyLeft'] - DetectorConfig[sn].ECalOffset) / DetectorConfig[sn].ECalSlope, 0))
                    rightChannel = int(round((MeasurementInfo['roiEnergyRight'] - DetectorConfig[sn].ECalOffset) / DetectorConfig[sn].ECalSlope, 0))
                ConsolePrintDebug("... ROI range: ch{} - ch{}".format(leftChannel, rightChannel))
                Data_ROIs[sn] = sum(Data_Spectra[sn][leftChannel:rightChannel])

        # Print results?
        ConsolePrint("Spectra integral(s): [" + ", ".join([str(sum(i)) for i in Data_Spectra.values()]) + "]")
        if MeasurementInfo['storeROIs']:
            ConsolePrint("ROI result(s): [" + ", ".join([str(i) for i in Data_ROIs.values()]) + "]")

    except Exception as ex:
        ConsolePrintError("*** Exception during analysis loop! ***", exception=ex)
        status_Fault = True
        return

    finally:
        # Call next coroutine
        loop.call_soon(Loop_Localize, loop)


def Loop_Localize(loop):

    global DetectorConfig
    global MeasurementInfo
    global status_Fault

    try:

        # Enabled?
        if not MeasurementInfo['doLocalization']:
            return

    except Exception as ex:
        ConsolePrintError("*** Exception during localization loop! ***", exception=ex)
        status_Fault = True
        return

    finally:
        # Call next coroutine
        loop.call_soon(Loop_StoreData, loop)


def Loop_StoreData(loop):

    global DetectorConfig
    global MeasurementInfo
    global Data_LiveTimes
    global Data_RealTimes
    global Data_ICRs
    global Data_ROIs
    global Data_Spectra
    global Output_File
    global Output_File_Timestamp
    global Output_CurrentDirectory
    global status_Fault

    try:

        # Enabled?
        if not MeasurementInfo['store']:
            return

        # Write to log
        ConsolePrint("Storing data...")

        # Get timestamp
        timestampNow = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if Output_File_Timestamp is None:
            Output_File_Timestamp = timestampNow.replace(' ', '').replace('-', '').replace(':', '')

        # Output format?
        if MeasurementInfo['storeAs'].upper() == "CSV":

            # CSV vars
            delimiter = ','

            # New file or not already open?
            if Output_File is None:

                # Output directory exists?
                outputDir = os.path.join(Output_CurrentDirectory, MeasurementInfo['storeDirectory'])
                if not os.path.exists(outputDir):
                    os.makedirs(outputDir)

                # Create new output file
                Output_File = open(os.path.join(outputDir, "NanoMCA_MultiAcq_{}.csv".format(Output_File_Timestamp)), mode='a+')

                # Add info block
                Output_File.write('"pyNanoMCA Multi-Acquisition"' + "\n")
                Output_File.write('"Detector names:"')
                for sn in list(Devices.keys()):
                    Output_File.write(delimiter + '"{}"'.format(DetectorConfig[sn].Name))
                Output_File.write("\n")
                Output_File.write('"Detector serials:"')
                for sn in list(Devices.keys()):
                    Output_File.write(delimiter + '"{}"'.format(str(sn)))
                Output_File.write("\n")
                if MeasurementInfo['storeROIs']:
                    Output_File.write('"ROI left [keV]:"' + delimiter + str(MeasurementInfo['roiEnergyLeft']) + "\n")
                    Output_File.write('"ROI right [keV]:"' + delimiter + str(MeasurementInfo['roiEnergyRight']) + "\n")

                # Blank line
                Output_File.write("\n")

                # Add 1st row header
                Output_File.write(delimiter)
                for sn in list(Devices.keys()):
                    Output_File.write(delimiter + '"LiveTime [s]"') if MeasurementInfo['storeLiveTimes'] else None
                for sn in list(Devices.keys()):
                    Output_File.write(delimiter + '"RealTime [s]"') if MeasurementInfo['storeRealTimes'] else None
                for sn in list(Devices.keys()):
                    Output_File.write(delimiter + '"ICR"') if MeasurementInfo['storeICRs'] else None
                for sn in list(Devices.keys()):
                    Output_File.write(delimiter + '"ROI"') if MeasurementInfo['storeROIs'] else None
                # for sn in list(Devices.keys()):
                #     Output_File.write(delimiter + '"Spectrum"') if MeasurementInfo['storeSpectra'] else None
                Output_File.write("\n")

                # Add 2nd row header
                Output_File.write('"Timestamp"' + delimiter)
                for sn in list(Devices.keys()):
                    Output_File.write(delimiter + '"{}"'.format(DetectorConfig[sn].Name)) if MeasurementInfo['storeLiveTimes'] else None
                for sn in list(Devices.keys()):
                    Output_File.write(delimiter + '"{}"'.format(DetectorConfig[sn].Name)) if MeasurementInfo['storeRealTimes'] else None
                for sn in list(Devices.keys()):
                    Output_File.write(delimiter + '"{}"'.format(DetectorConfig[sn].Name)) if MeasurementInfo['storeICRs'] else None
                for sn in list(Devices.keys()):
                    Output_File.write(delimiter + '"{}"'.format(DetectorConfig[sn].Name)) if MeasurementInfo['storeROIs'] else None
                # for sn in list(Devices.keys()):
                #     Output_File.write(delimiter + '"{}"'.format(DetectorConfig[sn].Name)) if MeasurementInfo['storeSpectra'] else None
                Output_File.write("\n")

            # Write data row...

            # ... Timestamp
            Output_File.write(timestampNow + delimiter)

            # ... Live times?
            for sn in list(Devices.keys()):
                Output_File.write(delimiter + "{:.4f}".format(Data_LiveTimes[sn])) if MeasurementInfo['storeLiveTimes'] else None

            # ... Real times?
            for sn in list(Devices.keys()):
                Output_File.write(delimiter + "{:.4f}".format(Data_RealTimes[sn])) if MeasurementInfo['storeRealTimes'] else None

            # ... ICRs?
            for sn in list(Devices.keys()):
                Output_File.write(delimiter + "{:.3f}".format(Data_ICRs[sn])) if MeasurementInfo['storeICRs'] else None

            # ... ROIs?
            for sn in list(Devices.keys()):
                Output_File.write(delimiter + str(Data_ROIs[sn])) if MeasurementInfo['storeROIs'] else None

            # ... Spectra?
            outputDir = os.path.join(Output_CurrentDirectory, MeasurementInfo['storeDirectory'])
            if MeasurementInfo['storeSpectra']:
                if MeasurementInfo['zeroCompression']:
                    for sn in list(Devices.keys()):
                        s = ZeroCompress(Data_Spectra[sn])
                        with open(os.path.join(outputDir, "NanoMCA_MultiAcq_{}_Spectra_SN{}.csv".format(Output_File_Timestamp, sn)), mode='a+') as Spectrum_File:
                            Spectrum_File.write(timestampNow + delimiter)
                            Spectrum_File.write(delimiter + ",".join([str(i) for i in s]))
                            Spectrum_File.write("\n")
                            Spectrum_File.flush()
                else:
                    for sn in list(Devices.keys()):
                        with open(os.path.join(outputDir, "NanoMCA_MultiAcq_{}_Spectra_SN{}.csv".format(Output_File_Timestamp, sn)), mode='a+') as Spectrum_File:
                            Spectrum_File.write(timestampNow + delimiter)
                            Spectrum_File.write(delimiter + ",".join([str(i) for i in Data_Spectra[sn]]))
                            Spectrum_File.write("\n")
                            Spectrum_File.flush()

            # ... Newline & flush
            Output_File.write("\n")
            Output_File.flush()

        else:
            raise NotImplementedError("Storage output format not implemented!")

    except Exception as ex:
        ConsolePrintError("*** Exception during store loop! ***", exception=ex)
        status_Fault = True
        return

    finally:
        # Call next coroutine
        loop.call_soon(Loop_PerformMeasurement, loop)


# ==========================================================================================================================
# === NanoMCA Devices ======================================================================================================

def Devices_Connect() -> Optional[OrderedDictType[int, Lib.NanoMCA]]:

    global DetectorConfig

    # Attempt to connect to all devices
    i = 0
    found: Dict[int, Lib.NanoMCA] = {}
    while i < len(DetectorConfig):
        # Create new nanoMCA instance and attempt to connect
        n = Lib.NanoMCA()
        if n.Connect(index=i):
            # Get the serial number
            sn = n.GetParameter_SerialNumber()
            # Recognized serial?
            if sn in list(DetectorConfig.keys()):
                found[sn] = n
            i += 1
        else:
            ConsolePrintError("Failed to connect to device #{}!".format(i))
            return None

    # Found all?
    if len(found.keys()) != len(DetectorConfig.keys()):
        ConsolePrintError("Failed to connect to all devices!")
        return None

    # Sort result and return
    devs: OrderedDictType[int, Lib.NanoMCA] = OrderedDict()
    for sn in list(DetectorConfig.keys()):
        devs[sn] = found[sn]
    return devs


def Devices_Disconnect() -> bool:

    global Devices

    if hasattr(Devices, "keys"):
        for i in list(Devices.keys()):
            Devices[i].Disconnect()

    return True


# ==========================================================================================================================
# === Utility Functions ====================================================================================================

def Cleanup():

    global Devices
    global loop_Main
    global Output_File

    # Write to log
    ConsolePrint("Cleanup...")

    # Stop main loop
    if loop_Main is not None:
        loop_Main.stop()
        while loop_Main.is_running():
            time.sleep(1)
        loop_Main.close()

    # Close output file
    if Output_File is not None:
        Output_File.close()
        Output_File = None

    # Disconnect devices
    Devices_Disconnect()

    # Exit
    ConsolePrint("Cleanup complete. Exiting...")
    logging.shutdown()
    sys.exit()


def ZeroCompress(spectrum: List[int]) -> Optional[List[int]]:

    try:
        # Determine final size of compressed spectrum
        i = 0
        inputSize = len(spectrum)
        outputSize = 0
        while i < inputSize:
            outputSize += 1
            if spectrum[i] == 0:
                outputSize += 1
                while (i + 1) < inputSize:
                    if spectrum[i + 1] != 0:
                        break
                    i += 1
            i += 1

        # Can it be compressed?
        if inputSize == outputSize:
            return spectrum

        # Create return array
        compressedSpectrum = [0]*outputSize

        # Compress spectrum into return array
        i = 0
        j = 0
        while i < inputSize:
            compressedSpectrum[j] = spectrum[i]
            j += 1
            # If the current channel value is 0, see how many more there are...
            if spectrum[i] == 0:
                # Start with one "zero in a row"
                compressedSpectrum[j] = 1
                while (i + 1) < inputSize:
                    if spectrum[i + 1] == 0:
                        # Increase the number of zeroes in a row
                        compressedSpectrum[j] += 1
                        i += 1
                    else:
                        j += 1
                        break
            i += 1

        # Done
        return compressedSpectrum

    except Exception as ex:
        ConsolePrintError("Exception performing zero compression!", exception=ex)
        return None


# ==========================================================================================================================
# === Logging ==============================================================================================================

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


#===========================================================================================================================
#=== EXECUTION =============================================================================================================
#===========================================================================================================================

# Library file executed directly?
if __name__ == '__main__':

    ConsolePrint("=========================================")
    ConsolePrint("========    p y N a n o M C A    ========")
    ConsolePrint("========    Multi Acquisition    ========")
    ConsolePrint("=========================================")

    # Print the version information
    ConsolePrint("Script version : v " + versionScript)
    ConsolePrint("                 =-=-=                   ")

    # Debug logging?
    if outputVerbose:
        _logger.setLevel(logging.DEBUG)

    # Parse configuration
    ConsolePrint("Parsing configuration...")
    ShapingInfo = config_Setup["Shaping"]
    DetectorConfig = OrderedDict([(list(d.keys())[0], list(d.values())[0]) for d in config_Setup["Detectors"]])
    MeasurementInfo = config_Setup["Measurement"]

    # Enable keyboard interrupt listener
    try:

        # Attempt to connect to all devices
        ConsolePrint("Connecting to all devices...")
        Devices = Devices_Connect()

        # Fault?
        if Devices is None:
            ConsolePrintError("Failed to connect to all devices!")
            Cleanup()

        # Create main loop
        ConsolePrint("=========================================")
        ConsolePrint("Starting main loop...")
        ConsolePrint("=========================================")
        loop_Main = asyncio.new_event_loop()
        asyncio.set_event_loop(loop_Main)

        # Initialized
        status_Initialized = True

        # Schedule first call in main loop to capture measurement, starting continuous loop cascade
        loop_Main.call_soon(Loop_PerformMeasurement, loop_Main)
        ConsolePrint("Main loop running. System online!")
        ConsolePrint("=========================================")

        # Loop
        try:
            loop_Main.run_forever()
        finally:
            pass

    except (SystemError, SystemExit, KeyboardInterrupt):
        ConsolePrint("=========================================")
        ConsolePrint(">> Caught keyboard interrtupt - Initiate clean shut-down...")

    finally:
        # Cleanup
        Cleanup()

    # Done
    ConsolePrint("=========================================")

    # Exit
    ConsolePrint("Exiting...")
