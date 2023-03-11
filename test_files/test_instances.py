"""
For running this script set working directory to ~/SimPyManufacturing
"""

import pandas as pd
import random
simulator_name = "simulator_3"

if simulator_name == "simulator_1":
    from classes.simulator_1 import Simulator
elif simulator_name == "simulator_2":
    from classes.simulator_2 import Simulator
elif simulator_name == "simulator_3":
    from classes.simulator_3 import Simulator

for factory_name in ["factory_1"]:
    print(factory_name)
    for size in [20, 40]:
        for id in range(1, 2):
            instance_name = f'{size}_{id}'
            data = []
            print(instance_name)
            plan = pd.read_pickle(f"factory_data/instances/instance_{instance_name}_{factory_name}.pkl")
            sequence = [i for i in range(0, round(plan.SIZE/2))]
            for SEED in range(1, 2):
                plan.set_sequence(sequence)
                simulator = Simulator(plan, printing=False)
                makespan, lateness = simulator.simulate(SIM_TIME=300000, RANDOM_SEED=SEED, write=True,
                                                       output_location=f"results/resource_usage/simulator={simulator_name}_instance_{instance_name}_{factory_name}_seed={SEED}.csv")
                data.append({"instance": instance_name,
                             "seed": SEED,
                             "sequence": sequence,
                             "makespan": makespan,
                             "lateness": lateness,
                             "makespan_lateness": makespan+lateness})

                random.shuffle(sequence)
            data = pd.DataFrame(data)
            print(f'min makespan value {data["makespan"].min()}')
            print(f'max makespan value {data["makespan"].max()}')
            print(f'min lateness value {data["lateness"].min()}')
            print(f'max lateness value {data["lateness"].max()}')
