import numpy as np
import pandas as pd
from datetime import datetime
from pymoo.core.problem import Problem
from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.operators.crossover.sbx import SBX
from pymoo.operators.mutation.pm import PM
from pymoo.operators.sampling.rnd import IntegerRandomSampling
from pymoo.optimize import minimize
from pymoo.termination import get_termination
from pymoo.core.callback import Callback
from fmpy.fmi2 import FMICallException
from twin4build.saref.property_.energy.energy import Energy
from twin4build.saref.property_.power.power import Power
from twin4build.saref.property_.temperature.temperature import Temperature
from twin4build.saref.property_.Co2.Co2 import Co2
from twin4build.utils.rsetattr import rsetattr
from dateutil import tz
import pickle
import twin4build as tb
from multiprocessing import Pool
import os

def frange(start, stop, step):
    while start <= stop:
        yield start
        start += step

class OptimizationProblem(Problem):
    def __init__(self, model, evaluator, startTime, endTime, stepSize, controllers, 
                 setpoints_per_controller, measuring_devices, objectives_to_include, 
                 gene_space, setpoint_interval, electricity_prices, heating_prices, num_cores=4):
        self.model = model
        self.evaluator = evaluator
        self.startTime = startTime
        self.endTime = endTime
        self.stepSize = stepSize
        self.controllers = controllers
        self.setpoints_per_controller = setpoints_per_controller
        self.measuring_devices = measuring_devices
        self.objectives_to_include = objectives_to_include
        self.electricity_prices = electricity_prices
        self.heating_prices = heating_prices
        self.setpoint_interval = setpoint_interval
        self.num_cores = num_cores
        self.gene_space = gene_space

        n_var = sum(len(gs) for gs in gene_space)
        xl = np.array([min(g) for group in gene_space for g in group])
        xu = np.array([max(g) for group in gene_space for g in group])

        self.discrete_options = []
        gene_index = 0
        for ctrl_idx, setpoints in enumerate(setpoints_per_controller):
            interval = setpoint_interval[ctrl_idx]
            for _ in setpoints:
                start = xl[gene_index]
                stop = xu[gene_index]
                options = list(frange(start, stop, interval))
                self.discrete_options.append(options)
                gene_index += 1

        self.xl = np.zeros(n_var, dtype=int)
        self.xu = np.array([len(options) - 1 for options in self.discrete_options], dtype=int)

        super().__init__(
            n_var=n_var,
            n_obj=len(objectives_to_include),
            n_constr=0,
            xl=self.xl,
            xu=self.xu,
            elementwise_evaluation=False
        )

    def map_to_discrete(self, design):
        return np.array([self.discrete_options[i][int(d)] for i, d in enumerate(design)])

    def evaluate_individual(self, design):
        try:
            discretized_design = self.map_to_discrete(design)
            gene_index = 0
            for ctrl_idx, controller_name in enumerate(self.controllers):
                controller = self.model.component_dict[controller_name]
                for setpoint_name in self.setpoints_per_controller[ctrl_idx]:
                    value = discretized_design[gene_index]
                    rsetattr(controller, setpoint_name, value)
                    gene_index += 1

            results_dict = self.evaluator.evaluate(
                startTime=self.startTime,
                endTime=self.endTime,
                stepSize=self.stepSize,
                models=[self.model],
                measuring_devices=self.measuring_devices,
                evaluation_metrics=["T"] * len(self.measuring_devices),
                method="optimize",
                electricity_prices=self.electricity_prices,
                heating_prices=self.heating_prices
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
                "temperature": temperature,
                "co2": co2,
                "consumption": total_consumption,
                "cost": total_cost
            }

            return [all_objectives[obj] for obj in self.objectives_to_include]
        except FMICallException as e:
            print(f"FMU error: {e}")
            return [-1e10] * len(self.objectives_to_include)

    def _evaluate(self, X, out, *args, **kwargs):
        with Pool(processes=self.num_cores) as pool:
            params = [X[i] for i in range(len(X))]
            F = pool.map(self.evaluate_individual, params)
        out["F"] = np.array(F)

    def close(self):
        pass

class HistoryCallback(Callback):
    def __init__(self):
        super().__init__()
        self.history = []

    def notify(self, algorithm):
        X = algorithm.pop.get("X")
        F = algorithm.pop.get("F")
        self.history.append((X, F))

class Optimizer:
    def __init__(self, model=None):
        self.model = model
        self.best_individuals_per_generation = []

    def run_ga(self, problem, num_generations=15, population_size=3, crossover_rate=0.5, mutation_rate=0.3, num_cores=4, save_dir="results"):
        # Ensure save_dir exists
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
            print(f"Created directory: {save_dir}")

        algorithm = NSGA2(
            pop_size=population_size,
            sampling=IntegerRandomSampling(),
            crossover=SBX(prob=crossover_rate, eta=15.0),
            mutation=PM(prob=mutation_rate, eta=20.0),
            eliminate_duplicates=True
        )
        termination = get_termination("n_gen", num_generations)
        callback = HistoryCallback()

        res = minimize(
            problem,
            algorithm,
            termination,
            callback=callback,
            verbose=True
        )
        problem.close()

        if res.X.ndim == 1:
            discrete_X = problem.map_to_discrete(res.X)
        else:
            discrete_X = np.array([problem.map_to_discrete(x) for x in res.X])

        # Save Pareto front
        pareto_df = pd.DataFrame(
            np.hstack((discrete_X, res.F)),
            columns=[f"x{i+1}" for i in range(discrete_X.shape[1])] + problem.objectives_to_include
        )
        pareto_path = os.path.join(save_dir, "pareto_front.csv")
        pareto_df.to_csv(pareto_path, index=False)
        print(f"Saved Pareto front to {pareto_path}")

        # Save problem configuration
        config = {
            "startTime": problem.startTime,
            "endTime": problem.endTime,
            "stepSize": problem.stepSize,
            "controllers": problem.controllers,
            "setpoints_per_controller": problem.setpoints_per_controller,
            "measuring_devices": problem.measuring_devices,
            "objectives_to_include": problem.objectives_to_include,
            "gene_space": problem.gene_space,
            "setpoint_interval": problem.setpoint_interval,
            "discrete_options": problem.discrete_options,
            "xl": problem.xl.tolist(),
            "xu": problem.xu.tolist(),
            "num_cores": problem.num_cores,
            "num_generations": num_generations,
            "population_size": population_size,
            "crossover_rate": crossover_rate,
            "mutation_rate": mutation_rate
        }
        config_path = os.path.join(save_dir, "problem_config.pkl")
        with open(config_path, "wb") as f:
            pickle.dump(config, f)
        print(f"Saved problem configuration to {config_path}")

        # Save convergence history
        history_data = {
            "X": [X for X, _ in callback.history],
            "F": [F for _, F in callback.history],
            "discrete_X": [np.array([problem.map_to_discrete(x) for x in X]) for X, _ in callback.history]
        }
        history_path = os.path.join(save_dir, "convergence_history.pkl")
        with open(history_path, "wb") as f:
            pickle.dump(history_data, f)
        print(f"Saved convergence history to {history_path}")

        return discrete_X, res.F