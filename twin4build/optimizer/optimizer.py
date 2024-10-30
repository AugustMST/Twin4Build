import pygad
import twin4build.base as base
from datetime import timedelta  # Import if needed for time calculations

class Optimizer:
    def __init__(self, model=None):
        self.model = model
        self.best_individuals_per_generation = []

    def fitness_function_wrapper(self, model, simulator, evaluator, stepSize, startTime, endTime, schedule, measuring_devices: list = [], weights: list = [], tchebycheff_z_star: list = [], electricity_price = None):
        time_difference = endTime - startTime
        total_seconds = time_difference.total_seconds()
        num_timesteps = int(total_seconds // stepSize)

        print(num_timesteps)

        def fitness_function(ga_instance, solution, solution_idx):
            setpoint_schedule = model.component_dict[schedule]

            # Set the CO2 setpoint based on the solution (genes)
            setpoint_schedule.weekDayRulesetDict["ruleset_default_value"] = 0
            setpoint_schedule.weekDayRulesetDict["ruleset_start_minute"] = [0] * num_timesteps
            setpoint_schedule.weekDayRulesetDict["ruleset_end_minute"] = [0] * num_timesteps
            setpoint_schedule.weekDayRulesetDict["ruleset_start_hour"] = list(range(0, num_timesteps))
            setpoint_schedule.weekDayRulesetDict["ruleset_end_hour"] = list(range(1, num_timesteps)) + [0]
            setpoint_schedule.weekDayRulesetDict["ruleset_value"] = solution

            print(setpoint_schedule.weekDayRulesetDict)

            # Run the simulation
            simulator.simulate(model, stepSize=stepSize, startTime=startTime, endTime=endTime, show_progress_bar=False)
            df = simulator.get_simulation_readings()

            tchebycheff_cost_list = []

            for i in range(len(measuring_devices)):
                cost = evaluator.get_kpi(df, measuring_devices[i], evaluation_metric="T", property_=None, model=model, electricity_prices = electricity_price)
                cost = cost.iloc[0]
                tchebycheff_cost = weights[i] * abs(cost - tchebycheff_z_star[i])
                tchebycheff_cost_list.append(tchebycheff_cost)

            fitness = -max(tchebycheff_cost_list)
            print(fitness)
            return fitness
        
        return fitness_function

    def run_ga(self, model, simulator, evaluator, stepSize, startTime, endTime, schedule, measuring_devices: list, weights: list, tchebycheff_z_star: list, 
               num_generations=100, population_size=3, crossover_rate=0.8, mutation_rate=0.1, setpoint_range: list = [], electricity_price = None):
        
        fitness_function = self.fitness_function_wrapper(model, simulator, evaluator, stepSize, startTime, endTime, schedule, measuring_devices, weights, tchebycheff_z_star, electricity_price=electricity_price)

        # Calculate NUM_HOURS based on the simulation parameters
        time_difference = endTime - startTime
        total_seconds = time_difference.total_seconds()
        num_timesteps = int(total_seconds // stepSize)  # Calculate number of timesteps

        ga_instance = pygad.GA(
            num_generations=num_generations,
            num_parents_mating=int(crossover_rate * population_size),
            fitness_func=fitness_function,
            sol_per_pop=population_size,
            num_genes=num_timesteps,
            init_range_low=setpoint_range[0],
            init_range_high=setpoint_range[1],
            mutation_percent_genes=int(mutation_rate * 100),
            gene_space={'low': setpoint_range[0], 'high': setpoint_range[1]},
            parent_selection_type="tournament",
            crossover_type="single_point",
            mutation_type="random",
            mutation_by_replacement=True,
            on_generation=self.callback_generation
        )

        ga_instance.run()
        solution, solution_fitness, solution_idx = ga_instance.best_solution()
        return solution, solution_fitness  # Return the best solution and its fitness
    
        
    # Optional: Callback function to print progress at each generation and store the best solution
    def callback_generation(self, ga_instance):
        # Ensure that the lists are not empty before accessing them
        if len(ga_instance.best_solutions) > 0 and len(ga_instance.best_solutions_fitness) > 0:
            best_solution = ga_instance.best_solutions[-1]  # Access last (best) solution
            best_solution_fitness = ga_instance.best_solutions_fitness[-1]  # Access corresponding fitness

            # Append the best solution to the list
            self.best_individuals_per_generation.append(best_solution)

            # Print the generation number and best fitness value
            print(f"Generation {ga_instance.generations_completed}: Best Fitness = {-best_solution_fitness}")
        else:
            # If lists are empty, handle this case (for example, by printing a message or taking other actions)
            print(f"Generation {ga_instance.generations_completed}: No best solution found yet.")

        return self.best_individuals_per_generation