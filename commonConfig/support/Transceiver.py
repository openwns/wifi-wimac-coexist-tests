from openwns.pyconfig import Sealed
from rise.Transmitter import Transmitter
import rise.scenario.Propagation
from ofdmaphy.Receiver import OFDMAReceiver

from rise.scenario.FTFading import *
#from rise.scenario.FTFadingConfiguration import *

class Transceiver(Sealed):
    propagation = None
    receiver = None
    transmitter = None

    def __init__(self, _config):
        self.receiver={}
        self.transmitter={}

	 ###### Set Propagation ######################################################
        self.propagation = rise.scenario.Propagation.Propagation()

        # AP <-> AP Propagation
        self.propagation.configurePair("AP", "AP", _config.parametersPropagation.channelLinkAP2AP)

        # AP <-> FRS Propagation
        self.propagation.configurePair("AP", "FRS", _config.parametersPropagation.channelLinkAP2FRS)
        self.propagation.configurePair("FRS", "AP", _config.parametersPropagation.channelLinkFRS2AP)

        # AP <-> UT Propagation
        self.propagation.configurePair("AP", "UT", _config.parametersPropagation.channelLinkAP2UT)
        self.propagation.configurePair("UT", "AP", _config.parametersPropagation.channelLinkUT2AP)

        # FRS <-> UT Propagation identical to AP <-> UT Propagation
        self.propagation.configurePair("FRS", "UT", _config.parametersPropagation.channelLinkFRS2UT)
        self.propagation.configurePair("UT", "FRS", _config.parametersPropagation.channelLinkUT2FRS)

        # FRS <-> FRS Propagation identical to AP <-> AP Propagation
        self.propagation.configurePair("FRS", "FRS", _config.parametersPropagation.channelLinkFRS2FRS)

        # UT <-> UT Propagation
        self.propagation.configurePair("UT", "UT", _config.parametersPropagation.channelLinkUT2UT)



        ##### Set Transceiver #########################################################
        self.receiver['AP'] = OFDMAReceiver( propagation = self.propagation,
                                             propagationCharacteristicName = "AP",
                                             receiverNoiseFigure = _config.parametersSystem.noiseFigureAP,
                                             FTFadingStrategy = FTFadingOff())
        self.receiver['AP'].logger.enabled = False

        self.receiver['FRS'] = OFDMAReceiver( propagation = self.propagation,
                                              propagationCharacteristicName = "FRS",
                                              receiverNoiseFigure = _config.parametersSystem.noiseFigureFRS,
                                              FTFadingStrategy = FTFadingOff())
        self.receiver['FRS'].logger.enabled = False



        self.receiver['UT'] = OFDMAReceiver( propagation = self.propagation,
                                             propagationCharacteristicName = "UT",
                                             receiverNoiseFigure = _config.parametersSystem.noiseFigureUT,
                                             FTFadingStrategy = FTFadingOff())
        self.receiver['UT'].logger.enabled = False



        self.transmitter['AP'] = Transmitter( propagation = self.propagation,
                                              propagationCharacteristicName = "AP" )
        self.transmitter['AP'].logger.enabled = False



        self.transmitter['FRS'] = Transmitter( propagation = self.propagation,
                                               propagationCharacteristicName = "FRS" )
        self.transmitter['FRS'].logger.enabled = False


        self.transmitter['UT'] = Transmitter( propagation = self.propagation,
                                              propagationCharacteristicName = "UT" )
        self.transmitter['UT'].logger.enabled = False


