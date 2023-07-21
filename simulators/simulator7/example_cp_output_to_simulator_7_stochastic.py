import json
import pandas as pd
from classes.classes import Scenario, ProductionPlan
from classes.operator import Operator
from classes.simulator_7 import Simulator
import numpy as np
from numpy import random

# Settings
size = 10
id = 1
cp_output = 'feasible'
x = random.randint(1000)
scenario_seed = x
policy_type = 2

# Read CP output and convert
instance_name = f"{size}_{id}_factory_1"
file_name = instance_name if cp_output == 'feasible' else f"{instance_name}_infeasible"
cp_output = pd.read_csv(f"results/cp_model/{file_name}.csv", delimiter=";")
print(f'Makespan according to CP outout is {max(cp_output["End"].tolist())}')
earliest_start = cp_output.to_dict('records')

# Read input instance
my_productionplan = ProductionPlan(
    **json.load(open('factory_data/stochastic/json_instances/instance_' + instance_name + '.json')))
my_productionplan.set_earliest_start_times(earliest_start)
my_productionplan.set_sequence(sequence=np.arange(size))
scenario_1 = my_productionplan.create_scenario(scenario_seed)

# Set printing to True if you want to print all events
operator = Operator(plan=scenario_1.PRODUCTION_PLAN, policy_type=policy_type, printing=False)
my_simulator = Simulator(plan=scenario_1.PRODUCTION_PLAN, operator=operator, printing=False)

# Run simulation
makespan, lateness, nr_unfinished = my_simulator.simulate(sim_time=1000, write=True, output_location=f""
f"simulators/simulator7/outputs/example_cp_output_to_simulator.csv")
print(f'According to the simulation, the makespan is {makespan} and the lateness is {lateness}')
print(f'The number of unfinished products {nr_unfinished}')
print(f'The number of clashes (i.e. activities that could not be processed) is {my_simulator.nr_clashes}')
