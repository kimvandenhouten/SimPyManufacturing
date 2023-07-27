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
my_factory = Factory(name="Myfactory", resource_name=["Filter", "Mixer", "Dryer"], capacity=[1, 1, 1])
product = Product(name="Enzyme_1", id=0)
activity0 = Activity(id=0, processing_time=[4, 4], product="Enzyme_1",
                     product_id="0", needs=[1, 0, 1])
activity1 = Activity(id=1, processing_time=[5, 5], product="Enzyme_1",
                     product_id="0", needs=[0, 1, 0])
product.add_activity(activity=activity0)
product.add_activity(activity=activity1)
product.set_temporal_relations(temporal_relations={(0, 1): 4})
my_factory.add_product(product=product)
activity0 = Activity(id=0, processing_time=[3, 3], product="Enzyme_2",
                     product_id="1", needs=[1, 0, 1])
activity1 = Activity(id=1, processing_time=[6, 6], product="Enzyme_2",
                     product_id="1", needs=[0, 1, 1])
product = Product(name="Enzyme_2", id=1)
product.add_activity(activity=activity0)
product.add_activity(activity=activity1)
product.set_temporal_relations(temporal_relations={(0, 1): 1})
my_factory.add_product(product=product)
# Set up a production plan for this factory
my_productionplan = ProductionPlan(id=0, size=2, name="ProductionPlanJanuary", factory=my_factory,
                                   product_ids=[0, 1], deadlines=[8, 20])
my_productionplan.list_products()

# Define partial schedule that includes earliest start times
earliest_start = [{"product_id": 0, "activity_id": 0, "earliest_start": 0},
                  {"product_id": 0, "activity_id": 1, "earliest_start": 1},
                  {"product_id": 1, "activity_id": 0, "earliest_start": 2},
                  {"product_id": 1, "activity_id": 1, "earliest_start": 4}]
my_productionplan.set_earliest_start_times(earliest_start)

# Here you can choose policy 1 or policy 2
operator = Operator(plan=my_productionplan, policy_type=1, printing=True)
my_simulator = Simulator(plan=my_productionplan, operator=operator, printing=False)
makespan, lateness, nr_unfinished = my_simulator.simulate(sim_time=1000, random_seed=1, write=True, output_location=
f"simulators/simulator7/outputs/minimal_example_simulator_7.csv")
print(f'According to the simulation, the makespan is {makespan} and the lateness is {lateness}')
print(f'The number of unfinished products {nr_unfinished}')
print(f'The number of clashes (returned activities) is {my_simulator.nr_clashes}')



