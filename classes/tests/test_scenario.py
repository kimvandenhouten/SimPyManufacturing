import json
import random
import unittest

import jsonpickle
import numpy as np

from classes.classes import Factory, ProductionPlan, Scenario


class TestScenarioCreation(unittest.TestCase):
    def init_production_plan(self):
        fp = open('./resources-test/data_stochastic.json', 'r')
        factory = Factory(**json.load(fp))
        my_productionplan = ProductionPlan(ID=0, SIZE=2, NAME="ProductionPlanJanuary", FACTORY=factory,
                                           PRODUCT_IDS=[0, 1], DEADLINES=[8, 20])
        my_productionplan.list_products()

        # This is the old format for the simulator input
        my_productionplan.set_sequence(sequence=[0, 1])

        # This is the new format for the simulator input
        earliest_start = [{"Product_ID": 0, "Activity_ID": 0, "Earliest_start": 0},
                          {"Product_ID": 0, "Activity_ID": 1, "Earliest_start": 1},
                          {"Product_ID": 1, "Activity_ID": 0, "Earliest_start": 2},
                          {"Product_ID": 1, "Activity_ID": 1, "Earliest_start": 3}]
        my_productionplan.set_earliest_start_times(earliest_start)

        return my_productionplan

    def test_scenario_creation(self):
        my_productionplan = self.init_production_plan()
        # create scenario and store
        scenario_1 = my_productionplan.create_scenario()
        scenario_1_json_str = scenario_1.to_json()
        with open('./resources-test/' + my_productionplan.FACTORY.NAME + '_scenario_1.json', 'w+') as f:
            f.write(scenario_1_json_str)
            f.close()

    def test_scenario_load(self):
        with open('./resources-test/factory_1_scenario_1.json', 'r') as f:
            scenario_1 = Scenario(**json.load(f))
            self.assertNotEqual(scenario_1.PRODUCTION_PLAN.FACTORY.PRODUCTS[0].ACTIVITIES[0].PROCESSING_TIME[0], None)

    def test_random_seeding(self):
        my_productionplan = self.init_production_plan()
        scenario_1 = my_productionplan.create_scenario(0)
        scenario_2 = my_productionplan.create_scenario(scenario_1.SEED)
        self.assertEqual(scenario_1.PRODUCTION_PLAN.FACTORY.PRODUCTS[0].ACTIVITIES[0].PROCESSING_TIME[0],
                         scenario_2.PRODUCTION_PLAN.FACTORY.PRODUCTS[0].ACTIVITIES[0].PROCESSING_TIME[0])
        self.assertEqual(scenario_1.PRODUCTION_PLAN.FACTORY.PRODUCTS[5].ACTIVITIES[1].PROCESSING_TIME[0],
                         scenario_2.PRODUCTION_PLAN.FACTORY.PRODUCTS[5].ACTIVITIES[1].PROCESSING_TIME[0])

        scenario_3 = my_productionplan.create_scenario(2)
        self.assertNotEqual(scenario_1.PRODUCTION_PLAN.FACTORY.PRODUCTS[0].ACTIVITIES[0].PROCESSING_TIME[0],
                            scenario_3.PRODUCTION_PLAN.FACTORY.PRODUCTS[0].ACTIVITIES[0].PROCESSING_TIME[0])

        scenario_4 = my_productionplan.create_scenario()
        self.assertNotEqual(scenario_3.PRODUCTION_PLAN.FACTORY.PRODUCTS[0].ACTIVITIES[0].PROCESSING_TIME[0],
                            scenario_4.PRODUCTION_PLAN.FACTORY.PRODUCTS[0].ACTIVITIES[0].PROCESSING_TIME[0])


if __name__ == '__main__':
    unittest.main()
