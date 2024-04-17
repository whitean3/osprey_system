# -*- coding: utf-8 -*-
"""
File:           pyOsprey_lib.py
Description:    Cross-platform communication library for the Osprey MCA
Creator:        Joshua A. Handley (2023)

NOT IMPLEMENTED:
    - MCS acquisitions
    - Preset mode: Sweeps
    - Preset mode: Integral

Copyright (c) 2023 ACT. All rights reserved.

***********************************************************************************************
*** See the Execution/Diagnostics section (end of file) to see example usage of the library ***
***********************************************************************************************
"""
#=== IMPORTS ============================================================================================

# Future import: Annotation suport for forward referenced typing
from __future__ import annotations

# Standard libs
import os
import sys
import time
import datetime
import logging
import traceback
from typing import Optional, List

# Parent folder
pathScript = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(pathScript, ".."))

# Enumerations
from pyOsprey_enumerations import OspreyEnums

# Osprey MCA SDK
pathScript = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(pathScript, "DataTypes"))
from DataTypes.DeviceFactory import *
#from pyOsprey.DataTypes.ParameterCodes import *
#from pyOsprey.DataTypes.CommandCodes import *
from DataTypes.ParameterTypes import *
from DataTypes.Parameter import *
#from pyOsprey.DataTypes.CounterData import *

# Histogram support
histogramSupport = False
try:
    import pyOsprey.printHistogram_lib as histogram
    histogramSupport = True
except ImportError:
    histogram = None
    pass

#========================================================================================================
#=== CONFIGURATION (User Configurable) ==================================================================

# Logging / Output
_loggingVerbose         = False
_loggingPrefix          = "Osprey:"
_loggingPrefixPadding   = 13

# Diagnostics (when executing this file directly)
diagnostics_ConnectionMethod    = OspreyEnums.ConnectionMethod.USB
diagnostics_IP_Override         = '10.0.1.4'
diagnostics_EnableMassStorage   = False
diagnostics_EnableTFTP          = False
diagnostics_DisableTFTP         = False
diagnostics_FirmwareUpdate      = False
diagnostics_AcquireSpectrum     = True
diagnostics_LiveTime_sec        = 5
diagnostics_Histogram_enabled   = True
diagnostics_Histogram_bins      = 48
diagnostics_Histogram_height    = 10
diagnostics_Write_CSVs          = False


# ========================================================================================================
# === GLOBALS ============================================================================================

# -- Version information
versionLib = "1.1.0"

# -- Logging
_logger = logging.getLogger('Main.Osprey')
_logger.propagate = True
if __name__ == '__main__':
    _logger = None


# ========================================================================================================
# === STRUCTURES =========================================================================================

class SpectrumData:

    Timestamp: Optional[datetime.datetime] = None
    LiveTime_sec: float = 0
    RealTime_sec: float = 0
    DeadTime: float = 0
    GrossCounts: int = 0
    CPS: float = 0
    """Deadtime, as value 0-100, in percent"""
    Spectrum: List[int] = []

    def __init__(
            self,
            timestamp: datetime.datetime,
            liveTime_sec: float,
            realTime_sec: float,
            spectrum: List[int]
    ):
        self.Timestamp = timestamp
        self.LiveTime_sec = liveTime_sec
        self.RealTime_sec = realTime_sec
        self.Spectrum = spectrum

        # Calculated values
        # ... Deadtime
        deadtime = 0
        if (liveTime_sec > 0) and (realTime_sec > 0):
            if liveTime_sec < realTime_sec:
                deadtime = (liveTime_sec / realTime_sec) * 100.0
        self.DeadTime = deadtime
        # ... Gross counts
        grossCounts = 0
        for cnt in spectrum:
            grossCounts += cnt
        self.GrossCounts = grossCounts
        # ... CPS
        cps = 0
        if liveTime_sec > 0:
            cps = round(grossCounts / liveTime_sec, 3)
        self.CPS = cps


# ========================================================================================================
# === OSPREY DEVICE ======================================================================================

