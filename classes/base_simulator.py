import copy
from collections import namedtuple

import simpy
import random

from classes.classes import SimulatorLogger, Action, FailureCode


class BaseSimulator:
    """This is a base class for versions 7 and 8 of the simulator. It implements everything except for the method
    activity_generator, which must be overridden by the subclasses."""

    def __init__(self, plan, operator, check_max_time_lag, printing=False):
        self.plan = plan
        self.resource_names = plan.factory.resource_names
        self.nr_resources = len(self.resource_names)
        self.capacity = plan.factory.capacity
        self.resources = []
        self.env = simpy.Environment()
        self.printing = printing
        self.nr_clashes = 0
        self.operator = operator
        self.logger = SimulatorLogger(self.__class__.__name__)
        self.pushback_mode = False
        self.check_max_time_lag = check_max_time_lag

    def _availability_constraint_check(self, needs, product_index, activity_id):
        # Check if all resources are available
        failure_code = None
        for r, need in enumerate(needs):
            if need > 0:
                resource_names = self.resource_names[r]
                available_machines = [i.resource_group for i in self.factory.items].count(resource_names)
                if self.printing:
                    print(
                        f'At time {self.env.now}: we need {need} {resource_names} for product index {product_index} activity {activity_id} and currently '
                        f'in the factory we have {available_machines} available')
                if available_machines < need:
                    failure_code = FailureCode.AVAILABILITY
        return failure_code

    def _precedence_constraint_check(self, product_index, activity_id):
        predecessors = self.plan.products[product_index].predecessors[activity_id]
        for pred_activity_id in predecessors:
            temp_rel = self.plan.products[product_index].temporal_relations[(pred_activity_id, activity_id)]
            min_lag = temp_rel.min_lag
            start_pred_log = self.logger.fetch_latest_entry(product_index,
                                                            pred_activity_id, Action.START)

            is_parallel_successor = start_pred_log is None and min_lag == 0

            if start_pred_log is None and min_lag != 0:
                if self.printing:
                    print(
                        f'At time {self.env.now}: product {product_index}, activity {activity_id} cannot start because '
                        f' predecessors {product_index}, {pred_activity_id} did not start yet')

                return FailureCode.PRECEDENCE
            else:
                if is_parallel_successor:
                    pass
                elif temp_rel.min_lag and self.env.now - start_pred_log.timestamp < min_lag:
                    if self.printing:
                        print(
                            f'At time {self.env.now}: product index {product_index} activity {activity_id} cannot start because '
                            f' minimal time lag with {product_index}, {pred_activity_id} is not satisfied')

                    return FailureCode.MIN_LAG

                elif self.check_max_time_lag and temp_rel.max_lag and self.env.now - start_pred_log.timestamp > temp_rel.max_lag:
                    if self.printing:
                        print(
                            f'At time {self.env.now}: product index {product_index} activity {activity_id} cannot start because '
                            f' maximal time lag with {product_index}, {pred_activity_id} is not satisfied')

                    return FailureCode.MAX_LAG

    def _compatibility_constraint_check(self, product_index, activity_id):
        for constraint in self.plan.products[product_index].activities[activity_id].constraints:
            if (constraint.product_id, constraint.activity_id) in self.logger.active_processes:
                if self.printing:
                    print(
                        f'At time {self.env.now}: activity {activity_id} of product {self.plan.products[product_index].id} has incompatibility with activity {constraint.activity_id} of product {constraint.product_id} which is currently active')
                return FailureCode.COMPATIBILITY

        return None

    def activity_processing(self, activity_id, product_index, proc_time, needs):
        """
        :param activity_id: id of the activity (int)
        :param product_index: id of the product (int)
        :param proc_time: processing time of this activity (int)
        :param needs: needs of the task
        :return: generator
        """
        # Trace back the moment in time that the resources are requested
        request_time = self.env.now

        self.logger.failure_code = (
                self._precedence_constraint_check(product_index, activity_id)
                or self._availability_constraint_check(needs, product_index, activity_id)
                or self._compatibility_constraint_check(product_index, activity_id))

        # If it is available start the request and processing
        if self.logger.failure_code is None:
            if self.printing:
                print(
                    f'At time {self.env.now}: product index {product_index} activity {activity_id} requested resources: {needs}')

            # SimPy request
            resources = []
            assert len(needs) == len(self.resource_names)
            for need, resource_name in zip(needs, self.resource_names):
                if need > 0:
                    for _ in range(0, need):
                        resource = yield self.factory.get(lambda resource: resource.resource_group == resource_name)
                        resources.append(resource)
            # Trace back the moment in time that the resources are retrieved
            retrieve_time = self.env.now

            if self.printing:
                print(
                    f'At time {self.env.now}: product index {product_index} activity {activity_id} retrieved resources: {needs}')

            start_time = self.activity_start(activity_id, product_index)

            # Generator for processing the activity
            yield self.env.timeout(proc_time)

            end_time = self.activity_end(activity_id, product_index)

            # Release the resources that were used during processing the activity
            # For releasing use the SimPy put function from the FilterStore object
            for resource in resources:
                yield self.factory.put(resource)

            if self.printing:
                print(
                    f'At time {self.env.now}: product index {product_index}  activity {activity_id} released resources: {needs}')

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

    def activity_generator(self):
        raise NotImplementedError()

    def simulate(self, sim_time=1000, random_seed=1, write=False, output_location="Results.csv"):
        """
        :param sim_time: time allowed for running the discrete-event simulation (int)
        :param random_seed: random seed when used in stochastic mode (int)
        :param write: set to true if you want to write output to a csv file (boolean)
        :param output_location: give location for output file (str)
        :return:
        """
        if self.printing:
            print(f'START factory SIMULATION FOR seed {random_seed}\n')

        # Set random seed
        random.seed(random_seed)

        # Reset environment
        self.env = simpy.Environment()

        # Create the factory that is a SimPy FilterStore object
        self.factory = simpy.FilterStore(self.env, capacity=sum(self.capacity))

        # Create the resources that are present in the SimPy FilterStore
        Resource = namedtuple('Machine', 'resource_group, id')
        items = []
        for r in range(0, self.nr_resources):
            for j in range(0, self.capacity[r]):
                resource = Resource(self.resource_names[r], j)
                items.append(copy.copy(resource))
        self.factory.items = items

        # Execute the activity_generator
        self.env.process(self.activity_generator())
        self.env.run(until=sim_time)

        if self.printing:
            print(f' \nSIMULATION OUTPUT\n ')
            self.logger.info.print()

        num_pushback = 0

        for act in self.plan.earliest_start:
            entry = self.logger.info.fetch_latest_entry(self.plan.products[act["product_index"]].id, act["activity_id"],
                                                        act["product_index"])
            if entry is None:
                self.logger.info.log(self.plan.products[act["product_index"]].id, act["activity_id"],
                                     act["product_index"],
                                     float("inf"), "NOT PROCESSED DUE TO CLASH",
                                     float("inf"), float("inf"), float("inf"), float("inf"), pushback=False)
            elif entry.pushback:
                num_pushback += 1

        finish_times = [entry.end_time for entry in self.logger.info.entries if entry.end_time != float("inf")]
        makespan = max(finish_times)
        lateness = 0

        nr_unfinished_products = 0
        for p in range(len(self.plan.products)):
            schedule = list(filter(lambda entry: entry.product_idx == p, self.logger.info.entries))
            finish = max([entry.end_time for entry in schedule])
            if finish == float("inf"):
                nr_unfinished_products += 1
                if self.printing:
                    print(f'Product {p} did not finish, while the deadline was {self.plan.products[p].deadline}.')

            else:
                lateness += max(0, finish - self.plan.products[p].deadline)
                if self.printing:
                    print(
                        f'Product {p} finished at time {finish}, while the deadline was {self.plan.products[p].deadline}.')

        if self.printing:
            print(f"The makespan corresponding to this schedule is {makespan}")
            print(f"The lateness corresponding to this schedule is {lateness}")
            print(f"The number of unfinished products is {nr_unfinished_products}")
            print(f"Number of activities processed during push back mode are {num_pushback}")
            print(f"Number of activities that failed during push back mode are {len(self.operator.pushback)}")

        if write:
            self.logger.info.to_csv(output_location)

        return makespan, lateness, nr_unfinished_products

    def activity_start(self, activity_id, product_index):
        # Trace back the moment in time that the activity starts processing
        start_time = self.env.now
        self.logger.log_activity(self.plan.products[product_index].id,
                                 activity_id, product_index, Action.START, start_time)
        return start_time

    def activity_end(self, activity_id, product_index):
        # Trace back the moment in time that the activity ends processing
        end_time = self.env.now
        self.logger.log_activity(self.plan.products[product_index].id,
                                 activity_id, product_index, Action.END, end_time)
        return end_time
