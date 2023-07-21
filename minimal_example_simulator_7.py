# This script contains a minimal example for the simulation tool that takes as input
# the start times for all activities. Each start time corresponds to the time in the
# system that this activity requests the needed resources.

from classes.classes import Factory
from classes.classes import Product
from classes.classes import Activity
import pandas as pd
from classes.classes import ProductionPlan
from classes.simulator_7 import Simulator
from classes.operator import Operator
# Set up a factory
my_factory = Factory(NAME="MyFactory", RESOURCE_NAMES=["Filter", "Mixer", "Dryer"], CAPACITY=[1, 1, 1])
product = Product(NAME="Enzyme_1", ID=0)
activity0 = Activity(ID=0, PROCESSING_TIME=[4, 4], PRODUCT="Enzyme_1",
                     PRODUCT_ID="0", NEEDS=[1, 0, 1])
activity1 = Activity(ID=1, PROCESSING_TIME=[5, 5], PRODUCT="Enzyme_1",
                     PRODUCT_ID="0", NEEDS=[0, 1, 0])
product.add_activity(activity=activity0)
product.add_activity(activity=activity1)
product.set_temporal_relations(TEMPORAL_RELATIONS={(0, 1): 4})
my_factory.add_product(product=product)
activity0 = Activity(ID=0, PROCESSING_TIME=[3, 3], PRODUCT="Enzyme_2",
                     PRODUCT_ID="1", NEEDS=[1, 0, 1])
activity1 = Activity(ID=1, PROCESSING_TIME=[6, 6], PRODUCT="Enzyme_2",
                     PRODUCT_ID="1", NEEDS=[0, 1, 1])
product = Product(NAME="Enzyme_2", ID=1)
product.add_activity(activity=activity0)
product.add_activity(activity=activity1)
product.set_temporal_relations(TEMPORAL_RELATIONS={(0, 1): 1})
my_factory.add_product(product=product)
# Set up a production plan for this factory
my_productionplan = ProductionPlan(ID=0, SIZE=2, NAME="ProductionPlanJanuary", FACTORY=my_factory,
                                PRODUCT_IDS=[0, 1], DEADLINES=[8, 20])
my_productionplan.list_products()

# Define partial schedule that includes earliest start times
earliest_start = [{"Product_ID": 0, "Activity_ID": 0, "Earliest_start": 0},
                  {"Product_ID": 0, "Activity_ID": 1, "Earliest_start": 1},
                  {"Product_ID": 1, "Activity_ID": 0, "Earliest_start": 2},
                  {"Product_ID": 1, "Activity_ID": 1, "Earliest_start": 4}]
my_productionplan.set_earliest_start_times(earliest_start)

# Here you can choose policy 1 or policy 2
operator = Operator(plan=my_productionplan, policy_type=1, printing=True)
my_simulator = Simulator(plan=my_productionplan, operator=operator, printing=False)
makespan, lateness, nr_unfinished = my_simulator.simulate(sim_time=1000, random_seed=1, write=True, output_location=f"minimal_example_simulator_7.csv")
print(f'According to the simulation, the makespan is {makespan} and the lateness is {lateness}')
print(f'The number of unfinished products {nr_unfinished}')
print(f'The number of clashes (returned activities) is {my_simulator.nr_clashes}')
gannt = pd.read_csv(f"minimal_example_simulator_7.csv")




