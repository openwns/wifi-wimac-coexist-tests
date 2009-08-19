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
    Seed = Int()
    
    WiFiDirection = String()
    WiFiPacketSize = Float()
    WiFiTraffic = Float()
    WiFiAMC = Bool()
    
    WiMAXDirection = String()
    WiMAXPacketSize = Float()
    WiMAXTraffic = Float()
    WiMAXAMC = Bool()

#
# Then, an instance of Set needs to be created
#

params = Set()

for d in [5]:
    for w in xrange(14):  
        for i in xrange(20):
            for seed in xrange(10):
                for dir in ['DL', 'UL', 'Both']:  
                    params.Distance = d
                    params.Seed = seed
                    params.WiFiDirection = 'DL'
                    params.WiFiPacketSize = 12000
                    params.WiFiTraffic = 2.5E5 * i
                    params.WiFiAMC = False
                
                    params.WiMAXPacketSize = 3000
                    params.WiMAXDirection = dir
                    params.WiMAXTraffic = w * 2.5E5
                    params.WiMAXAMC = False
                    params.write()    

