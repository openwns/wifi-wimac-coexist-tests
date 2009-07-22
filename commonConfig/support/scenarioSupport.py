import math
import random
#from pyx import *
from openwns.geometry.position import Position
from rise.Mobility import EventList
from openwns.distribution import Fixed
from rise.Antenna import *
from openwns.pyconfig import Sealed
from support.WiMACParameters import ParametersSystem

class Openangle(Sealed):
    min = None
    max = None
    def __init__(self, min, max):
#        print "creating openangle with min=" + str(min) + " and max="+ str(max)
        self.min = min
        self.max = max

def aequiAngular(n, radius, center, rotation):
    assert len(center) == 3
    assert n >= 0

    res = []
    for i in xrange(n):
        angle = 2.0  * math.pi / n * i + rotation * math.pi / 180
        res.append([round(center[0]+radius*math.sin(angle), 6),
                    round(center[1]+radius*math.cos(angle), 6),
                    center[2]])
    return res

def aequiAngularGen(n, radius, center, rotation):
    #assert len(center) == 3
    assert n >= 0

    for i in xrange(n):
        angle = 2.0  * math.pi / n * i + rotation * math.pi / 180
        yield Position(round(center.x+radius*math.sin(angle), 6),
                       round(center.y+radius*math.cos(angle), 6),
                       center.z)


def hexagonalGrid(nCircles, radius, center, rotation = 0.0):
    assert nCircles >= 0
    assert radius > 0
    #assert len(center) == 3

    res = [center]
    yield center
    for i in xrange(nCircles):
        resLen = len(res)
        for n in xrange(resLen):
            for it in [ itt for itt in aequiAngularGen(6, radius, res[n], rotation) if itt not in res]:
                yield it
                res += [it]

def numberOfAccessPointsForHexagonalScenario(nCircles):
    """ Calculates the number of access points that are needed to form
        a scenario of hexagonal layout with nCicles circles of cells.
    """
    return (nCircles*(nCircles+1)/2)*6+1

def generateRandomUTPos(maxDistance, center, nSectors):
    angle =  2.0 / nSectors * math.pi * random.random()
    radius = maxDistance * math.sqrt(random.random())
    return Position(round(center.x+radius*math.sin(angle), 6),
                    round(center.y+radius*math.cos(angle), 6),
                    ParametersSystem.heightUT)

#ditributes SS uniformly on a circle of 2/3 of the radius
def generateUTPosOnCircle(maxDistance, center, nthUser):
    angle =  2.0 * math.pi / 24 * nthUser + math.pi / 24
    radius = maxDistance * 2.0 / 3
    return Position(round(center.x+radius*math.sin(angle), 6),
                    round(center.y+radius*math.cos(angle), 6),
                    ParametersSystem.heightUT)

def openAngleDistribution(maxDistance, center, openangle, nSectors):
    """ Place nRT remote terminals around a relay station at center
        with openangle
    """
    minOpenangle = openangle.min * math.pi / 180
    maxOpenangle = openangle.max * math.pi / 180
    opening = (maxOpenangle - minOpenangle) / 2.0 / math.pi
    angle = 2.0 / nSectors * math.pi * random.random() * opening + minOpenangle
    radius = maxDistance * math.sqrt(random.random())
    return Position(round(center.x+radius*math.sin(angle), 6),
                    round(center.y+radius*math.cos(angle), 6),
                    ParametersSystem.heightUT)
     
