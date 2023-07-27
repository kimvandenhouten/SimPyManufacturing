import json
import unittest
from deepdiff import DeepDiff

from classes.classes import Factory, ProductionPlan

fp = open('./resources-test/data_stochastic.json', 'r')
factory = Factory(**json.load(fp))

# Set up a production plan for this factory
my_productionplan = ProductionPlan(id=0, size=2, name="ProductionPlanJanuary", factory=factory,
                                   product_ids=[0, 1], deadlines=[8, 20])
my_productionplan.list_products()

# This is the old format for the simulator input
my_productionplan.set_sequence(sequence=[0, 1])

# This is the new format for the simulator input
earliest_start = [{"product_id": 0, "activity_id": 0, "earliest_start": 0},
                  {"product_id": 0, "activity_id": 1, "earliest_start": 1},
                  {"product_id": 1, "activity_id": 0, "earliest_start": 2},
                  {"product_id": 1, "activity_id": 1, "earliest_start": 3}]
my_productionplan.set_earliest_start_times(earliest_start)


class MyTestCase(unittest.TestCase):
    def test_production_plan_jsonify(self):
        json_instance = my_productionplan.to_json()

        with open('./resources-test/production_plan_stochastic.json', 'w+') as fp:
            fp.write(json_instance)

    def test_production_plan_read(self):
        production_plan = ProductionPlan(**json.load(open('./resources-test/production_plan_stochastic.json')))

        d = DeepDiff(my_productionplan, production_plan)
        self.assertEqual(d, {})


if __name__ == '__main__':
    unittest.main()
