""" Module WiMAX Parameters - 802.16e
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module is a concentrate collection of all necessary configuration
    parameters for a WiMAX system.

    The parameters, wich are commented out are actual not in use by
    the WiMAC module.

    The following parameters are the original one, used by ComNets.

    Verification:
          verified 0: not verified
          verified 1: WiMAX Forum - 'Mobile WiMAC Part I:
                      A Technical Overview and Performance Evaluation' 
                      (page31) [v2.4]
          verified 2: Winner - 'Final Report on Link Level and System Level Channel Models'
                      (page 26) [D5.4 v. 1.00]
          verified 3: IEEE 802.16-2004 and/or IEEE 802.16e
          verified 4: WiMAX Forum System Evaluation Methodology
          verified 5: WiMAX System Profile
"""

from math import *
from openwns.pyconfig import Frozen
from openwns import dBm, dB

def getSamplingFrequencyOFDM(bandwidth, cyclicPrefix):
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

def getSamplingFrequencyOFDMA(bandwidth, cyclicPrefix):
    """
        bandwidth in MHz
    """

    # sampling factor refering to IEEE802.16e 8.4.2.3
    if bandwidth%1.75 == 0:
        n = 8.0/7;
    elif bandwidth%1.5 == 0:
        n = 28/25;
    elif bandwidth%1.25 == 0:
        n = 28/25;
    elif bandwidth%2.75 == 0:
        n = 28/25;
    elif bandwidth%2.0 == 0:
        n = 28/25;
    else:
        n = 8.0/7;

    return floor(n * bandwidth * 1e+6 / 8000) * 8000

def getFftSize(BW):

    if BW == 1.25:
        fft = 128;
    elif BW == 3.5:
        fft = 512;
    elif BW == 5:
        fft = 512;
    elif BW == 7:
        fft = 1024;
    elif BW == 8.75:
        fft = 1024;
    elif BW == 10:
        fft = 1024;
    elif BW == 20:
        fft = 2048;
    else:
        fft = 0;

    return fft


def getNumberOfChannels(subcarrierAllocation, fftSize):

    if subcarrierAllocation == 'AMC':
        if fftSize == 1024:
            Nsub = 16;
        elif fftSize == 512:
            Nsub = 8;
        elif fftSize == 128:
            Nsub = 2;
        else:
            Nsub = 0;
    else:
        # TODO implement this if PUSC/FUSC is used
        Nsub = 0;

    return Nsub

def getDataSubcarrierPerSubChannel(subcarrierAllocation, fftSize):

    if subcarrierAllocation == 'AMC':
        n = 48;
    else:
        # TODO implement this if PUSC/FUSC is used
        n = 0;

    return n

    subcarrierPerSubchannel = getDataSubcarrierPerSubChannel(subcarrierAllocation, fftSize)
    # verified 3 IEEE 7802.16e 8.4.6.3.1
    ###############################





###############################################################################
# System Parameters                                                           #
###############################################################################

class ParametersSystem(Frozen):
    height = {}
    numberOfAntennaRxTx = {}
    antennaArrayLayout = {}
    txPower = {}
    noiseFigure = {}                                      
                                      
                                      # ---Comments----------------------------
    centerFrequency = 5470  # [MHz]   # Not used at the moment by the WiMAC
                                      # implicitely modeled by the propagation model

    # radius of the cell including relays!
    cellRadius  = 750  # [meter]     # (verified 0)
    clusterOrder = 7                   # [cells per cluster]

    height['AP']  = 5.0  # [meter]        # (verified 0)
    height['FRS'] = 5.0  # [meter]        # (verified 0)
    height['UT']  = 1.5  # [meter]        # (verified 1)

    # in the future differentiate between Tx (SS:1) and Rx antennas (SS:2)
    numberOfAntennaRxTx['AP']  = 4        # (verified 0)
    numberOfAntennaRxTx['FRS'] = 4        # (verified 0)
    numberOfAntennaRxTx['UT']  = 1        # (verified 0)

    #this has currently no influence, layout is read directly from config.py
    antennaArrayLayout['AP']  = "circular"  #  (verified 0)
    antennaArrayLayout['FRS'] = "circular"  #  (verified 0)
    antennaArrayLayout['UT']  = "circular"  #  (verified 0)

    txPower['AP']  = dBm(30) # [dBm]      # (verified 0)
    txPower['FRS'] = dBm(30) # [dBm]      # (verified 0)
    txPower['UT']  = dBm(30) # [dBm]      # (verified 0)

    noiseFigure['AP']  = dB(5) # [dB]     # (verified 0)
    noiseFigure['FRS'] = dB(5) # [dB]     # (verified 0)
    noiseFigure['UT']  = dB(5) # [dB]     # (verified 0)



