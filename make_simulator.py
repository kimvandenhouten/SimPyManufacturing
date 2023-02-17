from classes import Activity, Product, ProductionPlan, Factory, Simulator
import random
# TODO: read input from CSV files ?

random.seed(1)
# MAKE FACTORY
factory = Factory(NAME="Seclin", RESOURCE_NAMES=["Fermenters", "Harvesting E", "Harvesting V", "FAM", "MF", "UF", "F+L",
                  "V300"], CAPACITY=[5, 4, 6, 3, 1, 4, 4, 11])

# MAKE PRODUCTS
## PRODUCT A
productA = Product(ID=0, NAME='Product A', TEMPORAL_RELATIONS={(0, 1): 2, (0, 2): 4})
activity0 = Activity(ID=0, PRODUCT="Product A", PRODUCT_ID="0", PROCESSING_TIME=[2, 2], NEEDS=[1, 0, 0, 0, 0, 0, 0, 0])
productA.add_activity(activity0)
activity1 = Activity(ID=1, PRODUCT="Product A", PRODUCT_ID="0", PROCESSING_TIME=[4, 4], NEEDS=[0, 1, 2, 0, 0, 0, 0, 0])
productA.add_activity(activity1)
activity2 = Activity(ID=2, PRODUCT="Product A", PRODUCT_ID="0", PROCESSING_TIME=[7, 7], NEEDS=[0, 0, 0, 1, 0, 0, 2, 2])
productA.add_activity(activity2)
productA.set_temporal_relations()
factory.add_product(productA)


## PRODUCT B
productB = Product(ID=1, NAME='Product B', TEMPORAL_RELATIONS={(0, 1): 2, (0, 2): 4, (0, 3): 6})
activity0 = Activity(ID=0, PRODUCT="Product B", PRODUCT_ID="1", PROCESSING_TIME=[7, 7], NEEDS=[1, 0, 0, 0, 0, 0, 0, 0])
productB.add_activity(activity0)
activity1 = Activity(ID=1, PRODUCT="Product B", PRODUCT_ID="1", PROCESSING_TIME=[8, 8], NEEDS=[0, 2, 2, 0, 0, 0, 0, 0])
productB.add_activity(activity1)
activity2 = Activity(ID=2, PRODUCT="Product B", PRODUCT_ID="1", PROCESSING_TIME=[9, 9], NEEDS=[0, 0, 0, 0, 1, 3, 3, 0])
productB.add_activity(activity2)
activity3 = Activity(ID=3, PRODUCT="Product B", PRODUCT_ID="1", PROCESSING_TIME=[9, 9], NEEDS=[0, 0, 0, 0, 0, 0, 0, 4])
productB.add_activity(activity3)
productB.set_temporal_relations()
factory.add_product(productB)

## PRODUCT C
productC = Product(ID=2, NAME='Product C', TEMPORAL_RELATIONS={(0, 1): 2, (0, 2): 4, (0, 3): 7})
activity0 = Activity(ID=0, PRODUCT="Product C", PRODUCT_ID="2", PROCESSING_TIME=[5, 5], NEEDS=[1, 1, 0, 0, 0, 0, 0, 0])
productC.add_activity(activity0)
activity1 = Activity(ID=1, PRODUCT="Product C", PRODUCT_ID="2", PROCESSING_TIME=[4, 4], NEEDS=[0, 1, 3, 0, 0, 0, 0, 0])
productC.add_activity(activity1)
activity2 = Activity(ID=2, PRODUCT="Product C", PRODUCT_ID="2", PROCESSING_TIME=[7, 7], NEEDS=[0, 0, 0, 0, 1, 1, 2, 0])
productC.add_activity(activity2)
activity3 = Activity(ID=3, PRODUCT="Product C", PRODUCT_ID="2", PROCESSING_TIME=[3, 3], NEEDS=[0, 0, 0, 0, 0, 0, 0, 2])
productC.add_activity(activity3)
productC.set_temporal_relations()
factory.add_product(productC)

## MAKE PRODUCTION PLAN
plan = ProductionPlan(ID=1, PRODUCT_IDS=[1, 1, 2, 0, 0, 2, 1], DEADLINES=[10, 11, 12, 13, 14, 15, 16], FACTORY=factory)
plan.list_products()

sequence = [0, 1, 2, 3, 4, 5, 6]
for iteration in range(0, 10):
    random.shuffle(sequence)
    plan.set_sequence(sequence)
    simulator = Simulator(plan)
    for SEED in [243674]:
        makespan, tardiness = simulator.simulate(SIM_TIME=1000, RANDOM_SEED=SEED, write=False)