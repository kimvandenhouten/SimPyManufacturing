import json
import unittest

import jsonpickle

from classes.classes import Factory, ProductionPlan, Scenario


class TestScenarioCreation(unittest.TestCase):
    def test_scenario_creation(self):
        fp = open('./resources-test/data_dist.json', 'r')
        factory = Factory(**json.load(fp)["FACTORIES"][0])
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

        # create scenario and store
        scenario_1 = Scenario(my_productionplan)
        scenario_1_json_str = jsonpickle.encode(scenario_1)
        with open('./resources-test/' + factory.NAME + '_scenario_1.json', 'w+') as f:
            f.write(scenario_1_json_str)
            f.close()

    def test_scenario_load(self):
        with open('./resources-test/MyFactory_scenario_1.json', 'r') as f:
            reloaded_str = f.read()
            scenario_1 = jsonpickle.decode(reloaded_str)
            self.assertNotEqual(scenario_1.PRODUCTION_PLAN.FACTORY.PRODUCTS[0].ACTIVITIES[0].PROCESSING_TIME[0], None)


if __name__ == '__main__':
    unittest.main()