###############################################################################
# PHY Parameters OFDM                                                         #
###############################################################################

class ParametersOFDM(Frozen):


    channelBandwidth = 20
    # nominal channel bandwidth
    # [MHz]
    # currently this parameter is used to calculate the symbol duration (below) and to
    # calculate the noise level in the OFDMA-receiver. The first usage is correct.
    # The latter one might be unprecise. However, I don't know if the inverse sampling
    # frequency (23MHz), or the bandwidth of the used carriers (23*192/256=17.25) is
    # better. Until someone knows the answer use the nominal channel bandwidth.
    #############

    cyclicPrefix = 1.0/4
    # G
    # Possible values: [1/4, 1/8, 1/16, 1/32]
    ######

    samplingFrequency = getSamplingFrequencyOFDM(channelBandwidth, cyclicPrefix)
    # [Hz]   Fp
    ######

    fftSize = 256
    # Nfft
    # (verified 3)
    ######

    subCarrierSpacing = samplingFrequency/fftSize
    # [kHz]
    # (verified 3)
    ######

    usefulSymbolTime = float(fftSize) / float(samplingFrequency)
    # [sec]   Tb=Nfft/Fp
    # (verified 3)
    ######

    guardTime = float(usefulSymbolTime) * float(cyclicPrefix)
    # [sec]   (Tg=Tb*Cp)
    # (verified 3)
    ######

    symbolDuration = float(usefulSymbolTime) + float(guardTime)
    # [sec]   (Ts=Tb+Tg)
    # (verified 3)
    ######

    slotDuration = 3.0 * symbolDuration
    # [sec]   (Ts=Tb+Tg)
    # (verified 3)
    ######
    frameDuration = 0.010
    # [sec]   (Tf)
    ######

    symbolsFrame = int(floor(float(frameDuration) / float(symbolDuration)))
    # [symbols](Tf/Ts)
    # Symbols per frame (720)
    ######

    # for OFDMA:
    # ttg = 0.00005 # 50 mu seconds from SSTTG from WiMAX Forum system profile
    ttg = 2 * symbolDuration
    rtg = ttg

    guardSubCarriers  = 55
    dcSubCarrier = 1
    pilotSubCarrier = 8
    #dataSubCarrier  = fftSize - guardSubCarriers - dcSubCarrier - pilotSubCarrier
    dataSubCarrier  = 192
    # number of subcarriers used for data transmission
    ######

    subchannels = 1
    subcarrierPerSubchannel = dataSubCarrier
    # OFDM uses one 'subchannel' only
    ###############################

    minimumBitsPerSymbol = 96
    # 0.5*192 for BPSK 1/2 on 192 subcarriers
    # PHY mode used to
    # transmit DL and UL MAP
    #################

    dlPreamble = 2
    fch = 1
    frameHead = dlPreamble + fch
    # length of frame
    # head elements in
    # OFDM symbols
    ###############

    mapBase = 56
    ie      = 48
    # DL/UL MAP base size and
    # additional size for each
    # Information Element
    #################


###############################################################################
# OFDMA Parameters                                                            #
###############################################################################

