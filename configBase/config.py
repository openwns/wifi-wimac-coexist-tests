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

import rise
import openwns
import openwns.evaluation.default
import openwns.evaluation.generators
import openwns.evaluation.tree
from openwns.pyconfig import Frozen
from openwns.pyconfig import Sealed

import ofdmaphy.OFDMAPhy
import rise.Scenario
import rise.Mobility

import random
random.seed(7)

# Scenario: 
# 1 WiFi AP with 1 STA at fixed distance "distance_AP_STA"
# 1 WiMAX BS with 1 SS at fixed distance "distance_BS_SS"
# Distance "distanceAP_BS" between BS and AP
#
#
#  [x,y,z]=[0,0,0]   
#         |
#         V        distanceAP_BS
#      AP O<------------------------>X BS
#         ^                          ^
#         |                          |
#         |distance_AP_STA           |distance_BS_SS
#         |                          |
#         v                          v
#     STA o                          x SS
#

class Config(object):
    
    class ConfigWiMAX(object):
        distance_BS_SS = 50.0
        
        # Even if False we transmit one packet to establish flow
        trafficULenabled = True     
        trafficDLenabled = True
        trafficUL = 1E6
        trafficDL = 1E6
        packetSize = 3000.0
        
        # If False only BPSK 1/2 is used no mather what channel estimation decides
        adaptiveMCS = False
    
    class ConfigWiFi(object):
        distance_AP_STA = 50.0                
        trafficULenabled = True
        trafficDLenabled = False
        trafficUL = 2E6
        trafficDL = 0
        packetSize = 3000.0
        
        # If False only 5Mbps is used no mather what channel estimation decides
        adaptiveMCS = False          
    
    distanceAP_BS = 1.0
    frequency = 5470.0 #GHz
    noIPHeader = True #Set to true to set IP header to 0
    probeWindowSize = 0.05 # Probe per 5 WiMAX frames
    
    simTime = 0.8
    # When should probing start?
    settlingTime = 0.05
    configWiMAX = ConfigWiMAX()
    configWiFi = ConfigWiFi()

config = Config()

firstWiFiID = 100    

if not config.configWiFi.trafficDLenabled:
    config.configWiFi.trafficDL = 0.0
if not config.configWiFi.trafficULenabled:
    config.configWiFi.trafficUL = 0.0
if not config.configWiMAX.trafficDLenabled:
    config.configWiMAX.trafficDL = 0.0
if not config.configWiMAX.trafficULenabled:
    config.configWiMAX.trafficUL = 0.0
    
WNS = openwns.Simulator(simulationModel = openwns.node.NodeSimulationModel())
WNS.maxSimTime = config.simTime # seconds
WNS.masterLogger.enabled = True
WNS.outputStrategy = openwns.simulator.OutputStrategy.DELETE
WNS.statusWriteInterval = 30 # in seconds
WNS.probesWriteInterval = 60 # in seconds

# ProbeBus:
#                                                             /---IdX---PDF
#                                                            /      .
#                                                  /---STA---       .
#                                                 /          \      .
#                                                /            \---IdY---PDF      
#                               /---WiFi---PDF---
#                              /                \---AP---PDF
# source---SettlingTime--PDF---
#                              \                /---BS---PDF
#                               \---WiMAC--PDF---
#                                                \           /---IdA---PDF
#                                                 \         /      .
#                                                  \---SS---       .
#                                                           \      .
#                                                            \---IdB---PDF

