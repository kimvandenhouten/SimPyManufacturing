# This script contains a minimal example for the simulation tool that takes as input
# the start times for all activities. Each start time corresponds to the time in the
# system that this activity requests the needed resources.

import numpy as np
from classes.classes import Factory
from classes.classes import Product
from classes.classes import Activity
import pandas as pd
from classes.classes import ProductionPlan

# Set up a factory
my_factory = Factory(NAME="MyFactory", RESOURCE_NAMES=["Filter", "Mixer", "Dryer"], CAPACITY=[1, 1, 1])
product = Product(NAME="Enzyme_1", ID=0)
activity0 = Activity(ID=0, PROCESSING_TIME=[4, 4], PRODUCT="Enzyme_1",
                     PRODUCT_ID="0", NEEDS="Filter")
activity1 = Activity(ID=1, PROCESSING_TIME=[5, 5], PRODUCT="Enzyme_1",
                     PRODUCT_ID="0", NEEDS="Mixer")
product.add_activity(activity=activity0)
product.add_activity(activity=activity1)
product.set_temporal_relations(TEMPORAL_RELATIONS={(0, 1): 4})
my_factory.add_product(product=product)
activity0 = Activity(ID=0, PROCESSING_TIME=[3, 3], PRODUCT="Enzyme_2",
                     PRODUCT_ID="1", NEEDS="Filter")
activity1 = Activity(ID=1, PROCESSING_TIME=[6, 6], PRODUCT="Enzyme_2",
                     PRODUCT_ID="1", NEEDS="Dryer")
product = Product(NAME="Enzyme_2", ID=1)
product.add_activity(activity=activity0)
product.add_activity(activity=activity1)
product.set_temporal_relations(TEMPORAL_RELATIONS={(0, 1): 1})
my_factory.add_product(product=product)

# Set up a production plan for this factory
my_productionplan = ProductionPlan(ID=0, SIZE=2, NAME="ProductionPlanJanuary", FACTORY=my_factory,
                                PRODUCT_IDS=[0, 1], DEADLINES=[8, 20])
my_productionplan.list_products()

# This is the old format for the simulator input
my_productionplan.set_sequence(sequence=[0, 1])

# This is the new format for the simulator input
earliest_start = [{"Product_ID": 0, "Activity_ID": 0, "Earliest_start": 0},
                  {"Product_ID": 0, "Activity_ID": 1, "Earliest_start": 4},
                  {"Product_ID": 1, "Activity_ID": 0, "Earliest_start": 0},
                  {"Product_ID": 1, "Activity_ID": 1, "Earliest_start": 1}]
my_productionplan.set_earliest_start_times(earliest_start)

# Import the new simulator
from classes.simulator_5 import Simulator
my_simulator = Simulator(plan=my_productionplan, printing=True)
my_simulator.simulate(SIM_TIME=1000, RANDOM_SEED=1, write=True, output_location=f"minimal_example_simulator_5.csv")
gannt = pd.read_csv(f"minimal_example_simulator_5.csv")

# initialize number of violations
constraint_checking = True
if constraint_checking:
    # Afterwards you can check the temporal relations
    print('------------------------------------------------------------ \n CONSTRAINT CHECKING \n')
    number_of_violations = 0
    # iterate over products
    for p, product in enumerate(my_productionplan.PRODUCTS):
        # obtain temporal relations
        for (i, j) in product.TEMPORAL_RELATIONS:
            print(i, j)
            print(f'The difference between the start time of activity {i} and activity {j} '
                  f'from product {p} should be exactly {product.TEMPORAL_RELATIONS[(i, j)]}')
            start_i = gannt.loc[(gannt['Product'] == p) & (gannt['Activity'] == i)]['Start'].values[0]
            start_j = gannt.loc[(gannt['Product'] == p) & (gannt['Activity'] == j)]['Start'].values[0]

            print(f'The simulated difference between the start time of activity {i} and activity {j} is {start_j-start_i}')
            if start_j-start_i == product.TEMPORAL_RELATIONS[(i, j)]:
                print("CONSTRAINT SATISFIED")
            else:
                print("CONSTRAINT VIOLATED")
                number_of_violations += 1

    # check violations of temporal relations by comparing start times of activities within temporal relations
    # report on violated relations
    print(f'TOTAL NUMBER OF VIOLATIONS {number_of_violations}')



