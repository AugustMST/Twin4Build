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
    IDEAL_CO2_LEVEL = 700
    ideal_co2_level = IDEAL_CO2_LEVEL

    # Initialize a DataFrame to hold the discomfort calculations
    filtered_df = pd.DataFrame()
    filtered_df.insert(0, "time", df_simulation_readings.index)
    filtered_df.insert(1, "co2_readings", df_simulation_readings[measuring_device].values)
    filtered_df.set_index("time", inplace=True)

    # Initialize a column for occupancy status
    filtered_df['is_occupied'] = False

    # The name 'Occupancy schedule" is fixed in the moment, find work around + talk to jakob about using model as input (so you dont have to set up a simulator)
    occupancy_df = get_occupancy_df(df_simulation_readings=df_simulation_readings, model=model)

    filtered_df['is_occupied'] = occupancy_df["occupancy_value"] > 0

    # Calculate dt only for occupied times
    dt = filtered_df['is_occupied'] * filtered_df.index.to_series().diff().dt.total_seconds() / 3600

    # Calculate discomfort only where the room is occupied
    filtered_df["discomfort"] = (filtered_df["co2_readings"] - ideal_co2_level) * dt
    filtered_df["discomfort"] = filtered_df["discomfort"].mask(filtered_df["discomfort"] < 0, 0)

    print(filtered_df.head(5))

    if evaluation_metric == "T":
        filtered_df["discomfort"] = filtered_df["discomfort"].cumsum()
        filtered_df = filtered_df.tail(n=1).set_index(pd.Index(["Total"]))
    else:
        filtered_df = filtered_df.resample(f'1{evaluation_metric}')

    kpi = filtered_df["discomfort"]

    return kpi

def get_occupancy_df(df_simulation_readings, model):
    occupancy_schedule_values = model.component_dict["[029A][029A_space_heater]"].savedInput["numberOfPeople"]
    
    start_time = df_simulation_readings.index.min()
    end_time = df_simulation_readings.index.max()

    num_points = len(occupancy_schedule_values)

    total_time_seconds = (end_time - start_time).total_seconds()

    time_interval_seconds = total_time_seconds / (num_points - 1)

    occupancy_time_index = pd.date_range(start=start_time, periods=num_points, freq=pd.to_timedelta(time_interval_seconds, unit='s'))

    occupancy_df = pd.DataFrame(data=occupancy_schedule_values, index=occupancy_time_index, columns=["occupancy_value"])

    return occupancy_df
      
