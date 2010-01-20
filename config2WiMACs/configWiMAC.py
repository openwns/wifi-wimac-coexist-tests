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

from openwns.interval import Interval

import wimac.support.Nodes
import wimac.KeyBuilder as CIDKeyBuilder
import wimac.evaluation.default
import wimac.LLMapping


from wimac.support.WiMACParameters import ParametersSystem, ParametersOFDM, ParametersMAC, ParametersPropagation, ParametersPropagation_NLOS

associations = {}

####################################################
###  Distinguished Simulation Settings             #
####################################################

class ConfWiMAC(Frozen):
	# Set basic WiMAX Parameters
	parametersSystem      = ParametersSystem
	parametersPhy         = ParametersOFDM
	parametersMAC         = ParametersMAC
	parametersPropagation = ParametersPropagation
    
    parametersPhy.slotDuration = 3.0 *  parametersPhy.symbolDuration

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
	packetSize = config.packetSize # Needed by PseudoBWReq

	nBSs = 2
	nRSs = 0
	nRmSs = 0
	nSSs = 2

WNS.modules.wimac.parametersPHY = ConfWiMAC.parametersPhy

####################################################
### Instantiating Nodes and setting Traffic        #
####################################################
rangs = []
for i in xrange(ConfWiMAC.nBSs):
	rang = wimac.support.Nodes.RANG("WiMAXRang" + str(i +1), i + 1)
	if config.noIPHeader:
		rang.nl.ipHeader.config.headerSize = 0
	rangs.append(rang)

#rangWiMAX = wimac.support.Nodes.RANG()
#
#if config.noIPHeader:
#    rangWiMAX.nl.ipHeader.config.headerSize = 0
#
# BSs with some SSs each
#def stationID():
#    id = 1
#    while (True):
#        yield id
#       id += 1
#
#stationIDs = stationID()

def stationID(k):
	id = 1 + k*100
	while (id <= (k+1)*100):
		yield id
		id += 1

stationIDsVictim = stationID(0)
stationIDsIntefering = stationID(1)

stationIDsList = []
stationIDsList.append(stationIDsVictim)
stationIDsList.append(stationIDsIntefering)

# List of base stations
accessPoints = []

k = 0
for i in xrange(ConfWiMAC.nBSs):
	stationIDs = stationIDsList[k]
	bs = wimac.support.Nodes.BaseStation(stationIDs.next(), ConfWiMAC)

	bs.phy.ofdmaStation.rxFrequency = config.frequency
	bs.phy.ofdmaStation.txFrequency = config.frequency

	bs.dll.logger.level = 2

	accessPoints.append(bs)
	associations[bs]=[]
	WNS.simulationModel.nodes.append(bs)
	k = k+1

# The RANG only has one IPListenerBinding that is attached
# to the listener. The listener is the only traffic sink
# within the RANG
for rang in rangs:
	ipListenerBinding = IPListenerBinding(rang.nl.domainName)
	listener = Listener(rang.nl.domainName + ".listener")
	rang.load.addListener(ipListenerBinding, listener)

# List of subscriber stations
userTerminals = []

k = 0
for bs in accessPoints:
	stationIDs = stationIDsList[k]
	rang = rangs[k]

	# victimBS
	if k == 0:
		trafficUL = config.TrafficULvictim
		trafficDL = config.TrafficDLvictim
	# inteferingBSs
	else:
		trafficUL = config.TrafficULintefering
		trafficDL = config.TrafficDLintefering

	for i in xrange(ConfWiMAC.nSSs):
		ss = wimac.support.Nodes.SubscriberStation(stationIDs.next(), ConfWiMAC)

		ss.phy.ofdmaStation.rxFrequency = config.frequency
		ss.phy.ofdmaStation.txFrequency = config.frequency

		if config.trafficDLenabled and trafficDL > 0.0:
			poissonDL = constanze.traffic.Poisson(
				offset = 0.01, 
				throughput = trafficDL, 
				packetSize = config.packetSize)
			ipBinding = IPBinding(rang.nl.domainName, ss.nl.domainName)
			rang.load.addTraffic(ipBinding, poissonDL)

		if config.trafficULenabled and trafficUL > 0.0:
			poissonUL = constanze.traffic.Poisson(
				offset = 0.0, 
				throughput = trafficUL,
				packetSize = config.packetSize)
		else:
			poissonUL = constanze.traffic.CBR0(duration = 1E-6, packetSize = 1)

		ipBinding = IPBinding(ss.nl.domainName, rang.nl.domainName)
		ss.load.addTraffic(ipBinding, poissonUL)
		ipListenerBinding = IPListenerBinding(ss.nl.domainName)
		listener = Listener(ss.nl.domainName + ".listener")
		ss.load.addListener(ipListenerBinding, listener)
		ss.dll.associate(bs.dll)

#		ss.nl.addRoute("0.0.0.0", "0.0.0.0", rang.ipAddress, "wimax")
		if config.noIPHeader:
		    ss.nl.ipHeader.config.headerSize = 0
		associations[bs].append(ss)
		userTerminals.append(ss)
		WNS.simulationModel.nodes.append(ss)
	rang.dll.addAP(bs)
	k += 1

