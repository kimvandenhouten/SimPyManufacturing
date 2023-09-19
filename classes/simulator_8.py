import copy
from collections import namedtuple

import simpy
import random

from classes.base_simulator import BaseSimulator
from classes.classes import SimulatorLogger, Action, FailureCode


class Simulator(BaseSimulator):
    def __init__(self, plan, operator, printing=False):
        super().__init__(plan, operator, printing)

    def activity_generator(self):
        """Generate activities that arrive at the factory based on earliest start times."""
        finish = False

        # Ask operator about next activity
        while not finish:
            activities_that_can_start = self.operator.send_next_activity(current_time=self.env.now)

            for (product_index, activity_id) in activities_that_can_start:
                needs = self.plan.products[product_index].activities[activity_id].needs
                proc_time = max(self.plan.products[product_index].activities[activity_id].processing_time[0], 1)
                self.env.process(self.activity_processing(activity_id, product_index, proc_time, needs))

            # Generator object that does a time-out for a time period equal to delay value
            yield self.env.timeout(1)