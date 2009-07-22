from Layer2 import *
import dll.UpperConvergence
import dll.CompoundSwitch
import wimac.Scheduler
import wimac.FUReseter
import openwns.Tools
import math
from wimac.FrameBuilder import ActivationAction, OperationMode
import support.FrameSetup as FrameSetup

class Association:
    def __init__(self,source, destination, id):
        self.source = source
        self.destination = destination
        self.id = id


class BaseStation(Layer2):

    subscriberStations = None
    relayStations = None

    def __init__(self, node, config, registryProxy = wimac.Scheduler.RegistryProxyWiMAC):
        super(BaseStation, self).__init__(node, "BS", config)
        self.ring = 1
        self.qosCategory = 'NoQoS'

        # BaseStation specific components
        self.upperconvergence = dll.UpperConvergence.AP()
        self.stationType = "AP"

        # control plane
        self.rngCompoundSwitch = dll.CompoundSwitch.CompoundSwitch()
        self.rngCompoundSwitch.onDataFilters.append(
            dll.CompoundSwitch.FilterAll('All') )
        self.rngCompoundSwitch.sendDataFilters.append(
            dll.CompoundSwitch.FilterNone('None') )
        self.rngCompoundSwitch.sendDataFilters.append(
            dll.CompoundSwitch.FilterAll('All') )

        # frame elements
        self.framehead = wimac.FrameBuilder.FrameHeadCollector('frameBuilder')
        self.dlmapcollector = wimac.FrameBuilder.DLMapCollector('frameBuilder', 'dlscheduler')
        self.ulmapcollector = wimac.FrameBuilder.ULMapCollector('frameBuilder', 'ulscheduler')
        self.dlscheduler = wimac.FrameBuilder.DataCollector('frameBuilder')
        self.dlscheduler.txScheduler = wimac.Scheduler.Scheduler(
            "frameBuilder",
            config.parametersPhy.symbolDuration,
            strategy = openwns.Scheduler.ProportionalFairDL(historyWeight = 0.99,
                                                        maxBursts = config.maxBursts,
                                                        powerControlSlave = False),
            freqChannels = config.parametersPhy.subchannels,
            maxBeams = config.maxBeams,
            beamforming = config.beamforming,
            friendliness_dBm = config.friendliness_dBm,
            plotFrames = False,
            callback = wimac.Scheduler.DLCallback( beamforming = config.beamforming )
            )
	self.ulContentionRNGc = wimac.FrameBuilder.ContentionCollector('frameBuilder', contentionAccess = wimac.FrameBuilder.ContentionCollector.ContentionAccess(False, 8, 3) )
        self.ulscheduler = wimac.FrameBuilder.DataCollector('frameBuilder')
        self.ulscheduler.rxScheduler = wimac.Scheduler.Scheduler(
            "frameBuilder",
            config.parametersPhy.symbolDuration,
            strategy = openwns.Scheduler.ProportionalFairUL(historyWeight = 0.99,
                                                        maxBursts = config.maxBursts,
                                                        powerControlSlave = False),
            freqChannels = config.parametersPhy.subchannels,
            maxBeams = config.maxBeams,
            beamforming =  config.beamforming,
            friendliness_dBm = config.friendliness_dBm,
            callback = wimac.Scheduler.ULCallback(),
            plotFrames = False,
            uplink = True
            )
        self.ulscheduler.rxScheduler.pseudoGenerator = \
            wimac.Scheduler.PseudoBWRequestGenerator('connectionManager',
                                                     'ulscheduler',
                                                     _packetSize = config.packetSize,
                                                     _pduOverhead = config.parametersMAC.pduOverhead)

        self.setupCompoundSwitch()
        self.setupFrame(config)
        self.fun = FUN()
        self.buildFUN(config)
	self.connect()


    def connect(self):
        # Connections Dataplane
        self.upperconvergence.connect(self.topTpProbe)
        self.topTpProbe.connect(self.topPProbe)

        self.topPProbe.connect(self.classifier)
        self.classifier.connect(self.synchronizer)
        self.synchronizer.connect(self.bufferSep)
        self.bufferSep.connect(self.crc)
        self.crc.connect(self.errormodelling)
        self.errormodelling.connect(self.compoundSwitch)
	self.compoundSwitch.connect(self.dlscheduler)
	self.compoundSwitch.upConnect(self.ulContentionRNGc)

        self.compoundSwitch.upConnect(self.ulscheduler)

        self.framehead.connect(self.frameBuilder)
        self.dlmapcollector.connect(self.frameBuilder)
        self.ulmapcollector.connect(self.frameBuilder)
        self.dlscheduler.connect(self.frameBuilder)
        self.ulContentionRNGc.connect(self.frameBuilder)
        self.ulscheduler.connect(self.frameBuilder)
        self.frameBuilder.connect(self.phyUser)

    def setupCompoundSwitch(self):
        self.compoundSwitch.onDataFilters.append( dll.CompoundSwitch.FilterAll('All') )
        self.compoundSwitch.sendDataFilters.append( dll.CompoundSwitch.FilterAll('All') )


    def setupFrame(self, config):

        myFrameSetup = FrameSetup.FrameSetup(config)

        # Insert Activations into Timing Control
        # first, configure only real compound collectors
        activation = wimac.FrameBuilder.Activation('framehead',
                                                   OperationMode( OperationMode.Sending ),
                                                   ActivationAction( ActivationAction.StartCollection ),
                                                   myFrameSetup.frameHeadLength )
        self.frameBuilder.timingControl.addActivation( activation )

        activation = wimac.FrameBuilder.Activation('dlmapcollector',
                                                   OperationMode( OperationMode.Sending ),
                                                   ActivationAction( ActivationAction.StartCollection ),
                                                   myFrameSetup.dlMapLength )
        self.frameBuilder.timingControl.addActivation( activation )

        activation = wimac.FrameBuilder.Activation('ulmapcollector',
                                                   OperationMode( OperationMode.Sending ),
                                                   ActivationAction( ActivationAction.StartCollection ),
                                                   myFrameSetup.ulMapLength )
        self.frameBuilder.timingControl.addActivation( activation )

        activation = wimac.FrameBuilder.Activation('dlscheduler',
                                                   OperationMode( OperationMode.Sending ),
                                                   ActivationAction( ActivationAction.StartCollection ),
                                                   myFrameSetup.dlDataLength )
        self.frameBuilder.timingControl.addActivation( activation )

        activation = wimac.FrameBuilder.Activation('ulscheduler',
                                                   OperationMode( OperationMode.Receiving ),
                                                   ActivationAction( ActivationAction.StartCollection ),
                                                   myFrameSetup.ulDataLength )
        self.frameBuilder.timingControl.addActivation( activation )

        activation = wimac.FrameBuilder.Activation('dlscheduler',
                                                   OperationMode( OperationMode.Sending ),
                                                   ActivationAction( ActivationAction.FinishCollection ),
                                                   myFrameSetup.dlDataLength )
        self.frameBuilder.timingControl.addActivation( activation )

        activation = wimac.FrameBuilder.Activation('ulscheduler',
                                                   OperationMode( OperationMode.Receiving ),
                                                   ActivationAction( ActivationAction.FinishCollection ),
                                                   myFrameSetup.ulDataLength )
        self.frameBuilder.timingControl.addActivation( activation )

        # second, now set phase durations
        activation = wimac.FrameBuilder.Activation('framehead',
                                                   OperationMode( OperationMode.Sending ),
                                                   ActivationAction( ActivationAction.Start ),
                                                   myFrameSetup.frameHeadLength )
        self.frameBuilder.timingControl.addActivation( activation )

        activation = wimac.FrameBuilder.Activation('dlmapcollector',
                                                   OperationMode( OperationMode.Sending ),
                                                   ActivationAction( ActivationAction.Start ),
                                                   myFrameSetup.dlMapLength )
        self.frameBuilder.timingControl.addActivation( activation )

        activation = wimac.FrameBuilder.Activation('ulmapcollector',
                                                   OperationMode( OperationMode.Sending ),
                                                   ActivationAction( ActivationAction.Start ),
                                                   myFrameSetup.ulMapLength )
        self.frameBuilder.timingControl.addActivation( activation )

        activation = wimac.FrameBuilder.Activation('dlscheduler',
                                                   OperationMode( OperationMode.Sending ),
                                                   ActivationAction( ActivationAction.Start ),
                                                   myFrameSetup.dlDataLength )
        self.frameBuilder.timingControl.addActivation( activation )

        # name of compound collector (here "ttg") is just informative
        activation = wimac.FrameBuilder.Activation('ttg',
                                                   OperationMode( OperationMode.Pausing ),
                                                   ActivationAction( ActivationAction.Pause ),
                                                   myFrameSetup.ttgLength )
        self.frameBuilder.timingControl.addActivation( activation )

        activation = wimac.FrameBuilder.Activation('ulscheduler',
                                                   OperationMode( OperationMode.Receiving ),
                                                   ActivationAction( ActivationAction.Start ),
                                                   myFrameSetup.ulDataLength )
        self.frameBuilder.timingControl.addActivation( activation )

        # next activations could be a pause, too
        # but they might be exchanged by real compound collector in the future
        activation = wimac.FrameBuilder.Activation('bwReq',
                                                   OperationMode( OperationMode.Pausing ),
                                                   ActivationAction( ActivationAction.Pause ),
                                                   myFrameSetup.bwReqLength )
        self.frameBuilder.timingControl.addActivation( activation )

        activation = wimac.FrameBuilder.Activation('ranging',
                                                   OperationMode( OperationMode.Pausing ),
                                                   ActivationAction( ActivationAction.Pause ),
                                                   myFrameSetup.rangingLength )
        self.frameBuilder.timingControl.addActivation( activation )

        # final phase RTG is modeled as simple gap only (no Timing Control activation)


