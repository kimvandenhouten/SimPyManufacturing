import json
import random
import unittest

import jsonpickle
import numpy as np

from classes.classes import Factory,ProductionPlan, Scenario


class TestScenarioCreation(unittest.TestCase):
    def init_production_plan(self):
        fp = open('./resources-test/data_stochastic.json', 'r')
        factory = Factory(**json.load(fp))
        my_productionplan = ProductionPlan(id=0, size=2, name="ProductionPlanJanuary", factory=factory,
                                           product_ids=[0, 1], deadlines=[8, 20])
        my_productionplan.list_products()

        # This is the old format for the simulator input
        my_productionplan.set_sequence(sequence=[0, 1])

        # This is the new format for the simulator input
        earliest_start = [{"product_index": 0, "activity_id": 0, "earliest_start": 0},
                          {"product_index": 0, "activity_id": 1, "earliest_start": 1},
                          {"product_index": 1, "activity_id": 0, "earliest_start": 2},
                          {"product_index": 1, "activity_id": 1, "earliest_start": 3}]
        my_productionplan.set_earliest_start_times(earliest_start)

        return my_productionplan

    def test_scenario_creation(self):
        my_productionplan = self.init_production_plan()
        # create scenario and store
        scenario_1 = my_productionplan.create_scenario()
        scenario_1_json_str = scenario_1.to_json()
        with open('./resources-test/' + my_productionplan.factory.name + '_scenario_1.json', 'w+') as f:
            f.write(scenario_1_json_str)
            f.close()

    def test_scenario_load(self):
        with open('./resources-test/factory_1_scenario_1.json', 'r') as f:
            scenario_1 = Scenario(**json.load(f))
            self.assertNotEqual(scenario_1.production_plan.products[0].activities[0].processing_time[0], None)

    def test_random_seeding(self):
        my_productionplan = self.init_production_plan()
        scenario_1 = my_productionplan.create_scenario(0)
        scenario_2 = my_productionplan.create_scenario(scenario_1.seed)
        self.assertEqual(scenario_1.production_plan.products[0].activities[0].processing_time[0],
                         scenario_2.production_plan.products[0].activities[0].processing_time[0])
        self.assertEqual(scenario_1.production_plan.products[1].activities[1].processing_time[0],
                         scenario_2.production_plan.products[1].activities[1].processing_time[0])

        scenario_3 = my_productionplan.create_scenario(2)
        self.assertNotEqual(scenario_1.production_plan.products[0].activities[0].processing_time[0],
                            scenario_3.production_plan.products[0].activities[0].processing_time[0])

        scenario_4 = my_productionplan.create_scenario()
        self.assertNotEqual(scenario_3.production_plan.products[0].activities[0].processing_time[0],
                            scenario_4.production_plan.products[0].activities[0].processing_time[0])

        #Ensure no sampling on factory product level
        self.assertEqual(scenario_1.production_plan.factory.products[0].activities[0].processing_time[0],
                         scenario_2.production_plan.factory.products[0].activities[0].processing_time[0])


if __name__ == '__main__':
    unittest.main()
