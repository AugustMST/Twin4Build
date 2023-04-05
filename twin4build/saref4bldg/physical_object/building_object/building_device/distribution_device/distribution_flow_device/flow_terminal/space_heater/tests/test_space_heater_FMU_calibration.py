import os
import sys
import datetime
from dateutil.tz import tzutc
import pandas as pd
import matplotlib.pyplot as plt
import json
import numpy as np
###Only for testing before distributing package
if __name__ == '__main__':
    uppath = lambda _path,n: os.sep.join(_path.split(os.sep)[:-n])
    file_path = uppath(os.path.abspath(__file__), 9)
    print(file_path)
    sys.path.append(file_path)

from twin4build.utils.data_loaders.load_from_file import load_from_file
from twin4build.utils.preprocessing.data_collection import DataCollection
from twin4build.utils.preprocessing.data_preparation import sample_data
from twin4build.saref4bldg.physical_object.building_object.building_device.distribution_device.distribution_flow_device.flow_terminal.space_heater.space_heater_FMUmodel import SpaceHeaterModel
from twin4build.saref.measurement.measurement import Measurement
from twin4build.utils.constants import Constants
def test():
    stepSize = 600
    space_heater = SpaceHeaterModel(
                    specificHeatCapacityWater = Measurement(hasValue=4180),
                    outputCapacity = Measurement(hasValue=2689),
                    temperatureClassification = "45/30-21",
                    thermalMassHeatCapacity = Measurement(hasValue=50000),
                    stepSize = stepSize, 
                    subSystemOf = [],
                    input = {"supplyWaterTemperature": 75},
                    output = {"outletWaterTemperature": 22,
                                "Energy": 0},
                    savedInput = {},
                    savedOutput = {},
                    saveSimulationResult = True,
                    connectedThrough = [],
                    connectsAt = [],
                    id = "space_heater")


    space_heater.initialize()
    parameters = {"Q_flow_nominal": space_heater.outputCapacity.hasValue,
                    "T_a_nominal": space_heater.nominalSupplyTemperature,
                    "T_b_nominal": space_heater.nominalReturnTemperature}

    space_heater.set_parameters(parameters)


    waterFlowRateMax = abs(space_heater.outputCapacity.hasValue/Constants.specificHeatCapacity["water"]/(space_heater.nominalSupplyTemperature-space_heater.nominalReturnTemperature))
    filename = os.path.join(os.path.abspath(uppath(os.path.abspath(__file__), 1)), "radiator_input.csv")
    filehandler = open(filename, 'rb')
    input = pd.read_csv(filehandler, low_memory=False)
    input["waterFlowRate"] = input["waterFlowRate"]*waterFlowRateMax
    input["supplyWaterTemperature"] = 40
    input = input.iloc[:-6,:]
    input = input.set_index("time")

    filename = os.path.join(os.path.abspath(uppath(os.path.abspath(__file__), 1)), "radiator_output.csv")
    filehandler = open(filename, 'rb')
    output = pd.read_csv(filehandler, low_memory=False)
    output = output["Power"].to_numpy()*1000
    output = np.cumsum(output*stepSize/3600/1000)
    output = output[6:]




    space_heater.heatTransferCoefficient = 5.54273276
    space_heater.thermalMassHeatCapacity.hasValue = 20.57764311
    start_pred = space_heater.do_period(input) ####
    

    


    fig, ax = plt.subplots(2)
    ax[0].plot(start_pred, color="black", linestyle="dashed", label="predicted")
    ax[0].plot(output, color="blue", label="Measured")
    ax[0].set_title('Before calibration')
    fig.legend()
    # input = input.set_index("time")
    input.plot(subplots=True)
    # plt.show()
    space_heater.calibrate(input=input, output=output)
    space_heater.reset()
    parameters = {"Radiator.UAEle": 0.70788274}
    space_heater.set_parameters(parameters)
    end_pred = space_heater.do_period(input)
    ax[1].plot(end_pred, color="black", linestyle="dashed", label="predicted")
    ax[1].plot(output, color="blue", label="Measured")
    ax[1].set_title('After calibration')
    plt.tight_layout(rect=[0, 0, 1, 0.9])
    fig.set_size_inches(15,8)

    # for a in ax:
        # a.set_ylim([18,22])
    # plt.tight_layout(rect=[0, 0, 1, 0.9])
    plt.show()


