import pygad
import pandas as pd
import numpy as np
from datetime import datetime
from fmpy.fmi2 import FMICallException
from twin4build.saref.property_.energy.energy import Energy
from twin4build.saref.property_.power.power import Power
from twin4build.saref.property_.temperature.temperature import Temperature
from twin4build.saref.property_.Co2.Co2 import Co2
from twin4build.utils.rsetattr import rsetattr

def frange(start, stop, step):
    while start <= stop:
        yield start
        start += step

class Optimizer:
    def __init__(self, model=None):
        self.model = model
        self.best_individuals_per_generation = []
        self.fitness_per_generation = []
        self.initialization_time = None
        self.iteration_number = 0

    def fitness_function(self, ga_instance, solution, solution_idx):

        gene_index = 0
        for ctrl_idx, controller_name in enumerate(self.controllers):
            controller = self.model.component_dict[controller_name]
            for setpoint_name in self.setpoints_per_controller[ctrl_idx]:
                value = solution[gene_index]
                rsetattr(controller, setpoint_name, value)
                gene_index += 1
        try:
            results_dict = self.evaluator.evaluate(
                startTime=self.startTime,
                endTime=self.endTime,
                stepSize=self.stepSize,
                models=[self.model],
                measuring_devices=self.measuring_devices,
                evaluation_metrics=["T"] * len(self.measuring_devices),
                method="optimize",
                single_plot=False,
                include_measured=False,
                measuring_device_name_map=None,
                options=None,
                modelTotalKpi=False,
                absolute=True,
                electricity_prices=self.electricity_prices,
                heating_prices=self.heating_prices,
                KPI=None,
                show=True
            )

            temperature = results_dict.get((Temperature, "temperature"), 0.0)
            co2 = results_dict.get((Co2, "co2"), 0.0)
            energy_consumption = results_dict.get((Energy, "energy"), 0.0)
            power_consumption = results_dict.get((Power, "power"), 0.0)
            energy_cost = results_dict.get((Energy, "cost"), 0.0)
            power_cost = results_dict.get((Power, "cost"), 0.0)

            total_consumption = energy_consumption + power_consumption
            total_cost = energy_cost + power_cost

            all_objectives = {
                "temperature": -temperature,
                "co2": -co2,
                "consumption": -total_consumption,
                "cost": -total_cost
            }

            fitness_values = [all_objectives[obj] for obj in self.objectives_to_include]

        except FMICallException as e:
            fitness_values = [-1e+10] * len(self.objectives_to_include)

        return fitness_values

    def run_ga(self, model, evaluator, stepSize, startTime, endTime, 
               controllers, setpoints_per_controller, measuring_devices, 
               objectives_to_include=["temperature", "co2", "consumption", "cost"],
               num_generations=15, population_size=3, 
               crossover_rate=0.5, mutation_rate=0.3, setpoint_ranges=None, 
               setpoint_interval=None, electricity_prices=None, heating_prices=None, 
               num_cores=1):
        
        self.model = model
        self.evaluator = evaluator
        self.startTime = startTime
        self.endTime = endTime
        self.stepSize = stepSize
        self.controllers = controllers
        self.setpoints_per_controller = setpoints_per_controller
        self.measuring_devices = measuring_devices
        self.electricity_prices = electricity_prices
        self.heating_prices = heating_prices
        self.objectives_to_include = objectives_to_include

        if not set(objectives_to_include).issubset({"temperature", "co2", "consumption", "cost"}):
            raise ValueError(f"objectives_to_include must be a subset of ['temperature', 'co2', 'consumption', 'cost']")

        if setpoint_ranges is None:
            raise ValueError("setpoint_ranges must be provided as a flat list of [min, max] pairs.")
        if setpoint_interval is None:
            setpoint_interval = [0.5] * len(controllers)

        gene_space = []
        for ctrl_idx, setpoints in enumerate(setpoints_per_controller):
            for sp_idx, _ in enumerate(setpoints):
                min_val, max_val = setpoint_ranges[ctrl_idx][sp_idx]
                interval = setpoint_interval[ctrl_idx]
                values = [round(x, 1) for x in frange(min_val, max_val, interval)]
                gene_space.append(values)

        self.initialization_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

        ga_instance = pygad.GA(
            num_generations=num_generations,
            num_parents_mating=int(crossover_rate * population_size),
            fitness_func=self.fitness_function,
            sol_per_pop=population_size,
            num_genes=len(gene_space),
            mutation_percent_genes=int(mutation_rate * 100),
            gene_space=gene_space,
            parent_selection_type="nsga2",
            crossover_type="single_point",
            mutation_type="random",
            mutation_by_replacement=True,
            on_generation=self.callback_generation,
            parallel_processing=("process", num_cores),
            fitness_batch_size=1,
            save_best_solutions = True
        )

        ga_instance.run()

        pareto_front = ga_instance.best_solutions
        pareto_fitness = ga_instance.best_solutions_fitness

        self.save_to_csv()

        return pareto_front, pareto_fitness


    def callback_generation(self, ga_instance):
        print("Iteration", self.iteration_number)

        # Collect best solutions for the current generation
        best_solutions = ga_instance.best_solutions
        best_solutions_fitness = ga_instance.best_solutions_fitness

        # Prepare data to append to the best_individuals_per_generation list
        generation_data = {
            "generation": self.iteration_number,
            "solutions": best_solutions,
            "fitness_values": best_solutions_fitness,
            "pareto_size": len(best_solutions),
        }

        # Append the current generation data to the list
        self.best_individuals_per_generation.append(generation_data)

        # Increment iteration number
        self.iteration_number += 1

    def save_to_csv(self):
        detailed_data, summary_data, full_pop_data = [], [], []

        # Full population tracking
        for gen_data in self.fitness_per_generation:
            generation = gen_data["generation"]
            fitness_list = gen_data["fitness"]

            for sol_idx, fit in enumerate(fitness_list):
                full_pop_data.append({
                    "generation": generation,
                    "solution_index": sol_idx,
                    **{obj: -fit[obj_idx] for obj_idx, obj in enumerate(self.objectives_to_include)}
                })

            avg_fitness = np.mean(fitness_list, axis=0)
            summary_data.append({
                "generation": generation,
                **{obj: -avg_fitness[idx] for idx, obj in enumerate(self.objectives_to_include)}
            })

        # Pareto front tracking
        for gen_data in self.best_individuals_per_generation:
            generation = gen_data["generation"]
            for sol_idx, (sol, fit) in enumerate(zip(gen_data["solutions"], gen_data["fitness_values"])):
                detailed_data.append({
                    "generation": generation,
                    "solution_index": sol_idx,
                    "solution": str(sol),
                    **{obj: -fit[obj_idx] for obj_idx, obj in enumerate(self.objectives_to_include)}
                })

        pd.DataFrame(detailed_data).to_csv(f"detailed_pareto_data_{self.initialization_time}.csv", index=False)
        pd.DataFrame(summary_data).to_csv(f"summary_population_data_{self.initialization_time}.csv", index=False)
        pd.DataFrame(full_pop_data).to_csv(f"full_population_fitness_{self.initialization_time}.csv", index=False)