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

import openwns
import openwns.logger
import openwns.geometry.position
import openwns.CRC
from openwns import dB, dBm, fromdB, fromdBm
from openwns.interval import Interval

import ofdmaphy.OFDMAPhy

import dll

import constanze.traffic
import constanze.node

import wifimac.support
import wifimac.evaluation.default
import wifimac.evaluation.ip
import wifimac.support.Transceiver
from wifimac.lowerMAC.RateAdaptation import Opportunistic
import wifimac.convergence.FrameSynchronization

commonLoggerLevel = 2
dllLoggerLevel = 2

bssFrequencies = [config.frequency]

# configuration class for AP and MP BSS transceivers
class MyBSSTransceiver(wifimac.support.Transceiver.Mesh):
    def __init__(self, beaconDelay, frequency):
        super(MyBSSTransceiver, self).__init__(frequency)
        self.layer2.beacon.delay = beaconDelay
        self.layer2.rtsctsThreshold = 1e6 * 8
        if config.configWiFi.adaptiveMCS:
            self.layer2.ra.raStrategy = Opportunistic()

# configuration class for STAs
class MySTAConfig(wifimac.support.Transceiver.Station):
    def __init__(self, initFrequency, position, scanFrequencies, scanDurationPerFrequency):
        super(MySTAConfig, self).__init__(frequency = initFrequency,
                                          position = position,
                                          scanFrequencies = scanFrequencies,
                                          scanDuration = scanDurationPerFrequency)
        self.layer2.rtsctsThreshold = 1e6 * 8
        if config.configWiFi.adaptiveMCS:
            self.layer2.ra.raStrategy = Opportunistic()

ofdmaPhyConfig = WNS.modules.ofdmaPhy
managerPool = wifimac.support.ChannelManagerPool(scenario = scenario,
                                                 numMeshChannels = 1,
                                                 ofdmaPhyConfig = ofdmaPhyConfig)

######################################
# Radio channel propagation parameters
xmax = config.distanceAP_BS
ymax = max(config.configWiMAX.distance_BS_SS,
    config.configWiFi.distance_AP_STA)

myPathloss = rise.scenario.Pathloss.PyFunction(
    validFrequencies = Interval(2000, 6000),
    validDistances = Interval(2, 5000), #[m]
    offset = dB(-27.552219),
    freqFactor = 20,
    distFactor = 35,
    distanceUnit = "m", # only for the formula, not for validDistances
    minPathloss = dB(42), # pathloss at 2m distance
    outOfMinRange = rise.scenario.Pathloss.Constant("42 dB"),
    outOfMaxRange = rise.scenario.Pathloss.Deny(),
    scenarioWrap = False,
    sizeX = xmax,
    sizeY = ymax)
myShadowing = rise.scenario.Shadowing.No()
myFastFading = rise.scenario.FastFading.No()
propagationConfig = rise.scenario.Propagation.Configuration(
    pathloss = myPathloss,
    shadowing = myShadowing,
    fastFading = myFastFading)
# End radio channel propagation parameters
##########################################

###################################
#Create nodes using the NodeCreator
nc = wifimac.support.NodeCreator(propagationConfig)

# one RANG
rang = nc.createRANG(listener = config.configWiFi.trafficULenabled, loggerLevel = commonLoggerLevel)

if config.noIPHeader:
  rang.nl.ipHeader.config.headerSize = 0

WNS.simulationModel.nodes.append(rang)

# create (magic) service nodes for ARP, DNS, Pathselection, Capability Information
WNS.simulationModel.nodes.append(nc.createVARP(commonLoggerLevel))
WNS.simulationModel.nodes.append(nc.createVDNS(commonLoggerLevel))
WNS.simulationModel.nodes.append(nc.createVPS(2, commonLoggerLevel))
WNS.simulationModel.nodes.append(nc.createVCIB(commonLoggerLevel))

# Single instance of id-generator for all nodes with ids
idGen = wifimac.support.idGenerator()
idGen.nextId = firstWiFiID