def setupHexagonalScenario(config, ofdmaPhyStations):
    """
    This method will setup the scenario as follows:
    1.) The APs are placed in hexagonal layout (hexagon with nCircles circles) with distanceBetweenAPs between them
    2.) AP and UTs have no mobility
    """

    assert numberOfAccessPointsForHexagonalScenario(config.nCircles) == config.nBSs

    # some handy abbreviations
    nBS = config.nBSs
    nSS = config.nSSs

    distanceBetweenBSs = config.parametersSystem.cellRadius * math.sqrt( 3 * config.parametersSystem.clusterOrder)

    listOfAccessPointPositions = hexagonalGrid(config.nCircles, distanceBetweenBSs,
                                               Position(config.scenarioXSize / 2, config.scenarioYSize / 2, 0.0) ) #[config.scenarioXSize / 2, config.scenarioYSize / 2, 0])
    n = 0
    for pos in listOfAccessPointPositions:
        ofdmaPhyStations[n].mobility.mobility.setCoords(Position(pos[0],pos[1],config.parametersSystem.heightAP))
        print ofdmaPhyStations[n].name + " at " + str(pos)
        apfile.write(str(n)+"\t"+str(pos[0])+"\t"+str(pos[1])+"\n")
        #  place User Terminals of the AP
        k = 0
        for ut in ofdmaPhyStations[n].subsciberStations:
            ut.mobility.mobility.setCoords(generateRandomUTPos(config.parametersSystem.cellRadius/2, pos, n, config.nSectors))
            utfile.write(ut.mobility.mobility.getCoords())
            k += 1
        listOfRSPositions = aequiAngularGen(config.nRSs, distanceBetweenBSs / 5, pos)
        k=0
        for rs in ut.relayStations:
            rs.mobility.mobility.setCoords(listOfRSPositions.next())
            
            l = 0
            for ss in rs.subscriberStations:
                ss.mobility.mobility.setCoords(
                    openAngleDistribution(
                    config.parametersSystem.cellRadius / 3,
                    rs.mobility.mobility.getCoords(),
                    Openangle(minOpening, maxOpening), config.nSectors))
                l += 1
            k += 1
        n += 1

def setupRelayScenario(config, ofdmaPhyStations, associations):
    """
    This method will setup the scenario as follows:
    1.) The APs are placed in hexagonal layout (hexagon with nCircles circles) with distanceBetweenAPs between them
    2.) AP and UTs have no mobility
    """

    assert numberOfAccessPointsForHexagonalScenario(config.nCircles) == config.nBSs

    # some handy abbreviations
    nBS = config.nBSs
    nRS = config.nRSs
    nSS = config.nSSs
    nRmS = config.nRmSs

    if nRS == 0:
        distanceBetweenBSs = config.parametersSystem.cellRadius * math.sqrt( 3 * config.parametersSystem.clusterOrder)
    elif nRS > 0:
        if nRS == 3:
            distanceBetweenBSs = config.parametersSystem.cellRadius * 3 * math.sqrt(config.parametersSystem.clusterOrder)
        else:
            exit('for this amount of relays per BS you have to calculate distance between BSs yourself')

    listOfAccessPointPositions = hexagonalGrid(config.nCircles, distanceBetweenBSs,
                                               Position(config.scenarioXSize / 2, config.scenarioYSize / 2, 0.0))
    n = 0
    for pos in listOfAccessPointPositions:
        ofdmaPhyStations[n].mobility.mobility.setCoords(Position(pos.x,pos.y,config.parametersSystem.heightAP))
        #  place User Terminals of the AP
        u = 0
        for ut in associations[ofdmaPhyStations[n]]:
            if ut.dll.stationType != 'UT':
                continue
            u = u + 1
            ut.mobility.mobility.setCoords(generateRandomUTPos(
                config.parametersSystem.cellRadius,
                ofdmaPhyStations[n].mobility.mobility.getCoords(),
                config.nSectors))

        listOfRSPositions = aequiAngularGen(config.nRSs, config.parametersSystem.cellRadius, pos, 0.0)
        k=0


        for rs in associations[ofdmaPhyStations[n]]:
            if rs.dll.stationType != 'FRS':
                continue
            rs.mobility.mobility.setCoords(listOfRSPositions.next())

            minOpening = 240 + k*120
            maxOpening = 480 + k*120
            for ut in associations[rs]:
                if ut.dll.stationType != 'UT':
                    continue
                ut.mobility.mobility.setCoords(
                    openAngleDistribution(
                    config.parametersSystem.cellRadius,
                    rs.mobility.mobility.getCoords(),
                    Openangle(minOpening, maxOpening), config.nSectors))
            k += 1
        n += 1


