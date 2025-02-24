from curses import KEY_SOPTIONS
import pandas as pd
import seaborn as sns

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
        filtered_df["power_readings"] = filtered_df["power_readings"].cumsum()
        filtered_df = filtered_df.tail(n=1).set_index(pd.Index(["Total"]))
    else:
        filtered_df = filtered_df.resample(f'1{evaluation_metric}').sum()

    kpi=filtered_df[["power_readings"]]

    return kpi

def powerCost_kpi_function(kpi, electricity_prices, evaluation_metric):
    # if len(electricity_prices) != len(kpi):
    #                     raise ValueError("Length of electricity prices does not match the number of time periods in power usage data.")

    # Calculate total cost for each period
    filtered_df = kpi
    filtered_df['electricity_price'] = electricity_prices[24:]
    filtered_df['cost'] = filtered_df['power_readings'] * filtered_df['electricity_price']

    # if evaluation_metric == "T":
    #     filtered_df["cost"] = filtered_df["cost"].cumsum()
    #     filtered_df = filtered_df.tail(n=1).set_index(pd.Index(["Total"]))
    # else:
    #filtered_df = filtered_df.resample(f'1{evaluation_metric}')
    kpi = filtered_df[["cost"]]
    
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


    space = model.component_dict[measuring_device].isContainedIn
    modeled_space = model.instance_map_reversed[space]
    schedule = space.hasProfile
    modeled_schedule = model.instance_map_reversed[schedule]
    occupancy_schedule_values = modeled_schedule.savedOutput["scheduleValue"]

    difference = len(occupancy_schedule_values) - len(df_simulation_readings)

    occupancy_schedule_values = occupancy_schedule_values[difference:]

    filtered_df["occupancy_value"] = occupancy_schedule_values
    
    filtered_df["occupancy_value"] = filtered_df["occupancy_value"].fillna(0)

    space = model.component_dict[modeled_space.id]

    try:
        occupancy_threshold = space.occupancyThreshold
    except AttributeError:  # If 'space' doesn't have 'occupancy_threshold'
        occupancy_threshold = 0.5
        print(f"AttributeError: '{space.id}' object has no attribute 'occupancy_threshold', assigning default value.")
    except Exception as e:  # Catch any other unexpected errors
        occupancy_threshold = 0.5
        print(f"An unexpected error occurred: {e}. Assigning default value.")

    filtered_df['is_occupied'] = filtered_df["occupancy_value"] > occupancy_threshold
    
    # Calculate dt only for occupied times
    dt = filtered_df['is_occupied'] * filtered_df.index.to_series().diff().dt.total_seconds() / 3600
    dt = dt.fillna(0)

    # Calculate discomfort only where the room is occupied
    filtered_df["discomfort"] = (filtered_df["co2_readings"] - ideal_co2_level) * dt
    filtered_df["discomfort"] = filtered_df["discomfort"].mask(filtered_df["discomfort"] < 0, 0)

    if evaluation_metric == "T":
        filtered_df["discomfort"] = filtered_df["discomfort"].cumsum()
        filtered_df = filtered_df.tail(n=1).set_index(pd.Index(["Total"]))
    else:
        filtered_df = filtered_df.resample(f'1{evaluation_metric}').sum()

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
    cooling_setpoint = 25

    # Initialize a DataFrame to hold the discomfort calculations
    filtered_df = pd.DataFrame()
    filtered_df.insert(0, "time", df_simulation_readings.index)
    filtered_df.insert(1, "temp_readings", df_simulation_readings[measuring_device].values)
    filtered_df.set_index("time", inplace=True)

    space = model.component_dict[measuring_device].isContainedIn
    modeled_space = model.instance_map_reversed[space]
    space_id = model.component_dict[modeled_space.id]

    schedule = space.hasProfile
    modeled_schedule = model.instance_map_reversed[schedule]
    occupancy_schedule_values = modeled_schedule.savedOutput["scheduleValue"]

    difference = len(occupancy_schedule_values) - len(df_simulation_readings)

    occupancy_schedule_values = occupancy_schedule_values[difference:]

    filtered_df["occupancy_value"] = occupancy_schedule_values

    try:
        ideal_level = space_id.occupantComfort
    except AttributeError:
        ideal_level = 22 
        print(f"AttributeError: '{space_id.id}' object has no attribute 'occupantComfort', assigning default value.")
    except Exception as e:  # Catch any other unexpected errors
        ideal_level = 22
        print(f"An unexpected error occurred: {e}. Assigning default value.")

    try:
        occupancy_threshold = space_id.occupancyThreshold
    except AttributeError:  # If 'space' doesn't have 'occupancy_threshold'
        occupancy_threshold = 0.5
        print(f"AttributeError: '{space_id.id}' object has no attribute 'occupancy_threshold', assigning default value.")
    except Exception as e:  # Catch any other unexpected errors
        occupancy_threshold = 0.5
        print(f"An unexpected error occurred: {e}. Assigning default value.")

    # Check occupancy status
    filtered_df['is_occupied'] = filtered_df["occupancy_value"] > occupancy_threshold

    # Calculate time difference in hours for occupied periods
    dt = filtered_df['is_occupied'] * filtered_df.index.to_series().diff().dt.total_seconds() / 3600
    dt = dt.fillna(0)

    # Compute discomfort
    if absolute or evaluation_metric == "T":
        filtered_df["discomfort"] = (
            abs((filtered_df["temp_readings"] - ideal_level)) * dt * (filtered_df["temp_readings"] < ideal_level)
        ) + (
            abs((filtered_df["temp_readings"] - cooling_setpoint)) * dt * (filtered_df["temp_readings"] > cooling_setpoint)
        )
    else:
        filtered_df["discomfort"] = (
            (filtered_df["temp_readings"] - ideal_level) * dt * (filtered_df["temp_readings"] < ideal_level)
        ) + (
            (filtered_df["temp_readings"] - cooling_setpoint) * dt * (filtered_df["temp_readings"] > cooling_setpoint)
        )

    # Resample and aggregate discomfort
    if evaluation_metric == "T":
        filtered_df = filtered_df.resample(f'1{"H"}').mean()
        filtered_df["discomfort"] = filtered_df["discomfort"].cumsum()
        filtered_df = filtered_df.tail(n=1).set_index(pd.Index(["Total"]))
    else:
        filtered_df = filtered_df.resample(f'1{evaluation_metric}').sum()

    kpi = filtered_df[["discomfort"]]

    return kpi


