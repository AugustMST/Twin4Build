import pygad
import pandas as pd
import ast
import random
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
        self.initialization_time = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.kpi_tracking = None
        self.setpoint_ranges = None
        self.iteration_number = 0

    def initialize_kpi_tracking(self):
        self.kpi_tracking = {
            "temperature": [float('inf'), float('-inf')],
            "co2": [float('inf'), float('-inf')],
            "consumption": [float('inf'), float('-inf')],
            "cost": [float('inf'), float('-inf')]
        }

    def update_min_max(self, name, value):
        self.kpi_tracking[name][0] = min(self.kpi_tracking[name][0], value)
        self.kpi_tracking[name][1] = max(self.kpi_tracking[name][1], value)

    def normalize(self, value, kpi_name):
        min_val, max_val = self.kpi_tracking[kpi_name]
        if max_val == min_val:
            return 0.0
        return (value - min_val) / (max_val - min_val + 1e-6)

    def warmup_simulation(self, num_samples=10):
        print("Running warmup simulations to establish KPI min/max ranges...")
        for _ in range(num_samples):
            for ctrl_idx, controller_name in enumerate(self.controllers):
                gene_index = 0
                controller = self.model.component_dict[controller_name]
                for setpoint_name in self.setpoints_per_controller[ctrl_idx]:
                    min_val, max_val = self.setpoint_ranges[ctrl_idx][gene_index]
                    random_setpoint = random.uniform(min_val, max_val)
                    rsetattr(controller, setpoint_name, random_setpoint)
                    gene_index += 1

            results_dict = self.evaluator.evaluate(
                startTime=self.startTime, endTime=self.endTime,
                stepSize=self.stepSize, models=[self.model],
                measuring_devices=self.measuring_devices, evaluation_metrics = ["T"]*len(self.measuring_devices),  show=False,
                electricity_prices=self.electricity_prices,
                heating_prices=self.heating_prices, method = "optimize"
            )

            temperature = results_dict.get((Temperature, "temperature"), 0.0)
            co2 = results_dict.get((Co2, "co2"), 0.0)
            energy_consumption = results_dict.get((Energy, "energy"), 0.0)
            power_consumption = results_dict.get((Power, "power"), 0.0)
            energy_cost = results_dict.get((Energy, "cost"), 0.0)
            power_cost = results_dict.get((Power, "cost"), 0.0)

            total_consumption = energy_consumption + power_consumption
            total_cost = energy_cost + power_cost

            self.update_min_max("temperature", temperature)
            self.update_min_max("co2", co2)
            self.update_min_max("consumption", total_consumption)
            self.update_min_max("cost", total_cost)

        print("Warmup complete. Initial KPI ranges:", self.kpi_tracking)

    def fitness_function(self, ga_instance, solution, solution_idx):
        gene_index = 0
        for ctrl_idx, controller_name in enumerate(self.controllers):
            controller = self.model.component_dict[controller_name]
            for setpoint_name in self.setpoints_per_controller[ctrl_idx]:
                rsetattr(controller, setpoint_name, solution[gene_index])
                gene_index += 1

        try:
            results_dict = self.evaluator.evaluate(
                startTime=self.startTime, endTime=self.endTime,
                stepSize=self.stepSize, models=[self.model],
                measuring_devices=self.measuring_devices, evaluation_metrics = ["T"]*len(self.measuring_devices),  show=False,
                electricity_prices=self.electricity_prices,
                heating_prices=self.heating_prices, method = "optimize"
            )

            temperature = results_dict.get((Temperature, "temperature"), 0.0)
            co2 = results_dict.get((Co2, "co2"), 0.0)
            energy_consumption = results_dict.get((Energy, "energy"), 0.0)
            power_consumption = results_dict.get((Power, "power"), 0.0)
            energy_cost = results_dict.get((Energy, "cost"), 0.0)
            power_cost = results_dict.get((Power, "cost"), 0.0)

            total_consumption = energy_consumption + power_consumption
            total_cost = energy_cost + power_cost

            normalized_temperature = self.normalize(temperature, "temperature")
            normalized_co2 = self.normalize(co2, "co2")
            normalized_consumption = self.normalize(total_consumption, "consumption")
            normalized_cost = self.normalize(total_cost, "cost")

            fitness = -(
                self.weights[0] * normalized_temperature +
                self.weights[1] * normalized_co2 +
                self.weights[2] * normalized_consumption +
                self.weights[3] * normalized_cost
            )
        except FMICallException:
            fitness = -1e+10

        return fitness

    def run_ga(self, model, evaluator, stepSize, startTime, endTime,
               controllers, setpoints_per_controller,
               measuring_devices, weights, num_generations=15,
               population_size=3, crossover_rate=0.5, mutation_rate=0.3,
               setpoint_ranges=None, setpoint_interval=None,
               electricity_prices=None, heating_prices=None,
               num_cores=1, stop_criteria="saturate_8"):

        self.model, self.evaluator = model, evaluator
        self.startTime, self.endTime, self.stepSize = startTime, endTime, stepSize
        self.controllers, self.setpoints_per_controller = controllers, setpoints_per_controller
        self.measuring_devices, self.weights = measuring_devices, weights
        self.electricity_prices, self.heating_prices = electricity_prices, heating_prices
        self.setpoint_ranges = setpoint_ranges

        self.initialize_kpi_tracking()
        self.setpoint_ranges = setpoint_ranges

        # Warmup to establish KPI ranges
        self.warmup_simulation(num_samples=5)

        # Build gene space using frange
        gene_space = []
        for ctrl_idx, setpoints in enumerate(setpoints_per_controller):
            for setpoint_index, setpoint_name in enumerate(setpoints):
                min_val, max_val = setpoint_ranges[ctrl_idx][setpoint_index]
                interval = setpoint_interval[ctrl_idx] if setpoint_interval else 0.5
                space = list(frange(min_val, max_val, interval))
                space = [round(v, 1) for v in space]
                gene_space.append(space)

        ga_instance = pygad.GA(
            num_generations=num_generations,
            num_parents_mating=int(crossover_rate * population_size),
            fitness_func=self.fitness_function,
            sol_per_pop=population_size,
            num_genes=len(gene_space),
            mutation_percent_genes=int(mutation_rate * 100),
            gene_space=gene_space,
            parent_selection_type="rank",
            crossover_type="single_point",
            mutation_type="random",
            mutation_by_replacement=True,
            on_generation=self.callback_generation,
            parallel_processing=("process", num_cores),
            stop_criteria=stop_criteria
        )
        ga_instance.run()
        self.save_to_csv()

    def callback_generation(self, ga_instance):
        solution, fitness, _ = ga_instance.best_solution()
        self.best_individuals_per_generation.append(solution.tolist())
        self.fitness_per_generation.append(fitness)
        print("Iteration: ", self.iteration_number, fitness)
        self.iteration_number = self.iteration_number + 1

    def save_to_csv(self):
        pd.DataFrame({
            "best_individuals": self.best_individuals_per_generation,
            "fitness": self.fitness_per_generation
        }).to_csv(f"generation_data_{self.initialization_time}.csv", index=False)
