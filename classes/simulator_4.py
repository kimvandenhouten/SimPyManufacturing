import copy
import simpy
import random
import pandas as pd
from collections import namedtuple
import numpy as np


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

    def resource_request(self, resource_group):
        """
        :param resource_group: name of the resource group (str)
        :return: generator object

        This is a process for requesting a SimPy FilterStore object from the group "resource_group"
        """
        resource = yield self.factory.get(lambda resource: resource.resource_group == resource_group)
        return resource

    def activity_processing(self, activity_id, product_id, proc_time, resources_required, resources_names):
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

        # Use SimPy all_of to ensure that all the resource needed are obtained at the same time
        # before the actual processing of the activity can start
        yield self.env.all_of(resources_required)

        # Trace back the moment in time that the resources are retrieved
        retrieve_time = self.env.now

        if self.printing:
            print(f'Product {product_id}, activity {activity_id} requested resources: {resources_names} at time: {request_time}')
            print(f'Product {product_id}, activity {activity_id} retrieved resources: {resources_names} at time: {retrieve_time}')

        # Trace back the moment in time that the activity starts processing
        start_time = self.env.now

        # Generator for processing the activity
        yield self.env.timeout(proc_time)

        # Trace back the moment in time that the activity ends processing
        end_time = self.env.now

        # Release the resources that were used during processing the activity
        for j, r in enumerate(resources_required):
            r_process = r.value

            # For releasing use the SimPy put function from the FilterStore object
            yield self.factory.put(r_process)
            resource_names = resources_names[j]
            if self.printing:
                print(f'Product {product_id}, activity {activity_id} released resources: {resource_names} at time: {end_time}')

            # Store relevant information
            self.resource_usage.append({"Product": product_id,
                                        "Activity": activity_id,
                                        "Resource": resource_names,
                                        "Check_resource_type": r_process.resource_group,
                                        "Machine_id": r_process.id,
                                        "Request moment": request_time,
                                        "Retrieve moment": retrieve_time,
                                        "Start": start_time,
                                        "Finish": end_time})

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
            proc_time = self.plan.products[product_id].activities[activity_id].processing_time
            proc_time = random.randint(*proc_time)

            # Combine the different resources needed for this activity in resources_required
            # and resource_names to store the requests processes for SimPy FilterStore objects
            resources_required, resources_names = [], []
            for r, need in enumerate(needs):
                if need > 0:
                    for _ in range(0, need):
                        resource_names = self.resource_names[r]
                        resources_required.append(
                            self.env.process(self.resource_request(resource_group=resource_names)))
                        resources_names.append(resource_names)
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
            self.env.process(self.activity_processing(activity_id, product_id, proc_time, resources_required,
                                                      resources_names))

    def simulate(self, SIM_TIME, random_seed, write=False, output_location="Results.csv"):
        """
        :param SIM_TIME: time allowed for running the discrete-event simulation (int)
        :param random_seed: random seed when used in stochastic mode (int)
        :param write: set to true if you want to write output to a csv file (boolean)
        :param output_location: give location for output file (str)
        :return:
        """

        if self.printing:
            print(f'START factory simulation for seed {random_seed}')

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
        makespan = max(self.resource_usage["Finish"])
        lateness = 0

        for p in self.plan.sequence:
            schedule = self.resource_usage[self.resource_usage["Product"] == p]
            finish = max(schedule["Finish"])
            if self.printing:
                print(f'Product {p} finished at time {finish}, while the deadline was {self.plan.products[p].deadline}.')
            lateness += max(0, finish - self.plan.products[p].deadline)

        if self.printing:
            print(f"The makespan corresponding to this schedule is {makespan}")
            print(f"The lateness corresponding to this schedule is {lateness}")

        if write:
            self.resource_usage.to_csv(output_location)

        return makespan, lateness

