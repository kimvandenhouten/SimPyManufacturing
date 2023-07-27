# This script contains a minimal example for the simulation tool that takes as input
# the start times for all activities. Each start time corresponds to the time in the
# system that this activity requests the needed resources.
import jsonpickle
import numpy as np
from classes.classes import Factory,Scenario
from classes.classes import Product
from classes.classes import Activity
import pandas as pd
from classes.classes import ProductionPlan
import json

# Set up a factory
fp = open('factory_data/stochastic/data_stochastic.json', 'r')
factory = Factory(**json.load(fp))

# Set up a production plan for this factory
my_productionplan = ProductionPlan(id=0, size=2, name="ProductionPlanJanuary", factory=factory,
                                   product_ids=[0, 1], deadlines=[8, 20])
my_productionplan.list_products()

# This is the old format for the simulator input
my_productionplan.set_sequence(sequence=[0, 1])

# This is the new format for the simulator input
earliest_start = [{"product_id": 0, "activity_id": 0, "earliest_start": 0},
                  {"product_id": 0, "activity_id": 1, "earliest_start": 1},
                  {"product_id": 1, "activity_id": 0, "earliest_start": 2},
                  {"product_id": 1, "activity_id": 1, "earliest_start": 3}]
my_productionplan.set_earliest_start_times(earliest_start)

# create scenario and store
scenario_1 = my_productionplan.create_scenario(0)

with open('simulators/simulator6/data/' + factory.name + '_scenario_1.json', 'w+') as f:
    f.write(scenario_1.to_json())
    f.close()

# re load scenario and use
with open('simulators/simulator6/data/' + factory.name + '_scenario_1.json', 'r') as f:
    scenario_1 = Scenario(**json.load(f))

# Import the new simulator
from classes.simulator_6 import Simulator

my_simulator = Simulator(plan=scenario_1.production_plan, printing=True)
my_simulator.simulate(SIM_TIME=1000, random_seed=1, write=True,
                      output_location=f"simulators/simulator6/outputs/minimal_example_simulator_6.csv")
gannt = pd.read_csv(f"simulators/simulator6/outputs/minimal_example_simulator_6.csv")

# ignore from here
# initialize number of violations
constraint_checking = False
if constraint_checking:
    # Afterwards you can check the temporal relations
    print('------------------------------------------------------------ \n CONSTRAINT CHECKING \n')
    number_of_violations = 0
    # iterate over products
    for p, product in enumerate(my_productionplan.products):
        # obtain temporal relations
        for (i, j) in product.temporal_relations:
            print(i, j)
            print(f'The difference between the start time of activity {i} and activity {j} '
                  f'from product {p} should be exactly {product.temporal_relations[(i, j)]}')
            start_i = gannt.loc[(gannt['Product'] == p) & (gannt['Activity'] == i)]['Start'].values[0]
            start_j = gannt.loc[(gannt['Product'] == p) & (gannt['Activity'] == j)]['Start'].values[0]

            print(
                f'The simulated difference between the start time of activity {i} and activity {j} is {start_j - start_i}')
            if start_j - start_i == product.temporal_relations[(i, j)]:
                print("CONSTRAINT SATISFIED")
            else:
                print("CONSTRAINT VIOLATED")
                number_of_violations += 1

    # check violations of temporal relations by comparing start times of activities within temporal relations
    # report on violated relations
    print(f'TOTAL NUMBER OF VIOLATIONS {number_of_violations}')