def bySystemStaTypeIdProbe(node, 
                      wifiIds, 
                      wimaxIds, 
                      minX, 
                      maxX, 
                      resolution = 1000, 
                      probeType = "Moments",
                      wifiPDUContext = False):
  
    if probeType == "Moments":
        probe = openwns.evaluation.generators.Moments()
    elif probeType == "PDF":
        probe = openwns.evaluation.generators.PDF(
            minXValue = p.minX, maxXValue = p.maxX, resolution = p.resolution)
    else:
        assert False, "Unknown probe type " + probeType
  
    # Global probe for both systems
    node.getLeafs().appendChildren(probe)           

    wifiNode = node.appendChildren(openwns.evaluation.generators.Accept(
                        by = 'MAC.Id', 
                        ifIn = wifiIds, 
                        suffix = 'WiFi'))
                        
    if wifiPDUContext:
        wifiNode.getLeafs().appendChildren(openwns.evaluation.generators.Accept(
                            by = 'MAC.CompoundIsForMe', 
                            ifIn = [1]))
        wifiNode = wifiNode.getLeafs().appendChildren(openwns.evaluation.generators.Accept(
                            by = 'MAC.CompoundIsUnicast', 
                            ifIn = [1]))
                           
    # WiFi probe for both station types
    wifiNode.getLeafs().appendChildren(probe)            
                                                       
    bsNode = wifiNode.appendChildren(openwns.evaluation.generators.Accept(
                        by = 'MAC.StationType', 
                        ifIn = [1], suffix = 'BS'))
    utNode = wifiNode.appendChildren(openwns.evaluation.generators.Accept(
                        by = 'MAC.StationType', 
                        ifIn = [3], suffix = 'UT'))
    bsNode.appendChildren(openwns.evaluation.generators.Separate(
                        by = 'MAC.Id', 
                        forAll = [wifiIds[0]], 
                        format = 'Id%d'))
    utNode.appendChildren(openwns.evaluation.generators.Separate(
                        by = 'MAC.Id', 
                        forAll = wifiIds[1:], 
                        format = 'Id%d'))
                                              
    wimaxNode = node.appendChildren(openwns.evaluation.generators.Accept(
                        by = 'MAC.Id', 
                        ifIn = wimaxIds, 
                        suffix = 'WiMAX'))
                        
    # WiMAC probe for both station types
    wimaxNode.getLeafs().appendChildren(probe)                         
                        
    bsNode = wimaxNode.appendChildren(openwns.evaluation.generators.Accept(
                        by = 'MAC.StationType', 
                        ifIn = [1], suffix = 'BS'))
    utNode = wimaxNode.appendChildren(openwns.evaluation.generators.Accept(
                        by = 'MAC.StationType', 
                        ifIn = [3], suffix = 'UT'))
    bsNode.appendChildren(openwns.evaluation.generators.Separate(
                        by = 'MAC.Id', 
                        forAll = [wimaxIds[0]], 
                        format = 'Id%d'))
    utNode.appendChildren(openwns.evaluation.generators.Separate(
                        by = 'MAC.Id', 
                        forAll = wimaxIds[1:], 
                        format = 'Id%d'))
                         
    # Final PDF
    node.getLeafs().appendChildren(probe)
    
####################################################
### PHY (PHysical Layer) settings                  #
####################################################
riseConfig = WNS.modules.rise
riseConfig.debug.transmitter = False
riseConfig.debug.main = False
riseConfig.debug.antennas = False

scenario = rise.Scenario.Scenario()

ofdmaPhyConfig = WNS.modules.ofdmaPhy
ofdmaPhySystem = ofdmaphy.OFDMAPhy.OFDMASystem('ofdma')
ofdmaPhySystem.Scenario = scenario
ofdmaPhyConfig.systems.append(ofdmaPhySystem)

execfile('configWiFi.py')
execfile('configWiMAC.py')

# Use WiFi channel model for WiMAX
ss.phy.ofdmaStation.receiver = sta.phy.ofdmaStation.receiver
ss.phy.ofdmaStation.transmitter = sta.phy.ofdmaStation.transmitter
bs.phy.ofdmaStation.receiver = ap.phy[0].ofdmaStation.receiver
bs.phy.ofdmaStation.transmitter = ap.phy[0].ofdmaStation.transmitter


maxDL = max(config.configWiMAX.trafficDL, config.configWiFi.trafficDL)
maxUL = max(config.configWiMAX.trafficUL, config.configWiFi.trafficUL)

wifiIds = apIDs + staIDs
wimaxIds = bsIDs + ssIDs 

class ProbeData(object):
    name = None
    minX = None
    maxX = None
    resolution = None
    probeType = None
    wifiPDUContext = None
        
    def __init__(self, name, minX, maxX, resolution = 1000, probeType = "Moments", wifiPDUContext = False):
        self.name = name
        self.minX = minX
        self.maxX = maxX
        self.resolution = resolution
        self.probeType = probeType
        self.wifiPDUContext = wifiPDUContext

probes = []
probes.append(ProbeData("layer2.window.incoming.bitThroughput", 0.0, 100E6, 10000, "PDF"))
probes.append(ProbeData("layer2.window.aggregated.bitThroughput", 0.0, 100E6, 10000, "PDF"))
probes.append(ProbeData("layer2.packet.incoming.delay", 0.0, 1.0, 10000, "PDF"))
probes.append(ProbeData("layer2.CRCloss", 0.0, 1.0, 1, "PDF"))
probes.append(ProbeData("layer2.dataSINR", -200, 200, 4000, "PDF", True))

for p in probes:
    node = openwns.evaluation.createSourceNode(WNS, p.name)
    node.getLeafs().appendChildren(
        openwns.evaluation.generators.SettlingTimeGuard(
            config.settlingTime))
    bySystemStaTypeIdProbe(node, wifiIds, wimaxIds, p.minX, p.maxX, 
                            p.resolution, p.probeType, p.wifiPDUContext)
        
openwns.setSimulator(WNS)
print "\n"
print " " + str(config.configWiFi.trafficDL / 1E6) + "Mbps" + "          " + str(config.configWiMAX.trafficDL / 1E6) + "Mbps"  
print "  AP-----" + str(config.distanceAP_BS) + "m-----BS"
print "  |                 |"
print " " + str(config.configWiFi.distance_AP_STA) + "m            " + str(config.configWiMAX.distance_BS_SS) + "m"
print "  |                 |"
print " STA                SS"
print " " + str(config.configWiFi.trafficUL / 1E6) + "Mbps" + "          " + str(config.configWiMAX.trafficUL / 1E6) + "Mbps"  
