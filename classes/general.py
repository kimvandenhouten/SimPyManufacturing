import copy
import logging
import logging.config
import sys

import numpy as np
import tomli as tomllib


def get_logger(name):
    if not getattr(get_logger, 'configured', False):
        with open("pyproject.toml", "rb") as f:
            config = tomllib.load(f).get("tool", {}).get("logging", {})
        if not config:
            raise KeyError("No logging configuration found")

        # NOTE: due to a bug in the logging library (?), handlers and formatters can't reliably be set through
        # dictConfig(). We set them manually now.

        console_handler = logging.StreamHandler(sys.stdout)
        format_dict = config.pop('formatters', {}).get('formatter', {})
        if format_dict:
            formatter = logging.Formatter(format_dict.get('format'))
            if 'default_time_format' in format_dict:
                formatter.default_time_format = format_dict['default_time_format']
            console_handler.setFormatter(formatter)
        logging.getLogger().addHandler(console_handler)

        logging.config.dictConfig(config)
        setattr(get_logger, 'configured', True)

    return logging.getLogger(name)


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
