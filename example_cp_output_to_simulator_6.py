import pandas as pd
import numpy as np
# Set instance name
size = 10
id = 1
instance_name = f"{size}_{id}_factory_1"

# Read CP output csv
# choose this one if you want to see an infeasible example
#file_name = f"{instance_name}_infeasible"

# choose this one if you want to see a feasible example
file_name = f"{instance_name}"
cp_output = pd.read_csv(f"results/cp_model/{file_name}.csv")
print(f'Makespan according to CP outout is {max(cp_output["End"].tolist())}')
# Convert to earlies starttimes dict
earliest_start = cp_output.to_dict('records')

# Read input instance
my_productionplan = pd.read_pickle(f"factory_data/instances/instance_{instance_name}.pkl")
my_productionplan.set_sequence(sequence=np.arange(size))
my_productionplan.set_earliest_start_times(earliest_start)

# Load simulator
from classes.simulator_6 import Simulator
my_simulator = Simulator(plan=my_productionplan, printing=False)  # Set printing to True if you want to print all events

# Run simulation
makespan, lateness = my_simulator.simulate(SIM_TIME=1000, RANDOM_SEED=1, write=True, output_location=f"example_cp_output_to_simulator.csv")
print(f'According to the simulation, the makespan is {makespan} and the lateness is {lateness}')
print(f'The number of clashes (i.e. activities that could not be processed) is {my_simulator.nr_clashes}')

# Todo: build in some kind of check
#gannt = pd.read_csv(f"example_cp_output_to_simulator_6.csv"")