class Osprey:
    
    # Class vars
    DTB = None
    Connected = False
    dtbInput = 1
    userAccount = "administrator"
    userPassword = "password"
    
    def Connect(self, method: OspreyEnums.ConnectionMethod, ip_address="", username="", password=""):
        """
        Connect to the Osprey at the default/provided IP address.
    
        @type  method: string
        @param method: The type of connection. Valid inputs = 'usb', 'ethernet'/'lan'
    
        @type  ip_address: string
        @param ip_address: IP address override, if defaults not desired, e.g. '10.0.0.5'
    
        @type  username: string
        @param username: The username to use for authenticating the unlock. Leave blank to use default/last used username.
    
        @type  password: string
        @param password: The password to use for authenticating the unlock. Leave blank to use default/last used password.
    
        @rtype:   bool
        @return:  If the connection was successful
        """
        ConsolePrint("[Function: Connect (method: '" + method.name + "', ip_address: '" + ip_address + "')]", isVerboseOutput=True)
        
        # Create Osprey interface
        self.DTB = DeviceFactory.createInstance(DeviceFactory.DeviceInterface.IDevice)
    
        # Set default Osprey address, if none provided
        if ip_address == "":
            if method == OspreyEnums.ConnectionMethod.USB:
                ip_address = "10.0.1.4"
            elif method == OspreyEnums.ConnectionMethod.Ethernet:
                ip_address = "10.0.0.3"
            else:
                ConsolePrint("*** ERROR *** Invalid connection method provided -- Got '" + str(method) + "'")
                return False
    
        # Set new global credentials, if provided
        if username != "":
            self.userAccount = username
        if password != "":
            self.userPassword = password
    
        # Connect, if a valid IP address is present
        if ip_address != "":
            ConsolePrint("[Open: IP address = '" + str(ip_address) + "']", isVerboseOutput=True)
            self.Connected = False
            try:
                # Try connecting to Osprey...
                self.DTB.open('', ip_address)
                self.Connected = True
            except:
                ConsolePrint("*** ERROR *** Could not connect to Osprey @ IP '" + str(ip_address) + "'")
                return False
    
        # Take ownership & default to PHA mode
        try:
            # Lock all inputs
            self.LockAllInputs(True)
        except:
            ConsolePrint("*** ERROR *** Could not take ownership of device")
            return False
    
        # Set input mode to PHA
        try:
            # Set PHA mode
            self.DTB.setParameter(ParameterCodes.Input_Mode, 0, self.dtbInput)
        except:
            ConsolePrint("*** ERROR *** Could not set input mode to PHA")
            return False
    
        # Success
        ConsolePrint("Connected @ {}!".format(str(ip_address)), isVerboseOutput=False)
        return True
        
    def Disconnect(self):
        """
        Disconnect from the Osprey.

        @rtype:   bool
        @return:  If the disconnection was successful
        """
        ConsolePrint("[Function: Disconnect]", isVerboseOutput=True)
        
        try:
            if self.Connected:
                # Unlock all inputs
                self.UnlockAllInputs()
    
                # Close connection
                self.DTB.close()
                ConsolePrint("Disconnected", isVerboseOutput=False)
    
            # Success
            self.Connected = False
            return True
        except:
            ConsolePrint("*** ERROR *** Failed to disconnect from device")
            self.Connected = False
            return False
        
    def LockInput(self, inputNumber, takeover):
        """
        Lock an input on the connected Osprey
    
        @type  inputNumber: int
        @param inputNumber: The input number to lock (where 0 = The SOM, for all configuration settings; 1 = PHA, MSS, LIST, & TLIST; 2 = MCS)
    
        @type  takeover: bool
        @param takeover: Whether or not to force takeover of the device, if it's already locked
    
        @rtype:   bool
        @return:  If the locking of input was successful
        """
        ConsolePrint("[Function: LockInput (inputNumber: " + str(inputNumber) + ", takeover: " + str(takeover) + ")]", isVerboseOutput=True)

        try:
            # Connected?
            if self.Connected:
    
                # Var, if lock override is enabled
                lockoverride = False
    
                # See if lock override is enabled
                option = self.DTB.getParameter(ParameterCodes.GPIO4_Control, 1)
                if 0 != (option & 0x0100):
                    lockoverride = True
    
                # Enumerate accounts
                accounts = self.DTB.enumerateUsers()
    
                # Extract the administrator account and password
                for userEntry in accounts:
                    if -1 == userEntry.lower().find("local administrator"):
                        continue
                    token = userEntry.split(",")
                    self.userAccount = token[0]
                    self.userPassword = token[2]
                    break
    
                # This is necessary to work on Python 2.7
                if sys.version_info < (3, 0):
                    self.userAccount = self.userAccount.encode('utf-8')
                    self.userPassword = self.userPassword.encode('utf-8')
    
                # If takeover, must unlock first
                if takeover:
                    self.DTB.unlock(self.userAccount, self.userPassword, inputNumber)
                self.DTB.lock(self.userAccount, self.userPassword, inputNumber)
    
                # Lock override requires only one lock to own all
                if lockoverride:
                    return
    
                # Success
                return True
    
            else:
                # Not connected
                ConsolePrint("*** ERROR *** Failed to lock input on device -- Osprey not connected!")
                return False
        except:
            ConsolePrint("*** ERROR *** Failed to lock input on device")
            return False
        
    def LockAllInputs(self, takeover):
        """
        Lock all inputs on the connected Osprey
    
        @type  takeover: bool
        @param takeover: Whether or not to force takeover of the device, if it's already locked
    
        @rtype:   bool
        @return:  If the locking of all inputs was successful
        """
        ConsolePrint("[Function: LockAllInputs]", isVerboseOutput=True)

        try:
            # Connected?
            if self.Connected:
    
                # Var, if lock override is enabled
                lockoverride = False
    
                # See if lock override is enabled
                option = self.DTB.getParameter(ParameterCodes.GPIO4_Control, 1)
                if 0 != (option & 0x0100):
                    lockoverride = True
    
                # Loop through all inputs
                for i in range(0, 3):
                    # Lock input
                    self.LockInput(i, takeover)
    
                    # Lock override requires only one lock to own all
                    if lockoverride:
                        return
    
                # Success
                return True
    
            else:
                # Not connected
                ConsolePrint("*** ERROR *** Failed to lock all inputs on device -- Osprey not connected!")
                return False

        except Exception as ex:
            ConsolePrintError("Exception locking all inputs on device!", ex)
            return False
        
    def UnlockInput(self, inputNumber):
        """
        Unlock an input on the connected Osprey
    
        @type  inputNumber: int
        @param inputNumber: The input number to unlock (where 0 = The SOM, for all configuration settings; 1 = PHA, MSS, LIST, & TLIST; 2 = MCS)
    
        @rtype:   bool
        @return:  If the unlocking of the input was successful
        """
        ConsolePrint("[Function: UnlockInput (inputNumber: " + str(inputNumber) + ")]", isVerboseOutput=True)

        try:
            # Connected?
            if self.Connected:
    
                # Unlock input
                self.DTB.unlock(self.userAccount, self.userPassword, inputNumber)
    
                # Success
                return True
    
            else:
                # Not connected
                ConsolePrint("*** ERROR *** Failed to unlock input on device -- Osprey not connected!")
                return False
        except:
            ConsolePrint("*** ERROR *** Failed to unlock input on device")
            return False
        
    def UnlockAllInputs(self):
        """
        Unlock all inputs on the connected Osprey
    
        @rtype:   bool
        @return:  If the unlocking of all inputs was successful
        """
        ConsolePrint("[Function: UnlockAllInputs]", isVerboseOutput=True)

        try:
            # Connected?
            if self.Connected:
    
                # Loop through all inputs
                for i in range(0, 3):
                    # Unlock input
                    self.UnlockInput(i)
    
                # Success
                return True
    
            else:
                # Not connected
                ConsolePrint("*** ERROR *** Failed to unlock all inputs on device -- Osprey not connected!")
                return False
        except:
            ConsolePrint("*** ERROR *** Failed to unlock all inputs on device")
            return False
        
    def HVPS_Enable(self, voltage_setpoint=-1):
        """
        Enable the high voltage power supply (HVPS) of the Osprey, with a set voltage if a standard (non-stabilized) probe is attached.
    
        NOTE:
            For stabilized probes, no argument is required, although an error will be thrown if called without a voltage argument for a standard probe.
    
        @type  voltage_setpoint: int
        @param voltage_setpoint: The high voltage set point, typically 800 for 2"x2" NaI probes and 750 for 1.5"x1.5" LaBr probes
    
        @rtype:   bool
        @return:  If the high voltage setting was successful
        """
        ConsolePrint("[Function: HVPS_Enable]", isVerboseOutput=True)
    
        # Connected?
        if self.Connected is True:
    
            # Stabilized probe identifier bit masks
            Stabilized_Probe_Busy = 0x00080000
            Stabilized_Probe_OK = 0x00100000
    
            # Is a stabilized probe attached?
            dtb_status = self.DTB.getParameter(ParameterCodes.Input_Status, self.dtbInput)
            if (dtb_status & Stabilized_Probe_OK) != Stabilized_Probe_OK:
    
                # No stabilized probe detected
                ConsolePrint("[HVPS: Unstabilized probe detected]", isVerboseOutput=True)
    
                # Voltage already enabled?
                if self.DTB.getParameter(ParameterCodes.Input_VoltageStatus, self.dtbInput) is False:
    
                    # Got a valid voltage?
                    if voltage_setpoint <= 0 or voltage_setpoint > 1300:
                        ConsolePrint("*** ERROR *** Invalid voltage setpoint for standard probe -- Got '" + str(voltage_setpoint) + " V'")
                        return False
    
                    # Set the HVPS setpoint
                    ConsolePrint("Setting voltage to " + str(voltage_setpoint) + " V...", isVerboseOutput=False)
                    self.DTB.setParameter(ParameterCodes.Input_Voltage, int(voltage_setpoint), self.dtbInput)
    
                    # Enable the HVPS
                    ConsolePrint("Enabling HVPS...", isVerboseOutput=False)
                    self.DTB.setParameter(ParameterCodes.Input_VoltageStatus, True, self.dtbInput)
    
                    # Wait until voltage ramping is complete
                    wroteOnce = False
                    while self.DTB.getParameter(ParameterCodes.Input_VoltageRamping, self.dtbInput) is True:
                        if not wroteOnce:
                            ConsolePrint("HVPS ramp-up...", isVerboseOutput=False)
                            wroteOnce = True
                        time.sleep(2)
    
                    # Unstabilized probe ready
                    ConsolePrint("HVPS enabled!", isVerboseOutput=False)
                    return True
    
                else:
    
                    # Unstabilized probe already ready
                    ConsolePrint("HVPS already enabled!", isVerboseOutput=False)
                    return True
    
            else:
    
                # Stabilized probe detected
                ConsolePrint("[HVPS: Stabilized probe detected]", isVerboseOutput=True)
    
                # Waiting for stabilized probe?
                if (dtb_status & Stabilized_Probe_Busy) == Stabilized_Probe_Busy:
                    ConsolePrint("Stabilized probe busy...", isVerboseOutput=False)
                    while (dtb_status & Stabilized_Probe_Busy) == Stabilized_Probe_Busy:
                        dtb_status = self.DTB.getParameter(ParameterCodes.Input_Status, self.dtbInput)
                        time.sleep(2)
    
                # Stabilized probe ready
                ConsolePrint("Stabilized probe ready!", isVerboseOutput=False)
                return True
    
        else:  # Not connected
    
            ConsolePrint("*** ERROR *** Cannot enable HVPS -- Osprey not connected!")
            return False
        
    def HVPS_Disable(self):
        """
        Disable the high voltage power supply (HVPS) of the Osprey.
    
        NOTE:
            For stabilized probes, an error may be thrown.
    
        @rtype:   bool
        @return:  If disabling the HVPS was successful
        """
        ConsolePrint("[Function: HVPS_Disable]", isVerboseOutput=True)
    
        # Connected?
        if self.Connected is True:
    
            # Stabilized probe identifier bit masks
            #Stabilized_Probe_Busy = 0x00080000
            Stabilized_Probe_OK = 0x00100000
    
            # Is a stabilized probe attached?
            dtb_status = self.DTB.getParameter(ParameterCodes.Input_Status, self.dtbInput)
            if (dtb_status & Stabilized_Probe_OK) != Stabilized_Probe_OK:
    
                # No stabilized probe detected
                ConsolePrint("[HVPS: Unstabilized probe detected]", isVerboseOutput=True)
    
                # Disable the HVPS
                ConsolePrint("Disabling HVPS...", isVerboseOutput=False)
                self.DTB.setParameter(ParameterCodes.Input_VoltageStatus, False, self.dtbInput)
    
                # Wait until voltage ramping is complete
                ConsolePrint("HVPS ramp-down...", isVerboseOutput=False)
                while self.DTB.getParameter(ParameterCodes.Input_VoltageRamping, self.dtbInput) is True:
                    time.sleep(2)
    
                # Unstabilized probe ready
                ConsolePrint("HVPS disabled!", isVerboseOutput=False)
                return True
    
            else:
    
                # Stabilized probe detected
                ConsolePrint("[HVPS: Stabilized probe detected]", isVerboseOutput=True)
    
                # Stabilized probe ready
                ConsolePrint("Unable to disable HVPS for stabilized probey!", isVerboseOutput=False)
                return True
    
        else:  # Not connected
    
            ConsolePrint("*** ERROR *** Cannot disable HVPS -- Osprey not connected!")
            return False

    def ADC_SetChannelCount(self, channelCount: int):
        """
        Set the number of ADC channels.

        @rtype:   bool
        @return:  If the number of channels was successfully set
        """
        ConsolePrint("[Function: ADC_SetChannelCount]", isVerboseOutput=True)

        if self.Connected:

            # Validate input
            if channelCount not in [256, 512, 1024, 2048]:
                channelCount = 1024
                ConsolePrint("Invalid channel count ({}) provided! Number of channels clamped to 1024".format(channelCount))

            # Set gains
            self.DTB.setParameter(ParameterCodes.Input_NumberOfChannels, channelCount, 1)
            return True

        else:  # Not connected

            ConsolePrint("*** ERROR *** Cannot set ADC channel count -- Osprey not connected!")
            return False

    def Amplifier_SetGains(self, gainCoarse: int, gainFine: float):
        """
        Set the amplifier gains individually.

        @rtype:   bool
        @return:  If the gain was successfully set
        """
        ConsolePrint("[Function: Amplifier_SetGains]", isVerboseOutput=True)

        if self.Connected:

            # Validate inputs
            if gainCoarse not in [1, 2, 4, 8]:
                ConsolePrint("Invalid coarse gain value (x{}) provided! Coarse gain must be x1, x2, x4, or x8.".format(gainCoarse))
                return False
            if (gainFine < 1.0) or (gainFine > 5.0):
                ConsolePrint("Invalid fine gain value (x{:.5f}) provided! Fine gain must be between x1.0-5.0.".format(gainFine))
                return False

            # Ensure fine gain is a multiple of 0.00004
            gainFine = round((gainFine / 0.00004), 5) * 0.00004

            # Set gains
            self.DTB.setParameter(ParameterCodes.Input_CoarseGain, gainCoarse, 1)
            self.DTB.setParameter(ParameterCodes.Input_FineGain, gainFine, 1)
            return True

        else:  # Not connected

            ConsolePrint("*** ERROR *** Cannot set gains -- Osprey not connected!")
            return False

    def Amplifier_SetGain(self, gainTotal: float):
        """
        Set the amplifier gain as a total gain value.

        @rtype:   bool
        @return:  If the gain was successfully set
        """
        ConsolePrint("[Function: Amplifier_SetGain]", isVerboseOutput=True)

        if self.Connected:

            # Validate gain
            if gainTotal < 1.0:
                ConsolePrint("Invalid total gain value (x{:.2f}) provided! Gain cannot be below x1.0.".format(gainTotal))
                return False
            if gainTotal > 40.0:
                ConsolePrint("Invalid total gain value (x{:.2f}) provided! Gain cannot be above x40.0.".format(gainTotal))
                return False

            # Determine best coarse and fine gain values
            if (gainTotal / 8.0) >= 1.0:
                coarseGain = 8.0
            elif (gainTotal / 4.0) >= 1.0:
                coarseGain = 4.0
            elif (gainTotal / 2.0) >= 1.0:
                coarseGain = 2.0
            else:
                coarseGain = 1.0
            fineGain = gainTotal / coarseGain

            # Ensure fine gain is a multiple of 0.00004
            fineGain = round((fineGain / 0.00004), 5) * 0.00004

            # Set gains
            self.DTB.setParameter(ParameterCodes.Input_CoarseGain, coarseGain, 1)
            self.DTB.setParameter(ParameterCodes.Input_FineGain, fineGain, 1)
            return True

        else:  # Not connected

            ConsolePrint("*** ERROR *** Cannot set gain -- Osprey not connected!")
            return False

    def Amplifier_SetLLD(self, lld_percent: Optional[float]):
        """
        Set the LLD.

        :param lld_percent: The LLD value, in percent (0-100.0, increments of 0.1), or None to enable automatic LLD.

        :return: If the gain was successfully set
        """
        ConsolePrint("[Function: Amplifier_SetLLD({})]".format(lld_percent), isVerboseOutput=True)

        if self.Connected:

            # Validate LLD
            if lld_percent is None:
                # Automatic mode
                self.DTB.setParameter(ParameterCodes.Input_LLDmode, OspreyEnums.AutomaticManual.Automatic.value, 1)
                return True
            elif lld_percent < 0:
                ConsolePrint("Invalid LLD percent value (x{:.2f}) provided! LLD cannot be below zero.".format(lld_percent))
                return False
            elif lld_percent > 100:
                ConsolePrint("Invalid LLD percent value (x{:.2f}) provided! LLD cannot be above 100.".format(lld_percent))
                return False
            else:
                # Manual mode
                self.DTB.setParameter(ParameterCodes.Input_LLDmode, OspreyEnums.AutomaticManual.Manual.value, 1)
                self.DTB.setParameter(ParameterCodes.Input_LLD, lld_percent, 1)
                return True

        else:  # Not connected

            ConsolePrint("*** ERROR *** Cannot set LLD -- Osprey not connected!")
            return False

    def TFTP_Enable(self):
        """
        Enable the TFTP server on the Osprey.
    
        @rtype:   bool
        @return:  If the TFTP server was successfully enabled
        """
        ConsolePrint("[Function: TFTP_Enable]", isVerboseOutput=True)
    
        try:
            if self.Connected:
                # Enable TFTP server
                self.DTB.setParameter(ParameterCodes.Network_FTP_Enable, 1, 0)
                strNetwork_FTP_Enable = str(self.DTB.getParameter(ParameterCodes.Network_FTP_Enable, 0))
                ConsolePrint("TFTP server enabled: " + strNetwork_FTP_Enable, isVerboseOutput=False)
                return strNetwork_FTP_Enable.lower() in ("true", "yes", "1")
            else:  # Not connected
                ConsolePrint("*** ERROR *** Cannot enable TFTP server -- Osprey not connected!")
                return False
        except:
            ConsolePrint("*** ERROR *** Failed to enable TFTP server on device")
            return False
        
    def TFTP_Disable(self):
        """
        Disable the TFTP server on the Osprey.
    
        @rtype:   bool
        @return:  If the TFTP server was successfully disabled
        """
        ConsolePrint("[Function: TFTP_Disable]", isVerboseOutput=True)
    
        try:
            if self.Connected:
                # Enable TFTP server
                self.DTB.setParameter(ParameterCodes.Network_FTP_Enable, 0, 0)
                strNetwork_FTP_Enable = str(self.DTB.getParameter(ParameterCodes.Network_FTP_Enable, 0))
                ConsolePrint("TFTP server enabled: " + strNetwork_FTP_Enable, isVerboseOutput=False)
                return strNetwork_FTP_Enable.lower() in ("false", "no", "0")
            else:  # Not connected
                ConsolePrint("*** ERROR *** Cannot disable TFTP server -- Osprey not connected!")
                return False
        except:
            ConsolePrint("*** ERROR *** Failed to disable TFTP server on device")
            return False
        
    def TFTP_Status(self):
        """
        Get the status of the TFTP server on the Osprey.
    
        @rtype:   bool
        @return:  If the TFTP server is enabled
        """
        ConsolePrint("[Function: TFTP_Status]", isVerboseOutput=True)
    
        try:
            if self.Connected:
                # Get status of TFTP server
                strNetwork_FTP_Enable = str(self.DTB.getParameter(ParameterCodes.Network_FTP_Enable, 0))
                return strNetwork_FTP_Enable.lower() in ("true", "yes", "1")
            else:  # Not connected
                ConsolePrint("*** ERROR *** Cannot get status of TFTP server -- Osprey not connected!")
                return False
        except:
            ConsolePrint("*** ERROR *** Failed to get status of TFTP server on device")
            return False
        
    def PresetTime_Set(self, preset_mode: OspreyEnums.PresetType, preset_time_sec=-1):
        """
        Set a preset time.
    
        @type  preset_mode: OspreyEnums.PresetType
        @param preset_mode: The preset to use for the acquisition.
    
        @type  preset_time_sec: double
        @param preset_time_sec: The preset time, in seconds
    
        @rtype:   bool
        @return:  If the preset time was successfully set
        """
        ConsolePrint("[Function: PresetTime_Set]", isVerboseOutput=True)
    
        if self.Connected:

            #   Osprey SDK 'PresetModes':
            #       PresetNone      0   No preset / count indefinitely
            #       PresetLiveTime  1   Count until live time limit
            #       PresetRealTime  2   Count until real time limit
            #       PresetSweeps    4   Count until sweeps limit
            #       PresetIntegral  8   Count until integral limit (requires start and stop region)
            if preset_mode == OspreyEnums.PresetType.Continuous:
                self.DTB.setParameter(ParameterCodes.Preset_Options, PresetModes.PresetNone, self.dtbInput)
                self.DTB.setParameter(ParameterCodes.Preset_Live, -1.0, self.dtbInput)
                return True
            elif preset_mode == OspreyEnums.PresetType.LiveTime:
                self.DTB.setParameter(ParameterCodes.Preset_Options, PresetModes.PresetLiveTime, self.dtbInput)
                self.DTB.setParameter(ParameterCodes.Preset_Live, float(preset_time_sec), self.dtbInput)
                return True
            elif preset_mode == OspreyEnums.PresetType.RealTime:
                self.DTB.setParameter(ParameterCodes.Preset_Options, PresetModes.PresetRealTime, self.dtbInput)
                self.DTB.setParameter(ParameterCodes.Preset_Real, float(preset_time_sec), self.dtbInput)
                return True
            else:
                ConsolePrint("*** ERROR *** Unknown preset mode")
                return False
    
        else:  # Not connected
    
            ConsolePrint("*** ERROR *** Cannot set preset time -- Osprey not connected!")
            return False
        
    def Acquisition_Start(self):
        """
        Start acquiring data to the desired preset.

        @rtype:   bool
        @return:  If the acquisition was successfully started
        """
        ConsolePrint("[Function: Acquisition_Start]", isVerboseOutput=True)
    
        if self.Connected:

            # Clear previous acquisition
            self.Acquisition_Clear()
    
            # Start acquiring
            self.DTB.control(CommandCodes.Start, self.dtbInput)
            return True
    
        else:  # Not connected
    
            ConsolePrint("*** ERROR *** Cannot start acquisition -- Osprey not connected!")
            return False
        
    def Acquisition_Stop(self):
        """
        Stop acquiring data.
    
        @rtype:   bool
        @return:  If the acquisition was successfully stopped
        """
        ConsolePrint("[Function: Acquisition_Stop]", isVerboseOutput=True)
    
        if self.Connected:
    
            # Stop acquiring
            self.DTB.control(CommandCodes.Stop, self.dtbInput)
            return True
    
        else:  # Not connected
    
            ConsolePrint("*** ERROR *** Cannot start acquisition -- Osprey not connected!")
            return False
        
    def Acquisition_Clear(self):
        """
        Clears any acquired data.
    
        @rtype:   bool
        @return:  If the acquisition data was successfully cleared
        """
        ConsolePrint("[Function: Acquisition_Clear]", isVerboseOutput=True)
    
        if self.Connected:
    
            # Clear data
            self.DTB.control(CommandCodes.Clear, self.dtbInput)
            return True
    
        else:  # Not connected
    
            ConsolePrint("*** ERROR *** Cannot clear acquisition data -- Osprey not connected!")
            return False
        
    def Acquisition_StopAll(self):
        """
        Disables/stops all acquisitions.
    
        NOTE:
            Called typically after connection to ensure Osprey is idle before use.
    
        @rtype:   bool
        @return:  If all acquisitions were successfully stopped
        """
        ConsolePrint("[Function: Acquisition_StopAll]", isVerboseOutput=True)
    
        if self.Connected:
    
            # Disable all acquisitions
            try:
                self.DTB.control(CommandCodes.Stop, self.dtbInput)
            except:
                pass
            #Abort acquisition (only needed for MSS or MCS collections)
            try:
                self.DTB.control(CommandCodes.Abort, self.dtbInput)
            except:
                pass
            #Stop SCA collection
            try:
                self.DTB.setParameter(ParameterCodes.Input_SCAstatus, 0, self.dtbInput)
            except:
                pass
            #Stop Aux counter collection
            try:
                self.DTB.setParameter(ParameterCodes.Counter_Status, 0, self.dtbInput)
            except:
                pass
            return True
    
        else:  # Not connected
    
            ConsolePrint("*** ERROR *** Cannot disable acquisitions -- Osprey not connected!")
            return False
        
    def IsAcquiring(self):
        """
        Checks if Osprey is currently acquiring data.
    
        @rtype:   bool
        @return:  If the Osprey is currently acquiring data
        """
        ConsolePrint("[Function: IsAcquiring]", isVerboseOutput=True)
    
        if self.Connected:
    
            # Status bit mask
            Busy = 0x00000001
    
            # Is the Osprey busy acquiring?
            dtb_status = self.DTB.getParameter(ParameterCodes.Input_Status, self.dtbInput)
            if (dtb_status & Busy) == Busy:
                return True
            else:
                return False
    
        else:  # Not connected
    
            ConsolePrint("*** ERROR *** Cannot check Osprey status -- Osprey not connected!")
            return False
        
    def GetData_CountRate(self):
        """
        Gets the current count rate from the Osprey.
    
        @rtype:   int or bool
        @return:  The current count rate, or False if request failed
        """
        ConsolePrint("[Function: Data_GetCountRate]", isVerboseOutput=True)
    
        if self.Connected:
    
            # Get ICR from the Osprey
            return self.DTB.getParameter(ParameterCodes.Input_Countrate, self.dtbInput)
    
        else:  # Not connected
    
            ConsolePrint("*** ERROR *** Cannot get count rate -- Osprey not connected!")
            return False
        
    def GetData_PHA(self, memory_group=1) -> Optional[SpectrumData]:
        """
        Gets the PHA spectrum from the Osprey's stored memory group.
    
        The spectral data is returned as a named tuple with the following attributes:
    
            SpectralData.spectrum : (list) the individual channel data
            SpectralData.integral : (int) the integral of the spectrum
            SpectralData.liveTime : (double) the elapsed live time
            SpectralData.realTime : (double) the elapsed real time
    
        @type  memory_group: int
        @param memory_group: The memory group to get the stored spectrum data
        """
        ConsolePrint("[Function: Data_GetSpectrum]", isVerboseOutput=True)
    
        if self.Connected:
    
            # Get spectrum data from the Osprey
            timestamp = datetime.datetime.utcnow()
            spectrumdata = self.DTB.getSpectralData(self.dtbInput, group=memory_group)
    
            # Get the channel data
            channeldata = spectrumdata.getSpectrum().getCounts()

            # Get the live/real-time data
            liveTime = spectrumdata.getLiveTime() / 1.0e6
            realTime = spectrumdata.getRealTime() / 1.0e6
    
            # Create and return structure
            return SpectrumData(timestamp, liveTime, realTime, channeldata)
    
        else:  # Not connected
    
            ConsolePrint("*** ERROR *** Cannot get spectrum -- Osprey not connected!")
            return None
        
    def MassStorageMode_Enable(self):
        """
        Enable mass storage mode on the Osprey so that it appears as a USB drive for file modifications.
        A power cycle is required to exit mass storage mode.
        Legacy Osprey MCAs are not supported.

        @rtype:   bool
        @return:  If mass storage mode was successfully enabled
        """
        ConsolePrint("[Function: MassStorageMode_Enable]", isVerboseOutput=True)

        try:
            if self.Connected:
                # Enable mass storage mode
                ConsolePrint("Entering mass storage mode...", isVerboseOutput=False)
                self.DTB.control(59, self.dtbInput)
                return True
            else:  # Not connected
                ConsolePrint("*** ERROR *** Cannot enter mass storage mode -- Osprey not connected!")
                return False
        except:
            ConsolePrint("*** ERROR *** Failed to enter mass storage mode on device")
            return False


