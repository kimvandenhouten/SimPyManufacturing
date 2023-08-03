import json


import pandas as pd
import numpy as np

from classes.classes import Scenario, ProductionPlan

# Set instance name
size = 10
id = 1
instance_name = f"{size}_{id}_factory_1"

# Read CP output csv
# choose this one if you want to see an infeasible example
# file_name = f"{instance_name}_infeasible"

# choose this one if you want to see a feasible example
file_name = f"{instance_name}"
cp_output = pd.read_csv(f"results/cp_model/{file_name}.csv", delimiter=";")

print(f'Makespan according to CP outout is {max(cp_output["End"].tolist())}')
# Convert to earlies starttimes dict
earliest_start = cp_output.to_dict('records') #TODO: check with Kim on this

# Read input instance
my_productionplan = ProductionPlan(
    **json.load(open('factory_data/instances_legacy/stochastic/json_instances/instance_' + instance_name + '.json')))
my_productionplan.set_earliest_start_times(earliest_start)
scenario_1 = my_productionplan.create_scenario(300)

# Load simulator
from classes.simulator_6 import Simulator

my_simulator = Simulator(plan=scenario_1.production_plan,
                         printing=False)  # Set printing to True if you want to print all events

# Run simulation
makespan, lateness, nr_unfinished = my_simulator.simulate(sim_time=1000, random_seed=300, write=True,
                                                          output_location=f"simulators/simulator6/data/example_cp_output_to_simulator.csv")
print(f'According to the simulation, the makespan is {makespan} and the lateness is {lateness}')
print(f'The number of unfinished products {nr_unfinished}')
print(f'The number of clashes (i.e. activities that could not be processed) is {my_simulator.nr_clashes}')

# Todo: build in some kind of check
# gannt = pd.read_csv(f"example_cp_output_to_simulator_6.csv"")
