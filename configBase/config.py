###############################################################################
# This file is part of openWNS (open Wireless Network Simulator)
# _____________________________________________________________________________
#
# Copyright (C) 2004-2008
# Chair of Communication Networks (ComNets)
# Kopernikusstr. 16, D-52074 Aachen, Germany
# phone: ++49-241-80-27910,
# fax: ++49-241-80-22242
# email: info@openwns.org
# www: http://www.openwns.org
# _____________________________________________________________________________
#
# openWNS is free software; you can redistribute it and/or modify it under the
# terms of the GNU Lesser General Public License version 2 as published by the
# Free Software Foundation;
#
# openWNS is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for more
# details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
import os
import sys
sys.path.append(os.path.join('.','commonConfig'))
sys.path.append(os.path.join('..','commonConfig'))

import rise
import openwns.node
import openwns
import openwns.evaluation.default
import constanze.traffic
import ip.IP
import ip.AddressResolver
from ip.VirtualARP import VirtualARPServer
from ip.VirtualDHCP import VirtualDHCPServer
from ip.VirtualDNS import VirtualDNSServer

import ofdmaphy.OFDMAPhy
import rise.Scenario
import rise.Mobility
from constanze.node import IPBinding, IPListenerBinding, Listener
from openwns.pyconfig import Frozen
from openwns.pyconfig import Sealed

import Nodes
import Layer2
import wimac.KeyBuilder as CIDKeyBuilder
import wimac.evaluation.default

from support.WiMACParameters import ParametersSystem, ParametersOFDM, ParametersMAC, ParametersPropagation, ParametersPropagation_NLOS
from support.scenarioSupport import setupRelayScenario
from support.scenarioSupport import calculateScenarioRadius, numberOfAccessPointsForHexagonalScenario
import support.PostProcessor as PostProcessor

import random
random.seed(7)


associations = {}

####################################################
###  Distinguished Simulation Settings             #
####################################################
class Config(Frozen):
    # Set basic WiMAX Parameters
    parametersSystem      = ParametersSystem
    parametersPhy         = ParametersOFDM
    parametersMAC         = ParametersMAC
    parametersPropagation = ParametersPropagation

    # WiMAC Layer2 forming
    beamforming = False
    maxBeams = 1
    friendliness_dBm = "-85 dBm"
    maxBursts = 20

    #only considered for mapsizes not synchronized with actual scheduling strategy
    dlStrategy = "ProportionalFairDL"
    ulStrategy = "ProportionalFairUL"

    arrayLayout = "linear" #"circular"
    eirpLimited = False
    positionErrorVariance = 0.0

    packetSize = 3000 #in bit
    trafficUL = 10000000 # bit/s per station
    trafficDL = 10000000

    nSectors = 1
    nCircles = 0
    nBSs = numberOfAccessPointsForHexagonalScenario(nCircles)
    nRSs = 0
    nSSs = 1
    nRmSs = 0

    numberOfStations =  nBSs * ( nRSs + nSSs + nRmSs * nRSs + 1 )

    scenarioXSize = 500#2 * calculateScenarioRadius(parametersSystem.clusterOrder, nCircles, parametersSystem.cellRadius)
    scenarioYSize = 500#scenarioXSize

    RSDistance = parametersSystem.cellRadius / 2.0

    writeOutput = True
    operationModeRelays = 'SDM' #'TDM' 'FDM'

#config = Config()
####################################################
# General Simulation settings                      #
####################################################

# create an instance of the WNS configuration
# The variable must be called WNS!!!!
WNS = openwns.Simulator(simulationModel = openwns.node.NodeSimulationModel())
WNS.maxSimTime = 0.1 # seconds
#Probe settings
WNS.masterLogger.backtrace.enabled = False
WNS.masterLogger.enabled = True
#WNS.masterLogger.loggerChain = [ wns.Logger.FormatOutputPair( wns.Logger.Console(), wns.Logger.File()) ]
WNS.outputStrategy = openwns.simulator.OutputStrategy.DELETE
WNS.statusWriteInterval = 120 # in seconds
WNS.probesWriteInterval = 3600 # in seconds


####################################################
### PHY (PHysical Layer) settings                  #
####################################################
riseConfig = WNS.modules.rise
riseConfig.debug.transmitter = False
riseConfig.debug.main = False
riseConfig.debug.antennas = False

# from ./modules/phy/OFDMAPhy--unstable--0.3/PyConfig/ofdmaphy/OFDMAPhy.py
ofdmaPhyConfig = WNS.modules.ofdmaPhy
ofdmaPhySystem = ofdmaphy.OFDMAPhy.OFDMASystem('ofdma')
ofdmaPhySystem.Scenario = rise.Scenario.Scenario(Config.scenarioXSize, Config.scenarioYSize)
ofdmaPhyConfig.systems.append(ofdmaPhySystem)

