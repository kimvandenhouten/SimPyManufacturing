import unittest
from classes.classes import Factory, CompatibilityConstraint, TemporalRelation
from classes.classes import Product
from classes.classes import Activity
import pandas as pd
from classes.classes import ProductionPlan
from classes.distributions import NormalDistribution
from classes.simulator_7 import Simulator
from classes.operator import Operator


# Set up a factory
class MyTestCase(unittest.TestCase):
    def test_simulator(self):
        compatibility_constraints = [[{"product_id": 0, "activity_id": 0}, {"product_id": 1, "activity_id": 0}]]
        my_factory = Factory(name="Myfactory", resource_names=["Filter", "Mixer", "Dryer"], capacity=[2, 2, 2])
        # set id which is not index for testing

        product = Product(name="Enzyme_1", id=0)
        activity0 = Activity(id=0, processing_time=[10, 10], product="Enzyme_1",
                             product_id="0", needs=[1, 0, 1], distribution=NormalDistribution(4, 2))
        activity1 = Activity(id=1, processing_time=[5, 5], product="Enzyme_1",
                             product_id="0", needs=[0, 1, 0], distribution=NormalDistribution(0, 2))
        product.add_activity(activity=activity0)
        product.add_activity(activity=activity1)
        product.set_temporal_relations(temporal_relations={(0, 1): TemporalRelation(1, 2)})
        my_factory.add_product(product=product)
        activity0 = Activity(id=0, processing_time=[3, 3], product="Enzyme_2",
                             product_id="1", needs=[1, 0, 1])
        activity1 = Activity(id=1, processing_time=[6, 6], product="Enzyme_2",
                             product_id="1", needs=[0, 1, 1])

        product = Product(name="Enzyme_2", id=1)
        product.add_activity(activity=activity0)
        product.add_activity(activity=activity1)
        product.set_temporal_relations(temporal_relations={(0, 1): TemporalRelation(1)})
        my_factory.add_product(product=product)

        my_factory.set_compatibility_constraints(compatibility_constraints)
        # Set up a production plan for this factory
        my_productionplan = ProductionPlan(id=0, size=2, name="ProductionPlanJanuary", factory=my_factory,
                                           product_ids=[0, 1], deadlines=[8, 20])
        my_productionplan.list_products()

        # Define partial schedule that includes earliest start times
        earliest_start = [{"product_index": 0, "activity_id": 0, "earliest_start": 0},
                          {"product_index": 0, "activity_id": 1, "earliest_start": 2},
                          {"product_index": 1, "activity_id": 0, "earliest_start": 6},
                          {"product_index": 1, "activity_id": 1, "earliest_start": 7}]
        my_productionplan.set_earliest_start_times(earliest_start)

        scenario = my_productionplan.create_scenario(0)

        # Here you can choose policy 1 or policy 2
        #operator = Operator(plan=scenario.production_plan, policy_type=1, printing=True)
        operator = Operator(plan=my_productionplan, policy_type=1, printing=True)
        my_simulator = Simulator(plan=scenario.production_plan, operator=operator, printing=True)
        makespan, lateness, nr_unfinished = my_simulator.simulate(sim_time=1000, random_seed=1, write=False, )

        self.assertEqual(int(makespan), 7)
        self.assertEqual(lateness, 0)
        self.assertEqual(nr_unfinished, 1)
        self.assertEqual(my_simulator.nr_clashes, 1)


if __name__ == '__main__':
    unittest.main()
