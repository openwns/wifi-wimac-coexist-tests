import os
import datetime
from support.FrameSetup import FrameSetup
from support.scenarioSupport import printClass, printStationPosition

class WiMACPostProcessor:

    def __call__(self, theWNS):
        if self.Config.writeOutput:
            _dir = theWNS.outputDir
            # Write WiMAC Parameters
            parameters = open(os.path.join(_dir, 'WiMACParameters'),"w")
            parameters.write("\n\n")
            parameters.write(printClass(self.Config.parametersSystem))
            parameters.write("\n\n\n")
            parameters.write(printClass(self.Config.parametersPhy))
            parameters.write("\n\n\n")
            parameters.write(printClass(self.Config.parametersMAC))
            parameters.write("\n\n\n")
            parameters.close()

            # Write Frame Setup
            frameSetup = FrameSetup(self.Config)
            frameSetupOutput = open(os.path.join(_dir, 'FrameSetup'),"w")
            frameSetupOutput.write(frameSetup.printFramePhases())
            frameSetupOutput.close()


            # Write StationPositions
            stationPos = open(os.path.join(_dir, 'stationPositions'),"w")
            try:
                stationPos.write(printStationPosition(self.accessPoints))
            except:
                pass
            stationPos.write("\n\n")

            try:
                stationPos.write(printStationPosition(self.relayStations))
            except:
                pass
            stationPos.write("\n\n")

            try:
                stationPos.write(printStationPosition(self.userTerminals))
            except:
                pass
            stationPos.write("\n\n")

            try:
                stationPos.write(printStationPosition(self.remoteStations))
            except:
                pass
            stationPos.close()

            # plot FUN
            #self.accessPoints[0].dll.fun.dot(os.path.join(_dir, 'funAP.dot'), showParameters=False)
            #self.userTerminals[0].dll.fun.dot(os.path.join(_dir, 'funUT.dot'), showParameters=False)
        return True
        
