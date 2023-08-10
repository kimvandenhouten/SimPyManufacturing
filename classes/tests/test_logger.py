import unittest
from collections import namedtuple

from classes.classes import SimulatorLogger, Action


class MyTestCase(unittest.TestCase):
    def test_logging(self):
        logger = SimulatorLogger("test_simulator")
        logger.log_activity(0, 0, Action.START)
        self.assertTrue((0, 0) in logger.active_processes)
        logger.log_activity(1, 0, Action.START)
        logger.log_activity(0, 0, Action.END)
        self.assertTrue((0, 0) not in logger.active_processes)
        self.assertTrue((1, 0) in logger.active_processes)

    def test_info(self):
        logger = SimulatorLogger("test_simulator")
        Resource = namedtuple('Machine', 'resource_group, id')
        resources = [Resource(resource_group='Harvesting tanks A', id=3)]
        needs = [0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0]
        logger.info.log(7, 0, 1, needs, resources, 1, 1, 1, 2)
        self.assertEqual(len(logger.info.entries), 1)
        self.assertEqual(logger.info.entries[0].product_id, 7)
        self.assertEqual(logger.info.entries[0].product_idx, 1)
        self.assertEqual(logger.info.entries[0].activity_id, 0)

        self.assertIsNotNone(logger.info.to_df())


if __name__ == '__main__':
    unittest.main()
