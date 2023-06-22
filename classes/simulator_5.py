import copy
import simpy
import random
import pandas as pd
from collections import namedtuple
import numpy as np


class Simulator:
    def __init__(self, plan, printing=False):
        self.plan = plan
        self.RESOURCE_NAMES = plan.FACTORY.RESOURCE_NAMES
        self.NR_RESOURCES = len(self.RESOURCE_NAMES)
        self.CAPACITY = plan.FACTORY.CAPACITY
        self.RESOURCES = []
        self.env = simpy.Environment()
        self.resource_usage = []
        self.printing = printing

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

        # Check if the required machine is available at this moment in time
        available_machines = [i.resource_group for i in self.factory.items].count(needs)
        print(f'At time {self.env.now} we have available {self.factory.items}')
        print(f'We need {needs}, and currently in the factory we have {available_machines} available\n')

        # If it is available start the request and processing
        if available_machines > 0:
            if self.printing:
                print(f'Product {product_ID}, activity {activity_ID} requested resources: {needs} at time: {request_time} \n')

            # SimPy request
            resource = yield self.factory.get(lambda resource: resource.resource_group == needs)

            # Trace back the moment in time that the resources are retrieved
            retrieve_time = self.env.now

            if self.printing:
                print(f'Product {product_ID}, activity {activity_ID} retrieved resources: {needs} at time: {retrieve_time} \n')

            # Trace back the moment in time that the activity starts processing
            start_time = self.env.now

            # Generator for processing the activity
            yield self.env.timeout(proc_time)

            # Trace back the moment in time that the activity ends processing
            end_time = self.env.now

            # Release the resources that were used during processing the activity
            # For releasing use the SimPy put function from the FilterStore object
            yield self.factory.put(resource)

            print(f'Product {product_ID}, activity {activity_ID} released resources: {needs} at time: {end_time} \n')

            # Store relevant information
            self.resource_usage.append({"Product": product_ID,
                                        "Activity": activity_ID,
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
            print(f"Since there are no resources available, ACTIVITY {activity_ID} will not be processed")
            self.resource_usage.append({"Product": product_ID,
                                        "Activity": activity_ID,
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
            earliest_start_times.append(dict["Earliest_start"])
        earliest_start_times_argsort = np.argsort(earliest_start_times)

        # Iterate through the different activities
        for id, i in enumerate(earliest_start_times_argsort):
            product_ID = self.plan.earliest_start[i]["Product_ID"]
            activity_ID = self.plan.earliest_start[i]["Activity_ID"]

            # Obtain information about resource needs and processing time
            needs = self.plan.PRODUCTS[product_ID].ACTIVITIES[activity_ID].NEEDS
            proc_time = self.plan.PRODUCTS[product_ID].ACTIVITIES[activity_ID].PROCESSING_TIME
            proc_time = random.randint(*proc_time)

            # If this is the first activity in the sorted start times list, we have no delay
            if id == 0:
                delay = self.plan.earliest_start[i]["Earliest_start"]

            # Else we should set the delay equal to the difference between the start time of this
            # activity and the activity before
            else:
                delay = self.plan.earliest_start[i]["Earliest_start"] - \
                        self.plan.earliest_start[earliest_start_times_argsort[id - 1]]["Earliest_start"]

            # Generator object that does a time-out for a time period equal to delay value
            yield self.env.timeout(delay)

            # Now the activity SimPy process can be started
            self.env.process(self.activity_processing(activity_ID, product_ID, proc_time, needs))

    def simulate(self, SIM_TIME, RANDOM_SEED, write=False, output_location="Results.csv"):
        """
        :param SIM_TIME: time allowed for running the discrete-event simulation (int)
        :param RANDOM_SEED: random seed when used in stochastic mode (int)
        :param write: set to true if you want to write output to a csv file (boolean)
        :param output_location: give location for output file (str)
        :return:
        """

        if self.printing:
            print(f'START FACTORY SIMULATION FOR SEED {RANDOM_SEED}')

        # Set random seed
        random.seed(RANDOM_SEED)

        # Reset environment
        self.env = simpy.Environment()

        # Create a list to store information about resource usage (gannt information)
        self.resource_usage = []

        # Create the factory that is a SimPy FilterStore object
        self.factory = simpy.FilterStore(self.env, capacity=sum(self.CAPACITY))

        # Create the resources that are present in the SimPy FilterStore
        Resource = namedtuple('Machine', 'resource_group, id')
        items = []
        for r in range(0, self.NR_RESOURCES):
            for j in range(0, self.CAPACITY[r]):
                resource = Resource(self.RESOURCE_NAMES[r], j)
                items.append(copy.copy(resource))
        self.factory.items = items

        # Execute the activity_generator
        self.env.process(self.activity_generator())
        self.env.run(until=SIM_TIME)

        # Process results
        self.resource_usage = pd.DataFrame(self.resource_usage)
        print(self.resource_usage)
        makespan = max(self.resource_usage["Finish"])
        lateness = 0

        for p in self.plan.SEQUENCE:
            schedule = self.resource_usage[self.resource_usage["Product"] == p]
            finish = max(schedule["Finish"])
            if self.printing:
                print(f'Product {p} finished at time {finish}, while the deadline was {self.plan.PRODUCTS[p].DEADLINE}.')
            lateness += max(0, finish - self.plan.PRODUCTS[p].DEADLINE)

        if self.printing:
            print(f"The makespan corresponding to this schedule is {makespan}")
            print(f"The lateness corresponding to this schedule is {lateness}")

        if write:
            self.resource_usage.to_csv(output_location)

        return makespan, lateness

