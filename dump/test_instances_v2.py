"""
For running this script set working directory to ~/SimPyManufacturing
"""

import pandas as pd
import random
from classes_v2 import Simulator


for instance_name in ['120_1']:
    data = []
    print(instance_name)
    plan = pd.read_pickle(f"factory_data/instances_v2/instance_{instance_name}.pkl")
    sequence = [i for i in range(0, plan.SIZE)]
    for SEED in range(0, 2):
        plan.set_sequence(sequence)
        simulator = Simulator(plan, printing=False)
        makespan, tardiness = simulator.simulate(SIM_TIME=30000, RANDOM_SEED=SEED, write=True, output_location=f"results/instance_{instance_name}_seed={SEED}.csv")
        random.shuffle(sequence)
        data.append({"instance": instance_name,
                     "seed": SEED,
                     "sequence": sequence,
                     "makespan": makespan,
                     "tardiness": tardiness})

    data = pd.DataFrame(data)
    print(data["makespan"].min())
    print(data["makespan"].max())
#data.to_csv("results/results_table.csv")