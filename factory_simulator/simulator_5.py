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

        # Check if the required machine is available at this moment in time
        available_machines = [i.resource_group for i in self.factory.items].count(needs)
        print(f'At time {self.env.now} we have available {self.factory.items}')
        print(f'We need {needs}, and currently in the factory we have {available_machines} available\n')

        # If it is available start the request and processing
        if available_machines > 0:
            if self.printing:
                print(f'Product {product_id}, activity {activity_id} requested resources: {needs} at time: {request_time} \n')

            # SimPy request
            resource = yield self.factory.get(lambda resource: resource.resource_group == needs)

            # Trace back the moment in time that the resources are retrieved
            retrieve_time = self.env.now

            if self.printing:
                print(f'Product {product_id}, activity {activity_id} retrieved resources: {needs} at time: {retrieve_time} \n')

            # Trace back the moment in time that the activity starts processing
            start_time = self.env.now

            # Generator for processing the activity
            yield self.env.timeout(proc_time)

            # Trace back the moment in time that the activity ends processing
            end_time = self.env.now

            # Release the resources that were used during processing the activity
            # For releasing use the SimPy put function from the FilterStore object
            yield self.factory.put(resource)

            print(f'Product {product_id}, activity {activity_id} released resources: {needs} at time: {end_time} \n')

            # Store relevant information
            self.resource_usage.append({"ProductIndex": product_id,
                                        "Activity": activity_id,
                                        "Resource": needs,
                                        "Check_resource_type": resource.resource_group,
                                        "Machine_id": resource.id,
                                        "Request moment": request_time,
                                        "Retrieve moment": retrieve_time,
                                        "Start": start_time,
                                        "Finish": end_time})

        # If it is not available then we don't process this activity, so we avoid that there starts a queue in the
        # factory
        else:
            print(f"Since there are no resources available, ACTIVITY {activity_id} will not be processed")
            self.resource_usage.append({"ProductIndex": product_id,
                                        "Activity": activity_id,
                                        "Resource": needs,
                                        "Check_resource_type": "NOT PROCESSED",
                                        "Machine_id": "NOT PROCESSED",
                                        "Request moment": float("inf"),
                                        "Retrieve moment": float("inf"),
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
            product_id = self.plan.earliest_start[i]["product_index"]
            activity_id = self.plan.earliest_start[i]["activity_id"]

            # Obtain information about resource needs and processing time
            needs = self.plan.products[product_id].activities[activity_id].needs
            proc_time = self.plan.products[product_id].activities[activity_id].processing_time
            proc_time = random.randint(*proc_time)

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

    def simulate(self, sim_time, random_seed, write=False, output_location="Results.csv"):
        """
        :param sim_time: time allowed for running the discrete-event simulation (int)
        :param random_seed: random seed when used in stochastic mode (int)
        :param write: set to true if you want to write output to a csv file (boolean)
        :param output_location: give location for output file (str)
        :return:
        """

        if self.printing:
            print(f'START factory SIMULATION FOR seed {random_seed}')

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
        self.env.run(until=sim_time)

        # Process results
        self.resource_usage = pd.DataFrame(self.resource_usage)
        print(self.resource_usage)
        makespan = max(self.resource_usage["Finish"])
        lateness = 0

        for p in self.plan.sequence:
            schedule = self.resource_usage[self.resource_usage["ProductIndex"] == p]
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

