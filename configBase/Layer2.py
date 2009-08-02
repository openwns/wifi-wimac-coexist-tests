from openwns.pyconfig import Sealed
from openwns.FUN import FUN, Node
from openwns.FlowSeparator import FlowSeparator
from openwns.Multiplexer import Dispatcher
from math import ceil

import openwns.ldk
import wimac.KeyBuilder

from openwns.FUN import FUN, Node
from openwns.FlowSeparator import FlowSeparator

import openwns.Probe
import openwns.Buffer
import openwns.ARQ
import openwns.SAR
import openwns.Tools
import openwns.FCF
import openwns.CRC
import wimac.Component
import wimac.Relay
import wimac.FrameBuilder
import wimac.KeyBuilder
import wimac.ErrorModelling
import wimac.Scanning
import wimac.Ranging
import wimac.MessageExchanger
import wimac.SetupConnection
import wimac.Handover
import wimac.PhyUser
import wimac.Services
from wimac.ProbeStartStop import ProbeStartStop
from wimac.FUs import Classifier, ACKSwitch


class Layer2(wimac.Component.Component):
    frameBuilder = None
    rngCompoundSwitch = None

    # Probes
    topTpProbe = None
    topPProbe = None
    bottomThroughputProbe = None
    bottomPacketProbe = None

    # DataPlane
    upperconvergence = None
    classifier = None
    synchronizer = None
    controlPlaneSync = None

    bufferSep = None
    branchDispatcher = None
    crc = None
    errormodelling = None
    compoundSwitch = None
    phyUser = None

    compoundBacktracker = None
    # functional units for scheduling
    framehead = None
    dlmapcollector = None
    ulmapcollector = None
    dlscheduler = None
    ulContentionRNGc = None
    ulscheduler = None

    connectionControl = None
    associateTo = None
    qosCategory = None
    randomStartDelayMax = None

    def __init__(self, node, stationName, config):
        super(Layer2, self).__init__(node, stationName)
        self.nameInComponentFactory = "wimac.Component"

        self.associations = []
        self.randomStartDelayMax = 0.0
        self.frameBuilder = openwns.FCF.FrameBuilder(0, wimac.FrameBuilder.TimingControl(),
            frameDuration = config.parametersPhy.frameDuration,
            symbolDuration = config.parametersPhy.symbolDuration )
        
        self.managementServices.append(
            wimac.Services.ConnectionManager( "connectionManager", "fuReseter" ) )

        interferenceCache = wimac.Services.InterferenceCache( 
            "interferenceCache", alphaLocal = 0.2, alphaRemote= 0.05 ) 
        interferenceCache.notFoundStrategy.averageCarrier = "-88.0 dBm"
        interferenceCache.notFoundStrategy.averageInterference = "-96.0 dBm"
        interferenceCache.notFoundStrategy.deviationCarrier = "0.0 mW"
        interferenceCache.notFoundStrategy.deviationInterference = "0.0 mW"
        interferenceCache.notFoundStrategy.averagePathloss = "0.0 dB"
        self.managementServices.append( interferenceCache )

        self.connectionControl = wimac.Services.ConnectionControl("connectionControl") 
        self.controlServices.append( self.connectionControl )
        
        self.classifier = Classifier()
        self.synchronizer = openwns.Tools.Synchronizer()

        self.bufferSep = FlowSeparator(
             wimac.KeyBuilder.CIDKeyBuilder(),
             openwns.FlowSeparator.PrototypeCreator(
             'buffer', openwns.Buffer.Dropping( size = 100,
                                       lossRatioProbeName = "wimac.buffer.lossRatio",
                                       sizeProbeName = "wimac.buffer.size")))

        self.branchDispatcher = openwns.ldk.Multiplexer.Dispatcher(opcodeSize = 0)
        # size of CRC command is abused to model overhead due to entire MAC header (48 bit without CRC)
        self.crc = openwns.CRC.CRC("errormodelling",
                               lossRatioProbeName = "wimac.crc.CRCLossRatio",
                               CRCsize = config.parametersMAC.pduOverhead,
                               isDropping = False)
        self.errormodelling = wimac.ErrorModelling.ErrorModelling('phyUser','phyUser',PrintMappings=False)
        self.compoundSwitch = wimac.CompoundSwitch.CompoundSwitch()

        self.phyUser = wimac.PhyUser.PhyUser(
            centerFrequency = config.parametersSystem.centerFrequency,
            bandwidth = config.parametersPhy.channelBandwidth,
            numberOfSubCarrier = config.parametersPhy.subchannels )

        self.topTpProbe = openwns.Probe.Window( "TopTp", "wimac.top", windowSize=0.01 )        
        self.topPProbe = openwns.Probe.Packet( "TopP", "wimac.top" )
        self.bottomThroughputProbe = openwns.Probe.Window( "BottomThroughput", "wimac.bottom", windowSize=0.01 )
        self.bottomPacketProbe = openwns.Probe.Packet( "BottomPacket", "wimac.bottom" )

    def buildFUN(self, config):
        #DataPlane
        self.upperconvergence = Node(self.upperConvergenceName, self.upperconvergence)
        self.topTpProbe = Node('topTpProbe', self.topTpProbe)
        self.topPProbe = Node('topPProbe', self.topPProbe)
        self.bottomThroughputProbe = Node('bottomThroughputProbe', self.bottomThroughputProbe)
        self.bottomPacketProbe = Node('bottomPacketProbe', self.bottomPacketProbe)
        self.classifier = Node('classifier', self.classifier)
        self.synchronizer = Node('synchronizer', self.synchronizer)
        self.bufferSep = Node('bufferSep', self.bufferSep)
        self.crc = Node('crc', self.crc)
        self.errormodelling = Node('errormodelling', self.errormodelling)
        self.phyUser = Node('phyUser', self.phyUser)
        self.framehead = Node('framehead', self.framehead)
        self.dlmapcollector = Node('dlmapcollector', self.dlmapcollector)
        self.ulmapcollector = Node('ulmapcollector', self.ulmapcollector)
        self.dlscheduler = Node('dlscheduler', self.dlscheduler)
        self.ulscheduler = Node('ulscheduler', self.ulscheduler)
        self.ulContentionRNGc = Node('ulcontentionrngc', self.ulContentionRNGc)
        self.frameBuilder = Node('frameBuilder', self.frameBuilder)

        #Dataplane
        self.compoundSwitch = Node('compoundSwitchWiMAX', self.compoundSwitch)

        self.fun.setFunctionalUnits(
        self.compoundSwitch,
        self.upperconvergence,
        self.topTpProbe,
        self.topPProbe,
        self.classifier,   
        self.synchronizer,
        self.crc,
        self.errormodelling,
        self.phyUser,
        self.bufferSep,
        self.framehead,
        self.dlmapcollector,
        self.ulmapcollector,
        self.dlscheduler,
        self.ulContentionRNGc,
        self.ulscheduler,
        self.frameBuilder
        )





