from classes.classes import Factory
from classes.classes import Product
from classes.classes import Activity

my_factory = Factory(NAME="MyFactory", RESOURCE_NAMES=["Filter", "Mixer", "Dryer"], CAPACITY=[1, 1, 1])
product = Product(NAME="Enzyme_1", ID=0)
activity0 = Activity(ID=0, PROCESSING_TIME=[4, 4], PRODUCT="Enzyme_1",
                     PRODUCT_ID="0", NEEDS=[1, 0, 0])
activity1 = Activity(ID=1, PROCESSING_TIME=[5, 5], PRODUCT="Enzyme_1",
                     PRODUCT_ID="0", NEEDS=[0, 1, 0])
product.add_activity(activity=activity0)
product.add_activity(activity=activity1)
product.set_temporal_relations(TEMPORAL_RELATIONS={(0, 1): 4})
my_factory.add_product(product=product)

# Make the activites for product 1
activity0 = Activity(ID=0, PROCESSING_TIME=[3, 3], PRODUCT="Enzyme_2",
                     PRODUCT_ID="1", NEEDS=[0, 0, 1])
activity1 = Activity(ID=1, PROCESSING_TIME=[6, 6], PRODUCT="Enzyme_2",
                     PRODUCT_ID="1", NEEDS=[0, 1, 0])
product = Product(NAME="Enzyme_2", ID=1)
product.add_activity(activity=activity0)
product.add_activity(activity=activity1)
product.set_temporal_relations(TEMPORAL_RELATIONS={(0, 1): 1})
my_factory.add_product(product=product)

from classes.classes import ProductionPlan
my_productionplan = ProductionPlan(ID=0, SIZE=2, NAME="ProductionPlanJanuary", FACTORY=my_factory,
                                PRODUCT_IDS=[0, 1], DEADLINES=[8, 20])
my_productionplan.list_products()
my_productionplan.set_sequence(sequence=[0, 1])

from classes.simulator_3 import Simulator
my_simulator = Simulator(plan=my_productionplan, printing=True)
my_simulator.simulate(SIM_TIME=1000, RANDOM_SEED=1, write=True, output_location=f"minimal_example.csv")