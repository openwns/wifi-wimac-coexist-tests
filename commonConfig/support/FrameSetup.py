from math import ceil, floor

from openwns.pyconfig import Sealed

from openwns.FCF import FrameBuilderNode, BasicPhaseDescriptor, DurationPolicy



class BasicFrameSetup(Sealed):
    """
       The class BasicFrameSetup calculates the basic frame setup, with
       all frame phases in symbols.

          - no TTG, RTG
          - no subframe
          - Rounding to the next symbol, caused of the dlULRatio
            for the benefit of the downlink phase

       Basic WiMAX MAC Frame:
         ____________________________    ________________________
        |         |     |     |      |  |      | cont. |  cont.  |
        |frameHead|dlMap|ulMap|dlData|  |ulData|ranging| bw req  |
        |_________|_____|_____|______|  |______|_______|_________|

    """
    ############################
    # initiate output parameters
    ############################

    # phases of the basic frame
    # DL:
    frameHead          = 0
    dlMap              = 0
    ulMap              = 0
    dlData             = 0
    # UL:
    ulData             = 0
    ranging            = 0
    bwReq              = 0
    ############################

    def __init__(self, _config, _symbolsPerFrame, _servedSS):

        if _symbolsPerFrame == 0:
            self.frameHead          = 0
            self.dlMap              = 0
            self.ulMap              = 0
            self.dlData             = 0
            self.ulData             = 0
            self.ranging            = 0
            self.bwReq              = 0
        elif _symbolsPerFrame > 0:

            # inputs are:
            #
            # frame duration (OFDM symbols per MAC frame)
            # preamble and FCH length
            # scheduling strategy and number of served SS for MAP duration
            # number and duration of

            minBitsPerSymbol            = _config.parametersPhy.minimumBitsPerSymbol
            subchannels                 = _config.parametersPhy.subchannels
            dlUlRatio                   = _config.parametersMAC.dlUlRatio
            rngNumberOfSlots            = _config.parametersMAC.rangingSlots
            rngSlotLength               = _config.parametersMAC.rangingSlotLength
            bwReqNumberOfSlots          = _config.parametersMAC.bwReqSlots
            bwReqSlotLength             = _config.parametersMAC.bwReqSlotLength
            # need to separate between DL and UL?
            mapHeaderBits               = _config.parametersPhy.mapBase
            mapFieldBits                = _config.parametersPhy.ie
            dlStrategy                  = _config.dlStrategy
            ulStrategy                  = _config.ulStrategy
            maxBursts                   = _config.maxBursts

            # Frame head:
            self.frameHead              = _config.parametersPhy.frameHead

            # DL MAP:

            # model behaviour of the scheduler:
            maxNumberIEs = _servedSS * subchannels
            if dlStrategy == "ProportionalFairDL":
                if ( maxBursts < _servedSS ):
                    maxNumberIEs = maxBursts * subchannels
            elif dlStrategy == "RelayPreferredProportionalFair":
                if ( maxBursts < _servedSS ):
                    maxNumberIEs = maxBursts * subchannels
            else:
                print 'unknown dl scheduler strategy'

            # TODO: the sum of both, DL and UL MAP, needs to be rounded to OFDM boundaries
            self.dlMap = ceil( (mapHeaderBits + (mapFieldBits * maxNumberIEs) ) / float(minBitsPerSymbol))

            # UL MAP:
            maxNumberIEs = _servedSS * subchannels
            if ulStrategy == "ProportionalFairUL":
                if ( maxBursts < _servedSS ):
                    maxNumberIEs = maxBursts * subchannels
            else:
                print 'unknown ul scheduler strategy'

            self.ulMap = ceil( (mapHeaderBits + (mapFieldBits * maxNumberIEs) ) / float(minBitsPerSymbol))

            # DL+UL subframe:
            dataPhaseLength = _symbolsPerFrame - (self.frameHead + self.dlMap + self.ulMap)

            # in OFDMA, fixed DL/UL ratios are foreseen (see WiMAX Forum Methodology document)
            self.dlData = ceil( dataPhaseLength * dlUlRatio )

            self.ranging = rngSlotLength * rngNumberOfSlots
            self.bwReq = bwReqSlotLength * bwReqNumberOfSlots

            self.ulData = dataPhaseLength - self.dlData - self.ranging - self.bwReq