def getMobilityWay(startPosition, endPosition, time, stationName = "noName:"):
    """
    This method give back a rise Mobility EventList.
    The Station move in defined time from startPosition to endPosition
    """

    wayPointsFile = open("wayPoints.junk","a")

    way = EventList(startPosition)
    currentPosition = startPosition

    a = 10
    steps = time*a
    stepsX=(endPosition.x-startPosition.x)/steps
    stepsY=(endPosition.y-startPosition.y)/steps

    for i in xrange(int(steps)):
        currentPosition=Position(x=(currentPosition.x + stepsX),
                                 y=(currentPosition.y + stepsY),
                                 z=currentPosition.z)
        way.addWaypoint(float(i+1)/a, currentPosition)

        j=(float(i+1)/a)
        x=currentPosition.x
        y=currentPosition.y
        z=currentPosition.z
        wayPointsFile.write(stationName + '   Time:%(j)2.07f    Pos:  %(x)12.6f; %(y)12.6f; %(z)9.6f \n' % vars())

    return way



def buildCluster(_clusterSize, _cellRadius, _center, _corrAngleGrad=0):
    """
    This method returns all access point positions from a cluster,
    in relation to the center (First access point in the list)
    """

    assert 0 <= _clusterSize <= 7
    assert _cellRadius >0
    assert 0 <= _corrAngleGrad <=359 # rotates the final result by corrAngle

    corrAngle = 30.0 * (2.0 * math.pi / 360)
    corrAngle += _corrAngleGrad * (2.0 * math.pi / 360)

    res = []
    res.append(_center)
    for i in xrange(_clusterSize-1):
        angle = 2.0  * math.pi / 6
        res.append( Position( round(_center.x+( math.sqrt(3)*_cellRadius*math.cos(i*angle+corrAngle) ), 6),
                              round(_center.y+( math.sqrt(3)*_cellRadius*math.sin(i*angle+corrAngle) ), 6),
                              _center.z)
                    )
    return res


def buildClusterGrid(_clusterSize, _cellRadius, _center, _corrAngleGrad=0):
    """
    This method returns a center position list of every cluster.
    """

    assert _clusterSize in [4, 7]
    assert _cellRadius > 0
    assert 0 <= _corrAngleGrad <=359 # rotates the final result by corrAngle

    d = math.sqrt(3*_clusterSize)*_cellRadius # reuse distance,
                                              #minimum distance between two co-channels cells

    if _clusterSize == 4:
        corrAngle = 30.0 * (2.0 * math.pi / 360.0)
    elif _clusterSize == 7:
        corrAngle=math.asin(math.sqrt(7.0)/14.0)
    else:
        exit('scenarioSupport::buildClusterGrid: Used ClusterSize is not supported!')

    corrAngle += _corrAngleGrad * (2.0 * math.pi / 360)

    res = []
    res.append(_center)
    for i in xrange(6):
        angle = 2.0  * math.pi / 6
        res.append( Position( round(_center.x+( d*math.cos(i*angle+corrAngle) ),6),
                              round(_center.y+( d*math.sin(i*angle+corrAngle) ),6),
                              _center.z)
                    )

    return res



def calculateScenarioRadius(_clusterSize, _nCircles, _cellRadius):
    """
    This method calculates the ScenarioRadius from size of the cluster,
    number of cluster circles around the center cluster and radius of the cells.
    """

    assert _clusterSize in [1, 3, 4, 7, 12]
    assert _nCircles in [0, 1]
    assert _cellRadius > 0

    if _clusterSize == 1:
        if _nCircles == 0:
            scenarioRadius = _cellRadius
	elif _nCircles == 1:
            scenarioRadius = math.sqrt(math.pow(0.5,2) + math.pow((3*math.sqrt(3.0)/2),2))*_cellRadius
        else:
            exit('scenarioSupport::calculateScenarioRadius: required number of circles is not supported')

    elif _clusterSize == 3:
        if _nCircles == 0:
            scenarioRadios = 2*_cellRadius
	elif _nCircles == 1:
            scenarioRadius = 5*_cellRadius
        else:
            exit('scenarioSupport::calculateScenarioRadius: required number of circles is not supported')

    elif _clusterSize == 4:
        if _nCircles == 0:
            scenarioRadios = 2.5*_cellRadius
	elif _nCircles == 1:
            scenarioRadius = math.sqrt(math.pow(5.5,2) + math.pow(1*math.sqrt(3.0),2))*_cellRadius
        else:
            exit('scenarioSupport::calculateScenarioRadius: required number of circles is not supported')

    elif _clusterSize == 7:
        if _nCircles == 0:
            scenarioRadius = math.sqrt(math.pow(0.5,2) + math.pow(1.5*math.sqrt(3.0),2))*_cellRadius
        elif _nCircles == 1:
            scenarioRadius = math.sqrt(math.pow(7,2) + math.pow(1*math.sqrt(3.0),2))*_cellRadius
        else:
            exit('scenarioSupport::calculateScenarioRadius: required number of circles is not supported')

    elif _clusterSize == 12:
        #values are not exact (hoy)
        if _nCircles == 0:
            scenarioRadius = 4 * _cellRadius
        elif _nCircles == 1:
            scenarioRadius = 10 * _cellRadius
        else:
            exit('scenarioSupport::calculateScenarioRadius: required number of circles is not supported')

    else:
        exit('scenarioSupport::claculateScenarioRadius: Used ClusterSize is not supported!')

    # add 10 percent margin for imperfect SS positioning (circle vs. hexagon!)
    scenarioRadius = int( math.ceil(scenarioRadius * 1.1) )

    return scenarioRadius



