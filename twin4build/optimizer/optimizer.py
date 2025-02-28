from tkinter import N
from types import NoneType

import pygad
import twin4build.base as base
from datetime import timedelta
from fmpy.fmi2 import FMICallException
import pandas as pd
from datetime import datetime

from twin4build.saref import property_
from twin4build.saref.property_.energy.energy import Energy
from twin4build.saref.property_.power.power import Power
from twin4build.saref.property_.temperature.temperature import Temperature
from twin4build.saref.property_.Co2.Co2 import Co2


class Optimizer:
    def __init__(self, model=None):
        self.model = model
        self.best_individuals_per_generation = []
        self.fitness_per_generation = []
        self.initialization_time = None
        self.counter = 0

    def fitness_function_wrapper(self, model, evaluator, stepSize, startTime, endTime, schedules, measuring_devices: list = [], weights: list = [], tchebycheff_z_star: list = [], electricity_price=None, heating_price = None):
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
            solution_matrix = solution.reshape((n_schedules, num_timesteps))

            for i, schedule_name in enumerate(schedules):
                setpoint_schedule = model.component_dict[schedule_name]
                setpoint_schedule.weekDayRulesetDict["ruleset_default_value"] = 0
                setpoint_schedule.weekDayRulesetDict["ruleset_start_minute"] = [0] * num_timesteps
                setpoint_schedule.weekDayRulesetDict["ruleset_end_minute"] = [0] * num_timesteps
                setpoint_schedule.weekDayRulesetDict["ruleset_start_hour"] = list(range(0, num_timesteps))
                setpoint_schedule.weekDayRulesetDict["ruleset_end_hour"] = list(range(1, num_timesteps)) + [0]
                setpoint_schedule.weekDayRulesetDict["ruleset_value"] = solution_matrix[i]

            try:
                results_dict = evaluator.evaluate(
                    startTime=startTime,
                    endTime=endTime,
                    stepSize=stepSize,
                    models=[model],
                    measuring_devices=measuring_devices,
                    evaluation_metrics=["T"] * len(measuring_devices),
                    method="optimize",
                    single_plot=False,
                    include_measured=False,
                    measuring_device_name_map=None,
                    options=None,
                    modelTotalKpi=False,
                    absolute=True,
                    electricity_prices=None,
                    heating_prices=None,
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
                    weights[i] * abs(cost[i] - tchebycheff_z_star[i])
                    for i in range(len(cost))
                ]

                fitness = -max(tchebycheff_cost_list)

            except FMICallException:
                fitness = -1e+10

            return fitness

        return fitness_function

    def run_ga(self, model, evaluator, stepSize, startTime, endTime, schedules, measuring_devices: list, weights: list, tchebycheff_z_star: list,
               num_generations=15, population_size=3, crossover_rate=0.5, mutation_rate=0.30, setpoint_ranges: list = [], electricity_price=None):

        fitness_function = self.fitness_function_wrapper(
            model, evaluator, stepSize, startTime, endTime, schedules, measuring_devices, weights, tchebycheff_z_star, electricity_price=electricity_price, 
        )

        time_difference = endTime - startTime
        total_seconds = time_difference.total_seconds()
        num_timesteps = int(total_seconds // stepSize)
        n_schedules = len(schedules)

        total_genes = num_timesteps * n_schedules

        gene_space = []
        for schedule_range in setpoint_ranges:
            gene_space.extend([{'low': schedule_range[0], 'high': schedule_range[1]}] * num_timesteps)

        if len(setpoint_ranges) == 1:
            gene_space *= n_schedules

        assert len(gene_space) == total_genes, f"gene_space length ({len(gene_space)}) does not match num_genes ({total_genes})"

        ga_instance = pygad.GA(
            num_generations=num_generations,
            num_parents_mating=int(crossover_rate * population_size),
            fitness_func=fitness_function,
            sol_per_pop=population_size,
            num_genes=total_genes,
            mutation_percent_genes=int(mutation_rate * 100),
            gene_space=gene_space,
            parent_selection_type="tournament",
            crossover_type="single_point",
            mutation_type="random",
            mutation_by_replacement=True,
            on_generation=self.callback_generation
        )

        ga_instance.run()
        solution, solution_fitness, _ = ga_instance.best_solution()

        solution_matrix = solution.reshape((n_schedules, num_timesteps))

        return solution_matrix, solution_fitness

    def callback_generation(self, ga_instance):
        solution, solution_fitness, _ = ga_instance.best_solution()

        if self.initialization_time is None:
            self.initialization_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

        self.best_individuals_per_generation.append(solution)
        self.fitness_per_generation.append(solution_fitness)

        self.save_to_csv()

    def save_to_csv(self):
        df = pd.DataFrame({
            "best_individuals_per_generation": self.best_individuals_per_generation,
            "fitness_per_generation": self.fitness_per_generation
        })

        filename = f"generation_data_{self.initialization_time}.csv"
        df.to_csv(filename, index=False)