def get_occupancy_df(df_simulation_readings, model, measuring_device):
    # Schedule Values
    space = model.component_dict[measuring_device].isContainedIn
    schedule = space.hasProfile
    modeled_schedule = model.instance_map_reversed[schedule]
    occupancy_schedule_values = modeled_schedule.savedOutput["scheduleValue"]

    # Simulation time bounds
    start_time = df_simulation_readings.index.min()
    end_time = df_simulation_readings.index.max()
    num_points = len(occupancy_schedule_values)
    total_time_seconds = (end_time - start_time).total_seconds()
    time_interval_seconds = total_time_seconds / (num_points - 1)

    # Generate occupancy time index
    occupancy_time_index = pd.date_range(
        start=start_time,
        periods=num_points,
        freq=pd.to_timedelta(time_interval_seconds, unit='s')
    )

    # Create occupancy DataFrame
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
                '020A_temperature_sensor': 20,
                '020B_temperature_sensor': 20,
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
                        fixed_value,
                        25,
                        color='red',
                        alpha=0.2
                    )
                    if i == 0:  # Add fixed value labels only once
                        lines.append(ax.axhline(y=fixed_value, color='red', linestyle='--'))
                        lines.append(ax.fill_between(df.index, fixed_value, 25, color='red', alpha=0.2))
                        labels.append('Comfort Dead Band  [C]')

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

import matplotlib.pyplot as plt
import matplotlib.lines as mlines
import matplotlib.patches as mpatches
import numpy as np

