"""
For running this script set working directory to ~/SimPyManufacturing
"""

import pandas as pd
import random
from classes import Simulator


for instance_name in ['40_1']:
    data = []
    print(instance_name)
    plan = pd.read_pickle(f"factory_data/instances/instance_{instance_name}.pkl")
    sequence = [i for i in range(0, plan.SIZE)]
    for SEED in range(1, 2):
        plan.set_sequence(sequence)
        simulator = Simulator(plan, printing=False)
        makespan, tardiness = simulator.simulate(SIM_TIME=300000, RANDOM_SEED=SEED, write=True,
                                                 output_location=f"results/resource_usage/instance_{instance_name}_seed={SEED}.csv")
        random.shuffle(sequence)
        data.append({"instance": instance_name,
                     "seed": SEED,
                     "sequence": sequence,
                     "makespan": makespan,
                     "tardiness": tardiness,
                     "makespan_tardiness": makespan+tardiness})

    data = pd.DataFrame(data)
    print(data["makespan_tardiness"].min())
    print(data["makespan_tardiness"].max())
