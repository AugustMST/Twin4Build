import pandas as pd

from twin4build.saref.property_ import occupancy

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
        filtered_df = filtered_df.resample(f'1{evaluation_metric}')
    
    kpi=filtered_df["power_readings"]

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

    filtered_df['is_occupied'] = occupancy_df["occupancy_value"] > 0
    occupancy_df["occupancy_value"] = occupancy_df["occupancy_value"].round()

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
        filtered_df = filtered_df.resample(f'1{evaluation_metric}')

    kpi = filtered_df["discomfort"]

    return kpi

def Temp_kpi_function(df_simulation_readings, measuring_device, evaluation_metric, model):
    IDEAL_Temp_LEVEL = 22
    ideal_level = IDEAL_Temp_LEVEL

    # Initialize a DataFrame to hold the discomfort calculations
    filtered_df = pd.DataFrame()
    filtered_df.insert(0, "time", df_simulation_readings.index)
    filtered_df.insert(1, "temp_readings", df_simulation_readings[measuring_device].values)
    filtered_df.set_index("time", inplace=True)

    # Initialize a column for occupancy status
    filtered_df['is_occupied'] = False

    # The name 'Occupancy schedule" is fixed in the moment, find work around + talk to jakob about using model as input (so you dont have to set up a simulator)
    occupancy_df = get_occupancy_df(df_simulation_readings=df_simulation_readings, model=model, measuring_device=measuring_device)

    occupancy_df["occupancy_value"] = occupancy_df["occupancy_value"].round()
    filtered_df['is_occupied'] = occupancy_df["occupancy_value"] > 0

    # Calculate dt only for occupied times
    dt = filtered_df['is_occupied'] * filtered_df.index.to_series().diff().dt.total_seconds() / 3600
    dt = dt.fillna(0)

    # Calculate discomfort only when the temperature is outside the range 21 - 23
    filtered_df["discomfort"] = ((filtered_df["temp_readings"] - ideal_level) * dt * ((filtered_df["temp_readings"] < 21) | (filtered_df["temp_readings"] > 23)))

    # Set discomfort to zero for any values less than zero
    #filtered_df["discomfort"] = filtered_df["discomfort"].mask(filtered_df["discomfort"] < 0, 0)

    # Aggregate discomfort based on the chosen evaluation metric
    if evaluation_metric == "T":
        filtered_df["discomfort"] = filtered_df["discomfort"].cumsum()
        filtered_df = filtered_df.tail(n=1).set_index(pd.Index(["Total"]))
    else:
        filtered_df = filtered_df.resample(f'1{evaluation_metric}')

    kpi = filtered_df["discomfort"]

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
      