# save IDs for probes
apIDs = []
staIDs = []
apAdrs = []

# selection of the BSS-frequency: iterating over the BSS-set
bssCount = 0

# One AP at [0, 0, 0]
apPos = openwns.geometry.position.Position(0, 0, 0)
apConfig = wifimac.support.Node(position = apPos)
apConfig.transceivers.append(MyBSSTransceiver(beaconDelay = 0.001, frequency = config.frequency))
ap = nc.createAP(idGen = idGen,
                 managerPool = managerPool,
                 config = apConfig)
ap.logger.level = commonLoggerLevel
ap.dll.logger.level = dllLoggerLevel
WNS.simulationModel.nodes.append(ap)
apIDs.append(ap.id)
apAdrs.extend(ap.dll.addresses)
rang.dll.addAP(ap)
print "Created AP at (" + str(apPos) + ")"

# One STA at [0, distance_AP_STA, 0]
staPos = openwns.geometry.position.Position(0, config.configWiFi.distance_AP_STA, 0)
staConfig = MySTAConfig(initFrequency = bssFrequencies[0],
                        position = staPos,
                        scanFrequencies = bssFrequencies,
                        scanDurationPerFrequency = 0.3)

sta = nc.createSTA(idGen, managerPool, rang,
                    config = staConfig,
                    loggerLevel = commonLoggerLevel,
                    dllLoggerLevel = dllLoggerLevel)
                                        
if config.noIPHeader:
    sta.nl.ipHeader.config.headerSize = 0

                    
print "Created STA at (" + str(staPos) + ")"

if(config.configWiFi.trafficDLenabled):
    # DL load RANG->STA
    tDL = constanze.traffic.Poisson(
        0.0, 
        config.configWiFi.trafficDL, 
        config.configWiFi.packetSize, 
        parentLogger = rang.logger)
    ipBinding = constanze.node.IPBinding(rang.nl.domainName, sta.nl.domainName, parentLogger = rang.logger)
    rang.load.addTraffic(ipBinding, tDL)

    # Listener at STA for DL
    ipListenerBinding = constanze.node.IPListenerBinding(sta.nl.domainName, parentLogger = sta.logger)
    listener = constanze.node.Listener(sta.nl.domainName + ".listener", probeWindow = 0.1, parentLogger = sta.logger)
    sta.load.addListener(ipListenerBinding, listener)

if(config.configWiFi.trafficULenabled):
    # UL load STA->RANG
    tUL = constanze.traffic.Poisson(
        0.0, 
        config.configWiFi.trafficUL, 
        config.configWiFi.packetSize,  
        parentLogger = sta.logger)
    ipBinding = constanze.node.IPBinding(sta.nl.domainName, rang.nl.domainName, parentLogger=sta.logger)
    sta.load.addTraffic(ipBinding, tUL)

prefix = "layer2"
for node in [sta, ap]:
    fu = node.dll.fun.functionalUnit[0]
    assert isinstance(fu, openwns.Probe.Window), "Dirty hack failed: FU Nr. 0 in WiFi FUN is not the Window Probe"
    rest = fu.incomingBitThroughputProbeName.split(fu.prefix)[1]
    fu.incomingBitThroughputProbeName = prefix + rest
    fu = node.dll.fun.functionalUnit[1]    
    assert isinstance(fu, openwns.Probe.Packet), "Dirty hack failed: FU Nr. 1 in WiFi FUN is not the Packet Probe"
    rest = fu.incomingDelayProbeName.split(fu.prefix)[1]
    fu.incomingDelayProbeName = prefix + rest
    
    for fu in node.dll.fun.functionalUnit:
        if isinstance(fu, wifimac.convergence.FrameSynchronization):
            fu.sinrProbeName = "layer2.dataSINR"
              
    for fu in node.dll.fun.functionalUnit:
        if isinstance(fu, openwns.CRC.CRC):
            fu.lossRatioProbeName = "layer2.CRCloss"

# Add STA
WNS.simulationModel.nodes.append(sta)
staIDs.append(sta.id)