def printStationPosition(stations):
    """
    This method returns a string with the position of the stations who are given in it.
    """

    result = ""
    for st in stations:
        frequency = st.phy.ofdmaStation.rxFrequency
        pos = st.mobility.mobility.getCoords()
        x = pos.x
        y = pos.y
        z = pos.z
        iD = st.dll.stationID
        name = st.dll.name
        result += ' %(name)s%(iD)03d   f:%(frequency)s MHz      Pos:  x(%(x)12.6f) y(%(y)12.6f) z(%(z)9.6f)\n' % vars()

    return result



def plotStationPosition(_baseStations, _subscriberStations, _fileName, _bsRadius):
    """
    This method plot the station position in a given file.
    """

    c = canvas.canvas()
    freq = []
    freqColor = dict()
    colorPalette = color.palette.Hue

    ## get all used frequencies
    for st in _baseStations:
        if st.phy.ofdmaStation.rxFrequency not in freq:
            freq.append(st.phy.ofdmaStation.rxFrequency)
    freq.sort()

    ## set color for each frequency
    freqColor[freq[0]]=color.rgb.black
    freq.pop(0)
    for f in freq:
        freqColor[f]=colorPalette.getcolor(float(freq.index(f))/float(len(freq)))

    ## plot base stations
    for st in _baseStations:
        pos = st.mobility.mobility.getCoords()
        iD = st.dll.stationID
        name = st.dll.name
        scaleFactor = _bsRadius

        circle = path.circle(pos.x/scaleFactor, pos.y/scaleFactor, _bsRadius/scaleFactor)
        c.stroke(circle, [style.linewidth.Thick,
                          freqColor[st.phy.ofdmaStation.txFrequency]])
        if freqColor[st.dll.centerFrequency]==color.rgb.black:
            c.fill(circle, [color.palette.Gray.getcolor(0.1)])

    ## plot subscriber stations
    for st in _subscriberStations:
        pos = st.mobility.mobility.getCoords()
        iD = st.dll.stationID
        name = st.dll.name
        scaleFactor = _bsRadius

        circle = path.circle(pos.x/scaleFactor, pos.y/scaleFactor, 0.01)
        c.stroke(circle, [style.linewidth.thin])

    c.writeEPSfile(_fileName)
    pass



def convertMACtoIP(macID):
    """
    Convert an MAC address to an IP address
    """
    assert macID < (256*255)-1

    _ip_x3 = (macID / 255)
    _ip_x4 = int(math.fmod(macID, 255))
    return "192.168."+str(_ip_x3)+"."+str(_ip_x4)



class Traffic:
    qosPriority = None   # Valid options: 'UGS', 'rtPS', 'nrtPS', 'BE'.
                         # 'NoQoS', 'Signaling' are valid too,
                         # but make no sense.
    packetSize = None    # [bits]
    rate = None          # [bit/s]


    def __init__(self, _qosPriority, _packetSize, _rate):
        self.qosPriority = _qosPriority
        self.packetSize = _packetSize
        self.rate = _rate



def printClass(that):
    """
       This method returns class members for printing.
    """

    result = ""
    result += str(that.__name__) + ':\n'
    result += '~~~~~~~~~~~~~~~~~~~\n'
    keys = that.__dict__.keys()
    keys.sort()
    for i in keys:
        result += '          ' + str(i) + ' = ' + str(that.__dict__[i]) + '\n'

    return result
