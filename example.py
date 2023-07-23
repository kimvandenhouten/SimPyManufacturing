from classes.classes import factory
my_factory = Factory(name="Myfactory", resource_name=["Filter", "Mixer", "Dryer"], capacity=[1, 1, 1])

from classes.classes import Product
product = Product(name="Enzyme_1", id=0)
product = Product(name="Enzyme_2", id=1)

from classes.classes import Activity
# Make the activites
activity0 = Activity(id=0, processing_time=[4, 4], product="Enzyme_1",
                     product_id="0", needs=[1, 0, 0])
activity1 = Activity(id=1, processing_time=[20, 30], product="Enzyme_1",
                     product_id="0", needs=[0, 1, 0])

# Add the activities to the product
product.add_activity(activity=activity0)
product.add_activity(activity=activity1)
# Set temporal relations, in this case meaning that activity 1 requests
# resources 10 minutes after start of activity 0.
product.set_temporal_relations(temporal_relations={(0, 1): 10})

# Add product to factory
my_factory.add_product(product=product)

from classes.classes import ProductionPlan
my_productionplan = ProductionPlan(id=0, size=10, name="ProductionPlanJanuary", factory=my_factory,
                                product_ids=[0, 0, 0], dealines=[70, 100, 120])
my_productionplan.list_products()
my_productionplan.set_sequence(sequence=[2, 0, 1])

from classes.simulator_3 import Simulator
my_simulator = Simulator(plan=my_productionplan, printing=True)
my_simulator.simulate(SIM_TIME=1000, random_seed=1)