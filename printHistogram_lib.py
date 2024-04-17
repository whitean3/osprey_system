# -*- coding: utf-8 -*-
"""
File:           printHistogram_lib.py
Description:    Library to generate and print a histogram to the terminal from a given list of data.
Creator:        Joshua A. Handley (2016)

Copyright (c) 2016 ACT. All rights reserved.
"""
# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=

# Get Python3 print() function
from __future__ import print_function

# Processing libs
import numpy as np

#========================================================================================================
#=== CONFIGURATION (User Configurable) ==================================================================

# Logging / Output
verboseOutput                   = False
outputPrefix                    = "Histogram:"
outputPrefixPadding             = 15

#========================================================================================================
#=== GLOBALS ============================================================================================

# -- Version information
versionLib                  = "1.0.0"

#=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
#=-= FUNCTIONS =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-

def Print_Histogram(datalist, bincount=48, height=10, markerChar='*'):
    """
    <Description>

    @type  arg1: string
    @param arg1: The...

    @rtype:   bool
    @return:  If...
    """
    # Calculate the bin width
    binwidth = len(datalist) / bincount

    # Create the bins of data
    bins = []
    for i in range(bincount + 1):
        bins.append(0)
    for i in range(len(datalist)):
        thisBinNum = int(i // binwidth)
        bins[thisBinNum] += datalist[i]

    # Get the maxima
    maxima = max(bins)

    # Got data?
    if maxima > 0:
        # Add histogram data line-by-line
        result = ""
        for y in range(height, 0, -1):
            for binnum in range(bincount):
                if (float(bins[binnum]) / float(maxima)) * height >= y:
                    result += markerChar
                else:
                    result += " "
                if binnum == bincount - 1:
                    result += "\n"

        # Add frames
        lines = result.split("\n")
        lines.pop()
        yscaleitems = []
        for l in range(len(lines)):
            yscaletick = np.ceil(float(height - l) / height * maxima)
            if yscaletick not in yscaleitems:
                lines[l] = "{:<5}".format(sizeof_fmt(yscaletick)) + " |" + lines[l] + "|"
                yscaleitems.append(yscaletick)
            else:
                lines[l] = "     " + " |" + lines[l] + "|"
        lines.insert(0, "       " + "_" * bincount + " ")
        lines.append("      |" + "=" * bincount + "|")
        lines.append("       0" + " " * (bincount - 3) + str(len(datalist)))
        result = "\n".join(lines)
    else:
        result = "*** No counts in histogram! ***"

    # Print the result
    print(result)


#========================================================================================================
#=== UTILITY FUNCTIONS ==================================================================================

def VerboseOutput(true_or_false):
    """
    Enable or disable verbose output of the library.

    """
    global verboseOutput

    if true_or_false is True:
        verboseOutput = True
    else:
        verboseOutput = False


def ConsolePrint(message, isVerboseOutput=False):
    if isVerboseOutput:
        print(('{0:<' + str(outputPrefixPadding) + '}{1:<15}').format(outputPrefix, message)) if verboseOutput else None
    else:
        print(('{0:<' + str(outputPrefixPadding) + '}{1:<15}').format(outputPrefix, message))


def sizeof_fmt(num, suffix=''):
    for unit in ['','k','M','B']:
        if abs(num) < 1000.0:
            return "%4.0f%s%s" % (num, unit, suffix)
        num /= 1000.0
    return "%4.0f%s%s" % (num, 'T', suffix)

#========================================================================================================
#=== EXECUTION / DIAGNOSTICS ============================================================================
#========================================================================================================

# Library file executed directly?
if __name__ == '__main__':
    ConsolePrint("")
