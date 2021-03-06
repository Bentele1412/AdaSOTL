#!/usr/bin/env python
import sys
sys.path.insert(0, "../../")

import traci
from sumolib import checkBinary
import os
import matplotlib.pyplot as plt
import numpy as np
from controllers.CycleBasedTLController import CycleBasedTLController
from arterial.additionalFuncs.helper import mapLPDetailsToTL, getMeanSpeedWaitingTime, getTLPhaseInfo, createTrafficLights, setFlows_arterial

def run(trafficLights, ctFactor, phaseShifts, lpSolveResultPaths):
    step = 0
    pathCounter = 0
    cycleBasedTLControllers = []
    while traci.simulation.getMinExpectedNumber() > 0:
        if step % 1200 == 0 and step < 3600:
            mapLPDetailsToTL(trafficLights, lpSolveResultPaths[pathCounter]) # TBD for arterial network
            maxNodeUtilization = max([tl.utilization for tl in trafficLights])
            numPhases, yellowPhaseDuration = getTLPhaseInfo()
            cycleTime = int(np.round(ctFactor * ((1.5 * (numPhases/2)*yellowPhaseDuration + 5)/(1 - maxNodeUtilization))))
            #print(cycleTime)
            pathCounter += 1
            if step == 0:
                for counter, tl in enumerate(trafficLights):
                    cycleBasedTLControllers.append(CycleBasedTLController(tl, cycleTime, phaseShifts[counter], numPhases, yellowPhaseDuration))
            else:
                for counter, controller in enumerate(cycleBasedTLControllers):
                    controller.setCycle(cycleTime, phaseShifts[counter])
        
        for controller in cycleBasedTLControllers:
            controller.step()
        traci.simulationStep()

        step += 1
    traci.close()
    sys.stdout.flush()

if __name__ == '__main__':
    sumoBinary = checkBinary('sumo')
    sumoGui = checkBinary('sumo-gui')
    configPath = os.path.abspath("../arterial.sumocfg")
    simulationTime = 3600
    numVehicles = 1200
    ctFactor = 0.9

    phaseShifts = [0, 10, 20, 10, 20, 30]
    lpSolveResultPaths = ['../LPSolve/arterialGrid_a_eps0,4.lp.csv', '../LPSolve/arterialGrid_b_eps0,4.lp.csv', '../LPSolve/arterialGrid_c_eps0,4.lp.csv']

    meanSpeeds = []
    meanWaitingTimes = []
    numReplications = 30

    for i in range(numReplications):

        #create instances
        trafficLights = createTrafficLights()

        setFlows_arterial(numVehicles, simulationTime, "../arterial.flow.xml")
        os.system('jtrrouter -c ../arterial.jtrrcfg')

        traci.start([sumoBinary, "-c", configPath,
                                        "--tripinfo-output", "../tripinfo.xml",
                                        "--statistic-output", "../statistics.xml"])

        run(trafficLights, ctFactor, phaseShifts, lpSolveResultPaths)

        meanSpeed, meanWaitingTime = getMeanSpeedWaitingTime("../statistics.xml", "../tripinfo.xml")
        meanSpeeds.append(float(meanSpeed))
        meanWaitingTimes.append(float(meanWaitingTime))
        print("Replication %i done." % (i+1))

    sortedSpeeds = sorted(meanSpeeds)
    sortedWaitingTimes = sorted(meanWaitingTimes)
    plt.plot(sortedSpeeds)
    plt.title("Mean speeds")
    plt.show()
    plt.plot(sortedWaitingTimes)    
    plt.title("Mean Waiting times")
    plt.show()