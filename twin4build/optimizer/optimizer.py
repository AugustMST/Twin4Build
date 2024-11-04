from types import NoneType
import pygad
import twin4build.base as base
from datetime import timedelta
from fmpy.fmi2 import FMICallException
import pandas as pd
from datetime import datetime

from twin4build.saref import property_
from twin4build.saref.property_.energy.energy import Energy


class Optimizer:
    def __init__(self, model=None):
        self.model = model
        self.best_individuals_per_generation = []
        self.fitness_per_generation = [] 
        self.initialization_time = None
        self.counter = 0

    def fitness_function_wrapper(self, model, simulator, evaluator, stepSize, startTime, endTime, schedules, measuring_devices: list = [], weights: list = [], tchebycheff_z_star: list = [], electricity_price = None):
        time_difference = endTime - startTime
        total_seconds = time_difference.total_seconds()
        num_timesteps = int(total_seconds // stepSize)
        n_schedules = len(schedules)

        week_day_ruleset = {
            "ruleset_start_minute": [0],
            "ruleset_end_minute": [0],
            "ruleset_start_hour": [0],
            "ruleset_end_hour": [0],
            "ruleset_value": [0]
            }

        for i in range(len(schedules)):
            model.component_dict[schedules[i]].useFile = False
            model.component_dict[schedules[i]].weekDayRulesetDict = week_day_ruleset

        def fitness_function(ga_instance, solution, solution_idx):
            # Reshape solution into (n_schedules, num_timesteps) format
            solution_matrix = solution.reshape((n_schedules, num_timesteps))

            # Assign each schedule's genes to the respective component in the model
            for i, schedule_name in enumerate(schedules):
                setpoint_schedule = model.component_dict[schedule_name]
                setpoint_schedule.weekDayRulesetDict["ruleset_default_value"] = 0
                setpoint_schedule.weekDayRulesetDict["ruleset_start_minute"] = [0] * num_timesteps
                setpoint_schedule.weekDayRulesetDict["ruleset_end_minute"] = [0] * num_timesteps
                setpoint_schedule.weekDayRulesetDict["ruleset_start_hour"] = list(range(0, num_timesteps))
                setpoint_schedule.weekDayRulesetDict["ruleset_end_hour"] = list(range(1, num_timesteps)) + [0]
                setpoint_schedule.weekDayRulesetDict["ruleset_value"] = solution_matrix[i]
            try:
                # Run the simulation
                simulator.simulate(model, stepSize=stepSize, startTime=startTime, endTime=endTime, show_progress_bar=False)
                df = simulator.get_simulation_readings()

                tchebycheff_cost_list = []

                for i in range(len(measuring_devices)):
                    cost = evaluator.get_kpi(df, measuring_devices[i], evaluation_metric="T", property_= None, model=model, electricity_prices=electricity_price)
                    cost = cost.iloc[0]
                    tchebycheff_cost = weights[i] * abs(cost - tchebycheff_z_star[i])
                    tchebycheff_cost_list.append(tchebycheff_cost)
                    print(tchebycheff_cost_list)

                # Calculate fitness as the negative of the max tchebycheff cost (minimization)
                fitness = -max(tchebycheff_cost_list)

            except FMICallException as e:
                fitness = -1e+10  # Large negative fitness to penalize this solution

            return fitness
        
        return fitness_function

    def run_ga(self, model, simulator, evaluator, stepSize, startTime, endTime, schedules, measuring_devices: list, weights: list, tchebycheff_z_star: list, 
               num_generations=15, population_size=3, crossover_rate=0.5, mutation_rate=0.30, setpoint_ranges: list = [], electricity_price = None):
        
        fitness_function = self.fitness_function_wrapper(model, simulator, evaluator, stepSize, startTime, endTime, schedules, measuring_devices, weights, tchebycheff_z_star, electricity_price=electricity_price)

        # Calculate NUM_HOURS based on the simulation parameters
        time_difference = endTime - startTime
        total_seconds = time_difference.total_seconds()
        num_timesteps = int(total_seconds // stepSize)  # Calculate number of timesteps
        n_schedules = len(schedules)

        # Total number of genes = num_timesteps * n_schedules
        total_genes = num_timesteps * n_schedules

        # Create a gene space list for each gene based on the respective schedule range
        gene_space = []
        for schedule_range in setpoint_ranges:
            gene_space.extend([{'low': schedule_range[0], 'high': schedule_range[1]}] * num_timesteps)

        ga_instance = pygad.GA(
            num_generations=num_generations,
            num_parents_mating=int(crossover_rate * population_size),
            fitness_func=fitness_function,
            sol_per_pop=population_size,
            num_genes=total_genes,
            mutation_percent_genes=int(mutation_rate * 100),
            gene_space=gene_space,  # Apply different ranges for each schedule
            parent_selection_type="tournament",
            crossover_type="single_point",
            mutation_type="random",
            mutation_by_replacement=True,
            on_generation=self.callback_generation
        )

        ga_instance.run()
        solution, solution_fitness, solution_idx = ga_instance.best_solution()

        # Reshape the best solution into (n_schedules, num_timesteps)
        solution_matrix = solution.reshape((n_schedules, num_timesteps))

        return solution_matrix, solution_fitness  # Return the best solution matrix and its fitness
    
    # Optional: Callback function to print progress at each generation and store the best solution
    def callback_generation(self, ga_instance):
        solution, solution_fitness, solution_idx = ga_instance.best_solution()
        best_solution = solution  # Access last (best) solution
        best_solution_fitness = solution_fitness  # Access corresponding fitness
        
        # Record initialization time only for the first entry
        if self.initialization_time is None:
            self.initialization_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        
        # Append the best solution and fitness to the lists
        self.best_individuals_per_generation.append(best_solution)
        self.fitness_per_generation.append(best_solution_fitness)


        # Save to CSV after updating lists
        self.save_to_csv()
        

    def save_to_csv(self):
        # Create a DataFrame with columns for best individuals and fitness per generation
        df = pd.DataFrame({
            "best_individuals_per_generation": self.best_individuals_per_generation,
            "fitness_per_generation": self.fitness_per_generation
        })

        # Define the filename using the initialization time
        filename = f"generation_data_{self.initialization_time}.csv"

        # Save DataFrame to CSV
        df.to_csv(filename, index=False)

