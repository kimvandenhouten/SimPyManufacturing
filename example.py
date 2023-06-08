from classes.classes import Factory
my_factory = Factory(NAME="MyFactory", RESOURCE_NAMES=["Filter", "Mixer", "Dryer"], CAPACITY=[1, 1, 1])

from classes.classes import Product
product = Product(NAME="Enzyme_1", ID=0)
product = Product(NAME="Enzyme_2", ID=1)

from classes.classes import Activity
# Make the activites
activity0 = Activity(ID=0, PROCESSING_TIME=[4, 4], PRODUCT="Enzyme_1",
                     PRODUCT_ID="0", NEEDS=[1, 0, 0])
activity1 = Activity(ID=1, PROCESSING_TIME=[20, 30], PRODUCT="Enzyme_1",
                     PRODUCT_ID="0", NEEDS=[0, 1, 0])

# Add the activities to the product
product.add_activity(activity=activity0)
product.add_activity(activity=activity1)
# Set temporal relations, in this case meaning that activity 1 requests
# resources 10 minutes after start of activity 0.
product.set_temporal_relations(TEMPORAL_RELATIONS={(0, 1): 10})

# Add product to factory
my_factory.add_product(product=product)

from classes.classes import ProductionPlan
my_productionplan = ProductionPlan(ID=0, SIZE=10, NAME="ProductionPlanJanuary", FACTORY=my_factory,
                                PRODUCT_IDS=[0, 0, 0], DEADLINES=[70, 100, 120])
my_productionplan.list_products()
my_productionplan.set_sequence(sequence=[2, 0, 1])

from classes.simulator_3 import Simulator
my_simulator = Simulator(plan=my_productionplan, printing=True)
my_simulator.simulate(SIM_TIME=1000, RANDOM_SEED=1)