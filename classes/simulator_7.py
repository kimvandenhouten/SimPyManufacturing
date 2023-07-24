import copy
import simpy
import random
import pandas as pd
from collections import namedtuple
import numpy as np


class Simulator:
    def __init__(self, plan, operator, printing=False):
        self.plan = plan
        self.resource_names = plan.FACTORY.RESOURCE_NAMES
        self.nr_resources = len(self.resource_names)
        self.capacity = plan.FACTORY.CAPACITY
        self.resources = []
        self.env = simpy.Environment()
        self.resource_usage = {}
        self.printing = printing
        self.nr_clashes = 0
        self.operator = operator

    def activity_processing(self, activity_ID, product_ID, proc_time, needs):
        """
        :param activity_ID: ID of the activity (int)
        :param product_ID: ID of the product (int)
        :param proc_time: processing time of this activity (int)
        :param resources_required: list with SimPy processes for resource requests (list)
        :param resources_names: list with the corresponding resource names (list)
        :return: generator
        """
        # Trace back the moment in time that the resources are requested
        request_time = self.env.now

        if self.printing:
            print(f'At time {self.env.now}: the available resources are {self.factory.items}')

        # Check all machines are available
        start_processing = True
        for r, need in enumerate(needs):
            if need > 0:
                resource_name = self.resource_names[r]
                available_machines = [i.resource_group for i in self.factory.items].count(resource_name)
                if self.printing:
                    print(f'At time {self.env.now}: we need {need} {resource_name} for product {product_ID}, activity {activity_ID} and currently '
                          f'in the factory we have {available_machines} available')
                if available_machines < need:
                    start_processing = False

        # If it is avaiglable start the request and processing
        if start_processing:
            self.signal_to_operator = False
            if self.printing:
                print(f'At time {self.env.now}: PRODUCT {product_ID} ACTIVITY {activity_ID} requested resources: {needs}')

            # SimPy request
            resources = []
            for r, need in enumerate(needs):
                if need > 0:
                    resource_name = self.resource_names[r]
                    for _ in range(0, need):
                        resource = yield self.factory.get(lambda resource: resource.resource_group == resource_name)
                        resources.append(resource)
            # Trace back the moment in time that the resources are retrieved
            retrieve_time = self.env.now

            if self.printing:
                print(f'At time {self.env.now}: PRODUCT {product_ID} ACTIVITY {activity_ID} retrieved resources: {needs}')

            # Trace back the moment in time that the activity starts processing
            start_time = self.env.now

            # Generator for processing the activity
            yield self.env.timeout(proc_time)

            # Trace back the moment in time that the activity ends processing
            end_time = self.env.now

            # Release the resources that were used during processing the activity
            # For releasing use the SimPy put function from the FilterStore object
            for resource in resources:
                yield self.factory.put(resource)

            if self.printing:
                print(f'At time {self.env.now}: PRODUCT {product_ID} ACTIVITY {activity_ID} released resources: {needs}')

            self.resource_usage[(product_ID, activity_ID)] = \
                                        {"Product": product_ID,
                                        "Activity": activity_ID,
                                        "Needs": needs,
                                        "Resources": resources,
                                        "Request": request_time,
                                        "Retrieve": retrieve_time,
                                        "Start": start_time,
                                        "Finish": end_time}

        # If it is not available then we don't process this activity, so we avoid that there starts a queue in the
        # factory
        else:
            if self.printing:
                print(f"At time {self.env.now}: there are no resources available for PRODUCT {product_ID} ACTIVITY {activity_ID}, so it cannot start")
            self.operator.signal_failed_activity(product_ID=product_ID, activity_ID=activity_ID,
                                                 current_time=self.env.now)
            self.nr_clashes += 1

    def activity_generator(self):
        """Generate activities that arrive at the factory based on earliest start times."""

        finish = False

        # Ask operator about next activity
        while not finish:
            send_activity, delay, activity_ID, product_ID, proc_time, needs, finish = \
                self.operator.send_next_activity(current_time=self.env.now)

            if send_activity:
                self.env.process(self.activity_processing(activity_ID, product_ID, proc_time, needs))

            # Generator object that does a time-out for a time period equal to delay value
            yield self.env.timeout(delay)

    def simulate(self, sim_time=1000, random_seed=1, write=False, output_location="Results.csv"):
        """
        :param SIM_TIME: time allowed for running the discrete-event simulation (int)
        :param RANDOM_SEED: random seed when used in stochastic mode (int)
        :param write: set to true if you want to write output to a csv file (boolean)
        :param output_location: give location for output file (str)
        :return:
        """
        if self.printing:
            print(f'START FACTORY SIMULATION FOR SEED {random_seed}\n')

        # Set random seed
        random.seed(random_seed)

        # Reset environment
        self.env = simpy.Environment()

        for act in self.plan.earliest_start:
            self.resource_usage[(act["Product_ID"], act["Activity_ID"])] = {"Product": act["Product_ID"],
                                        "Activity": act["Activity_ID"],
                                        "Needs": float("inf"),
                                        "Resources": "NOT PROCESSED DUE TO CLASH",
                                        "Request": float("inf"),
                                        "Retrieve": float("inf"),
                                        "Start": float("inf"),
                                        "Finish": float("inf")}

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

        # Process results
        resource_usage_df = []
        for i in self.resource_usage:
            resource_usage_df.append(self.resource_usage[i])

        self.resource_usage = pd.DataFrame(resource_usage_df)

        if self.printing:
            print(f' \nSIMULATION OUTPUT\n {self.resource_usage}')
        finish_times = self.resource_usage["Finish"].tolist()
        finish_times = [i for i in finish_times if i != float("inf")]
        makespan = max(finish_times)
        lateness = 0

        nr_unfinished_products = 0
        for p in self.plan.SEQUENCE:
            schedule = self.resource_usage[self.resource_usage["Product"] == p]
            finish = max(schedule["Finish"])
            if finish == float("inf"):
                nr_unfinished_products += 1
                if self.printing:
                    print(f'Product {p} did not finish, while the deadline was {self.plan.PRODUCTS[p].DEADLINE}.')

            else:
                lateness += max(0, finish - self.plan.PRODUCTS[p].DEADLINE)
                if self.printing:
                    print(f'Product {p} finished at time {finish}, while the deadline was {self.plan.PRODUCTS[p].DEADLINE}.')

        if self.printing:
            print(f"The makespan corresponding to this schedule is {makespan}")
            print(f"The lateness corresponding to this schedule is {lateness}")
            print(f"The number of unfinished products is {nr_unfinished_products}")

        if write:
            self.resource_usage.to_csv(output_location)

        return makespan, lateness, nr_unfinished_products

