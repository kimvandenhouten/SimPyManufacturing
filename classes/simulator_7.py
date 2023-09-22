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
            send_activity, delay, activity_id, product_index, proc_time, needs, finish = \
                self.operator.send_next_activity(current_time=self.env.now)

            if send_activity:
                self.env.process(self.activity_processing(activity_id, product_index, proc_time, needs))

            # Generator object that does a time-out for a time period equal to delay value
            yield self.env.timeout(delay)

        if self.printing:
            print(f'Starting pushback activity. Pushback list is {self.operator.pushback}')

        pushback = copy.deepcopy(self.operator.pushback)
        initial_earliest_starts = copy.deepcopy(self.plan.earliest_start)

        if len(pushback) > 0:
            self.pushback_mode = True   # We remember that we have done pushback so we can report this later
            for product in pushback:
                first_start_time = min(act['earliest_start'] for act in product)
                offset = self.env.now - first_start_time

                for act in product:
                    act['earliest_start'] += offset

                self.plan.earliest_start = product
                self.operator.plan.earliest_start = product

                finish = False

                # Ask operator about next activity
                while not finish:
                    send_activity, delay, activity_id, product_index, proc_time, needs, finish = \
                        self.operator.send_next_activity(current_time=self.env.now)

                    if send_activity:
                        self.env.process(
                            self.activity_processing(activity_id, product_index, proc_time, needs))

                    # Generator object that does a time-out for a time period equal to delay value
                    yield self.env.timeout(delay)
                if self.printing:
                    print(f'Pushback completed. Activites that did not succeed in pushback mode are:')
                    for i in self.operator.pushback:
                        print(i)
                self.plan.earliest_start = initial_earliest_starts
