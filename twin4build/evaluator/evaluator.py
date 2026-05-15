from asyncio import AbstractEventLoopPolicy
import os
from re import M
import sys
import datetime
from xmlrpc.client import Boolean
import warnings

warnings.filterwarnings("ignore", category=FutureWarning)

from twin4build.saref.device.device import Device
from twin4build.saref4bldg.physical_object.building_object.building_device.distribution_device.distribution_flow_device.energy_conversion_device.coil.coil import Coil
from twin4build.saref4bldg.physical_object.building_object.building_device.distribution_device.distribution_flow_device.energy_conversion_device.coil.coil_heating_system import CoilHeatingSystem
from twin4build.saref4bldg.physical_object.building_object.building_device.distribution_device.distribution_flow_device.flow_moving_device.fan.fan import Fan
from twin4build.saref4bldg.physical_object.building_object.building_device.distribution_device.distribution_flow_device.flow_terminal.space_heater import space_heater_FMUmodel
from twin4build.saref4bldg.physical_object.building_object.building_device.distribution_device.distribution_flow_device.flow_terminal.space_heater.space_heater import SpaceHeater
from twin4build.saref4bldg.physical_object.building_object.building_device.distribution_device.distribution_flow_device.flow_terminal.space_heater.space_heater_system import SpaceHeaterSystem
from twin4build.simulator.simulator import Simulator
from twin4build.saref.device.sensor.sensor import Sensor
from twin4build.saref.device.meter.meter import Meter
from twin4build.utils.data_loaders.load_spreadsheet import load_spreadsheet
from twin4build.utils.uppath import uppath
from twin4build.utils.plot.plot import get_fig_axes, load_params
from twin4build.utils.plot.plot import bar_plot_line_format
from twin4build.saref.property_.temperature.temperature import Temperature
from twin4build.saref.property_.Co2.Co2 import Co2
from twin4build.saref.property_.power.power import Power
from twin4build.saref.property_.opening_position.opening_position import OpeningPosition #This is in use
from twin4build.saref.property_.energy.energy import Energy #This is in use
from twin4build.model.model import Model
from twin4build.saref4bldg.building_space.building_space import BuildingSpace
from twin4build.evaluator.evaluator_kpi_functions import *
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import warnings
import matplotlib.dates as mdates
import seaborn as sns
import matplotlib.ticker as ticker
from twin4build.utils.plot.plot import get_fig_axes, load_params, _convert_limits, Colors
from twin4build.utils.bayesian_inference import generate_quantiles

