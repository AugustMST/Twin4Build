import pandas as pd

from twin4build.saref.property_ import occupancy
from twin4build.simulator.simulator import Simulator

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

def power_kpi_function(df_simulation_readings, measuring_device, evaluation_metric):
    filtered_df = pd.DataFrame()
    filtered_df.insert(0, "time", df_simulation_readings.index)
    filtered_df.insert(1, "power_readings", df_simulation_readings[measuring_device].values)
    filtered_df.set_index("time", inplace=True)

    
    filtered_df["power_readings"] = filtered_df["power_readings"].fillna(0)
    
    if evaluation_metric == "T":
        filtered_df = filtered_df.resample(f'1{"H"}').sum()
        filtered_df["power_readings"] = filtered_df["power_readings"].cumsum()
        filtered_df = filtered_df.tail(n=1).set_index(pd.Index(["Total"]))
    else:
        filtered_df = filtered_df.resample(f'1{evaluation_metric}').mean()
    
    kpi=filtered_df[["power_readings"]]

    return kpi

def powerCost_kpi_function(kpi, electricity_prices, evaluation_metric):
    if len(electricity_prices) != len(kpi):
                        raise ValueError("Length of electricity prices does not match the number of time periods in power usage data.")

    # Calculate total cost for each period
    filtered_df = kpi
    filtered_df['electricity_price'] = electricity_prices
    filtered_df['cost'] = filtered_df['power_readings'] * filtered_df['electricity_price']

    if evaluation_metric == "T":
        filtered_df["cost"] = filtered_df["cost"].cumsum()
        filtered_df = filtered_df.tail(n=1).set_index(pd.Index(["Total"]))
    else:
        filtered_df = filtered_df.resample(f'1{evaluation_metric}')
        kpi = filtered_df["cost"] 
    
    return kpi

def CO2_kpi_function(df_simulation_readings, measuring_device, evaluation_metric, model):
    IDEAL_CO2_LEVEL = 900
    ideal_co2_level = IDEAL_CO2_LEVEL

    # Initialize a DataFrame to hold the discomfort calculations
    filtered_df = pd.DataFrame()
    filtered_df.insert(0, "time", df_simulation_readings.index)
    filtered_df.insert(1, "co2_readings", df_simulation_readings[measuring_device].values)
    filtered_df.set_index("time", inplace=True)

    # Initialize a column for occupancy status
    filtered_df['is_occupied'] = False

    # The name 'Occupancy schedule" is fixed in the moment, find work around + talk to jakob about using model as input (so you dont have to set up a simulator)
    occupancy_df = get_occupancy_df(df_simulation_readings=df_simulation_readings, model=model, measuring_device=measuring_device)

    space = model.component_dict[measuring_device].isContainedIn
    modeled_space = model.instance_map_reversed[space]
    space = model.component_dict[modeled_space.id]

    try:
        occupancy_threshold = space.occupancyThreshold
    except AttributeError:  # If 'space' doesn't have 'occupancy_threshold'
        occupancy_threshold = 0.5
        print(f"AttributeError: '{space.id}' object has no attribute 'occupancy_threshold', assigning default value.")
    except Exception as e:  # Catch any other unexpected errors
        occupancy_threshold = 0.5
        print(f"An unexpected error occurred: {e}. Assigning default value.")

    #occupancy_df["occupancy_value"] = occupancy_df["occupancy_value"].round()
    filtered_df['is_occupied'] = occupancy_df["occupancy_value"] > occupancy_threshold

    # Calculate dt only for occupied times
    dt = filtered_df['is_occupied'] * filtered_df.index.to_series().diff().dt.total_seconds() / 3600
    dt = dt.fillna(0)

    # Calculate discomfort only where the room is occupied
    filtered_df["discomfort"] = (filtered_df["co2_readings"] - ideal_co2_level) * dt
    filtered_df["discomfort"] = filtered_df["discomfort"].mask(filtered_df["discomfort"] < 0, 0)

    if evaluation_metric == "T":
        filtered_df = filtered_df.resample(f'1{"H"}').mean()
        filtered_df["discomfort"] = filtered_df["discomfort"].cumsum()
        filtered_df = filtered_df.tail(n=1).set_index(pd.Index(["Total"]))
    else:
        filtered_df = filtered_df.resample(f'1{evaluation_metric}').mean()

    kpi = filtered_df[["discomfort"]]

    return kpi