#========================================================================================================
#=== UTILITY FUNCTIONS ==================================================================================

def VerboseOutput(enabled):
    """
    Enable or disable verbose logging output of the library.
    """
    global _loggingVerbose
    _loggingVerbose = enabled


def ConsolePrint(message, isVerboseOutput=False):
    global _logger

    if _logger is not None:
        if isVerboseOutput:
            _logger.debug(message) if _loggingVerbose else None
        else:
            _logger.info(message)
    else:
        if isVerboseOutput:
            print(('{0:<' + str(_loggingPrefixPadding) + '}{1:<15}').format(_loggingPrefix, message)) if _loggingVerbose else None
        else:
            print(('{0:<' + str(_loggingPrefixPadding) + '}{1:<15}').format(_loggingPrefix, message))


def ConsolePrintError(message, exception=None):
    global _logger

    if _logger is not None:
        if exception is not None:
            _logger.exception(message)
            _logger.exception(str(exception))
        else:
            _logger.error(message)
    else:
        print(('{0:<' + str(_loggingPrefixPadding) + '}{1:<15}').format("** " + _loggingPrefix, "*** " + str(message)))
        if exception is not None:
            traceback.print_exc()


#========================================================================================================
#=== EXECUTION / DIAGNOSTICS ============================================================================
#========================================================================================================