class ParametersOFDMA(Frozen):

    # OFDMA parameters not yet completed
    # check this before usage!!

    channelBandwidth = 10
    # nominal channel bandwidth
    # [MHz]
    # [1.25, 3.5, 5, 7, 8.75, 10, 20]
    # default 5 or 10 (or 20)
    # (verified 4)
    ###########

    cyclicPrefix = 1.0/8
    # Possible values: [1/4, 1/8, 1/16, 1/32]
    # default 1.0/8
    # (verified 4 & 5)
    ######

    samplingFrequency = getSamplingFrequencyOFDM(channelBandwidth, cyclicPrefix)
    # [Hz]
    ######

    fftSize = getFftSize(channelBandwidth)
    # Nfft
    # (verified 4)
    ######

    subCarrierSpacing = samplingFrequency/fftSize
    #subCarrierSpacing = 10937.5 Hz # (for 5, 10, 20 MHz channel bandwidth)
    # [kHz]
    # (verified 4)
    ######

    usefulSymbolTime = float(fftSize) / float(samplingFrequency)
    #usefulSymbolTime = 0.0000914 s # (for 5, 10, 20 MHz channel bandwidth)
    # [sec]   Tb=Nfft/Fp
    # (verified 4)
    ######

    guardTime = float(usefulSymbolTime) * float(cyclicPrefix)
    # [sec]   (Tg=Tb*Cp)
    # (verified 3)
    ######

    symbolDuration = float(usefulSymbolTime) + float(guardTime)
    # [sec]   (Ts=Tb+Tg)
    # (verified 3)
    ######

    slotDuration = 3 * symbolDuration

    frameDuration = 0.005
    # [sec]   (Tf)
    # verified 5
    ######

    symbolsFrame = int(floor(float(frameDuration) / float(symbolDuration)))
    # 47 useful symbols + 1.6 symbols for RTG/TTG (for 0.005s frame duration)
    # [symbols](Tf/Ts)
    # Symbols per frame
    # verified 4 & 5
    ######

    # ttg = 0.00005 # 50 mu seconds from SSTTG from WiMAX Forum system profile
    ttg = 1.6 / 2 * symbolDuration
    rtg = ttg

    symbolsDlSubframe = 26
    # number of OFDM symbols for DL data and DL preamble
    # [35..26] for 5 and 10 MHz
    # [30..24] for 8.75 MHz
    # [24..18] for 3.5 and 7 MHz channelBandwidth
    # verified 5
    #############
    symbolsUlSubframe = symbolsFrame - symbolsDlSubframe
    # number of OFDM symbols for UL data, contention phases, and TTG/RTG

    subcarrierAllocation = 'AMC'
    # ['PUSC', 'FUSC', 'AMC']
    # PUSC and FUSC not yet supported by WiMAC
    # default is PUSC
    # verified 4
    #############

    numberOfSubchannels = getNumberOfChannels(subcarrierAllocation, fftSize)
    subcarrierPerSubchannel = getDataSubcarrierPerSubChannel(subcarrierAllocation, fftSize)
    # verified 3 IEEE 7802.16e 8.4.6.3.1
    ###############################

    minimumBitsPerSymbol = 1 * numberOfSubchannels * subcarrierPerSubchannel
    # QPSK 1/2:
    # PHY mode used to
    # transmit DL and UL MAP
    # maybe include repetition code (factor 2, 4, or 6)
    ##############################

    dlPreamble = 1
    frameHead = dlPreamble
    # length of frame
    # head elements in
    # OFDM symbols
    # TODO: maybe include FCH
    # into MAP phases
    ###############

    mapBase = 0
    ie      = 0
    # TODO OFDMA
    # DL/UL MAP base size and
    # additional size for each
    # Information Element
    #################


###############################################################
# MAC Parameters Frame Setup                                  #
###############################################################
class ParametersMAC(Frozen):

    dlUlRatio = 0.5
    # DL ratio of the data frame
    ######

    rangingSlots = 2
    rangingSlotLength = 8  # [symbols]
    # Ranging contention access configuration
    # Reminder: Ranging phase is located in the uplink frame phase
    # (verified 0)
    ######

    bwReqSlots = 5
    bwReqSlotLength = 2 # [symbols]
    # Bandwidth contention access configuration
    # Reminder: Bandwidth phase is located in the uplink frame phase
    # (verified 0)
    ######

    pduOverhead = 48
    # pduOverhead = 48 + 32 # including CRC
    # overhead due to MAC header

    subFrameRatio = 0
    #  sub frame ratio of the uplink frame phase
    #  Reminder: Sub frame is located in the uplink frame phase.
    #####




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



class ParametersPropagation_NLOS(Frozen):

    ###### Define Propagation Models ##########################################

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
    channelLinkAP2AP   = __ClNLOS

    # AP <-> FRS
    channelLinkAP2FRS  = __ClNLOS
    channelLinkFRS2AP  = __ClNLOS

    # AP <-> UT
    channelLinkAP2UT   = __ClNLOS
    channelLinkUT2AP   = __ClNLOS

    # FRS <-> FRS
    channelLinkFRS2FRS = __ClNLOS

    # FRS <-> UT
    channelLinkFRS2UT  = __ClNLOS
    channelLinkUT2FRS  = __ClNLOS

    # UT <-> UT
    channelLinkUT2UT   = __ClNLOS


