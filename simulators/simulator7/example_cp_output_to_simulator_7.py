import json
import jsonpickle
import pandas as pd
import numpy as np
from classes.classes import Scenario
from classes.operator import Operator

# Set instance name
size = 10
id = 1
instance_name = f"{size}_{id}_factory_1"

# Read CP output csv
# choose this one if you want to see an infeasible example
#file_name = f"{instance_name}_infeasible"

# choose this one if you want to see a feasible example
file_name = f"{instance_name}"
cp_output = pd.read_csv(f"results/cp_model/{file_name}.csv", delimiter=";")

print(f'Makespan according to CP outout is {max(cp_output["End"].tolist())}')
# Convert to earlies starttimes dict
earliest_start = cp_output.to_dict('records')

# Read input instance
my_productionplan = pd.read_pickle(f"factory_data/instances_new/instance_{instance_name}.pkl")
my_productionplan.set_earliest_start_times(earliest_start)

# Load simulator
from classes.simulator_7 import Simulator
# Set printing to True if you want to print all events
operator = Operator(plan=my_productionplan, policy_type=1, printing=False)
my_simulator = Simulator(plan=my_productionplan, operator=operator, printing=False)

# Run simulation
makespan, lateness, nr_unfinished = my_simulator.simulate(sim_time=1000, random_seed=3, write=True, output_location=f""
f"simulators/simulator7/outputs/example_cp_output_to_simulator.csv")
print(f'According to the simulation, the makespan is {makespan} and the lateness is {lateness}')
print(f'The number of unfinished products {nr_unfinished}')
print(f'The number of clashes (i.e. activities that could not be processed) is {my_simulator.nr_clashes}')
