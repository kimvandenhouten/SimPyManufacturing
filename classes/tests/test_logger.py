import unittest

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


if __name__ == '__main__':
    unittest.main()
