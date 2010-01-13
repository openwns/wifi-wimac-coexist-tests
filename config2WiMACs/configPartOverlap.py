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
# 1 WiMAX BS(victim) with 2 SS at fixed distance "distance_BSv_SSv"
# 1 WiMAX BS(interfering) with 2 SS at fixed distance "distance_BSi_SSi"
# Distance "distance" between BS(victim) and BS(interfering)
#
#
#  [x,y,z]=[0,0,0]      distance_BSv_SSv                                distance_BSi_SSi
#         |                    |                                               |
#         |                    |                                               |
#         |                    |                                               |
#         v           vBS      v                                               v    iBS
#    vSS1 0 <--------> x1 <--------> vSS2 <------------------------> iSS1 <--------> x2 <--------> iSS2
#                ^                                                                           ^ 
#                |        <-------------------------distance----------------------->         |       
#                |                                                                           |
#                |                                                                           |
#         distance_BSv_SSv                                                            distance_BSi_SSi
#

from SimConfig import params

class Config(object):
	noIPHeader = True #Set to true to set IP header to 0
	distance_BSv_SSv = 30
	distance_BSi_SSi = 30
	distance = params.distance
	ulRatio = 1.0
	SS_perSystem = 2

	trafficDLenabled = (ulRatio < 1.0)
	trafficULenabled = (ulRatio > 0.0)

	TrafficDLvictim = (1.0 - ulRatio) * params.TrafficULvictim
	TrafficULvictim = ulRatio * params.TrafficULvictim / SS_perSystem
	TrafficDLintefering = (1.0 - ulRatio) * params.TrafficULintefering
	TrafficULintefering = ulRatio * params.TrafficULintefering / SS_perSystem

	packetSize = 3000.0
    
	# If False only BPSK 1/2 is used no mather what channel estimation decides
	adaptiveMCS = False

	frequency = 5470.0 #GHz

	simTime = 55
	# When should probing start?
	settlingTime = 5

config = Config()

if not config.trafficDLenabled:
	config.TrafficDLvictim = 0.0
	config.TrafficDLintefering = 0.0

if not config.trafficULenabled:
	config.TrafficULvictim = 0.0
	config.TrafficULintefering = 0.0

WNS = openwns.Simulator(simulationModel = openwns.node.NodeSimulationModel())
WNS.maxSimTime = config.simTime # seconds
WNS.masterLogger.enabled = True
WNS.outputStrategy = openwns.simulator.OutputStrategy.DELETE
WNS.statusWriteInterval = 30 # in seconds
WNS.probesWriteInterval = 600 # in seconds

# ProbeBus:
#                                                             /--IdX--PDF
#                                                            /      .
#                                                    /--SS---       .
#                                                   /        \      .
#                                                  /          \--IdY--PDF      
#                               /--victimSys-PDF---
#                              /                   \--BS--PDF
# source---SettlingTime--PDF---
#                              \                   /--BS--PDF
#                               \--interfSys-PDF---
#                                                  \          /--IdA--PDF
#                                                   \        /      .
#                                                    \--SS---       .
#                                                            \      .
#                                                             \--IdB--PDF

def bySystemStaTypeIdProbe(node, 
						wimaxIds, 
						minX, 
						maxX, 
						resolution = 1000, 
						probeType = "Moments"):

	if probeType == "Moments":
		probe = openwns.evaluation.generators.Moments()
	elif probeType == "PDF":
		probe = openwns.evaluation.generators.PDF(
            minXValue = p.minX, maxXValue = p.maxX, resolution = p.resolution)
	else:
		assert False, "Unknown probe type " + probeType

    # Global probe for both systems
	node.getLeafs().appendChildren(probe)           

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
						forAll = [wimaxIds[0],wimaxIds[1]],
#						forAll = [wimaxIds[0]], 
						format = 'Id%d'))
	utNode.appendChildren(openwns.evaluation.generators.Separate(
						by = 'MAC.Id', 
						forAll = wimaxIds[2:],
#						forAll = wimaxIds[1:], 
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
#scenario = rise.Scenario.Scenario(xmin = 0,
#									ymin = 0,
#									xmax = config.distance_BSv_SSv + config.distance + config.distance_BSi_SSi, 
#									ymax = 0)
#									ymax = max(config.distance_BSi_SSi,
#												config.distance_BSv_SSv))

ofdmaPhyConfig = WNS.modules.ofdmaPhy
ofdmaPhySystem = ofdmaphy.OFDMAPhy.OFDMASystem('ofdma')
ofdmaPhySystem.Scenario = scenario
ofdmaPhyConfig.systems.append(ofdmaPhySystem)

execfile('configWiMAC.py')

wimaxIds = bsIDs + ssIDs 

class ProbeData(object):
	name = None
	minX = None
	maxX = None
	resolution = None
	probeType = None

	def __init__(self, name, minX, maxX, resolution = 1000, probeType = "Moments"):
		self.name = name
		self.minX = minX
		self.maxX = maxX
		self.resolution = resolution
		self.probeType = probeType

probes = []
probes.append(ProbeData("wimac.top.packet.incoming.size", 0.0, 0.0, 0))
probes.append(ProbeData("wimac.top.packet.incoming.delay", 0.0, 1.0, 10000))
probes.append(ProbeData("wimac.top.packet.outgoing.delay", 0.0, 1.0, 10000))
probes.append(ProbeData("wimac.top.window.incoming.bitThroughput", 0.0, 100E6))
probes.append(ProbeData("wimac.top.window.outgoing.bitThroughput", 0.0, 100E6))
probes.append(ProbeData("wimac.cirFrameHead", -40.0, 100.0, 1000, "PDF"))
probes.append(ProbeData("wimac.cirSDMA", -40.0, 100.0, 1000, "PDF"))

for p in probes:
	node = openwns.evaluation.createSourceNode(WNS, p.name)
	node.getLeafs().appendChildren(
		openwns.evaluation.generators.SettlingTimeGuard(
			config.settlingTime))
	bySystemStaTypeIdProbe(node, wimaxIds, p.minX, p.maxX,
							p.resolution, p.probeType)

openwns.setSimulator(WNS)

print "\n"

print " " + str(config.TrafficULvictim / 1E6) + "Mbps           " + str(config.TrafficDLvictim / 1E6) + "Mbps            " + str(config.TrafficULvictim / 1E6) + "Mbps                    " + str(config.TrafficULintefering / 1E6) + "Mbps           " + str(config.TrafficDLintefering / 1E6) + "Mbps            " + str(config.TrafficULintefering / 1E6) + "Mbps"

print "  vSS1 <----" + str(config.distance_BSv_SSv) + "m----> vBS <----" + str(config.distance_BSv_SSv) + "m----> vSS2-----------------------iSS1 <----" + str(config.distance_BSi_SSi) + "m----> iBS <----" + str(config.distance_BSi_SSi) + "m----> iSS2"


print "                       <----------------------------" + str(config.distance) + "m---------------------------->"