####################################################
### WiMAC settings                                 #
####################################################

WNS.modules.wimac.parametersPHY = Config.parametersPhy

####################################################
### Instantiating Nodes and setting Traffic        #
####################################################
# one RANG
rangWiMAX = Nodes.RANG()

# BSs with some SSs each

def stationID():
    id = 1
    while (True):
        yield id
        id += 1

stationIDs = stationID()

accessPoints = []

for i in xrange(Config.nBSs):
    bs = Nodes.BaseStation(stationIDs.next(), Config)
    bs.dll.logger.level = 2
    accessPoints.append(bs)
    associations[bs]=[]
    WNS.simulationModel.nodes.append(bs)

# The RANG only has one IPListenerBinding that is attached
# to the listener. The listener is the only traffic sink
# within the RANG
ipListenerBinding = IPListenerBinding(rangWiMAX.nl.domainName)
listener = Listener(rangWiMAX.nl.domainName + ".listener")
rangWiMAX.load.addListener(ipListenerBinding, listener)

userTerminals = []
k = 0
for bs in accessPoints:
    for i in xrange(Config.nSSs):
        ss = Nodes.SubscriberStation(stationIDs.next(), Config)
        poissonDL = constanze.traffic.Poisson(offset = 0.05, throughput = Config.trafficDL, packetSize = Config.packetSize)
        ipBinding = IPBinding(rangWiMAX.nl.domainName, ss.nl.domainName)
        rangWiMAX.load.addTraffic(ipBinding, poissonDL)
        
        poissonUL = constanze.traffic.Poisson(offset = 0.0, throughput = Config.trafficUL, packetSize = Config.packetSize)
        ipBinding = IPBinding(ss.nl.domainName, rangWiMAX.nl.domainName)
        ss.load.addTraffic(ipBinding, poissonUL)
        ipListenerBinding = IPListenerBinding(ss.nl.domainName)
        listener = Listener(ss.nl.domainName + ".listener")
        ss.load.addListener(ipListenerBinding, listener)
        ss.dll.associate(bs.dll)
        associations[bs].append(ss)
        userTerminals.append(ss)
        WNS.simulationModel.nodes.append(ss)
    rangWiMAX.dll.addAP(bs)
    k += 1

# each access point is connected to some fixed relay stations
k = 0
relayStations = []
for bs in accessPoints:
    l = 0
    for i in xrange(Config.nRSs):
        rs = Nodes.RelayStation(stationIDs.next(), Config)
        rs.dll.associate(bs.dll)
        associations[rs]=[]
        associations[bs].append(rs)
        relayStations.append(rs)
        WNS.simulationModel.nodes.append(rs)

        l += 1
    k += 1

# each relay station is connected to some remote stations
remoteStations = []
k = 0
for bs in accessPoints:
    l = 0
    for rs in associations[bs]:
        if rs.dll.stationType != 'FRS':
            continue
        i = 0
        for i in xrange(Config.nRmSs):
            ss = Nodes.SubscriberStation(stationIDs.next(), Config)
            ss.dll.logger.level = 2
            cbrDL = constanze.traffic.CBR(offset = 0.05, throughput = Config.trafficDL, packetSize = Config.packetSize)
            ipBinding = IPBinding(rangWiMAX.nl.domainName, ss.nl.domainName)
            rangWiMAX.load.addTraffic(ipBinding, cbrDL)

            cbrUL = constanze.traffic.CBR(offset = 0.0, throughput = Config.trafficUL, packetSize = Config.packetSize)
            ipBinding = IPBinding(ss.nl.domainName, rangWiMAX.nl.domainName)
            ss.load.addTraffic(ipBinding, cbrUL)
            ipListenerBinding = IPListenerBinding(ss.nl.domainName)
            listener = Listener(ss.nl.domainName + ".listener")
            ss.load.addListener(ipListenerBinding, listener)

            ss.dll.associate(rs.dll)
            # 192.168.1.254 = "nl address of RANG" = rangWiMAX.nl.address ?
            associations[rs].append(ss)
            remoteStations.append(ss)
            WNS.simulationModel.nodes.append(ss)
        l += 1
    k += 1

WNS.simulationModel.nodes.append(rangWiMAX)

# Positions of the stations are determined here
setupRelayScenario(Config, WNS.simulationModel.nodes, associations)

#set mobility
intracellMobility = False

