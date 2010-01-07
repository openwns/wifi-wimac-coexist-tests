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
from rise.PhyMode import PhyMode,PhyModeMapper
from constanze.node import IPBinding, IPListenerBinding, Listener
from openwns.pyconfig import Frozen
from openwns.pyconfig import Sealed

import wimac.support.Nodes
import wimac.KeyBuilder as CIDKeyBuilder
import wimac.evaluation.default
import wimac.LLMapping


from support.WiMACParameters import ParametersSystem, ParametersOFDM, ParametersMAC, ParametersPropagation, ParametersPropagation_NLOS

associations = {}

####################################################
###  Distinguished Simulation Settings             #
####################################################

class Conf(Frozen):
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
    positionErrorVariance = 0.0
    numberOfTimeSlots = 100
    
    #only considered for mapsizes not synchronized with actual scheduling strategy
    dlStrategy = "ProportionalFairDL"
    ulStrategy = "ProportionalFairUL"
    
    arrayLayout = "circular" 
    eirpLimited = False
    packetSize = config.configWiMAX.packetSize # Needed by PseudoBWReq
    
    nRSs = 0
    nRmSs = 0
    nSSs = 1

WNS.modules.wimac.parametersPHY = Conf.parametersPhy

####################################################
### Instantiating Nodes and setting Traffic        #
####################################################
# one RANG
rangWiMAX = wimac.support.Nodes.RANG()
                                        
if config.noIPHeader:
    rangWiMAX.nl.ipHeader.config.headerSize = 0


# BSs with some SSs each

def stationID():
    id = 1
    while (True):
        yield id
        id += 1

stationIDs = stationID()

accessPoints = []

bs = wimac.support.Nodes.BaseStation(stationIDs.next(), Conf)

bs.phy.ofdmaStation.rxFrequency = config.frequency
bs.phy.ofdmaStation.txFrequency = config.frequency
bs.dll.logger.level = 2
associations[bs]=[]
WNS.simulationModel.nodes.append(bs)

# The RANG only has one IPListenerBinding that is attached
# to the listener. The listener is the only traffic sink
# within the RANG
ipListenerBinding = IPListenerBinding(rangWiMAX.nl.domainName)
listener = Listener(rangWiMAX.nl.domainName + ".listener")
rangWiMAX.load.addListener(ipListenerBinding, listener)

userTerminals = []

ss = wimac.support.Nodes.SubscriberStation(stationIDs.next(), Conf)

ss.phy.ofdmaStation.rxFrequency = config.frequency
ss.phy.ofdmaStation.txFrequency = config.frequency
if config.configWiMAX.trafficDLenabled and config.configWiMAX.trafficDL > 0.0:
    poissonDL = constanze.traffic.Poisson(
        offset = 0.01, 
        throughput = config.configWiMAX.trafficDL, 
        packetSize = config.configWiMAX.packetSize)
    ipBinding = IPBinding(rangWiMAX.nl.domainName, ss.nl.domainName)
    rangWiMAX.load.addTraffic(ipBinding, poissonDL)

if config.configWiMAX.trafficULenabled and config.configWiMAX.trafficUL > 0.0:
    poissonUL = constanze.traffic.Poisson(
        offset = 0.0, 
        throughput = 
        config.configWiMAX.trafficUL, 
        packetSize = config.configWiMAX.packetSize)
else:
    poissonUL = constanze.traffic.CBR0(duration = 1E-6,
                        throughput = 1.0, 
                        packetSize = config.configWiMAX.packetSize)       
      
ipBinding = IPBinding(ss.nl.domainName, rangWiMAX.nl.domainName)
ss.load.addTraffic(ipBinding, poissonUL)
ipListenerBinding = IPListenerBinding(ss.nl.domainName)
listener = Listener(ss.nl.domainName + ".listener")
ss.load.addListener(ipListenerBinding, listener)
ss.dll.associate(bs.dll)

if config.noIPHeader:
    ss.nl.ipHeader.config.headerSize = 0

associations[bs].append(ss)
userTerminals.append(ss)
WNS.simulationModel.nodes.append(ss)
rangWiMAX.dll.addAP(bs)

WNS.simulationModel.nodes.append(rangWiMAX)

class AllBPSKMapper(PhyModeMapper):
    def __init__(self, symbolDuration, subCarriersPerSubChannel):
        super(AllBPSKMapper, self).__init__(symbolDuration, subCarriersPerSubChannel)

        self.setMinimumSINR(-1000.0);
        self.addPhyMode(Interval(-1000.0,   1000.0, "(]"), wimac.LLMapping.WIMAXPhyMode1)

if not config.configWiMAX.adaptiveMCS:
    symbolDuration = Conf.parametersPhy.symbolDuration
    subCarriersPerSubChannel = Conf.parametersPhy.dataSubCarrier
    
    bs.dll.dlscheduler.config.txScheduler.registry.setPhyModeMapper(AllBPSKMapper(
        symbolDuration, subCarriersPerSubChannel))
    bs.dll.ulscheduler.config.rxScheduler.registry.setPhyModeMapper(AllBPSKMapper(
        symbolDuration, subCarriersPerSubChannel))
    ss.dll.ulscheduler.config.txScheduler.registry.setPhyModeMapper(AllBPSKMapper(
        symbolDuration, subCarriersPerSubChannel))
        
    

bsIDs = []
bsIDs.append(bs.dll.stationID)
ssIDs = []
ssIDs.append(ss.dll.stationID)

posBS = openwns.geometry.position.Position(config.distanceAP_BS, 0, 0)
bs.mobility.mobility.setCoords(posBS)
print "Created BS at (" + str(posBS) + ")"

posSS = pos = openwns.geometry.position.Position(config.distanceAP_BS, config.configWiMAX.distance_BS_SS, 0)
ss.mobility.mobility.setCoords(posSS)
print "Created SS at (" + str(posSS) + ")"

prefix = "layer2"
for node in [ss, bs]:
    rest = node.dll.topTpProbe.config.incomingBitThroughputProbeName.split(ss.dll.topPProbe.config.prefix)[1]
    node.dll.topTpProbe.config.incomingBitThroughputProbeName = prefix + rest
    rest = node.dll.topTpProbe.config.aggregatedBitThroughputProbeName.split(ss.dll.topPProbe.config.prefix)[1]
    node.dll.topTpProbe.config.aggregatedBitThroughputProbeName = prefix + rest
    rest = node.dll.topPProbe.config.incomingDelayProbeName.split(ss.dll.topPProbe.config.prefix)[1]
    node.dll.topPProbe.config.incomingDelayProbeName = prefix + rest
    node.dll.topTpProbe.config.windowSize = config.probeWindowSize
    node.dll.topTpProbe.config.sampleInterval = config.probeWindowSize
    node.dll.crc.config.lossRatioProbeName = "layer2.CRCloss"
    node.dll.crc.config.isDropping = True
    node.dll.phyUser.config.cirProbeName = "layer2.dataSINR"

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
