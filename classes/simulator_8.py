import copy
from collections import namedtuple
import numpy as np
import simpy
import random

from classes.base_simulator import BaseSimulator
from classes.classes import SimulatorLogger, Action, FailureCode


class Simulator(BaseSimulator):
    def __init__(self, plan, operator, check_max_time_lag, printing=False):
        super().__init__(plan, operator, check_max_time_lag, printing)

    def activity_generator(self):
        """Generate activities that arrive at the factory based on earliest start times."""
        finish = False

        # Ask operator about next activity
        while not finish:
            send_activity, delay, activity_id, product_index, finish, required_resources\
                = self.operator.send_next_activity(current_time=self.env.now)

            if send_activity:
                needs = self.plan.products[product_index].activities[activity_id].needs
                proc_time = max(self.plan.products[product_index].activities[activity_id].processing_time[0], 1)
                self.env.process(self.activity_processing(activity_id, product_index, proc_time, needs, required_resources))

            # Generator object that does a time-out for a time period equal to delay value
            yield self.env.timeout(delay)

    def activity_start(self, activity_id, product_index, resources):
        start_time = super().activity_start(activity_id, product_index)
        self.operator.set_start_time(activity_id, product_index, start_time, resources)
        return start_time

    def activity_end(self, activity_id, product_index):
        end_time = super().activity_end(activity_id, product_index)
        self.operator.set_end_time(activity_id, product_index, end_time)
        return end_time

    def activity_fail(self, product_index, activity_id):
        failed = True
        self.nr_clashes += 1
        return failed

    def activity_processing(self, activity_id, product_index, proc_time, needs, required_resources):
        """
        :param activity_id: id of the activity (int)
        :param product_index: id of the product (int)
        :param proc_time: processing time of this activity (int)
        :param needs: needs of the task
        :return: generator
        """
        # Trace back the moment in time that the resources are requested
        request_time = self.env.now
        self.logger.info.to_csv('simulators/simulator8/logger_info.csv')
        self.logger.failure_code = (
                self._precedence_constraint_check(product_index, activity_id)
                or self._availability_constraint_check(needs, product_index, activity_id)
                or self._compatibility_constraint_check(product_index, activity_id))

        # If it is available start the request and processing
        if self.logger.failure_code is None:
            if self.printing:
                print(
                    f'At time {self.env.now}: product index {product_index} activity {activity_id} requests resources')

            # SimPy request
            for (resource_name, resource_id) in required_resources:
                resources = []
                resource = yield self.factory.get(lambda resource: resource.resource_group == resource_name and
                                                                   resource.id == resource_id)
                resources.append(resource)

            # Trace back the moment in time that the resources are retrieved
            retrieve_time = self.env.now

            if self.printing:
                print(
                    f'At time {self.env.now}: product index {product_index} activity {activity_id} retrieved resource {resources}')

            start_time = self.activity_start(activity_id, product_index, resources)

            # Generator for processing the activity
            yield self.env.timeout(proc_time)
            end_time = self.activity_end(activity_id, product_index)

            # Release the resources that were used during processing the activity
            # For releasing use the SimPy put function from the FilterStore object
            for resource in resources:
                yield self.factory.put(resource)

            if self.printing:
                print(
                    f'At time {self.env.now}: product index {product_index}  activity {activity_id} released resources: {resources}')

            self.logger.info.log(self.plan.products[product_index].id, activity_id, product_index, needs, resources,
                                 request_time, retrieve_time, start_time, end_time, self.pushback_mode)
            # print(self.plan.PRODUCTS[product_ID].ACTIVITIES[activity_ID].start_time)
            # print(self.resource_usage[(product_ID, activity_ID)])

        # If it is not available then we don't process this activity, so we avoid that there starts a queue in the
        # factory
        else:
            if self.printing:
                print(
                    f"At time {self.env.now}: we receive failure {self.logger.failure_code.name} for product index {product_index} activity {activity_id}, so it cannot start with ")
            self.activity_fail(product_index, activity_id)
            self.operator.signal_failed_activity(product_index=product_index, activity_id=activity_id,
                                                 current_time=self.env.now, logger=self.logger)

            yield self.env.timeout(0)



