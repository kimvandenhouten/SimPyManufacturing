import json
import pandas as pd
from classes.classes import Scenario, ProductionPlan
from classes.operator import Operator
from classes.simulator_7 import Simulator
import numpy as np
from numpy import random
from matplotlib import pyplot as plt

# Settings
instance_size = 10
instance_id = 1
cp_output = 'feasible'
scenario_seeds = random.randint(100000, size=1)
policy_type = 2
printing = False

# Read CP output and convert
instance_name = f"{instance_size}_{instance_id}_factory_1"
file_name = instance_name if cp_output == 'feasible' else f"{instance_name}_infeasible"
cp_output = pd.read_csv(f"results/cp_model/{file_name}.csv", delimiter=";")
print(f'Makespan according to CP outout is {max(cp_output["End"].tolist())}')
earliest_start = cp_output.to_dict('records')

seed = scenario_seeds[0]
# Read input instance
my_productionplan = ProductionPlan(
    **json.load(open('factory_data/instances_legacy/stochastic/json_instances/instance_' + instance_name + '.json')))
my_productionplan.set_earliest_start_times(earliest_start)
my_productionplan.set_sequence(sequence=np.arange(instance_size))
scenario_1 = my_productionplan.create_scenario(seed)

# Set printing to True if you want to print all events
operator = Operator(plan=scenario_1.production_plan, policy_type=policy_type, printing=False)
my_simulator = Simulator(plan=scenario_1.production_plan, operator=operator, printing=False)

# Run simulation
makespan, lateness, nr_unfinished = my_simulator.simulate(sim_time=2000, write=False, output_location=f""
f"simulators/simulator7/outputs/example_cp_output_to_simulator.csv")
if printing:
    print(f'According to the simulation, the makespan is {makespan} and the lateness is {lateness}')
    print(f'The number of unfinished products {nr_unfinished}')
    print(f'The number of clashes (i.e. activities that could not be processed) is {my_simulator.nr_clashes}')

gannt = my_simulator.logger.info.to_df()

# Afterwards you can check the temporal relations
print('------------------------------------------------------------ \n CONSTRAINT CHECKING \n')
number_of_violations = 0
# iterate over products
for p, product in enumerate(my_productionplan.products):
    # obtain temporal relations
    for (i, j) in product.temporal_relations:
        print(i, j)
        print(f'The difference between the start time of activity {i} and activity {j} '
              f'from product {p} should be at least {product.temporal_relations[(i, j)].min_lag}')
        start_i = gannt.loc[(gannt['ProductIndex'] == p) & (gannt['Activity'] == i)]['Start'].values[0]
        start_j = gannt.loc[(gannt['ProductIndex'] == p) & (gannt['Activity'] == j)]['Start'].values[0]

        print(f'The simulated difference between the start time of activity {i} and activity {j} is {start_j-start_i}')
        if start_j-start_i >= product.temporal_relations[(i, j)].min_lag:
            print("CONSTRAINT SATISFIED")
        else:
            print("CONSTRAINT VIOLATED")
            number_of_violations += 1

# check violations of temporal relations by comparing start times of activities within temporal relations
# report on violated relations
print(f'TOTAL NUMBER OF VIOLATIONS {number_of_violations}')