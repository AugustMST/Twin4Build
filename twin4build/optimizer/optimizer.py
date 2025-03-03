import pygad
import pandas as pd
from datetime import datetime
from fmpy.fmi2 import FMICallException
from twin4build.saref.property_.energy.energy import Energy
from twin4build.saref.property_.power.power import Power
from twin4build.saref.property_.temperature.temperature import Temperature
from twin4build.saref.property_.Co2.Co2 import Co2
from twin4build.utils.rsetattr import rsetattr
import ast


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

            cost = [temperature, co2, total_consumption, total_cost]

            tchebycheff_cost_list = [
                self.weights[i] * abs(cost[i] - self.tchebycheff_z_star[i])
                for i in range(len(cost))
            ]

            fitness = -max(tchebycheff_cost_list)

        except FMICallException:
            fitness = -1e+10

        return fitness

    def run_ga(self, model, evaluator, stepSize, startTime, endTime, 
               controllers, setpoints_per_controller, 
               measuring_devices, weights, tchebycheff_z_star,
               num_generations=15, population_size=3, 
               crossover_rate=0.5, mutation_rate=0.3, 
               setpoint_ranges=None, setpoint_interval=None, 
               electricity_prices=None, heating_prices=None, 
               num_cores=1, stop_criteria=None):
        """
        Run the Genetic Algorithm with rank selection and optional stop criteria.

        Args:
            stop_criteria (str or list): Stop criteria for the GA. Examples:
                - "reach_40": Stop if fitness >= 40.
                - "saturate_7": Stop if fitness does not change for 7 generations.
                - ["reach_40", "saturate_7"]: Combine multiple criteria.
        """
        self.model = model
        self.evaluator = evaluator
        self.startTime = startTime
        self.endTime = endTime
        self.stepSize = stepSize
        self.controllers = controllers
        self.setpoints_per_controller = setpoints_per_controller
        self.measuring_devices = measuring_devices
        self.weights = weights
        self.tchebycheff_z_star = tchebycheff_z_star
        self.electricity_prices = electricity_prices
        self.heating_prices = heating_prices

        if setpoint_ranges is None:
            raise ValueError("setpoint_ranges must be provided as a flat list of [min, max] pairs.")
        if setpoint_interval is None:
            setpoint_interval = [0.5] * len(controllers)

        gene_space = []
        for controller_index, setpoints in enumerate(setpoints_per_controller):
            for setpoint_index, setpoint_name in enumerate(setpoints):
                min_val, max_val = setpoint_ranges[controller_index][setpoint_index]
                interval = setpoint_interval[controller_index]
                possible_values = [round(x, 1) for x in frange(min_val, max_val, interval)]
                gene_space.append(possible_values)

        num_genes = len(gene_space)
        assert num_genes == sum(len(sp) for sp in setpoints_per_controller), \
            f"Mismatch: {num_genes} genes provided but {sum(len(sp) for sp in setpoints_per_controller)} setpoints found."

        self.initialization_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

        ga_instance = pygad.GA(
            num_generations=num_generations,
            num_parents_mating=int(crossover_rate * population_size),
            fitness_func=self.fitness_function,
            sol_per_pop=population_size,
            num_genes=num_genes,
            mutation_percent_genes=int(mutation_rate * 100),
            gene_space=gene_space,
            parent_selection_type="rank",  # Use rank selection
            crossover_type="single_point",
            mutation_type="random",
            mutation_by_replacement=True,
            on_generation=self.callback_generation,
            parallel_processing=("process", num_cores),
            stop_criteria=stop_criteria  # Add stop criteria here
        )

        ga_instance.run()

        solution, solution_fitness, _ = ga_instance.best_solution()
        self.save_to_csv()

        return solution, solution_fitness

    def callback_generation(self, ga_instance):
        solution, solution_fitness, _ = ga_instance.best_solution()
        self.best_individuals_per_generation.append(solution)
        self.fitness_per_generation.append(solution_fitness)
        print(f"Generation {len(self.fitness_per_generation)}: Best Fitness = {solution_fitness}")

    def save_to_csv(self):
        df = pd.DataFrame({
            "best_individuals_per_generation": self.best_individuals_per_generation,
            "fitness_per_generation": self.fitness_per_generation
        })
        filename = f"generation_data_{self.initialization_time}.csv"
        df.to_csv(filename, index=False)

    def initialize_model_with_best_solution(self, csv_filename, controllers, setpoints_per_controller):
        """
        Initializes the model with the best solution from the CSV file.

        Args:
            csv_filename (str): The filename of the CSV file containing the optimization results.
            controllers (list): List of controller names.
            setpoints_per_controller (list): List of lists, where each sublist contains setpoints for a controller.
        """
        df = pd.read_csv(csv_filename)

        best_row = df.loc[df['fitness_per_generation'].idxmax()]
        best_individual = best_row['best_individuals_per_generation']

        best_individual = ast.literal_eval(best_individual)

        gene_index = 0
        for ctrl_idx, controller_name in enumerate(controllers):
            controller = self.model.component_dict[controller_name]
            for setpoint_name in setpoints_per_controller[ctrl_idx]:
                value = best_individual[gene_index]
                rsetattr(controller, setpoint_name, value)
                gene_index += 1

        print("Model initialized with the best solution from the CSV file.")