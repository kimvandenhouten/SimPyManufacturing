import copy
import simpy
import random
import pandas as pd
import numpy as np


class Activity:
    def __init__(self, ID, PROCESSING_TIME, PRODUCT, PRODUCT_ID, NEEDS):
        self.ID = ID
        self.PRODUCT = PRODUCT
        self.PRODUCT_ID = PRODUCT_ID
        self.PROCESSING_TIME = PROCESSING_TIME
        self.NEEDS = NEEDS
        self.SEQUENCE_ID = int()


class Product:
    def __init__(self, ID, NAME):
        self.ID = ID
        self.NAME = NAME
        self.DEADLINE = int()
        self.ACTIVITIES = []
        self.TEMPORAL_RELATIONS = {}

    def add_activity(self, activity):
        """
        Add a product to the product
        :param product: Class Product
        """
        self.ACTIVITIES.append(activity)

    def set_temporal_relations(self, TEMPORAL_RELATIONS):
        self.TEMPORAL_RELATIONS = TEMPORAL_RELATIONS
        self.PREDECESSORS = [[] for _ in self.ACTIVITIES]
        self.SUCCESSORS = [[] for _ in self.ACTIVITIES]
        for (i, j) in self.TEMPORAL_RELATIONS.keys():
            self.PREDECESSORS[j].append(i)
            self.SUCCESSORS[i].append(j)


class Factory:
    def __init__(self, NAME, RESOURCE_NAMES, CAPACITY):
        self.NAME = NAME
        self.PRODUCTS = []
        self.RESOURCE_NAMES = RESOURCE_NAMES
        self.CAPACITY = CAPACITY

    def add_product(self, product):
        """
        Add a product to the production plan
        :param product: Class Product
        """
        self.PRODUCTS.append(product)


class ProductionPlan:
    def __init__(self, ID, SIZE, NAME, FACTORY, PRODUCT_IDS, DEADLINES):
        self.ID = ID
        self.SIZE = SIZE
        self.NAME = NAME
        self.FACTORY = FACTORY
        self.PRODUCT_IDS = PRODUCT_IDS
        self.DEADLINES = DEADLINES
        self.SEQUENCE = []
        self.PRODUCTS = []

    def list_products(self):
        """
        Add a product to the production plan
        :param product: Class Product
        """
        self.PRODUCTS = []
        for i in range(0, len(self.PRODUCT_IDS)):
            product = copy.copy(self.FACTORY.PRODUCTS[self.PRODUCT_IDS[i]])
            product.DEADLINE = self.DEADLINES[i]
            self.PRODUCTS.append(product)
        self.SIZE = len(self.PRODUCT_IDS)

    def set_sequence(self, sequence):
        """
        Give the sequence in which the products will be processed
        :param sequence: list of integers
        """
        self.SEQUENCE = sequence

    def convert_to_dataframe(self):
        df = pd.DataFrame()
        df["Product_ID"] = self.PRODUCT_IDS
        df["Deadlines"] = self.DEADLINES
        return df


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

    def product(self, p, priority):

        # FIRST DO THE REQUESTING
        activities = self.plan.PRODUCTS[p].ACTIVITIES
        durations = []
        resources_required = {}
        resources_names = {}
        for i in range(0, len(activities)):
            activity = activities[i]
            needs = activity.NEEDS
            duration = random.randint(*activity.PROCESSING_TIME)
            durations.append(duration)
            resources_required_act = []
            resources_names_act = []
            for r in range(0, self.NR_RESOURCES):
                need = needs[r]
                if need > 0:
                    for _ in range(0, need):
                        resource = self.RESOURCES[r]
                        resource_name = self.RESOURCE_NAMES[r]
                        resources_required_act.append(resource.request(priority=priority))
                        resources_names_act.append(resource_name)
            resources_required[i] = resources_required_act
            resources_names[i] = resources_names_act
        request_time = self.env.now
        if self.printing:
            print(f'Product {p} requested resources: {resources_names} at time: {request_time}')
        for i in range(0, len(activities)):
            yield self.env.all_of(resources_required[i])
            start_time = self.env.now
            if self.printing:
                print(f'Product {p}, activity {i}, retrieved resources: {resources_names[i]} at time: {start_time}')


        # NOW START WITH THE ACTUAL PROCESSING
        yield self.env.timeout(durations[0])
        for i in range(0, len(activities)):
            if i == 0:
                # First activity finishes after duration of first activity
                yield self.env.timeout(0)
                end_time = self.env.now
            else:
                if i == 1:
                    temp_rel = self.plan.PRODUCTS[p].TEMPORAL_RELATIONS[(0, i)]
                else:
                    temp_rel = self.plan.PRODUCTS[p].TEMPORAL_RELATIONS[(0, i)] - self.plan.PRODUCTS[p].TEMPORAL_RELATIONS[(0, i-1)]
                yield self.env.timeout(temp_rel)
                end_time = self.env.now

            for j in range(0, len(resources_required[i])):

                r = resources_required[i][j]
                r.resource.release(r)
                resource_name = resources_names[i][j]
                if self.printing:
                    print(f'Product {p} released resources: {resource_name} at time: {end_time}')

                self.resource_usage.append({"Activity": i,
                                            "Product": p,
                                            "Resource": resource_name,
                                            "Request moment": request_time,
                                            "Retrieve moment": start_time,
                                            "Start": end_time - durations[i],
                                            "Finish": end_time})

    def product_generator(self):
        """Generate activities that arrive at the factory. For certain activities there are temporal relations,
        this means that there are fixed time intervals between the request times for the two activities."""
        if self.printing:
            print(f"The products are processed according to the production sequence {self.plan.SEQUENCE}.")
        # Schedule activities with priority ordering
        priority = 0
        for p in self.plan.SEQUENCE:

            self.env.process(self.product(p, priority=priority))
            priority += 1
            yield self.env.timeout(3)

    def simulate(self, SIM_TIME, RANDOM_SEED, write=False, output_location="Results.csv"):
        if self.printing:
            print(f'START Factory simulation for seed {RANDOM_SEED}')
        random.seed(RANDOM_SEED)
        # Reset environment
        self.env = simpy.Environment()
        self.resource_usage = []
        self.RESOURCES = []
        for r in range(0, self.NR_RESOURCES):
            self.RESOURCES.append(simpy.PriorityResource(self.env, self.CAPACITY[r]))

        self.env.process(self.product_generator())

        # Execute!
        self.env.run(until=SIM_TIME)

        # Process results
        self.resource_usage = pd.DataFrame(self.resource_usage)
        makespan = max(self.resource_usage["Finish"])
        tardiness = 0

        for p in self.plan.SEQUENCE:
            schedule = self.resource_usage[self.resource_usage["Product"] == p]
            finish = max(schedule["Finish"])
            if self.printing:
                print(f'Product {p} finished at time {finish}, while the deadline was {self.plan.PRODUCTS[p].DEADLINE}.')
            tardiness += max(0, finish - self.plan.PRODUCTS[p].DEADLINE)

        if self.printing:
            print(f"The makespan corresponding to this schedule is {makespan}")
            print(f"The tardiness corresponding to this schedule is {tardiness}")
        if write:
            self.resource_usage.to_csv(output_location)

        return makespan, tardiness

