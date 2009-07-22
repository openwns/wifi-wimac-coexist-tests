""" Module WiMAX Parameters - 802.16e
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module is a concentrate collection of all necessary configuration
    parameters for a WiMAX system.

    The parameters, wich are commented out are actual not in use by
    the WiMAC module.

    The following parameters are mainly for WiMAX mobility IEEE802.16e.
    They are mainly inherit form the paper listed under 'verified 1'.

    Verification:
          verified 0: not verified
          verified 1: WiMAX Forum - 'Mobile WiMAC Part I:
                      A Technical Overview and Performance Evaluation' 
                      (page31) [v2.4]
          verified 2: Winner - 'Final Report on Link Level and System Level Channel Models'
                      (page 26) [D5.4 v. 1.00]
"""

from math import *
from openwns.pyconfig import Frozen
from openwns import dBm, dB

def getSamplingFrequency(bandwidth, cyclicPrefix):
    """
        bandwidth in MHz
    """

    # sampling factor refering to IEEE802.16 8.3.2.4 
    if bandwidth%1.75 == 0:
        n = 8.0/7;
    elif bandwidth%1.5 == 0:
        n = 86.0/75;
    elif bandwidth%1.25 == 0:
        n = 144.0/125;
    elif bandwidth%2.75 == 0:
        n = 316.0/275;
    elif bandwidth%2.0 == 0:
        n = 57.0/50
    else:
        n = 8.0/7;

    return floor(n * bandwidth * 1e+6 / 8000) * 8000


###############################################################################
# System Paraeter                                                             #
###############################################################################

class ParametersSystem(Frozen):
                                      # ---Comments----------------------------
    centerFrequency = 2500 # [MHz]    # (verified 1)
    bandwidthChannel = 10  # [MHz]    # (verified 1)
#   duplex = 'TDD'                    # Only for completing

    cellRadius  = 1617   # [meter]    # (verified 1)
    clusterSize = 7      # [cells per cluster] # (verified 0)

    distanceUTtoAPmin = 36 # [meter]  # (verified 1)

    heightAP  = 32   # [meter]        # (verified 1)
    heightFRS = None # [meter]        # No information about in 'verified 1'
    heightUT  = 1.5  # [meter]        # (verified 1)

    antennaPattern = 70 # [degree]    # (verified 1) (-3dB) with 20dB front-to-back ratio

    antennaGainAP  = 15   # [dBi]     # (verified 1)
    antennaGainFRS = None # [dBi]     # No information about in 'verified 1'
    antennaGainUT  = -1   # [dBi]     # (verified 1)

    numberOfAntennaAPTx  = 2          # (verified 1)
    numberOfAntennaAPRx  = 2          # (verified 1)
    numberOfAntennaFRSTx = None       # No information about in 'verified 1'
    numberOfAntennaFRSRx = None       # No information about in 'verified 1'
    numberOfAntennaUTTx  = 1          # (verified 1)
    numberOfAntennaUTRx  = 2          # (verified 1)

    txPowerAP  = dBm(43) # [dBm]      # (verified 1)
    txPowerFRS = None    # [dBm]      #
    txPowerUT  = dBm(23) # [dBm]      # (verified 1)

    noiseFigureAP  = dB(4) # [dB]     # (verified 1)
    noiseFigureFRS = None  # [dB]     # No information about in 'verified 1'
    noiseFigureUT  = dB(7) # [dB]     # (verified 1)



###############################################################################
# OFDMA Parameters                                                            #
###############################################################################

