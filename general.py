from classes import Simulator
import copy
import numpy as np


class Settings:
    def __init__(self, size=5, method="local_search", time_limit=180, budget=400, stop_criterium="Time",
                 simulator="Seclin", seed=1, instance="5_1", objective="makespan", init="random"):
        self.method = method
        self.init = init
        self.time_limit = time_limit
        self.budget = budget
        self.stop_criterium = stop_criterium
        self.seed = seed
        self.simulator = simulator
        self.instance = instance
        self.size = size
        self.objective = objective

    def make_file_name(self):
        if self.stop_criterium == "Time":
            return f'{self.method}_simulator={self.simulator}_time_limit={self.time_limit}_seed={self.seed}_instance_' \
                   f'{self.instance}_objective={self.objective}_init={self.init}'

        else:
            return f'{self.method}_simulator={self.simulator}_budget={self.budget}_seed={self.seed}_instance_' \
                   f'{self.instance}_objective={self.objective}_init={self.init}'


def evaluator_simpy(plan, sequence, seed, sim_time=10000000, objective="Makespan", printing=False):
    plan.set_sequence(sequence)
    simulator = Simulator(plan, printing=printing)
    makespan, tardiness = simulator.simulate(SIM_TIME=sim_time, RANDOM_SEED=seed, write=False)
    if printing:
        print(f"Makespan is {makespan}")
        print(f"Tardiness is {tardiness}")
        print(f"Average tardiness is {tardiness/plan.SIZE}")

    if objective == "Makespan":
        if printing:
            print(f'Fitness is {makespan}')
        return makespan
    elif objective == "Tardiness":
        if printing:
            print(f'Fitness is {tardiness / plan.SIZE}')
        return tardiness / plan.SIZE
    elif objective == "Makespan_Lateness":
        if printing:
            print(f'Fitness is {makespan + tardiness}')
        return makespan + tardiness
    elif objective == "Makespan_Average_Lateness":
        if printing:
            print(f'Fitness is {makespan + tardiness / plan.SIZE}')
        return makespan + tardiness / plan.SIZE


def combine_sequences(best_sequences, x=None):
    unique_months = list(best_sequences.keys())
    fermentation_sequence = []
    # Combine the optimized sequences per month
    counter = 0
    for month_id in range(0, len(unique_months)):
        best_seq = best_sequences[unique_months[month_id]]
        best_seq= best_seq + counter
        fermentation_sequence.append(best_seq)
        counter += len(best_sequences[unique_months[month_id]])
    if x is not None:
        new_seq = copy.copy(x)
        new_seq = new_seq + counter
        fermentation_sequence.append(new_seq)

    fermentation_sequence = np.concatenate(fermentation_sequence)
    return fermentation_sequence