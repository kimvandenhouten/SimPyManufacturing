import copy


import simpy
import random
import pandas as pd
from collections import namedtuple
import numpy as np

from classes.classes import SimulatorLogger, Action


class Simulator:
    def __init__(self, plan, printing=False):
        self.plan = plan
        self.resource_names = plan.factory.resource_names
        self.nr_resources = len(self.resource_names)
        self.capacity = plan.factory.capacity
        self.resources = []
        self.env = simpy.Environment()
        self.resource_usage = []
        self.printing = printing
        self.nr_clashes = 0
        self.logger = SimulatorLogger(self.__class__.__name__)

    def activity_processing(self, activity_id, product_id, proc_time, needs):
        """
        :param activity_id: id of the activity (int)
        :param product_id: id of the product (int)
        :param proc_time: processing time of this activity (int)
        :param resources_required: list with SimPy processes for resource requests (list)
        :param resources_names: list with the corresponding resource names (list)
        :return: generator
        """
        # Trace back the moment in time that the resources are requested
        request_time = self.env.now

        if self.printing:
            print(f'At time {self.env.now} we have available {self.factory.items}')

        # Check all machines are available
        start_processing = True
        for r, need in enumerate(needs):
            if need > 0:
                resource_names = self.resource_names[r]
                available_machines = [i.resource_group for i in self.factory.items].count(resource_names)
                if self.printing:
                    print(
                        f'We need {need} {resource_names} for product {product_id}, activity {activity_id} and currently '
                        f'in the factory we have {available_machines} available')
                if available_machines < need:
                    start_processing = False

        # TODO: check if there is a compatibility check
        # If there is a clash, set start_processing to False
        for constraint in self.plan.products[product_id].activities[activity_id].constraints:
            if (constraint.product_id, constraint.activity_id) in self.logger.active_processes:
                start_processing = False
                print(f'Activity {activity_id} of product {product_id} has incompatibility with activity {constraint.activity_id} of product {constraint.product_id} which is currently active')
                break

        # If it is available start the request and processing
        if start_processing:
            if self.printing:
                print(
                    f'\nProduct {product_id}, activity {activity_id} requested resources: {needs} at time: {request_time} \n')

            # SimPy request
            resources = []
            for r, need in enumerate(needs):
                if need > 0:
                    resource_names = self.resource_names[r]
                    for _ in range(0, need):
                        resource = yield self.factory.get(lambda resource: resource.resource_group == resource_names)
                        resources.append(resource)
            # Trace back the moment in time that the resources are retrieved
            retrieve_time = self.env.now

            if self.printing:
                print(
                    f'Product {product_id}, activity {activity_id} retrieved resources: {needs} at time: {retrieve_time} \n')

            # Trace back the moment in time that the activity starts processing
            start_time = self.env.now

            # TODO:
            self.logger.log_activity(product_id, activity_id, Action.START,start_time)

            # Generator for processing the activity
            yield self.env.timeout(proc_time)

            # Trace back the moment in time that the activity ends processing
            end_time = self.env.now

            # TODO:
            self.logger.log_activity(product_id, activity_id, Action.END,end_time)

            # Release the resources that were used during processing the activity
            # For releasing use the SimPy put function from the FilterStore object
            for resource in resources:
                yield self.factory.put(resource)

            if self.printing:
                print(
                    f'Product {product_id}, activity {activity_id} released resources: {needs} at time: {end_time} \n')

            # Store relevant information
            self.resource_usage.append({"Product": product_id,
                                        "Activity": activity_id,
                                        "Needs": needs,
                                        "resources": resources,
                                        "Request": request_time,
                                        "Retrieve": retrieve_time,
                                        "Start": start_time,
                                        "Finish": end_time})

        # If it is not available then we don't process this activity, so we avoid that there starts a queue in the
        # factory
        else:
            print(
                f"Since there are no resources available, product {product_id} ACTIVITY {activity_id} will not be processed")
            self.nr_clashes += 1
            self.resource_usage.append({"Product": product_id,
                                        "Activity": activity_id,
                                        "Needs": needs,
                                        "resources": "NOT PROCESSED",
                                        "Request": float("inf"),
                                        "Retrieve": float("inf"),
                                        "Start": float("inf"),
                                        "Finish": float("inf")})

    def activity_generator(self):
        """Generate activities that arrive at the factory based on earliest start times."""

        # Sort activities by earliest start time
        earliest_start_times = []
        for i, dict in enumerate(self.plan.earliest_start):
            earliest_start_times.append(dict["earliest_start"])
        earliest_start_times_argsort = np.argsort(earliest_start_times)

        # Iterate through the different activities
        for id, i in enumerate(earliest_start_times_argsort):
            product_id = self.plan.earliest_start[i]["product_id"]
            activity_id = self.plan.earliest_start[i]["activity_id"]

            # Obtain information about resource needs and processing time
            needs = self.plan.products[product_id].activities[activity_id].needs
            proc_time = self.plan.products[product_id].activities[activity_id].processing_time[0]

            # If this is the first activity in the sorted start times list, we have no delay
            if id == 0:
                delay = self.plan.earliest_start[i]["earliest_start"]

            # Else we should set the delay equal to the difference between the start time of this
            # activity and the activity before
            else:
                delay = self.plan.earliest_start[i]["earliest_start"] - \
                        self.plan.earliest_start[earliest_start_times_argsort[id - 1]]["earliest_start"]

            # Generator object that does a time-out for a time period equal to delay value
            yield self.env.timeout(delay)

            # Now the activity SimPy process can be started
            self.env.process(self.activity_processing(activity_id, product_id, proc_time, needs))

    def simulate(self, SIM_TIME, random_seed, write=False, output_location="Results.csv"):
        """
        :param SIM_TIME: time allowed for running the discrete-event simulation (int)
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

        # Create a list to store information about resource usage (gannt information)
        self.resource_usage = []

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
        self.env.run(until=SIM_TIME)

        # Process results
        self.resource_usage = pd.DataFrame(self.resource_usage)
        print(self.resource_usage)
        finish_times = self.resource_usage["Finish"].tolist()
        finish_times = [i for i in finish_times if i != float("inf")]
        makespan = max(finish_times)
        lateness = 0

        nr_unfinished_products = 0
        for p in self.plan.sequence:
            schedule = self.resource_usage[self.resource_usage["Product"] == p]
            finish = max(schedule["Finish"])
            if finish == float("inf"):
                if self.printing:
                    print(f'Product {p} did not finish, while the deadline was {self.plan.products[p].deadline}.')
                nr_unfinished_products += 1
            else:
                if self.printing:
                    print(
                        f'Product {p} finished at time {finish}, while the deadline was {self.plan.products[p].deadline}.')
                lateness += max(0, finish - self.plan.products[p].deadline)

        if self.printing:
            print(f"The makespan corresponding to this schedule is {makespan}")
            print(f"The lateness corresponding to this schedule is {lateness}")
            print(f"The number of unfinished products is {nr_unfinished_products}")

        if write:
            self.resource_usage.to_csv(output_location)

        return makespan, lateness, nr_unfinished_products