def subplot_across_properties_occupancy(simulation_results_df: list, list_models: list, measuring_devices: list):
    for model in list_models:
        Temperature_list = []
        Co2_list = []
        Energy_list = []
        FanPower_list = []
        CoilPower_list = []

        # Classify measuring devices by property type
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

        dataframes = simulation_results_df
        list_of_properties = [Temperature_list, Co2_list, Energy_list, FanPower_list, CoilPower_list]

        for sensor_list in list_of_properties:
            subset_columns = sensor_list

            fixed_values = {
                '007A_temperature_sensor': 21,
                '011A_temperature_sensor': 22,
                '012A_temperature_sensor': 22,
                '013A_temperature_sensor': 20.5,
                '015A_temperature_sensor': 22,
                '020A_temperature_sensor': 20,
                '020B_temperature_sensor': 20,
                '029A_temperature_sensor': 22.5,
                '031A_temperature_sensor': 21,
                '033A_temperature_sensor': 22.5,
                '035A_temperature_sensor': 21,
            }

            common_columns = set.intersection(*(set(df.columns) for df in dataframes))
            filtered_columns = [col for col in subset_columns if col in common_columns]

            # Calculate number of rows and columns (2 columns)
            n_columns = 2
            n_rows = (len(filtered_columns) + 1) // 2  # Calculate rows based on number of columns

            # Set A4 size dimensions (in inches)
            fig_width = 8.27  # A4 width in inches
            fig_height = 11.7  # A4 height in inches

            # Create subplots with 2 columns and adjust the figure size to A4 dimensions
            fig, axes = plt.subplots(n_rows, n_columns, figsize=(fig_width, fig_height), sharex=True)

            if n_rows == 1:
                axes = [axes]
            else:
                axes = axes.flatten()

            lines = []
            labels = []

            new_column_names = ["Space_01 Temperature Sensor", "Space_03 Temperature Sensor" ,"Space_04 Temperature Sensor","Space_05 Temperature Sensor",
                                "Space_06 Temperature Sensor","Space_07 Temperature Sensor","Space_08 Temperature Sensor","Space_09 Temperature Sensor",
                                "Space_10 Temperature Sensor","Space_11 Temperature Sensor","Space_12 Temperature Sensor",]

            subplot_labels = [f"({chr(97 + i)})" for i in range(len(filtered_columns))]  # Generates ['(a)', '(b)', '(c)', ...]

            for i, column in enumerate(filtered_columns):
                ax = axes[i]

                # Add subplot label in the top-left corner
                ax.text(0.02, 0.95, subplot_labels[i], transform=ax.transAxes, fontsize=10, fontweight='bold', va='top')

                # Set subplot title
                ax.set_title(new_column_names[i], fontsize=9)

                # Plot each dataframe's data for this column
                for idx, df in enumerate(dataframes):
                    model_label = list_models[idx].id

                    # Plot data with a label only the first time
                    if i == 0:
                        line, = ax.plot(df.index, df[column], label=model_label)
                        lines.append(line)
                        labels.append(model_label)
                    else:
                        ax.plot(df.index, df[column])
                    
                    # Retrieve occupancy schedule values
                    space = model.component_dict[column].isContainedIn
                    modeled_space = model.instance_map_reversed[space]
                    schedule = space.hasProfile
                    modeled_schedule = model.instance_map_reversed[schedule]
                    occupancy_schedule_values = modeled_schedule.savedOutput["scheduleValue"]
                    space_id = model.component_dict[modeled_space.id]

                    # Align occupancy values with the data
                    difference = len(occupancy_schedule_values) - len(df)
                    if difference > 0:
                        occupancy_schedule_values = occupancy_schedule_values[difference:]

                    is_occupied = np.array(occupancy_schedule_values) > space_id.occupancyThreshold

                    # Count True and False values
                    num_true = np.sum(is_occupied)
                    num_false = len(is_occupied) - num_true

                    # Print the counts
                    print(column, f"Number of True values (occupied): {num_true}")
                    print(column, f"Number of False values (not occupied): {num_false}")

                    # Determine y-axis limits based on data
                    ymin, ymax = df[column].min(), df[column].max()
                    ax.set_ylim(ymin, ymax)

                    # Add shading for occupied periods
                    ax.fill_between(
                        df.index,
                        0,
                        300,  # Assuming 300 is the upper bound for shading
                        where=is_occupied,
                        color='gray',
                        alpha=0.3,
                        transform=ax.get_xaxis_transform(),
                        label='Occupied'
                    )

                    #ax.set_title(f'{column}', fontsize=9)
                    ax.set_title(new_column_names[i], fontsize=9)
                    ax.set_ylabel('Degree Celsius', fontsize=7)
                    ax.tick_params(axis='x', rotation=45)

                # Add fixed value lines and bands
                if column in fixed_values:
                    fixed_value = fixed_values[column]
                    ax.axhline(y=fixed_value, color='red', linestyle='--', label=f'Fixed value: {fixed_value}')
                    ax.fill_between(
                        df.index,
                        fixed_value,
                        25,
                        color='red',
                        alpha=0.2
                    )

                # Ensure temperature-related y-axis is between 18 and 25
                if isinstance(model.component_dict[column].observes[0], Temperature):
                    ax.set_ylim(19, 25)

            # Hide unused subplots
            for j in range(len(filtered_columns), len(axes)):
                fig.delaxes(axes[j])

            # Add a single legend outside the plot
            # fig.legend(lines, labels, loc='lower center', fontsize=8, ncol=8)
            # Define handles for custom legend items
            red_stippled_line = mlines.Line2D([], [], color='red', linestyle='--', label='Minimum Temperature')
            gray_shading = mpatches.Patch(color='gray', alpha=0.3, label='PIR Sensor Active')
            red_shading = mpatches.Patch(color='red', alpha=0.2, label='Heating Deadband')

            # Add custom legend items
            fig.legend(
                handles=lines + [red_stippled_line, gray_shading, red_shading],  # Include existing model lines + new items
                labels=labels + ['Minimum Temperature', 'PIR Sensor Active', "Heating Deadband"],
                loc='lower center',
                fontsize=8,
                ncol=4  # Adjust column count to fit
)

            # Adjust layout to ensure everything fits properly on the A4 page
            plt.tight_layout(pad=2.0)  # Add some padding to ensure nothing is cut off

            # Save the plot to a file (A4 size)
            plt.savefig("temperature_subplot_A4.png", dpi=300, bbox_inches='tight')
            plt.show()