if(intracellMobility):

    for ss in userTerminals:
        associatedBS = None
        for bs in accessPoints:
            if bs.dll.stationID == ss.dll.associateTo:
                associatedBS = bs
                bsPos = associatedBS.mobility.mobility.getCoords()
                break
        if associatedBS == None:
            print 'no associated BS found'
            exit(1)

        # too large, SS might be outside the hexagon
        maxDistance_ = Config.parametersSystem.cellRadius
        # too small, corners are not filled
        # maxDistance_ = (math.sqrt(3.0)/2.0) * Config.parametersSystem.cellRadius
        # equal area
        # maxDistance_ = math.sqrt( 3.0/2.0/math.pi*math.sqrt(3.0)) * Config.parametersSystem.cellRadius
        ss.mobility.mobility = rise.Mobility.BrownianCirc(center=bsPos,
                                                          maxDistance = maxDistance_ )

# TODO: for multihop simulations: replicate the code for remote stations

#plotStations.plot()


# Here we specify the stations we want to probe.
# This is usually only the center cell with the BS and its associated stations.
loggingStationIDs = []
pos = accessPoints[0].mobility.mobility.getCoords()
print "Created BS at (" + str(pos) + ")"


for st in associations[accessPoints[0]]:
    if st.dll.stationType == 'FRS':
        loggingStationIDs.append(st.dll.stationID)
        for st2 in associations[st]:
            if st2.dll.stationType == 'UT':
                loggingStationIDs.append(st2.dll.stationID)

    if st.dll.stationType == 'UT':
        loggingStationIDs.append(st.dll.stationID)
        pos = st.mobility.mobility.getCoords()
        print "Created SS at (" + str(pos) + ")"

wimac.evaluation.default.installEvaluation(WNS, [1], loggingStationIDs)
openwns.evaluation.default.installEvaluation(WNS)

# one Virtual ARP Zone
varpWiMAX = VirtualARPServer("vARP", "WIMAXRAN")
WNS.simulationModel.nodes = [varpWiMAX] + WNS.simulationModel.nodes

vdhcpWiMAX = VirtualDHCPServer("vDHCP@",
                          "WIMAXRAN",
                          "192.168.0.2", "192.168.254.253",
                          "255.255.0.0")

vdnsWiMAX = VirtualDNSServer("vDNS", "ip.DEFAULT.GLOBALWiMAX")
WNS.simulationModel.nodes.append(vdnsWiMAX)

WNS.simulationModel.nodes.append(vdhcpWiMAX)

### PostProcessor ###
postProcessor = PostProcessor.WiMACPostProcessor()
postProcessor.Config = Config
postProcessor.accessPoints = accessPoints
postProcessor.relayStations = relayStations
postProcessor.userTerminals = userTerminals
postProcessor.remoteStations = remoteStations
WNS.addPostProcessing(postProcessor)

import openwns

import wifimac.support.Transceiver

#######################
# Simulation parameters
#
# Simulation of the string topology: all nodes are placed equidistantly
# on a string, on each end of the string, an AP is positioned
# Traffic is either DL only or bidirectional
#
simTime = 0.000001
settlingTime = 3.0
commonLoggerLevel = 1
dllLoggerLevel = 2

# length of the string
numMPs = 0
numSTAs = 1
numAPs = 1
distanceBetweenMPs = 50
verticalDistanceSTAandMP = 10

# load
meanPacketSize = 1480 * 8
offeredDL = 6.0e6
offeredUL = 0.0e6
ulIsActive = False
dlIsActive = True
startDelayUL = 1.01
startDelayDL = 1.02
# wether MPs send/receive traffic
activeMPs = False

# Available frequencies for bss and backbone, in MHz
meshFrequency = 5500
bssFrequencies = [5470]
# End simulation parameters
###########################

####################
# Node configuration

# configuration class for AP and MP mesh transceivers
class MyMeshTransceiver(wifimac.support.Transceiver.Mesh):
    def __init__(self, beaconDelay, frequency):
        super(MyMeshTransceiver, self).__init__(frequency)
        # changes to the default config
        self.layer2.beacon.delay = beaconDelay

# configuration class for AP and MP BSS transceivers
class MyBSSTransceiver(wifimac.support.Transceiver.Mesh):
    def __init__(self, beaconDelay, frequency):
        super(MyBSSTransceiver, self).__init__(frequency)
        self.layer2.beacon.delay = beaconDelay
        self.layer2.rtsctsThreshold = 800#1e6*8
        self.layer2.txop.txopLimit = 0.01

# configuration class for STAs
class MySTAConfig(wifimac.support.Transceiver.Station):
    def __init__(self, initFrequency, position, scanFrequencies, scanDurationPerFrequency):
        super(MySTAConfig, self).__init__(frequency = initFrequency,
                                          position = position,
                                          scanFrequencies = scanFrequencies,
                                          scanDuration = scanDurationPerFrequency)
        self.layer2.rtsctsThreshold = 800#1e6*8

# End node configuration
########################

###########################################
# Scenario setup etc. is in configCommon.py
execfile('configCommon.py')
