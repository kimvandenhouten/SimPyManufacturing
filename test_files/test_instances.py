"""
For running this script set working directory to ~/SimPyManufacturing
"""

import pandas as pd
from classes import Simulator

instance_name = "120_1"
plan = pd.read_pickle(f"factory_data/instances/instance_{instance_name}.pkl")
sequence = range(0, plan.SIZE)
plan.set_sequence(sequence)
simulator = Simulator(plan, printing=False)
for SEED in [243674]:
    makespan, tardiness = simulator.simulate(SIM_TIME=100000, RANDOM_SEED=SEED, write=False)