class SubscriberStation(Layer2):
    forwarder = None

    def __init__(self, node, config):
        super(SubscriberStation, self).__init__(node, "SS", config)
        # actually this can be 2 + 2*numberOfRingAssociated to (1. BS, 2. Relay, ...)
        self.upperconvergence = dll.UpperConvergence.UT()
        self.stationType = "UT"

        # control plane
        self.rngCompoundSwitch = dll.CompoundSwitch.CompoundSwitch()
        self.rngCompoundSwitch.onDataFilters.append( dll.CompoundSwitch.FilterAll('All') )
	self.rngCompoundSwitch.sendDataFilters.append( dll.CompoundSwitch.FilterCommand('RNGCompounds', 'ranging') )
	self.rngCompoundSwitch.sendDataFilters.append( dll.CompoundSwitch.FilterAll('All') )

        # frame elements
        self.framehead = wimac.FrameBuilder.FrameHeadCollector('frameBuilder')
        self.dlmapcollector = wimac.FrameBuilder.DLMapCollector('frameBuilder', None)
        self.ulmapcollector = wimac.FrameBuilder.ULMapCollector('frameBuilder', None)
        self.dlscheduler = wimac.FrameBuilder.DataCollector('frameBuilder')
        self.dlscheduler.rxScheduler = wimac.FrameBuilder.SSDLScheduler('frameBuilder', 'dlmapcollector')
	self.ulContentionRNGc = wimac.FrameBuilder.ContentionCollector('frameBuilder', contentionAccess = wimac.FrameBuilder.ContentionCollector.ContentionAccess(False, 8, 3) )
        self.ulscheduler = wimac.FrameBuilder.DataCollector('frameBuilder')
        self.ulscheduler.txScheduler = wimac.FrameBuilder.SSULScheduler('frameBuilder', 'ulmapcollector')

        self.setupCompoundSwitch()
        self.setupFrame(config)
        self.fun = FUN()
        self.buildFUN(config)
	self.connect()


    def associate(self, destination):
        assert isinstance(destination, Layer2)
        it = Association(self, destination, destination.getAssociationID())
        self.associations.append(it)
        self.associateTo = destination.stationID
        self.qosCategory = 'BE'
        self.ring = destination.ring + 1
        self.connectionControl.associateTo(destination.stationID)
        self.phyUser.config.bandwidth = destination.phyUser.config.bandwidth
        self.phyUser.config.centerFrequency = destination.phyUser.config.centerFrequency
        self.phyUser.config.numberOfSubCarrier = destination.phyUser.config.numberOfSubCarrier

    def connect(self):
        # Connections Dataplane
        self.upperconvergence.connect(self.topTpProbe)
        self.topTpProbe.connect(self.topPProbe)
        self.topPProbe.connect(self.classifier)
        self.classifier.connect(self.synchronizer)
        self.synchronizer.connect(self.bufferSep)
        self.bufferSep.connect(self.crc)
        self.crc.connect(self.errormodelling)
        self.errormodelling.connect(self.compoundSwitch)
        self.compoundSwitch.upConnect(self.dlscheduler)
	self.compoundSwitch.connect(self.ulContentionRNGc)
	self.compoundSwitch.connect(self.ulscheduler)

        self.framehead.connect(self.frameBuilder)
        self.dlmapcollector.connect(self.frameBuilder)
        self.ulmapcollector.connect(self.frameBuilder)
        self.dlscheduler.connect(self.frameBuilder)
        self.ulContentionRNGc.connect(self.frameBuilder)
        self.ulscheduler.connect(self.frameBuilder)
        self.frameBuilder.connect(self.phyUser)

    def setupCompoundSwitch(self):
	self.compoundSwitch.onDataFilters.append( dll.CompoundSwitch.FilterAll('All') )
        self.compoundSwitch.sendDataFilters.append( dll.CompoundSwitch.FilterNone('None') )
	self.compoundSwitch.sendDataFilters.append( dll.CompoundSwitch.FilterAll('All') )


    def setupFrame(self, config):

        myFrameSetup = FrameSetup.FrameSetup(config)

        # Insert Activations into Timing Control
        # first, configure only real compound collectors
        activation = wimac.FrameBuilder.Activation('framehead',
                                                   OperationMode( OperationMode.Receiving ),
                                                   ActivationAction( ActivationAction.StartCollection ),
                                                   myFrameSetup.frameHeadLength )
        self.frameBuilder.timingControl.addActivation( activation )

        activation = wimac.FrameBuilder.Activation('dlmapcollector',
                                                   OperationMode( OperationMode.Receiving ),
                                                   ActivationAction( ActivationAction.StartCollection ),
                                                   myFrameSetup.dlMapLength )
        self.frameBuilder.timingControl.addActivation( activation )

        activation = wimac.FrameBuilder.Activation('ulmapcollector',
                                                   OperationMode( OperationMode.Receiving ),
                                                   ActivationAction( ActivationAction.StartCollection ),
                                                   myFrameSetup.ulMapLength )
        self.frameBuilder.timingControl.addActivation( activation )

        activation = wimac.FrameBuilder.Activation('dlscheduler',
                                                   OperationMode( OperationMode.Receiving ),
                                                   ActivationAction( ActivationAction.StartCollection ),
                                                   myFrameSetup.dlDataLength )
        self.frameBuilder.timingControl.addActivation( activation )

        activation = wimac.FrameBuilder.Activation('ulscheduler',
                                                   OperationMode( OperationMode.Sending ),
                                                   ActivationAction( ActivationAction.StartCollection ),
                                                   myFrameSetup.ulDataLength )
        self.frameBuilder.timingControl.addActivation( activation )

        activation = wimac.FrameBuilder.Activation('dlscheduler',
                                                   OperationMode( OperationMode.Receiving ),
                                                   ActivationAction( ActivationAction.FinishCollection ),
                                                   myFrameSetup.dlDataLength )
        self.frameBuilder.timingControl.addActivation( activation )

        activation = wimac.FrameBuilder.Activation('ulscheduler',
                                                   OperationMode( OperationMode.Receiving ),
                                                   ActivationAction( ActivationAction.FinishCollection ),
                                                   myFrameSetup.ulDataLength )
        self.frameBuilder.timingControl.addActivation( activation )


        # second, now set phase durations
        activation = wimac.FrameBuilder.Activation('framehead',
                                                   OperationMode( OperationMode.Receiving ),
                                                   ActivationAction( ActivationAction.Start ),
                                                   myFrameSetup.frameHeadLength )
        self.frameBuilder.timingControl.addActivation( activation )

        activation = wimac.FrameBuilder.Activation('dlmapcollector',
                                                   OperationMode( OperationMode.Receiving ),
                                                   ActivationAction( ActivationAction.Start ),
                                                   myFrameSetup.dlMapLength )
        self.frameBuilder.timingControl.addActivation( activation )

        activation = wimac.FrameBuilder.Activation('ulmapcollector',
                                                   OperationMode( OperationMode.Receiving ),
                                                   ActivationAction( ActivationAction.Start ),
                                                   myFrameSetup.ulMapLength )
        self.frameBuilder.timingControl.addActivation( activation )

        activation = wimac.FrameBuilder.Activation('dlscheduler',
                                                   OperationMode( OperationMode.Receiving ),
                                                   ActivationAction( ActivationAction.Start ),
                                                   myFrameSetup.dlDataLength )
        self.frameBuilder.timingControl.addActivation( activation )

        activation = wimac.FrameBuilder.Activation('ttg',
                                                   OperationMode( OperationMode.Pausing ),
                                                   ActivationAction( ActivationAction.Pause ),
                                                   myFrameSetup.ttgLength )
        self.frameBuilder.timingControl.addActivation( activation )

        activation = wimac.FrameBuilder.Activation('ulscheduler',
                                                   OperationMode( OperationMode.Sending ),
                                                   ActivationAction( ActivationAction.Start ),
                                                   myFrameSetup.ulDataLength )
        self.frameBuilder.timingControl.addActivation( activation )

        activation = wimac.FrameBuilder.Activation('bwReq',
                                                   OperationMode( OperationMode.Pausing ),
                                                   ActivationAction( ActivationAction.Pause ),
                                                   myFrameSetup.bwReqLength )
        self.frameBuilder.timingControl.addActivation( activation )

        activation = wimac.FrameBuilder.Activation('ranging',
                                                   OperationMode( OperationMode.Pausing ),
                                                   ActivationAction( ActivationAction.Pause ),
                                                   myFrameSetup.rangingLength )
        self.frameBuilder.timingControl.addActivation( activation )