class Evaluator:
    """
    This Evaluator class evaluates and compares different scenarios.
    """
    def __init__(self):
        self.simulator = Simulator()

    def get_kpi(self, df_simulation_readings, measuring_device, evaluation_metric, property_=None, model=None, electricity_prices=None, absolute=True, heating_prices=None, return_type="single"):
        '''
        Calculates a Key Performance Indicator (KPI) based on simulation readings, 
        a measuring device, an evaluation metric, and a property to be evaluated. 

        Parameters:
        - df_simulation_readings: DataFrame containing the kpi indexed by time.
        - measuring_device: The name of the measuring device column in the DataFrame (the measuring device measuring property_).
        - evaluation_metric: The evaluation metric describes the time interval to evaluate power usage (eg: 'T', 'H', 'D')
        - property_: The property being evaluated (Temperature, CO2, Energy, Power).
        - model: The simulation model being evaluated (required if property_ is None).
        - electricity_prices: Optional time series of electricity prices (used for Power if the property belongs to a Fan).
        - heating_prices: Optional time series of heating prices (used for Power if the property belongs to a Coil).
        - absolute: Boolean flag indicating if absolute temperature discomfort should be computed.
        - return_type: Controls the return format:
            - "single" (default): Returns the primary KPI DataFrame for the property (backward compatible).
            - "dict": Returns a dictionary containing all computed KPIs (useful if both energy and cost are calculated).

        Returns:
        - If return_type="single": A DataFrame representing the primary KPI for the property.
        - If return_type="dict": A dictionary where each entry corresponds to a different KPI (e.g., {'energy': df, 'cost': df}).

        The following KPIs are calculated depending on property type:
        - Temperature: Occupant discomfort based on temperature deviation from setpoint.
        - CO2: Occupant discomfort based on CO2 concentration exceeding 1000 ppm.
        - Energy: Energy consumption over time.
        - Power: Power usage over time.
            - If electricity or heating prices are provided, an additional 'cost' KPI is computed.
        '''

        if property_ is None:
            property_ = model.component_dict[measuring_device].observes[0]

        kpi_dict = {}

        if isinstance(property_, Temperature):
            kpi = Temp_kpi_function(df_simulation_readings, measuring_device, evaluation_metric, model, absolute=absolute)
            kpi_dict["temperature"] = kpi
            kpi = average_temperature_function(df_simulation_readings, measuring_device)
            kpi_dict["average_temperature"] = kpi

        elif isinstance(property_, Energy):
            if evaluation_metric == "T":
                filtered_df = df_simulation_readings.resample(f'1{"h"}')
                filtered_df = filtered_df.last() - filtered_df.first()
                filtered_df = filtered_df.cumsum()
                filtered_df = filtered_df.tail(n=1).set_index(pd.Index(["Total"]))
                kpi = filtered_df[[measuring_device]]
            else:
                filtered_df = df_simulation_readings.resample(f'1{evaluation_metric}')
                filtered_df = filtered_df.last() - filtered_df.first()
                kpi = filtered_df[[measuring_device]]#.rename(columns={measuring_device: "energy"})
            kpi_dict["energy"] = kpi
            

            if heating_prices is not None:
                filtered_df['heat_prices'] = heating_prices*len(filtered_df[measuring_device])
                filtered_df['cost'] = filtered_df[measuring_device] * filtered_df['heat_prices']
             
                if evaluation_metric == "T":
                    filtered_df["cost"] = filtered_df["cost"].cumsum()
                    filtered_df = filtered_df.tail(n=1).set_index(pd.Index(["Total"]))
                else:
                    filtered_df = filtered_df.resample(f'1{evaluation_metric}').sum()

                kpi_dict["cost"] = filtered_df[["cost"]]

        elif isinstance(property_, Co2):
            kpi = CO2_kpi_function(df_simulation_readings, measuring_device, evaluation_metric, model)
            kpi_dict["co2"] = kpi

        elif isinstance(property_, Power):
            kpi = power_kpi_function(df_simulation_readings, measuring_device, evaluation_metric)
            kpi_dict["power"] = kpi

            if electricity_prices is not None and isinstance(property_.isPropertyOf, Fan):
                kpi = power_kpi_function(df_simulation_readings, measuring_device, "H")
                cost_kpi = powerCost_kpi_function(kpi, electricity_prices, evaluation_metric)
                filtered_df = cost_kpi

                if evaluation_metric == "T":
                    filtered_df["cost"] = filtered_df["cost"].cumsum()
                    filtered_df = filtered_df.tail(n=1).set_index(pd.Index(["Total"]))
                else:
                    filtered_df = filtered_df.resample(f'1{evaluation_metric}').sum()

                kpi_dict["cost"] = filtered_df[["cost"]]

            elif heating_prices is not None and isinstance(property_.isPropertyOf, Coil):
                filtered_df = kpi
                filtered_df['heat_prices'] = heating_prices*len(filtered_df["power_readings"])
                filtered_df['cost'] = filtered_df["power_readings"] * filtered_df['heat_prices']

                if evaluation_metric == "T":
                    filtered_df["cost"] = filtered_df["cost"].cumsum()
                    filtered_df = filtered_df.tail(n=1).set_index(pd.Index(["Total"]))
                else:
                    filtered_df = filtered_df.resample(f'1{evaluation_metric}').sum()

                kpi_dict["cost"] = filtered_df[["cost"]]



        # Return logic
        if return_type == "dict":
            return kpi_dict
        else:
            # Return only the primary KPI for backward compatibility
            if "cost" in kpi_dict:
                return kpi_dict["cost"]
            elif "energy" in kpi_dict:
                return kpi_dict["energy"]
            elif "power" in kpi_dict:
                return kpi_dict["power"]
            elif "temperature" in kpi_dict:
                return kpi_dict["temperature"]
            elif "co2" in kpi_dict:
                return kpi_dict["co2"]
            else:
                raise ValueError("No KPI computed for given property.")

    def evaluate(self,
                startTime=None,
                endTime=None,
                stepSize=None,
                models=None,
                measuring_devices=None,
                evaluation_metrics=None,
                method="simulate",
                single_plot=False,
                include_measured=False,
                measuring_device_name_map=None,
                options=None,
                modelTotalKpi = False,
                absolute = True,
                electricity_prices = None,
                heating_prices = None,
                KPI = None,
                initialization_period = 0,
                show=True):
        figsize = (15, 4)
        '''
            startTime: start time of the simulation
            endTime: end time of the simulation
            stepSize: time step size of the simulation
            models: a list of model instances to evaluate
            measuring_devices: a list of strings indicating the components in the models to be evaluated
            evaluation_metrics: a list of strings indicating the evaluation metrics to use (H: hourly, D: daily, W: weekly, M: monthly, A: annually, T: total).
        '''

        load_params()
        legal_evaluation_metrics = ["H", "D", "W", "M", "A", "T"] #hourly, daily, weekly, monthly, annually, Total

        assert isinstance(models, list) and all([isinstance(model, Model) for model in models]), "Argument \"models\" must be a list of Model instances."
        # assert isinstance(measuring_devices, list) and all([isinstance(measuring_device, Sensor) or isinstance(measuring_device, Meter) for measuring_device in measuring_devices]), "Argument \"measuring_devices\" must be a list of Sensor or Meter instances."
        # assert isinstance(measuring_devices, list) and all([isinstance(measuring_device, str) for measuring_device in measuring_devices]) and all([measuring_device in model.component_dict.keys() for (model, measuring_device) in zip(models, measuring_devices)]), f"Argument \"measuring_devices\" must be a list of strings with components that are included in all models."
        assert isinstance(evaluation_metrics, list) and all([isinstance(evaluation_metric, str) for evaluation_metric in evaluation_metrics]) and all([evaluation_metric in legal_evaluation_metrics for evaluation_metric in evaluation_metrics]), f"Argument \"evaluation_metrics\" must be a list of strings of either: {','.join(legal_evaluation_metrics)}."
        assert len(measuring_devices)==len(evaluation_metrics), "Length of measuring device must be equal to length of evaluation metrics."
        allowed_methods = ["simulate","bayesian_inference", "optimize"]
        assert method in allowed_methods, f"The \"method\" argument must be one of the following: {', '.join(allowed_methods)} - \"{method}\" was provided."
        load_params()
        self.result_dict = {}
        self.bar_plot_dict = {}
        self.acc_plot_dict = {}

        if isinstance(startTime, datetime.datetime):
            startTime = startTime
        if isinstance(endTime, datetime.datetime):
            endTime = endTime
        if isinstance(stepSize, (int,float)):
            stepSize = stepSize


        if include_measured:
            actual_readings_dict = {}
            self.simulator = Simulator(models[0])
            for i, (startTime_, endTime_, stepSize_)  in enumerate(zip(startTime, endTime, stepSize)):
                actual_readings = self.simulator.get_actual_readings(startTime=startTime_, endTime=endTime_, stepSize=stepSize_)
                if i==0:
                    actual_readings_dict["time"] = np.array(self.simulator.dateTimeSteps)
                else:
                    actual_readings_dict["time"] = np.concatenate((self.actual_readings["time"], np.array(self.simulator.dateTimeSteps)), axis=0)
                for measuring_device in measuring_devices:
                    if i==0:
                        actual_readings_dict[measuring_device] = actual_readings[measuring_device].to_numpy()
                    else:
                        actual_readings_dict[measuring_device] = np.concatenate((self.actual_readings[measuring_device], actual_readings[measuring_device].to_numpy()), axis=0)
    
            actual_readings = pd.DataFrame.from_dict(actual_readings_dict)
            actual_readings.set_index("time", inplace=True)
        
        
        kpi_dict = {measuring_device:pd.DataFrame() for measuring_device in measuring_devices}
        self.simulation_readings_dict = {measuring_device:pd.DataFrame() for measuring_device in measuring_devices}

        if measuring_device_name_map is None:
            measuring_device_name_map = {measuring_device:measuring_device for measuring_device in measuring_devices}
        else:
            for measuring_device in measuring_devices:
                if measuring_device not in measuring_device_name_map:
                    measuring_device_name_map[measuring_device] = measuring_device

        if method=="simulate" and modelTotalKpi == False:
            for model in models:
                self.simulator.simulate(model,
                                    stepSize=stepSize,
                                    startTime=startTime,
                                    endTime=endTime)
                df_simulation_readings = self.simulator.get_simulation_readings()
                for measuring_device, evaluation_metric in zip(measuring_devices, evaluation_metrics):
                    property_ = (model.component_dict[measuring_device].observes)[0]
                    kpi = self.get_kpi(df_simulation_readings, measuring_device, evaluation_metric, property_, model)
                    kpi_dict[measuring_device].insert(0, model.id, kpi)
                    if "time" not in kpi_dict[measuring_device]:
                        kpi_dict[measuring_device].insert(0, "time", kpi.index)
                    

                    # self.simulation_readings_dict[measuring_device].insert(0, model.id, df_simulation_readings[measuring_device])
                    # schedule_readings = property_.isControlledBy.savedInput["setpointValue"]
                    # simulation_readings_dict[measuring_device].insert(0, model.id, df_simulation_readings[measuring_device])
                    # if "time" not in self.simulation_readings_dict[measuring_device]:
                        # self.simulation_readings_dict[measuring_device].insert(0, "time", df_simulation_readings.index)

            for measuring_device, evaluation_metric in zip(measuring_devices, evaluation_metrics):
                kpi_dict[measuring_device].set_index("time", inplace=True)
                fig, ax = plt.subplots()
                self.bar_plot_dict[measuring_device] = (fig,ax)
                fig.set_size_inches(figsize)
                fig.suptitle(measuring_device, fontsize=18)
                kpi_dict[measuring_device].plot(kind="bar", ax=ax, rot=0).legend(fontsize=8)
                ax.set_xticklabels(map(bar_plot_line_format, kpi_dict[measuring_device].index, [evaluation_metric]*len(kpi_dict[measuring_device].index)))
                for container in ax.containers:
                    labels = ["{:.2f}".format(v) if v/kpi_dict[measuring_device].max().max() > 0.01 else "" for v in container.datavalues]
                    ax.bar_label(container, labels=labels)
                ax.set_xlabel(None)
                

                # self.simulation_readings_dict[measuring_device].set_index("time", inplace=True)
                # fig, ax = plt.subplots()
                # self.acc_plot_dict[measuring_device] = (fig,ax)
                # fig.set_size_inches(figsize)
                # fig.suptitle(measuring_device, fontsize=18)
                # self.simulation_readings_dict[measuring_device].plot(ax=ax, rot=0).legend(fontsize=8)

        elif method=="bayesian_inference":
            if options is None:
                options = {}

            

            if "compare_with" in options:
                compare_with = options["compare_with"]
                del options["compare_with"]
            else:
                compare_with = "model"

            if "limit" in options:
                limit = options["limit"]
                del options["limit"]
            else:
                limit = 68 #1 sigma

            quantile = _convert_limits([limit])[0]
            err_dict = {measuring_device: [] for measuring_device in measuring_devices}

            

            for model in models:
                result = self.simulator.bayesian_inference(model,
                                                            stepSize=stepSize,
                                                            startTime=startTime,
                                                            endTime=endTime,
                                                            **options)
                




                for measuring_device, evaluation_metric in zip(measuring_devices, evaluation_metrics):
                    property_ = (model.component_dict[measuring_device].observes)[0]
                    simulation_readings = [d for d in result["values"] if d["id"]==measuring_device][0][compare_with]
                    print("----")
                    print("measuring_device", measuring_device)
                    print("simulation_readings", simulation_readings)
                    median_simulation_readings = generate_quantiles(simulation_readings, np.array([0.5]))
                    n_samples = simulation_readings.shape[0]
                    kpis = []
                    for i in range(n_samples):
                        df_simulation_readings = pd.DataFrame()
                        time = result["time"]
                        df_simulation_readings.insert(0, "time", time)
                        df_simulation_readings.insert(0, measuring_device, simulation_readings[i,:])
                        df_simulation_readings.set_index("time", inplace=True)
                        kpi = self.get_kpi(df_simulation_readings, measuring_device, evaluation_metric, property_) ####################
                        kpis.append(kpi)
                    kpis = np.array(kpis)
                    # kpis = kpis.reshape((len(kpis), 1))
                    median_kpi = generate_quantiles(kpis, np.array([0.5]))
                    q = generate_quantiles(kpis, np.array(quantile))
                    q[0] = median_kpi-q[0]
                    q[1] = q[1]-median_kpi
                    err_dict[measuring_device].append(q)
                    kpi_dict[measuring_device].insert(len(kpi_dict[measuring_device].columns), model.id, median_kpi[0,:])
                    if "time" not in kpi_dict[measuring_device]:
                        # print(kpi.index)
                        # print(kpi_dict[measuring_device])
                        kpi_dict[measuring_device].insert(0, "time", kpi.index)
                    self.simulation_readings_dict[measuring_device].insert(len(self.simulation_readings_dict[measuring_device].columns), model.id, median_simulation_readings[0,:])
                    # schedule_readings = property_.isControlledBy.savedInput["setpointValue"]
                    # simulation_readings_dict[measuring_device].insert(0, model.id, df_simulation_readings[measuring_device])
                    if "time" not in self.simulation_readings_dict[measuring_device]:
                        self.simulation_readings_dict[measuring_device].insert(0, "time", result["time"])

            if include_measured:
                for measuring_device, evaluation_metric in zip(measuring_devices, evaluation_metrics):
                    property_ = model.component_dict[measuring_device].observes
                    kpi = self.get_kpi(actual_readings, measuring_device, evaluation_metric, property_) ####################
                    kpi_dict[measuring_device].insert(0, "Baseline measured", kpi.to_numpy())
                    l = err_dict[measuring_device][::-1]
                    l.append(np.array([[0],[0]]))
                    l = l[::-1]
                    err_dict[measuring_device] = l

            for measuring_device, evaluation_metric in zip(measuring_devices, evaluation_metrics):
                kpi_dict[measuring_device].set_index("time", inplace=True)
            if single_plot:
                for measuring_device, evaluation_metric in zip(measuring_devices, evaluation_metrics):
                    property_ = model.component_dict[measuring_device].observes
                    fig, ax = plt.subplots()
                    self.bar_plot_dict[measuring_device] = (fig,ax)
                    fig.set_size_inches(figsize)
                    fig.suptitle(measuring_device_name_map[measuring_device], fontsize=18)
                    print(kpi_dict[measuring_device])
                    print(err_dict[measuring_device])
                    kpi_dict[measuring_device].plot(kind="bar", ax=ax, rot=0, yerr=err_dict[measuring_device]).legend(fontsize=12)
                    ax.set_xticklabels(map(bar_plot_line_format, kpi_dict[measuring_device].index, [evaluation_metric]*len(kpi_dict[measuring_device].index)))
                    containers = [container for container in ax.containers if hasattr(container, "datavalues")]
                    for container in containers:
                        labels = ["{:.2f}".format(v) if v/kpi_dict[measuring_device].max().max() > 0.01 else "" for v in container.datavalues]
                        ax.bar_label(container, labels=labels, fontsize=11)
                    ax.set_xlabel(None)

                    if isinstance(property_, Temperature):
                        ax.set_ylabel(r"$d$ [Kh]", color="black")
                    

                    self.simulation_readings_dict[measuring_device].set_index("time", inplace=True)
                    fig, ax = plt.subplots()
                    # self.acc_plot_dict[measuring_device] = (fig,ax)
                    
                    fig.set_size_inches(figsize)
                    fig.suptitle(measuring_device_name_map[measuring_device], fontsize=18)
                    # self.simulation_readings_dict[measuring_device].plot(ax=ax, rot=0, zorder=1)
                    for column in self.simulation_readings_dict[measuring_device]:
                        ax.plot(self.simulation_readings_dict[measuring_device].index, self.simulation_readings_dict[measuring_device][column], label=column, zorder=1)

                    ##############
                    
                    if isinstance(property_, Temperature):
                        controller = property_.isObservedBy[0] #We assume that there is only one controller for each property or that they have the same setpoint schedule
                        schedule = controller.hasProfile
                        # modeled_components = self.simulator.model.instance_map[self.component_dict[controller.id]]
                        # base_controller = [v for v in modeled_components if isinstance(v, base.Controller)][0]
                        modeled_schedule = self.simulator.model.instance_map_reversed[schedule]
                        schedule_readings = modeled_schedule.savedOutput["scheduleValue"]
                        ylim = ax.get_ylim()
                        ax.fill_between(self.simulation_readings_dict[measuring_device].index, 0, schedule_readings, facecolor="black", edgecolor=Colors.red ,alpha=0.1, label=r"Heating setpoint", linewidth=3, zorder=2)
                        ax.set_ylim(ylim)
                        ax.set_ylabel(r"$T_z$ [$^\circ$C]", color="black")
                    ax.legend(fontsize=12)
                    mylocator = mdates.HourLocator(interval=8, tz=None)
                    ax.xaxis.set_minor_locator(mylocator)
                    myFmt = mdates.DateFormatter('%H')
                    ax.xaxis.set_minor_formatter(myFmt)

                    mylocator = mdates.WeekdayLocator(
                        byweekday=[mdates.MO, mdates.TU, mdates.WE, mdates.TH, mdates.FR, mdates.SA, mdates.SU], interval=1,
                        tz=None)
                    ax.xaxis.set_major_locator(mylocator)
                    myFmt = mdates.DateFormatter('%a')
                    ax.xaxis.set_major_formatter(myFmt)

                    ax.tick_params(axis='x', which='major', pad=10)  # move the tick labels
            else:
                for key in kpi_dict.keys():
                    kpi_dict[key]['Space'] = measuring_device_name_map[key]
                
                df = pd.concat(kpi_dict.values())
                # df = pd.DataFrame(kpi_dict)
                fig, ax = plt.subplots()
                fig.set_size_inches(figsize)
                # fig.suptitle(measuring_device, fontsize=18)
                df.plot(kind="bar", ax=ax, x="Space", rot=0).legend(fontsize=8)
                # ax.set_xticklabels(map(bar_plot_line_format, df.index, [evaluation_metric]*len(df.index)))
                # containers = [container for container in ax.containers if hasattr(container, "datavalues")]
                # for container in containers:
                #     labels = ["{:.2f}".format(v) if v/kpi_dict[measuring_device].max().max() > 0.01 else "" for v in container.datavalues]
                #     ax.bar_label(container, labels=labels)
                # ax.set_xlabel(None)
                
                for measuring_device, evaluation_metric in zip(measuring_devices, evaluation_metrics):
                    self.simulation_readings_dict[measuring_device].set_index("time", inplace=True)
                    fig, ax = plt.subplots()
                    # self.acc_plot_dict[measuring_device] = (fig,ax)
                    fig.set_size_inches(figsize)
                    fig.suptitle(measuring_device, fontsize=18)
                    self.simulation_readings_dict[measuring_device].plot(ax=ax, rot=0).legend(fontsize=8)

        elif method == "optimize":
            property_kpi_sum = {}

            for model in models:
                self.simulator.simulate(model,
                                        stepSize=stepSize,
                                        startTime=startTime,
                                        endTime=endTime,
                                        show_progress_bar = False)
                df_simulation_readings = self.simulator.get_simulation_readings()
                df_simulation_readings = df_simulation_readings.iloc[initialization_period:]
                df_simulation_readings = df_simulation_readings.clip(lower=0)

                for measuring_device, evaluation_metric in zip(measuring_devices, evaluation_metrics):
                    property_ = model.component_dict[measuring_device].observes[0]
                    property_type = type(property_)


                    kpi_dict = self.get_kpi(df_simulation_readings=df_simulation_readings,
                                            measuring_device=measuring_device,
                                            evaluation_metric=evaluation_metric,
                                            model=model,
                                            electricity_prices=electricity_prices,
                                            heating_prices=heating_prices,
                                            return_type="dict")

                    # Convert Power KPI to kW if needed
                    if property_type is Power and "power" in kpi_dict:
                        kpi_dict["power"] = kpi_dict["power"] / 1000

                    if (property_type is Power and "cost" in kpi_dict) and isinstance(property_.isPropertyOf, Fan):
                        kpi_dict["cost"] = kpi_dict["cost"]

                    if (property_type is Power and "cost" in kpi_dict) and isinstance(property_.isPropertyOf, Coil):
                        kpi_dict["cost"] = kpi_dict["cost"]/1000

                    if property_type is Energy and "cost" in kpi_dict:
                        kpi_dict["cost"] = kpi_dict["cost"]

                    # For each available KPI (energy, cost, etc.), update the sums
                    for kpi_name, kpi_df in kpi_dict.items():
                        kpi_value = kpi_df.values[0, 0]

                        # Use (property_type, kpi_name) tuple as the key to distinguish e.g., (Power, 'power') vs (Power, 'cost')
                        key = (property_type, kpi_name)

                        if key not in property_kpi_sum:
                            property_kpi_sum[key] = kpi_value
                        else:
                            property_kpi_sum[key] += kpi_value


        elif modelTotalKpi == True and method == "simulate":

            df_simulation_readings_list = []

            plot_mode = "comparison"

            dataframe_result_dict = {}

            for model in models:
                property_types = ["Temperature_" + model.id, "Co2_" + model.id, "Energy_" + model.id, 
                                "FanPower_" + model.id, "CoilPower_" + model.id]

                dataframe_list = {prop_type: pd.DataFrame() for prop_type in property_types}

                # Simulate the model
                self.simulator.simulate(model, stepSize=stepSize, startTime=startTime, endTime=endTime)
                df_simulation_readings = self.simulator.get_simulation_readings()

                rows_to_drop = initialization_period
                df_simulation_readings = df_simulation_readings.iloc[rows_to_drop:]

                df_simulation_readings_list.append(df_simulation_readings)
                
                for measuring_device in measuring_devices:
                    # Determine the property type
                    property_ = (model.component_dict[measuring_device].observes)[0]

                    if isinstance(property_, Temperature) and isinstance(property_.isPropertyOf, BuildingSpace):
                        prop_type = "Temperature_" + model.id
                    elif isinstance(property_, Co2) and isinstance(property_.isPropertyOf, BuildingSpace):
                        prop_type = "Co2_" + model.id
                    elif isinstance(property_, Energy) and isinstance(property_.isPropertyOf, SpaceHeater):
                        prop_type = "Energy_" + model.id
                    elif isinstance(property_, Power) and isinstance(property_.isPropertyOf, Fan):
                        prop_type = "FanPower_" + model.id
                    elif isinstance(property_, Power) and isinstance(property_.isPropertyOf, Coil):
                        prop_type = "CoilPower_" + model.id
                    else:
                        continue  # Skip if property type is not recognized

                    df = dataframe_list[prop_type]

                    # Compute KPI and update the DataFrame
                    for evaluation_metric in evaluation_metrics:

                        kpi = self.get_kpi(df_simulation_readings, measuring_device, evaluation_metric="h", model=model, property_=property_, absolute = absolute, electricity_prices=electricity_prices, heating_prices = heating_prices, return_type="single")
                        if not pd.api.types.is_datetime64_any_dtype(kpi.index):
                            df = df.reindex(kpi.index)

                        #df[measuring_device] = kpi.iloc[:, 0]
                        df[measuring_device] = kpi
                

                # Add the updated DataFrames to the result dictionary
                dataframe_result_dict.update(dataframe_list)
                
            # At the end, convert the dictionary to a list if necessary
            dataframe_names = list(dataframe_result_dict.keys())

            if plot_mode == "comparison":
                # Create a dictionary to store total values for each model and property type
                comparison_dict = {prop_type: [] for prop_type in ["Temperature", "Co2", "Energy", "FanPower", "CoilPower"]}
                models_ids = []

                # Iterate over each model and property type to gather total values
                for model in models:
                    model_id = model.id
                    models_ids.append(model_id)

                    for prop_type in ["Temperature", "Co2", "Energy", "FanPower", "CoilPower"]:
                        df_name = f"{prop_type}_{model_id}"
                        if df_name in dataframe_result_dict:
                            df = dataframe_result_dict[df_name]

                            if not df.empty:  # Ensure the DataFrame is not empty
                                df["Total"] = df.sum(axis=1)

                            # Get the sum of the 'Total' column for the model and property type
                            if "Total" in df.columns:
                                total_value = df["Total"].sum()
                                if prop_type == "FanPower" or prop_type == "CoilPower":
                                    total_value = total_value/1000
                                    if electricity_prices != None and prop_type == "FanPower":
                                        total_value = total_value*1000
                            else:
                                total_value = 0  # Default to 0 if the 'Total' column is not present
                        else:
                            total_value = 0  # Default to 0 if the DataFrame doesn't exist

                        #df.to_csv(f"{str(df_name)}.csv")
                        
                        comparison_dict[prop_type].append(total_value)

                print(comparison_dict)

                # Use Seaborn styling
                sns.set(style="white")

                # Extract values from the dict
                temperature_discomfort = comparison_dict["Temperature"]
                co2_discomfort = comparison_dict["Co2"]
                energy = comparison_dict["Energy"]
                fan_power = comparison_dict["FanPower"]
                heating_coil = comparison_dict["CoilPower"]
                scenarios = models_ids  # x-axis labels

                energy = [z / 1000 for z in energy]
                fan_power = [z / 1000 for z in fan_power]
                heating_coil = [z / 1000 for z in heating_coil]

                print(fan_power)

                x = np.arange(len(scenarios))
                # Adjust bar width based on number of scenarios
                if len(scenarios) == 1:
                    width = 0.15  # Much thinner bars for single scenario
                else:
                    width = 0.15  # Default width

                fig, ax1 = plt.subplots(figsize=(14, 7))
                ax2 = ax1.twinx()
                ax3 = ax1.twinx()
                ax3.spines["right"].set_position(("outward", 70))

                # Bar colors and edges
                pastel_red = "#FD2145"
                pastel_blue = "#2884F6"
                light_grey = "#D3D3D3"
                medium_grey = "#A9A9A9"
                dark_grey = "#696969"
                dark_blue_edge = "#FD2145"
                dark_green_edge = "#CB0112"
                dark_orange_edge = "#660000"

                # Plot bars
                bars_energy = ax2.bar(x - width, energy, width, label="Space Heater Consumption", color=light_grey, edgecolor=dark_blue_edge, linestyle="--", linewidth=1.5)
                bars_fan = ax2.bar(x, fan_power, width, label="Fan Power Consumption", color=medium_grey, edgecolor=dark_green_edge, linestyle="--", linewidth=1.5)
                bars_coil = ax2.bar(x + width, heating_coil, width, label="Heating Coil Consumption", color=dark_grey, edgecolor=dark_orange_edge, linestyle="--", linewidth=1.5)

                bars_temp = ax1.bar(x - 2*width, temperature_discomfort, width, label="Temperature Discomfort", color=pastel_blue, edgecolor="darkblue")
                bars_co2 = ax3.bar(x + 2*width, co2_discomfort, width, label="CO2 Discomfort", color=pastel_red, edgecolor="darkred")

                # Axes labels
                ax1.set_xlabel("Scenario", fontsize=16)
                ax1.set_ylabel("Temperature Discomfort [Kh]", color=pastel_blue, fontsize=14)
                ax2.set_ylabel("Energy Consumption [MWh]", color=medium_grey, fontsize=14)
                ax3.set_ylabel("CO₂ Discomfort [ppmh]", color=pastel_red, fontsize=14)
                ax3.set_ylim(bottom=0)  # <- This fixes the issue
                #ax1.set_title("Comparison of Discomfort and Energy Consumption")
                ax1.set_title("Discomfort and Energy Consumption of Recommissioned Setpoint Strategies", fontsize=18)

                ax1.set_xticks(x)
                ax1.set_xticklabels(scenarios, fontsize = 16)
                ax1.tick_params(axis="x", pad=15)

                # Match tick label colors
                ax1.yaxis.set_tick_params(labelcolor=pastel_blue)
                ax2.yaxis.set_tick_params(labelcolor=medium_grey)
                ax3.yaxis.set_tick_params(labelcolor=pastel_red)

                # Combine legends
                handles1, labels1 = ax1.get_legend_handles_labels()
                handles2, labels2 = ax2.get_legend_handles_labels()
                handles3, labels3 = ax3.get_legend_handles_labels()

                handles = handles1 + handles2 + handles3
                labels = labels1 + labels2 + labels3

                ax1.legend(handles, labels, loc="upper center", bbox_to_anchor=(0.5, -0.2), ncol=4, frameon=False, fontsize=14)

                ax1.grid(True, which='both', axis='y', linestyle='--', linewidth=0.7, color='gray')

                plt.tight_layout()
                
                plt.savefig("Scenario_energy_comparison_3.png", dpi=500, bbox_inches='tight')
                output_path = os.path.join(os.path.dirname(__file__), "evaluator_plot.png")
                plt.savefig(output_path, format="png", bbox_inches="tight")
                #plt.show()

                return comparison_dict
        


                # # Add a 'Total' column by summing the costs for each scenario
                # total_cost = np.array(comparison_dict["Energy"]) + np.array(
                #     comparison_dict["FanPower"]) + np.array(comparison_dict["CoilPower"])
                # comparison_dict["Total Cost [DKK]"] = total_cost

                # # Define categories and metrics
                # scenarios = models_ids
                # space_heater = comparison_dict['Energy']
                # fan_power = comparison_dict['FanPower']
                # heating_coil = comparison_dict['CoilPower']
                # total = comparison_dict['Total Cost [DKK]']

                # # Plotting
                # x = np.arange(len(scenarios))
                # width = 0.15  # width of bars

                # fig, ax1 = plt.subplots(figsize=(14, 7))

                # # Pastel colors for bars
                # pastel_red = "#2884F6"
                # pastel_blue = "#2884F6"
                # pastel_green = "#99FF99"
                # pastel_orange = "#FFCC99"
                # light_grey_fill = "#E0E0E0"  # Lighter grey for fill

                # # Distinct shades of grey for energy consumption
                # light_grey = "#D3D3D3"  # Light grey for space heater
                # medium_grey = "#A9A9A9"  # Medium grey for fan power
                # dark_grey = "#696969"  # Dark grey for heating coil
                # dark_purple = "#7F4B8B"  # Dark purple for total cost

                # # Distinct edge colors for each energy consumption category
                # dark_blue_edge = "#FD2145"  # Dark blue for space heater
                # dark_green_edge = "#CB0112"  # Dark green for fan power
                # dark_orange_edge = "#660000"  # Dark orange for heating coil
                # dark_purple_edge = "#7F4B8B"  # Dark purple for total cost

                # # Plot bars for energy consumption (space heater, fan, heating coil) with stippled edges
                # bars_space_heater = ax1.bar(x - width, space_heater, width, label='Space Heater Cost (DH)', color=light_grey,
                #                             edgecolor=dark_blue_edge, linestyle='-', linewidth=0.5)
                # bars_fan_power = ax1.bar(x, fan_power, width, label='Fan Cost (Electricity)', color=medium_grey,
                #                         edgecolor=dark_green_edge, linestyle='-', linewidth=0.5)
                # bars_heating_coil = ax1.bar(x + width, heating_coil, width, label='Heating Coil Cost (DH)', color=dark_grey,
                #                             edgecolor=dark_orange_edge, linestyle='-', linewidth=0.5)

                # # Plot the total cost bar
                # bars_total = ax1.bar(x + 2 * width, total, width, label='Total Energy Cost', color=pastel_orange, edgecolor="k",
                #                     linestyle='-', linewidth=0.5)

                # # Set the labels for the axes with increased font size
                # ax1.set_ylabel('Energy Price [DKK]', color=dark_grey, fontsize=14)

                # # Set the title with increased font size 
                # ax1.set_title('Comparison Energy Cost for Baseline & Scenarios #1, #2, #3 & #4', fontsize=16)

                # ax1.set_xticks(x)
                # ax1.set_xticklabels(scenarios, fontsize=12)

                # # Set y-axis colors corresponding to the bars
                # ax1.yaxis.set_tick_params(labelcolor=dark_grey, labelsize=12)

                # # Adjust x-axis tick label position to make them four columns below the x-axis label
                # ax1.tick_params(axis='x', pad=15)

                # # Combine the legends into one box with larger font
                # handles, labels = ax1.get_legend_handles_labels()
                # ax1.legend(handles, labels, loc='upper center', bbox_to_anchor=(0.5, -0.2), ncol=5, frameon=False, fontsize=12)

                # # Set y-axis limits
                # ax1.set_ylim(0,
                #             max(max(space_heater), max(fan_power), max(heating_coil), max(total) + 1000) + 1)  # For energy consumption

                # # Enable grid for the temperature axis only
                # ax1.grid(True, which='both', axis='y', linestyle='--', linewidth=0.7, color='gray')

                # # Find the baseline total cost
                # baseline_cost = total[0]

                # # Add a horizontal dashed red line at the baseline total cost
                # ax1.axhline(y=baseline_cost, color='red', linestyle='--', linewidth=1.5, label='Baseline Total Cost')

                # # Shade the area for scenarios below or above the baseline
                # for i in range(1, len(scenarios)):  # Skip the baseline scenario
                #     if total[i] < baseline_cost:
                #         # For cheaper scenarios, use a light green color
                #         ax1.fill_between([x[i] + 1.5 * width, x[i] + 2.5 * width], total[i], baseline_cost, color=pastel_green,
                #                         alpha=0.3, hatch="\\\\\\", edgecolor="k")

                #         # Calculate percentage difference from baseline
                #         percentage_diff = ((baseline_cost - total[i]) / baseline_cost) * 100
                #         # Add green percentage text above the total cost bars for cheaper scenarios
                #         ax1.text(x[i] + 2 * (width * 1.05), total[0] + 125, f"-{percentage_diff:.1f}%", color='green', fontsize=12,
                #                 ha='center')

                #     elif total[i] > baseline_cost:
                #         # For more expensive scenarios, use a light orange color
                #         ax1.fill_between([x[i] + 1.5 * width, x[i] + 2.5 * width], baseline_cost, total[i], color=pastel_orange,
                #                         alpha=0.3, hatch="////", edgecolor="k")

                #         # Calculate percentage difference from baseline
                #         percentage_diff = ((total[i] - baseline_cost) / baseline_cost) * 100
                #         # Add red percentage text above the total cost bars for more expensive scenarios
                #         ax1.text(x[i] + 2 * (width * 1.05), total[i] + 125, f"+{percentage_diff:.1f}%", color='red', fontsize=12,
                #                 ha='center')

                # # Update legend entry for the baseline line
                # handles, labels = ax1.get_legend_handles_labels()
                # handles.append(plt.Line2D([0], [0], color='red', linestyle='--', linewidth=1.5, label='Baseline Total Cost'))
                # ax1.legend(handles, labels, loc='upper center', bbox_to_anchor=(0.5, -0.2), ncol=5, frameon=False, fontsize=12)

                # # Adjust layout to avoid overlap with legend
                # plt.tight_layout()

                # # Save the figure
                # plt.savefig("metrics_comparison_cost.png", dpi=500, bbox_inches='tight')

                # # Show the plot
                # plt.show()

                # plt.clf()

                

                # subplot_across_properties_occupancy(df_simulation_readings_list, models, measuring_devices)  

                # subplot_spaces_03_04_06_11(df_simulation_readings_list, models, measuring_devices)  

                

                # plot_mode = "time"
            
            elif plot_mode == "time":
                # Plot the data over time for each property
                for property_type in ["Temperature", "Co2", "Energy", "FanPower", "CoilPower"]:
                    plt.figure(figsize=(10, 6))
                    for model in models:
                        df_name = f"{property_type}_{model.id}"
                        if df_name in dataframe_result_dict:
                            df = dataframe_result_dict[df_name]
                            if not df.empty:
                                df["Total"].plot(label=f"Model {model.id}")
                    
                    plt.title(f"Total Values Over Time: {property_type}")
                    plt.xlabel("Time")
                    plt.ylabel("Total Value")
                    plt.legend(title="Models")
                    plt.tight_layout()
                    plt.show()

        elif KPI is not None:
            if KPI == "ThermalComfort":
                keys = ['a', 'b', 'c']
                resultsDict = dict.fromkeys(keys, None)  # Default value is None
                
                for model in models:
                    # Simulate the model
                    self.simulator.simulate(model, stepSize=stepSize, startTime=startTime, endTime=endTime) 
                    df_simulation_readings = self.simulator.get_simulation_readings()

        if show:
            plt.show()

        if method == 'optimize':
            return property_kpi_sum  
        

