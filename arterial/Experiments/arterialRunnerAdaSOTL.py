#!/usr/bin/env python
import sys
sys.path.insert(0, "../../")

'''
Imports
'''
import os
import traci
from sumolib import checkBinary
from controllers.AdaSOTL import AdaSOTL
from arterial.additionalFuncs.helper import getMeanSpeedWaitingTime, createTrafficLights, setFlows_arterial

if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("please declare environment variable 'SUMO_HOME'")


def run(sotls):
    step = 0
    while traci.simulation.getMinExpectedNumber() > 0:
        traci.simulationStep()
        for sotl in sotls:
            sotl.step()
        step += 1
    traci.close()
    sys.stdout.flush()


if __name__ == '__main__':
    sumoBinary = checkBinary('sumo')
    sumoGui = checkBinary('sumo-gui')
    configPath = os.path.abspath("../arterial.sumocfg")
    simulationTime = 3600
    numVehicles = 1200

    #create instances
    minGreenTime = 20
    maxGreenTime = 55 
    trafficLights = createTrafficLights(minGreenTime, maxGreenTime)

    mu = 3
    beta = 1.18
    alpha = 4
    sotls = []
    for tl in trafficLights:
        sotls.append(AdaSOTL(tl, mu, alpha, beta))

    setFlows_arterial(numVehicles, simulationTime, "../arterial.flow.xml", delta_r_t=1/16)
    os.system('jtrrouter -c ../arterial.jtrrcfg')

    traci.start([sumoBinary, "-c", configPath,
                                    "--tripinfo-output", "../tripinfo.xml",
                                    "--statistic-output", "../statistics.xml"])
    
    run(sotls)

    meanSpeed, meanWaitingTime = getMeanSpeedWaitingTime("../statistics.xml", "../tripinfo.xml")
    print("Mean speed: ", meanSpeed)
    print("Mean waiting time: ", meanWaitingTime)