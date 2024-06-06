import json
import pandas as pd
from classes.classes import Scenario, ProductionPlan
from classes.operator import Operator
from classes.simulator_7 import Simulator
import numpy as np
from numpy import random
from matplotlib import pyplot as plt

# In this file it is expected that because we only do the deterministic run there should not be any clashes.
# However, due to the fact that product index 9 activity 0, and activity 1 have a min lag equal to zero, we
# enter the situation in which both are scheduled at the same earliest start time, but because of a tie,
# activity 1 is sent to the factory earlier than activity 0. This raises a precedence constraint. However,
# we shouldn't get one.
# TODO: fix this issue


# Settings
nr_scenarios = 1000
scenario_seeds = random.randint(100000, size=nr_scenarios)
policy_type = 2
printing = True

for instance_size in [10]:
    for instance_id in range(4, 5):
        # Read CP output and convert
        instance_name = f"{instance_size}_{instance_id}_factory_1"
        print(instance_name)
        file_name = instance_name
        cp_output = pd.read_csv(f"results/cp_model/development/instances_type_2/start times {file_name}.csv")
        makespan_cp_output = max(cp_output["end"].tolist())
        print(f'Makespan according to CP outout is {makespan_cp_output}')
        earliest_start = cp_output.to_dict('records')
        evaluation = []

        # deterministic check:
        # Read input instance
        my_productionplan = ProductionPlan(
            **json.load(open('factory_data/development/instances_type_2/instance_' + instance_name + '.json')))
        my_productionplan.set_earliest_start_times(earliest_start)
        my_productionplan.set_sequence(sequence=np.arange(instance_size))

        # Set printing to True if you want to print all events
        operator = Operator(plan=my_productionplan, policy_type=policy_type, printing=False)
        my_simulator = Simulator(plan=my_productionplan, operator=operator, printing=True)

        # Run simulation
        makespan, lateness, nr_unfinished = my_simulator.simulate(sim_time=2000, write=False)

        print(f'According to the deterministic simulation, the makespan is {makespan}')
        print(f'The number of unfinished products {nr_unfinished}')
        print(f'The number of clashes (i.e. activities that could not be processed) is {my_simulator.nr_clashes}')