for rang in rangs:
	WNS.simulationModel.nodes.append(rang)

class AllBPSKMapper(PhyModeMapper):
	def __init__(self, symbolDuration, subCarriersPerSubChannel):
		super(AllBPSKMapper, self).__init__(symbolDuration, subCarriersPerSubChannel)
		self.setMinimumSINR(-1000.0);
		self.addPhyMode(Interval(-1000.0,   1000.0, "(]"), wimac.LLMapping.WIMAXPhyMode1)

if not config.adaptiveMCS:
	symbolDuration = ConfWiMAC.parametersPhy.symbolDuration
	subCarriersPerSubChannel = ConfWiMAC.parametersPhy.dataSubCarrier

	bs.dll.dlscheduler.config.txScheduler.registry.setPhyModeMapper(AllBPSKMapper(symbolDuration, subCarriersPerSubChannel))
	bs.dll.ulscheduler.config.rxScheduler.registry.setPhyModeMapper(AllBPSKMapper(symbolDuration, subCarriersPerSubChannel))
#    ss.dll.ulscheduler.config.txScheduler.registry.setPhyModeMapper(AllBPSKMapper(symbolDuration, subCarriersPerSubChannel))

bsIDs = []
for bs in accessPoints:
	bsIDs.append(bs.dll.stationID)

ssIDs = []
for ss in userTerminals:
	ssIDs.append(ss.dll.stationID)


bsPositions = []
#First the victim base station
bsPositions.append(openwns.geometry.position.Position(config.distance_BSv_SSv, 0, 0))
#Then the intefering base stations
bsPositions.append(openwns.geometry.position.Position(config.distance_BSv_SSv + config.distance, 0, 0))

k = 0
for bs in accessPoints:
	posBS = bsPositions[k]
	bs.mobility.mobility.setCoords(posBS)
	if k == 0:
		print "Created victim BS at (" + str(posBS) + ")"
	else:
		print "Created intefering BS at (" + str(posBS) + ")"
	k += 1


ssPositions = []
#First the victim subscriber stations
ssPositions.append(openwns.geometry.position.Position(0, 0, 0))
ssPositions.append(openwns.geometry.position.Position(2 * config.distance_BSv_SSv, 0, 0))
#Then the intefering subscriber stations
ssPositions.append(openwns.geometry.position.Position(config.distance_BSv_SSv + config.distance - config.distance_BSi_SSi, 0, 0))
ssPositions.append(openwns.geometry.position.Position(config.distance_BSv_SSv + config.distance + config.distance_BSi_SSi, 0, 0))

k = 0
for ss in userTerminals:
	posSS = ssPositions[k]
	ss.mobility.mobility.setCoords(posSS)
	#victim System
	if k < ConfWiMAC.nSSs:
		print "Created victim SS at (" + str(posSS) + ")"
	else: #other Systems
		print "Created intefering SS at (" + str(posSS) + ")"
	k += 1

#prefix = "layer2"
#for node in [ss, bs]:
#    rest = node.dll.topTpProbe.config.incomingBitThroughputProbeName.split(ss.dll.topPProbe.config.prefix)[1]
#    node.dll.topTpProbe.config.incomingBitThroughputProbeName = prefix + rest
#    rest = node.dll.topTpProbe.config.aggregatedBitThroughputProbeName.split(ss.dll.topPProbe.config.prefix)[1]
#    node.dll.topTpProbe.config.aggregatedBitThroughputProbeName = prefix + rest
#    rest = node.dll.topPProbe.config.incomingDelayProbeName.split(ss.dll.topPProbe.config.prefix)[1]
#    node.dll.topPProbe.config.incomingDelayProbeName = prefix + rest
#    node.dll.topTpProbe.config.windowSize = config.configWiMAX.probeWindowSize
#    node.dll.topTpProbe.config.sampleInterval = config.configWiMAX.probeWindowSize
#    node.dll.crc.config.lossRatioProbeName = "layer2.CRCloss"
#    node.dll.crc.config.isDropping = True
#    node.dll.phyUser.config.cirProbeName = "layer2.dataSINR"

# one Virtual ARP Zone
varpWiMAX = VirtualARPServer("vARP", "WIMAXRAN")
WNS.simulationModel.nodes = [varpWiMAX] + WNS.simulationModel.nodes

vdhcpWiMAX = VirtualDHCPServer("vDHCP@",
							"WIMAXRAN",
							"192.168.0.2", "192.168.254.252",
#							"192.168.0.2", "192.168.254.253",
							"255.255.0.0")

#vdnsWiMAX = VirtualDNSServer("vDNS", "ip.DEFAULT.GLOBALWiMAX")
vdnsWiMAX = VirtualDNSServer("vDNS", "ip.DEFAULT.GLOBAL")
WNS.simulationModel.nodes.append(vdnsWiMAX)

WNS.simulationModel.nodes.append(vdhcpWiMAX)