def plot_comparison(models, dataframe_result_dict, plot_mode="comparison"):
    # Set Seaborn style to 'darkgrid' (close to classic)
    sns.set(style="darkgrid")

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
                    # Get the sum of the 'Total' column for the model and property type
                    if "Total" in df.columns:
                        total_value = df["Total"].sum()
                        # Convert FanPower and CoilPower from Watts to kWh
                        if prop_type == "FanPower" or prop_type == "CoilPower":
                            total_value = total_value / 1000  # Convert to kWh for power values
                    else:
                        total_value = 0  # Default to 0 if the 'Total' column is not present
                else:
                    total_value = 0  # Default to 0 if the DataFrame doesn't exist

                comparison_dict[prop_type].append(total_value)

        # Convert to a DataFrame for easy plotting
        comparison_df = pd.DataFrame(comparison_dict, index=models_ids)

        # Create a figure
        fig, ax1 = plt.subplots(figsize=(12, 6))

        # Dark pastel color palette for bars
        dark_pastel_palette = sns.dark_palette("seagreen", reverse=True, n_colors=2)

        # Plot Temperature on the primary y-axis
        comparison_df[["Temperature"]].plot(kind="bar", ax=ax1, position=0, width=0.8, color=dark_pastel_palette[0])

        # Set labels for the first y-axis (Temperature)
        ax1.set_ylabel("Temperature Discomfort [Kh]")
        ax1.set_xlabel("Model ID")
        ax1.set_xticklabels(models_ids, rotation=90)

        # Create the secondary y-axis for CO2 and Energy-related properties
        ax2 = ax1.twinx()
        dark_pastel_co2_palette = sns.dark_palette("lightcoral", reverse=True, n_colors=1)  # Light pastel for CO2
        energy_palette = sns.dark_palette("orange", reverse=True, n_colors=3)  # Dark pastel orange for energy

        # Plot CO2, Energy, FanPower, CoilPower on the secondary y-axis
        comparison_df[["Co2"]].plot(kind="bar", ax=ax2, position=1, width=0.8, color=dark_pastel_co2_palette)
        comparison_df[["Energy", "FanPower", "CoilPower"]].plot(kind="bar", ax=ax2, position=2, width=0.8, color=energy_palette)

        # Set labels for the second y-axis (CO2 and Energy)
        ax2.set_ylabel("CO2 Discomfort [PPM] and Energy Consumption [kWh]")

        # Set title
        plt.title("Comparison of Temperature, CO2, and Energy Consumption")

        # Adjust layout to avoid overlap
        plt.tight_layout()
        plt.show()