# Library file executed directly?
if __name__ == '__main__':

    # Run diagnostic test...
    ConsolePrint("=========================================")
    ConsolePrint("=========  O s p r e y   L i b  =========")
    ConsolePrint("========= D I A G N O S T I C S =========")
    ConsolePrint("=========================================")

    # Print the version information
    ConsolePrint("pyOsprey Library Version : v " + versionLib)

    ConsolePrint("                 =-=-=                   ")

    # Create new device
    osprey = Osprey()

    # Attempt to connect
    if osprey.Connect(method=diagnostics_ConnectionMethod, ip_address=diagnostics_IP_Override):

        # Enable TFTP server?
        if diagnostics_EnableTFTP:
            osprey.TFTP_Enable()

        # Disable TFTP server?
        if diagnostics_DisableTFTP:
            osprey.TFTP_Disable()

        # Get status of TFTP server
        tftpStatus = osprey.TFTP_Status()
        ConsolePrint("TFTP server enabled?: " + str(tftpStatus), isVerboseOutput=False)

        # Enter mass storage mode?
        if diagnostics_EnableMassStorage:
            osprey.MassStorageMode_Enable()

        # Perform firmware update?
        if diagnostics_FirmwareUpdate:
            try:
                if osprey.Connected:
                    ConsolePrint("Performing firmware update...", isVerboseOutput=False)
                    osprey.DTB.control(31, input)
                else:  # Not connected
                    ConsolePrint("*** ERROR *** Cannot perform firmware update -- not connected!")
            except Exception as e:
                ConsolePrint("*** ERROR *** Failed to perform firmware update on device")
                ConsolePrint(str(e))

        # Acquisition test?
        if (not diagnostics_EnableTFTP) and (not diagnostics_DisableTFTP) and (not diagnostics_EnableMassStorage) and diagnostics_AcquireSpectrum:

            # Enable the HVPS
            success = osprey.HVPS_Enable(voltage_setpoint=750)

            # Start an acquisition for a preset live time
            ConsolePrint("Acquire for " + str(diagnostics_LiveTime_sec) + " seconds (Preset live time)...")
            if osprey.Acquisition_StopAll():
                if osprey.PresetTime_Set(preset_mode=OspreyEnums.PresetType.LiveTime, preset_time_sec=diagnostics_LiveTime_sec):
                    osprey.Acquisition_Start()

            # Wait for acquisition to complete
            waitTime_sec = 0
            while osprey.IsAcquiring():
                time.sleep(1)
                waitTime_sec += 1
                ConsolePrint("... Elapsed time: " + str(waitTime_sec) + " sec")

            #TODO: Check if Osprey still connected... need 'IsOK' function

            # Get data
            icr = osprey.GetData_CountRate()
            spectrumData = osprey.GetData_PHA()
            if spectrumData is not None:

                ConsolePrint("Acquisition complete!")
                ConsolePrint("Actual live time : " + str(round(spectrumData.LiveTime_sec, 3)))
                ConsolePrint("Actual real time : " + str(round(spectrumData.RealTime_sec, 3)))
                if spectrumData.LiveTime_sec > 0:
                    ConsolePrint("Total counts     : " + str(spectrumData.GrossCounts) + " (" + str(round(spectrumData.GrossCounts / spectrumData.LiveTime_sec, 1)) + " cps)")
                else:
                    ConsolePrint("Total counts     : " + str(spectrumData.GrossCounts) + " (? cps)")
                ConsolePrint("Overload counts  : " + "+" + str(spectrumData.Spectrum[-1]) + " counts")
                ConsolePrint("Spectrum maxima  : " + str(max(spectrumData.Spectrum[:-1])) + " counts")

                # Histogram?
                if histogramSupport and diagnostics_Histogram_enabled:
                    ConsolePrint("Spectrum:")
                    # Print histogram
                    histogram.Print_Histogram(spectrumData.Spectrum, bincount=diagnostics_Histogram_bins, height=diagnostics_Histogram_height, markerChar='*')

            # Disconnect
            osprey.Disconnect()

    else:

        ConsolePrint("Unable to connect to Osprey! Check IP settings")

    ConsolePrint("=========================================")

    # End of diagnostics
    ConsolePrint("Diagnostics COMPLETE!")
    ConsolePrint("Exiting...")