def test_n():
    stepSize = 600
    space_heater = SpaceHeaterModel(
                    outputCapacity = Measurement(hasValue=2689),
                    temperatureClassification = "45/30-21",
                    thermalMassHeatCapacity = Measurement(hasValue=500000),
                    stepSize = stepSize,
                    saveSimulationResult = True,
                    id = "space_heater")

    # waterFlowRateMax = abs(space_heater.outputCapacity.hasValue/Constants.specificHeatCapacity["water"]/(space_heater.nominalSupplyTemperature-space_heater.nominalReturnTemperature))
    waterFlowRateMax = 0.1*1000/3600
    input = pd.DataFrame()

    startPeriod = datetime.datetime(year=2021, month=12, day=20, hour=0, minute=0, second=0) 
    endPeriod = datetime.datetime(year=2021, month=12, day=28, hour=0, minute=0, second=0)
    format = "%m/%d/%Y %I:%M:%S %p"


    response_filename = os.path.join(uppath(os.path.abspath(__file__), 10), "test", "data", "time_series_data", "OE20-601b-2_kafka_temperature.txt")
    data = [json.loads(line) for line in open(response_filename, 'rb')]
    data = data[1:] #remove header information
    data = np.array([row[0][0] for row in data])
    data = data[data[:, 0].argsort()]
    constructed_time_list,constructed_value_list,got_data = sample_data(data=data, stepSize=stepSize, start_time=startPeriod, end_time=endPeriod, dt_limit=1200)
 

    filename = os.path.join(os.path.abspath(uppath(os.path.abspath(__file__), 10)), "test", "data", "time_series_data", "OE20-601b-2.csv")
    space = load_from_file(filename=filename, stepSize=stepSize, start_time=startPeriod, end_time=endPeriod, format=format, dt_limit=9999)

    filename = os.path.join(os.path.abspath(uppath(os.path.abspath(__file__), 10)), "test", "data", "time_series_data", "VA01_FTF1_SV.csv")
    VA01_FTF1_SV = load_from_file(filename=filename, stepSize=stepSize, start_time=startPeriod, end_time=endPeriod, format=format, dt_limit=9999)


    input.insert(0, "time", space["Time stamp"])
    input.insert(0, "indoorTemperature", space["Indoor air temperature (Celcius)"])
    input.insert(0, "waterFlowRate", space["Space heater valve position (0-100%)"]*waterFlowRateMax/100)
    input.insert(0, "supplyWaterTemperature", VA01_FTF1_SV["FTF1_SV"])
    input.insert(0, "Power", space["HeatPower (kW)"])

    input.replace([np.inf, -np.inf], np.nan, inplace=True)

    input = input.iloc[:-6,:]
    output = input["Power"].to_numpy()*1000
    output = np.cumsum(output*stepSize/3600/1000)
    input.drop(columns=["Power"])
    input = input.iloc[0:-6]
    output = output[6:]

    input = input.set_index("time")

    space_heater.initialize()
    parameters = {"Q_flow_nominal": space_heater.outputCapacity.hasValue,
                    "T_a_nominal": space_heater.nominalSupplyTemperature,
                    "T_b_nominal": space_heater.nominalReturnTemperature}

    space_heater.set_parameters(parameters)


    start_pred = space_heater.do_period(input, stepSize=stepSize) ####
    fig, ax = plt.subplots(2)
    ax[0].plot(start_pred, color="black", linestyle="dashed", label="predicted")
    ax[0].plot(output, color="blue", label="Measured")
    ax[0].set_title('Before calibration')
    fig.legend()
    # input = input.set_index("time")
    input.plot(subplots=True)
    space_heater.calibrate(input=input, output=output, stepSize=stepSize)
    end_pred = space_heater.do_period(input, stepSize=stepSize)
    ax[1].plot(end_pred, color="black", linestyle="dashed", label="predicted")
    ax[1].plot(output, color="blue", label="Measured")
    ax[1].set_title('After calibration')

    fig, ax = plt.subplots()
    arr = np.array(space_heater.savedOutput["outletWaterTemperature"])
    print(arr.shape)
    for i in range(arr.shape[1]):
        ax.plot(arr[:,i])
    plt.show()


if __name__ == '__main__':
    test_n()