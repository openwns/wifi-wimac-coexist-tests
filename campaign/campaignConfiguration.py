#! /usr/bin/python
###############################################################################
# This file is part of openWNS (open Wireless Network Simulator)
# _____________________________________________________________________________
#
# Copyright (C) 2004-2007
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

from wrowser.simdb.Parameters import Parameters, Bool, Int, Float, String

###################################
# Simple parameter generation HowTo
#
# First, you need to define your simulation parameters in a class derived from Parameters, e.g.
#
class Set(Parameters):
    Distance = Float()
    
    WiFiDirection = String()
    WiFiPacketSize = Float()
    WiFiULTraffic = Float()
    WiFiDLTraffic = Float()
    WiFiAMC = Bool()
    
    WiMAXDirection = String()
    WiMAXPacketSize = Float()
    WiMAXULTraffic = Float()
    WiMAXDLTraffic = Float()
    WiMAXAMC = Bool()

#
# Then, an instance of Set needs to be created
#

params = Set()

for d in [2, 5, 25, 50, 75, 100]:
    for i in xrange(20):
        params.Distance = d
        params.WiFiDirection = 'DL'
        params.WiFiPacketSize = 12000
        params.WiFiULTraffic = 0.0
        params.WiFiDLTraffic = 2.5E5 + 2.5E5 * i
        params.WiFiAMC = False
    
        params.WiMAXDirection = 'DL'
        params.WiMAXPacketSize = 3000
        params.WiMAXULTraffic = 0.0
        params.WiMAXDLTraffic = 4E6
        params.WiMAXAMC = False
        params.write()    

for d in [2, 5, 25, 50, 75, 100]:
    for i in xrange(20):
        params.Distance = d
        params.WiFiDirection = 'DL'
        params.WiFiPacketSize = 12000
        params.WiFiULTraffic = 0.0
        params.WiFiDLTraffic = 2.5E5 + 2.5E5 * i
        params.WiFiAMC = False
    
        params.WiMAXDirection = 'UL'
        params.WiMAXPacketSize = 3000
        params.WiMAXULTraffic = 4E6
        params.WiMAXDLTraffic = 0.0
        params.WiMAXAMC = False
        params.write()    

for d in [2, 5, 25, 50, 75, 100]:
    for i in xrange(20):
        params.Distance = d
        params.WiFiDirection = 'DL'
        params.WiFiPacketSize = 12000
        params.WiFiULTraffic = 0.0
        params.WiFiDLTraffic = 2.5E5 + 2.5E5 * i
        params.WiFiAMC = False
    
        params.WiMAXDirection = 'Both'
        params.WiMAXPacketSize = 3000
        params.WiMAXULTraffic = 4E6
        params.WiMAXDLTraffic = 4E6
        params.WiMAXAMC = False
        params.write()    
    
for d in [2, 5, 25, 50, 75, 100]:
    for i in xrange(20):
        params.Distance = d
        params.WiFiDirection = 'DL'
        params.WiFiPacketSize = 12000
        params.WiFiULTraffic = 0.0
        params.WiFiDLTraffic = 2.5E5 + 2.5E5 * i
        params.WiFiAMC = False
    
        params.WiMAXDirection = 'DL'
        params.WiMAXPacketSize = 12000
        params.WiMAXULTraffic = 0.0
        params.WiMAXDLTraffic = 4E6
        params.WiMAXAMC = False
        params.write()    

for d in [2, 5, 25, 50, 75, 100]:
    for i in xrange(20):
        params.Distance = d
        params.WiFiDirection = 'DL'
        params.WiFiPacketSize = 12000
        params.WiFiULTraffic = 0.0
        params.WiFiDLTraffic = 2.5E5 + 2.5E5 * i
        params.WiFiAMC = False
    
        params.WiMAXDirection = 'UL'
        params.WiMAXPacketSize = 12000
        params.WiMAXULTraffic = 4E6
        params.WiMAXDLTraffic = 0.0
        params.WiMAXAMC = False
        params.write()    

for d in [2, 5, 25, 50, 75, 100]:
    for i in xrange(20):
        params.Distance = d
        params.WiFiDirection = 'DL'
        params.WiFiPacketSize = 12000
        params.WiFiULTraffic = 0.0
        params.WiFiDLTraffic = 2.5E5 + 2.5E5 * i
        params.WiFiAMC = False
    
        params.WiMAXDirection = 'Both'
        params.WiMAXPacketSize = 12000
        params.WiMAXULTraffic = 4E6
        params.WiMAXDLTraffic = 4E6
        params.WiMAXAMC = False
        params.write()    
    