class FrameSetup(Sealed):
    """
       The class FrameSetup calculates the frame setup, with
       all frame phases both in seconds and in symbols.

          - Rounding to the next symbol, caused of the
            subFrameRatio for the benefit of the main-frame phase


       WiMAX MAC Frame:
         _______________________________________________________________________
        |         |     |     |      |   |        |      |  cont. |  cont.  |   |
        |frameHead|dlMap|ulMap|dlData|TTG|subFrame|ulData| bw req | ranging |RTG|
        |_________|_____|_____|______|___|________|______|________|_________|___|


       WiMAX Multihop SubFrame:
        __________________________________________________________________________________________________
       |           |            |        |        |         |   |         |  cont. |  cont.  |            |
       |subPrePause|subFrameHead|subDlMap|subUlMap|subDlData|TTG|subUlData| bw req | ranging |subPostPause|
       |___________|____________|________|________|_________|___|_________|________|_________|____________|

        - additional RTG necessary?
        - same number of ranging and bw req slots in the multihop subframe?

    """
    ############################
    # initiate output parameters
    ############################

    # phases of the MAIN frame [seconds]
    frameDuration      = 0
    usefulFrame        = 0
    # DL:
    frameHead          = 0
    frameHeadLength    = 0
    dlMap              = 0
    dlMapLength        = 0
    ulMap              = 0
    ulMapLength        = 0
    dlData             = 0
    dlDataLength       = 0

    ttgLength          = 0

    # UL:
    ulData             = 0
    ulDataLength       = 0
    ranging            = 0
    rangingLength      = 0
    bwReq              = 0
    bwReqLength        = 0

    rtgLength          = 0

    # phases of the MULTIHOP subframe
    subframe           = 0
    subframeLength     = 0
    usefulSubframe     = 0
    # DL:
    subPrePause        = 0
    subPrePauseLength  = 0
    subFrameHead       = 0
    subFrameHeadLength = 0
    subDlMap           = 0
    subDlMapLength     = 0
    subUlMap           = 0
    subUlMapLength     = 0
    subDlData          = 0
    subDlDataLength    = 0

    # UL:
    subUlData          = 0
    subUlDataLength    = 0
    subRanging         = 0
    subRangingLength   = 0
    subBwReq           = 0
    subBwReqLength     = 0
    subPostPause       = 0
    subPostPauseLength = 0
    ############################



    def __init__(self, _config):

        # inputs are:
        #
        # frame length in seconds
        # TTG / RTG durations (not necessarily integer multiples of OFDM symbols)
        # multihop setup and subFrame ratio

        symbolDuration              = _config.parametersPhy.symbolDuration

        self.ttgLength              = _config.parametersPhy.ttg
        self.rtgLength              = _config.parametersPhy.rtg
        # print 'TTG and RTG together are ' + str(self.ttgLength + self.rtgLength) + ' ms long\n'
        # print 'they require ' + str( (self.ttgLength+self.rtgLength) / symbolDuration ) + ' OFDM symbols'

        # maybe get useful number of OFDM symbols from config.parametersPhy
        self.frameDuration          = _config.parametersPhy.frameDuration

        nRSs                        = _config.nRSs
        nSSs                        = _config.nSSs
        nRmSs                       = _config.nRmSs

        if nRSs == 0:
            subframeRatio           = 0
        else:
            subframeRatio           = _config.subframeRatio

        # maybe read this from config.parametersPhy directly
        usefulFrameLength = self.frameDuration - self.ttgLength - self.rtgLength
        #in [#symbols]
        self.usefulFrame = floor( usefulFrameLength / symbolDuration)

        if nRSs > 0:
            #in [#symbols]
            self.subframe = floor( self.usefulFrame * subframeRatio )

            if(_config.operationModeRelays == 'TDM'):
                self.usefulSubframe = ceil( self.subframe / nRSs ) - ceil(self.ttgLength / symbolDuration)
            elif(_config.operationModeRelays == 'SDM'):
                self.usefulSubframe = self.subframe - ceil(self.ttgLength / symbolDuration)
                # - ceil(self.rtgLength / symbolDuration)
            else :
                print error
            self.subframeLength = self.subframe * symbolDuration
        else:
            self.subframe = 0
            self.usefulSubframe = 0
            self.subframeLength = 0.0


        # DL data phase:
        mainFrame = self.usefulFrame - self.subframe
        #print '### ### ### subframe usefulSubframe subframeLength mainFrame subframeRatio nRSs',  self.subframe , self.usefulSubframe, self.subframeLength, mainFrame, subframeRatio, nRSs

        mainFrameSetup = BasicFrameSetup(_config, mainFrame, (nSSs + nRSs) )
        subFrameSetup  = BasicFrameSetup(_config, self.usefulSubframe, nRmSs)


        self.frameHead            = mainFrameSetup.frameHead
        self.dlMap                = mainFrameSetup.dlMap
        self.ulMap                = mainFrameSetup.ulMap
        self.dlData               = mainFrameSetup.dlData
        self.ulData               = mainFrameSetup.ulData
        self.ranging              = mainFrameSetup.ranging
        self.bwReq                = mainFrameSetup.bwReq

        self.frameHeadLength      = self.frameHead  * symbolDuration
        self.dlMapLength          = self.dlMap      * symbolDuration
        self.ulMapLength          = self.ulMap      * symbolDuration
        self.dlDataLength         = self.dlData     * symbolDuration
        self.ulDataLength         = self.ulData     * symbolDuration
        self.rangingLength        = self.ranging    * symbolDuration
        self.bwReqLength          = self.bwReq      * symbolDuration


        self.subPrePause          = 0
        self.subFrameHead         = subFrameSetup.frameHead
        self.subDlMap             = subFrameSetup.dlMap
        self.subUlMap             = subFrameSetup.ulMap
        self.subDlData            = subFrameSetup.dlData
        self.subUlData            = subFrameSetup.ulData
        self.subRanging           = subFrameSetup.ranging
        self.subBwReq             = subFrameSetup.bwReq
        self.subPostPause         = 0

        self.subPrePauseLength    = 0
        self.subFrameHeadLength   = self.subFrameHead  * symbolDuration
        self.subDlMapLength       = self.subDlMap      * symbolDuration
        self.subUlMapLength       = self.subUlMap      * symbolDuration
        self.subDlDataLength      = self.subDlData     * symbolDuration
        self.subUlDataLength      = self.subUlData     * symbolDuration
        self.subRangingLength     = self.subRanging    * symbolDuration
        self.subBwReqLength       = self.subBwReq      * symbolDuration
        self.subPostPauseLength   = 0


    def printFramePhases(self):
        result = "\n"

        result += '#############################################\n'
        result += '## Frame configuration      [symbols]      ##\n'
        result += '#############################################\n'
        result += '\n'

        total = 0
        result += '   Frame:\n'
        result += '   ~~~~~~~ \n'
        keys = ['frameHead',
                'dlMap',
                'ulMap',
                'dlData',
                'ranging',
                'bwReq',
                'subframe',
                'ulData']
        for i in keys:
            result += '   ' + str(i) + " = " + str(self.__dict__[i]) + '\n'
            total += self.__dict__[i]
        result += '   _________________________\n'
        result += '   FrameDuration      : ' + str(self.__dict__['usefulFrame']) + '\n'
        result += '   FrameDuration total: ' + str(total) + '\n'

        result += '#############################################\n'
        result += '## Frame configuration      [milli seconds]      ##\n'
        result += '#############################################\n'
        result += '\n'

        total = 0
        result += '   Frame:\n'
        result += '   ~~~~~~~ \n'
        keys = ['frameHeadLength',
                'dlMapLength',
                'ulMapLength',
                'dlDataLength',
                'rangingLength',
                'bwReqLength',
                'subframeLength',
                'ulDataLength']
        for i in keys:
            result += '   ' + str(i) + " = " + str(self.__dict__[i] * 1000) + '\n'
            total += (self.__dict__[i])
        result += '   _________________________\n'
        result += '   FrameDuration      : ' + str(self.frameDuration * 1000) + '\n'
        result += '   FrameDuration total: ' + str(total * 1000) + '\n\n'

        result += '   TTG: ' + str(self.ttgLength * 1000) + '\n'
        result += '   RTG: ' + str(self.rtgLength * 1000) + '\n\n'

        result += '#############################################\n'
        result += '## subframe configuration      [symbols]   ##\n'
        result += '#############################################\n'
        result += '\n'

        total = 0
        result += '\n\n'
        result += '   SubFrame:\n'
        result += '   ~~~~~~~~~~ \n'
        keys = ['subPrePause',
                'subFrameHead',
                'subDlMap',
                'subUlMap',
                'subDlData',
                'subUlData',
                'subRanging',
                'subBwReq',
                'subPostPause']
        for i in keys:
            result += '   ' + str(i) + " = " + str(self.__dict__[i]) + '\n'
            total +=  self.__dict__[i]
        result += '   ____________________________\n'
        result += '   SubFrameDuration      : ' + str(self.usefulSubframe) + '\n'
        result += '   SubFrameDuration total: ' + str(total) + '\n'
        result += '\n'

        result += '#############################################\n'
        result += '## subframe configuration      [milli seconds]   ##\n'
        result += '#############################################\n'
        result += '\n'

        total = 0
        result += '\n\n'
        result += '   SubFrame:\n'
        result += '   ~~~~~~~~~~ \n'
        keys = ['subPrePauseLength',
                'subFrameHeadLength',
                'subDlMapLength',
                'subUlMapLength',
                'subDlDataLength',
                'subUlDataLength',
                'subRangingLength',
                'subBwReqLength',
                'subPostPauseLength']
        for i in keys:
            result += '   ' + str(i) + " = " + str(self.__dict__[i] * 1000) + '\n'
            total +=  (self.__dict__[i])
        result += '   ____________________________\n'
        result += '   SubFrameDuration      : ' + str(self.subframeLength * 1000) + '\n'
        result += '   SubFrameDuration total: ' + str(total * 1000) + '\n'
        result += '\n'

        result += '   TTG: ' + str(self.ttgLength * 1000) + '\n'
#        result += '   RTG: ' + str(self.rtgLength * 1000) + '\n\n'


        return result