class ParametersOFDMA(Frozen):
    bandwidthChannelSystem = ParametersSystem.bandwidthChannel
    # [MHz]
    ######

    gardUsefulRatio = 1.0/8
    # G=Tg/Tb
    # Possible values: [1/4, 1/8, 1/16, 1/32]
    # (varified 1)
    ######

    samplingFrequency = getSamplingFrequency(bandwidthChannelSystem, gardUsefulRatio)
    # [Hz]   Fp
    ######

    fftSize = 1024
    # Nfft
    # (varified 1)
    ######

    subCarrierFrequencySpacing = 10.94
    # [kHz]
    # Not used at the moment by the WiMAC
    # (varified 1)
    ######

    usefulSymbolTime = float(fftSize) / float(samplingFrequency)
    # [sec]   Tb=Nfft/Fp
    ######

    guardTime = float(usefulSymbolTime) * float(gardUsefulRatio)
    # [sec]   (Tg=Tb*Cp)
    ######

    symbolDuration = float(usefulSymbolTime) + float(guardTime)
    # [sec]   (Ts=Tb+Tg)
    ######

    frameDuration = 0.005
    # [sec]   (Tf)
    ######

    symbolsFrame = int(floor(float(frameDuration) / float(symbolDuration)))
    # [symbol](Tf/Ts)
    # Symbols per frame
    ######

    dlUlRatio = 0.5
    # DL ratio of the data frame
    # (varified 0)
    ######

    puscDLSubCarriersNull  = 184
    puscDLSubCarriersPilot = 120
    puscDLSubCarriersData  = fftSize - puscDLSubCarriersNull - puscDLSubCarriersPilot
    puscDLSubChannels = 30
    # --Downlink Partially Used Sub-Channel--
    #   (varified 1)
    ######

    puscULSubCarriersNull  = 184
    puscULSubCarriersPilot = 280
    puscULSubCarriersData  = fftSize - puscULSubCarriersNull - puscULSubCarriersPilot
    puscULSubChannels = 35
    # --Uplink Partially Used Sub-Channel--
    #   (varified 1)
    ######

    rangingSlots = 3
    rangingSlotLength = 8 # [symbols]
    # Ranging contention access configuration
    # Reminder: Raning phase is located in the uplink frame phase
    # (verified 0)
    # old rangingSlots values 5; example scenario=3; (mpr used 4)
    ######

    bandwidthSlots = 0
    bandwidthSlotLength = 0  # [symbols]
    # Bandwidth contention access configuration
    # Reminder: Bandwidth phase is located in the uplink frame phase
    # (verified 0)
    ######

    subFrameRatio = 0
    #  sub frame ratio of the uplink frame phase
    #  Reminder: Sub frame is located in the uplink frame phase.
    #####

    makeshiftBandwidthChannelSystem = bandwidthChannelSystem  * float(puscDLSubCarriersData) / float(fftSize)
    makeshiftSubCarriers = 1
    # !!!! Workaround !!!!!
    # The bandwidth has been reduced since "23 MHz" are split up among
    # "256" sub carrier but only "192" of them serve as means for data transmission.
    # This means we're using the receiver/transmitter in an OFDM  style.
    # "dlPuscSubcarriersData" data sub carrier are available in reality but
    # since we transmit on all sub carrier at the same time we regard this as one big sub band.
    ######


###############################################################################
#  Propagation Model                                                          #
###############################################################################

from openwns.interval import Interval
import rise.scenario.Propagation
import rise.scenario.Pathloss as Pathloss
import rise.scenario.Shadowing as Shadowing
import rise.scenario.FastFading as FastFading

class ParametersPropagation(Frozen):

    ###### Define Propagation Models ##########################################

    __ClLOS = rise.scenario.Propagation.Configuration(
        pathloss = Pathloss.SingleSlope(validFrequencies = Interval(4000, 6000),
                                    validDistances = Interval(2, 20000), # [m]
                                    offset = "41.9 dB",
                                    freqFactor = 0,
                                    distFactor = "23.8 dB",
                                    distanceUnit = "m", # nur fuer die Formel, nicht fuer validDistances
                                    minPathloss = "49.06 dB", # pathloss at 2m distance
                                    outOfMinRange = Pathloss.Constant("49.06 dB"), #Pathloss.FreeSpace(),
                                    outOfMaxRange = Pathloss.Deny()
                                    ),
        shadowing = Shadowing.No(),
        fastFading = FastFading.No())
    # (verified 2) Models suggested by hoy
    ######

    __ClNLOS = rise.scenario.Propagation.Configuration(
        pathloss = Pathloss.SingleSlope(validFrequencies = Interval(4000, 6000),
                                    validDistances = Interval(8, 5000), # [m]
                                    offset = "27.7 dB",
                                    freqFactor = 0,
                                    distFactor = "40.2 dB",
                                    distanceUnit = "m", # nur fuer die Formel, nicht fuer validDistances
                                    minPathloss = "64.0 dB", # pathloss at 8m distance
                                    outOfMinRange = Pathloss.Constant("64.0 dB"),
                                    outOfMaxRange = Pathloss.Deny()
                                    ),
        shadowing = Shadowing.No(),
        fastFading = FastFading.No())
    # (verified 2) Models suggested by hoy
    ######


    ##### Used Propagation Models   ############################################

    # AP <-> AP
    channelLinkAP2AP   = __ClLOS

    # AP <-> FRS
    channelLinkAP2FRS  = __ClLOS
    channelLinkFRS2AP  = __ClLOS

    # AP <-> UT
    channelLinkAP2UT   = __ClLOS
    channelLinkUT2AP   = __ClLOS

    # FRS <-> FRS
    channelLinkFRS2FRS = __ClLOS

    # FRS <-> UT
    channelLinkFRS2UT  = __ClLOS
    channelLinkUT2FRS  = __ClLOS

    # UT <-> UT
    channelLinkUT2UT   = __ClLOS