def get_Energy(df_simulation_readings, measuring_device, evaluation_metric, model):
    # Create a dataframe with time and energy readings
    filtered_df = pd.DataFrame()
    filtered_df.insert(0, "time", df_simulation_readings.index)
    filtered_df.insert(1, "energy_readings", df_simulation_readings[measuring_device].values)
    filtered_df.set_index("time", inplace=True)

    # Fill missing values with 0
    filtered_df["energy_readings"] = filtered_df["energy_readings"].fillna(0)

    if evaluation_metric == "T":
        # If evaluation_metric is "T" (total), take the last value after resampling
        filtered_df = filtered_df.resample('1H').mean()  # Resample to hourly data
        filtered_df["energy_readings"] = filtered_df["energy_readings"].iloc[-1]  # Take the last reading
        # Set the index as "Total" for clarity
        filtered_df = filtered_df.tail(n=1).set_index(pd.Index(["Total"]))
    else:
        # Otherwise, resample the data based on the evaluation_metric (e.g., hourly "H", daily "D")
        filtered_df = filtered_df.resample(f'1{evaluation_metric}').mean()

        # Calculate the difference in energy readings (diff) for the time period
        filtered_df["energy_readings_diff"] = filtered_df["energy_readings"].diff().fillna(0)

        # Optionally drop the cumulative column if only variations are needed
        filtered_df = filtered_df[["energy_readings_diff"]]

    # Return the KPI based on energy difference
    kpi = filtered_df[["energy_readings_diff"]]

def Temp_kpi_function(df_simulation_readings, measuring_device, evaluation_metric, model, absolute=True):

    space = model.component_dict[measuring_device].isContainedIn
    modeled_space = model.instance_map_reversed[space]
    space = model.component_dict[modeled_space.id]

    try:
        ideal_level = space.occupantComfort
    except AttributeError:
        ideal_level = 22 
        print(f"AttributeError: '{space.id}' object has no attribute 'occupantComfort', assigning default value.")
    except Exception as e:  # Catch any other unexpected errors
        ideal_level = 22
        print(f"An unexpected error occurred: {e}. Assigning default value.")

    try:
        occupancy_threshold = space.occupancyThreshold
    except AttributeError:  # If 'space' doesn't have 'occupancy_threshold'
        occupancy_threshold = 0.5
        print(f"AttributeError: '{space.id}' object has no attribute 'occupancy_threshold', assigning default value.")
    except Exception as e:  # Catch any other unexpected errors
        occupancy_threshold = 0.5
        print(f"An unexpected error occurred: {e}. Assigning default value.")

    # Initialize a DataFrame to hold the discomfort calculations
    filtered_df = pd.DataFrame()
    filtered_df.insert(0, "time", df_simulation_readings.index)
    filtered_df.insert(1, "temp_readings", df_simulation_readings[measuring_device].values)
    filtered_df.set_index("time", inplace=True)

    # Initialize a column for occupancy status
    filtered_df['is_occupied'] = False

    # The name 'Occupancy schedule" is fixed in the moment, find work around + talk to jakob about using model as input (so you dont have to set up a simulator)
    occupancy_df = get_occupancy_df(df_simulation_readings=df_simulation_readings, model=model, measuring_device=measuring_device)

    #occupancy_df["occupancy_value"] = occupancy_df["occupancy_value"].round()
    filtered_df['is_occupied'] = occupancy_df["occupancy_value"] > occupancy_threshold

    # Calculate dt only for occupied times
    dt = filtered_df['is_occupied'] * filtered_df.index.to_series().diff().dt.total_seconds() / 3600
    dt = dt.fillna(0)
    if absolute or evaluation_metric=="T":
        filtered_df["discomfort"] = abs(((filtered_df["temp_readings"] - ideal_level) * dt * ((filtered_df["temp_readings"] < ideal_level-0.5) | (filtered_df["temp_readings"] > ideal_level+0.5))))
    else:
         filtered_df["discomfort"] = ((filtered_df["temp_readings"] - ideal_level) * dt * ((filtered_df["temp_readings"] < ideal_level-0.5) | (filtered_df["temp_readings"] > ideal_level+0.5)))

    # Aggregate discomfort based on the chosen evaluation metric
    if evaluation_metric == "T":
        filtered_df = filtered_df.resample(f'1{"H"}').mean()
        filtered_df["discomfort"] = filtered_df["discomfort"].cumsum()
        filtered_df = filtered_df.tail(n=1).set_index(pd.Index(["Total"]))
    else:
        filtered_df = filtered_df.resample(f'1{evaluation_metric}').mean()

    kpi = filtered_df[["discomfort"]]

    return kpi


def get_occupancy_df(df_simulation_readings, model, measuring_device):
    # Schedule Values
    space = model.component_dict[measuring_device].isContainedIn
    schedule = space.hasProfile
    modeled_schedule = model.instance_map_reversed[schedule]
    occupancy_schedule_values = modeled_schedule.savedOutput["scheduleValue"]

    start_time = df_simulation_readings.index.min()
    end_time = df_simulation_readings.index.max()
    num_points = len(occupancy_schedule_values)
    total_time_seconds = (end_time - start_time).total_seconds()
    time_interval_seconds = total_time_seconds / (num_points - 1)

    occupancy_time_index = pd.date_range(start=start_time, periods=num_points, freq=pd.to_timedelta(time_interval_seconds, unit='s'))

    occupancy_df = pd.DataFrame(data=occupancy_schedule_values, index=occupancy_time_index, columns=["occupancy_value"])

    return occupancy_df

