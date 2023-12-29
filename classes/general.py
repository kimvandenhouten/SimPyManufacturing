import copy
import logging
import numpy as np


logger = None


def get_logger():
    global logger
    if logger is not None:
        return logger
    logger = logging.getLogger('SimPyManufacturing')
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # fh = logging.FileHandler('SimPyManufacturing.log')
    # fh.setLevel(logging.DEBUG)
    # fh.setFormatter(formatter)
    # logger.addHandler(fh)

    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    return logger


class Settings:
    def __init__(self, size=5, method="local_search", time_limit=180, budget=400, stop_criterium="Time",
                 simulator="Seclin", seed=1, instance="5_1", objective="makespan", init="random", l1=1, l2=1, k=40, m=20):
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
        self.l1 = l1
        self.l2 = l2
        self.k = k
        self.m = m

    def make_file_name(self):
        if self.stop_criterium == "Time":
            return f'{self.method}_simulator={self.simulator}_time_limit={self.time_limit}_seed={self.seed}_instance_' \
                   f'{self.instance}_objective={self.objective}_init={self.init}'

        else:
            return f'{self.method}_simulator={self.simulator}_budget={self.budget}_seed={self.seed}_instance_' \
                   f'{self.instance}_objective={self.objective}_init={self.init}'


def evaluator_simpy(plan, setting, sequence, sim_time=10000000, printing=False):

    if setting.simulator == "simulator_1":
        from classes.simulator_1 import Simulator
    if setting.simulator == "simulator_2":
        from classes.simulator_2 import Simulator
    if setting.simulator == "simulator_3":
        from classes.simulator_3 import Simulator

    plan.set_sequence(sequence)
    simulator = Simulator(plan, printing=printing)
    makespan, lateness = simulator.simulate(sim_time=sim_time, random_seed=setting.seed, write=False)
    fitness = setting.l1 * makespan + setting.l2 * lateness

    if printing:
        print(f"Makespan is {makespan}")
        print(f"Lateness is {lateness}")
        print(f"Fitness {fitness}")

    return fitness


def combine_sequences(best_sequences, x=None):
    unique_months = list(best_sequences.keys())
    fermentation_sequence = []
    # Combine the optimized sequences per month
    counter = 0
    for month_id in range(0, len(unique_months)):
        best_seq = best_sequences[unique_months[month_id]]
        best_seq = best_seq + counter
        fermentation_sequence.append(best_seq)
        counter += len(best_sequences[unique_months[month_id]])
    if x is not None:
        new_seq = copy.copy(x)
        new_seq = new_seq + counter
        fermentation_sequence.append(new_seq)

    fermentation_sequence = np.concatenate(fermentation_sequence)
    return fermentation_sequence
