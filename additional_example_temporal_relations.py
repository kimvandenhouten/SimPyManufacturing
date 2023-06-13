from classes.classes import Factory
from classes.classes import Product
from classes.classes import Activity
import pandas as pd

instance_name = "10_1_factory_1"
my_productionplan = pd.read_pickle(f"factory_data/instances/instance_{instance_name}.pkl")
my_productionplan.set_sequence(sequence=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9])

from classes.simulator_3 import Simulator
my_simulator = Simulator(plan=my_productionplan, printing=False)
my_simulator.simulate(SIM_TIME=100000, RANDOM_SEED=1, write=True, output_location=f"additional_example.csv")
print('------------------------------------------------------------ \n END OF SIMULATION PRINTING \n')
# TODO: automatically check whether constraints are violated

# read input
print('------------------------------------------------------------ \n CONSTRAINT CHECKING \n')
gannt = pd.read_csv("additional_example.csv")

# initialize number of violations
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