def is_list_of_lists(variable):
    if isinstance(variable, list):  # Check if it's a list
        return all(isinstance(sublist, list) for sublist in variable)  # Check if all elements are lists
    return False

import matplotlib.pyplot as plt
import numpy as np

def plot_best_scenario(models, comparison_df, weights, plot_mode="weighted_score"):
    """
    Visualize the best scenario for models based on weighted scores for properties.
    
    Parameters:
    - models: List of model objects with an 'id' attribute.
    - comparison_df: DataFrame containing the total values for each property per model.
    - weights: Dictionary containing the weights for each property.
    - plot_mode: A flag to choose between 'weighted_score' or 'stacked_contribution' plot types.
    """
    # Create a dictionary to store weighted scores for each model
    model_scores = {}
    
    # Prepare data for plotting contributions in case of stacked bar plot
    contributions = {
        "Temperature": [],
        "Energy": [],
        "FanPower": [],
        "CoilPower": [],
        "Co2": []
    }

    models_ids = [model.id for model in models]  # Assuming models have an 'id' attribute

    # Iterate over each model and calculate the weighted score
    for model_id in models_ids:
        # Get normalized values for each property
        temperature_total = comparison_df["Temperature"].loc[model_id]
        energy_total = comparison_df["Energy"].loc[model_id]
        fanpower_total = comparison_df["FanPower"].loc[model_id]
        coilpower_total = comparison_df["CoilPower"].loc[model_id]
        co2_total = comparison_df["Co2"].loc[model_id]

        # Normalize each property to range [0, 1] by dividing by max value, handle potential zero division
        temperature_normalized = temperature_total / comparison_df["Temperature"].max() if comparison_df["Temperature"].max() != 0 else 0
        energy_normalized = energy_total / comparison_df["Energy"].max() if comparison_df["Energy"].max() != 0 else 0
        fanpower_normalized = fanpower_total / comparison_df["FanPower"].max() if comparison_df["FanPower"].max() != 0 else 0
        coilpower_normalized = coilpower_total / comparison_df["CoilPower"].max() if comparison_df["CoilPower"].max() != 0 else 0
        co2_normalized = co2_total / comparison_df["Co2"].max() if comparison_df["Co2"].max() != 0 else 0

        # Calculate the contributions based on weights
        contributions["Temperature"].append(weights["Temperature"] * temperature_normalized)
        contributions["Energy"].append(weights["Energy"] * energy_normalized)
        contributions["FanPower"].append(weights["FanPower"] * fanpower_normalized)
        contributions["CoilPower"].append(weights["CoilPower"] * coilpower_normalized)
        contributions["Co2"].append(weights["Co2"] * co2_normalized)

        # Calculate the weighted score for the model
        weighted_score = (
            weights["Temperature"] * temperature_normalized +
            weights["Energy"] * energy_normalized +
            weights["FanPower"] * fanpower_normalized +
            weights["CoilPower"] * coilpower_normalized +
            weights["Co2"] * co2_normalized
        )

        # Store the weighted score for the model
        model_scores[model_id] = weighted_score

    # Determine the best model based on the highest weighted score
    best_model_id = min(model_scores, key=model_scores.get)
    best_model_score = model_scores[best_model_id]

    print(f"The best model is Model {best_model_id} with a score of {best_model_score:.4f}")

    # Plotting based on the selected plot_mode
    if plot_mode == "weighted_score":
        # Bar Plot for Weighted Scores
        scores = list(model_scores.values())
        plt.figure(figsize=(10, 6))
        plt.bar(models_ids, scores, color='skyblue')
        plt.title("Weighted Scores for Each Model")
        plt.xlabel("Model ID")
        plt.ylabel("Weighted Score")
        plt.xticks(rotation=90)
        plt.tight_layout()
        plt.show()

    elif plot_mode == "stacked_contribution":
        # Stacked Bar Plot for Contributions
        fig, ax = plt.subplots(figsize=(12, 8))

        ax.bar(models_ids, contributions["Temperature"], label="Temperature", color='lightcoral')
        ax.bar(models_ids, contributions["Energy"], bottom=contributions["Temperature"], label="Energy", color='skyblue')
        ax.bar(models_ids, contributions["FanPower"], bottom=np.array(contributions["Temperature"]) + np.array(contributions["Energy"]), label="FanPower", color='lightgreen')
        ax.bar(models_ids, contributions["CoilPower"], bottom=np.array(contributions["Temperature"]) + np.array(contributions["Energy"]) + np.array(contributions["FanPower"]), label="CoilPower", color='gold')
        ax.bar(models_ids, contributions["Co2"], bottom=np.array(contributions["Temperature"]) + np.array(contributions["Energy"]) + np.array(contributions["FanPower"]) + np.array(contributions["CoilPower"]), label="CO2", color='lightblue')

        # Set titles and labels
        plt.title("Contribution of Each Property to Weighted Score")
        plt.xlabel("Model ID")
        plt.ylabel("Contribution to Score")
        plt.xticks(rotation=90)
        plt.legend(title="Property Type")
        plt.tight_layout()
        plt.show()

def subplot_across_properties(simulation_results_df: list, list_models: list, measuring_devices: list):
    for model in list_models:
        Temperature_list = []
        Co2_list = []
        Energy_list = []
        FanPower_list = []
        CoilPower_list = []

        for measuring_device in measuring_devices:
            property_ = (model.component_dict[measuring_device].observes)[0]
            if isinstance(property_, Temperature) and isinstance(property_.isPropertyOf, BuildingSpace):
                Temperature_list.append(measuring_device)
            elif isinstance(property_, Co2) and isinstance(property_.isPropertyOf, BuildingSpace):
                Co2_list.append(measuring_device)
            elif isinstance(property_, Energy) and isinstance(property_.isPropertyOf, SpaceHeater):
                Energy_list.append(measuring_device)
            elif isinstance(property_, Power) and isinstance(property_.isPropertyOf, Fan):
                FanPower_list.append(measuring_device)
            elif isinstance(property_, Power) and isinstance(property_.isPropertyOf, Coil):
                CoilPower_list.append(measuring_device)
            else:
                continue

        dataframes = simulation_results_df
        list_of_properties = [Temperature_list, Co2_list, Energy_list, FanPower_list, CoilPower_list]

        for sensor_list in list_of_properties:
            subset_columns = sensor_list

            fixed_values = {
                '007A_temperature_sensor': 21,
                '011A_temperature_sensor': 22,
                '012A_temperature_sensor': 22,
                '013A_temperature_sensor': 21,
                '015A_temperature_sensor': 22,
                '020A_temperature_sensor': 21.5,
                '020B_temperature_sensor': 21.5,
                '029A_temperature_sensor': 23,
                '031A_temperature_sensor': 21,
                '033A_temperature_sensor': 23,
                '035A_temperature_sensor': 21,
            }

            common_columns = set.intersection(*(set(df.columns) for df in dataframes))
            filtered_columns = [col for col in subset_columns if col in common_columns]

            # Calculate number of rows and columns (2 columns)
            n_columns = 2
            n_rows = (len(filtered_columns) + 1) // 2  # Calculate rows based on number of columns

            # Create subplots with 2 columns and adjust the figure size
            fig, axes = plt.subplots(n_rows, n_columns, figsize=(8, 3 * n_rows), sharex=True)

            # Flatten axes if there's only one row to ensure it's iterable
            if n_rows == 1:
                axes = [axes]
            else:
                axes = axes.flatten()

            lines = []
            labels = []

            for i, column in enumerate(filtered_columns):
                ax = axes[i]

                for idx, df in enumerate(dataframes):
                    model_label = list_models[idx].id
                    
                    # Plot data with a label only the first time
                    if i == 0:  # Add model label only for the first column
                        line, = ax.plot(df.index, df[column], label=model_label)
                        lines.append(line)
                        labels.append(model_label)
                    else:
                        ax.plot(df.index, df[column])

                if column in fixed_values:
                    fixed_value = fixed_values[column]
                    ax.axhline(y=fixed_value, color='red', linestyle='--', label=f'Fixed value: {fixed_value}')
                    ax.fill_between(
                        df.index,
                        fixed_value - 0.5,
                        fixed_value + 0.5,
                        color='red',
                        alpha=0.2
                    )
                    if i == 0:  # Add fixed value labels only once
                        lines.append(ax.axhline(y=fixed_value, color='red', linestyle='--'))
                        lines.append(ax.fill_between(df.index, fixed_value - 0.5, fixed_value + 0.5, color='red', alpha=0.2))
                        labels.append('Dead band +/-0.5 C')

                ax.set_title(f'Column: {column}', fontsize=9)
                ax.set_ylabel('Value', fontsize=7)
                ax.tick_params(axis='x', rotation=45)  # Rotate x-axis labels

            # Hide any unused subplots
            for j in range(len(filtered_columns), len(axes)):
                fig.delaxes(axes[j])

            # Add the single legend outside the plot
            fig.legend(lines, labels, loc='lower center', fontsize=8, ncol=8)

            # Adjust layout to avoid overlapping labels
            plt.tight_layout()

            # Display the plot
            plt.show()
