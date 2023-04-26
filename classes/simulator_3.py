import copy
import simpy
import random
import pandas as pd
from collections import namedtuple


class Simulator:
    def __init__(self, plan, delay=3, printing=False):
        self.plan = plan
        self.RESOURCE_NAMES = plan.FACTORY.RESOURCE_NAMES
        self.NR_RESOURCES = len(self.RESOURCE_NAMES)
        self.CAPACITY = plan.FACTORY.CAPACITY
        self.RESOURCES = []
        self.delay_between_products = delay
        self.env = simpy.Environment()
        self.resource_usage = []
        self.printing = printing

    def resource_request(self, product, resource_group):
        resource = yield self.factory.get(lambda resource: resource.resource_group == resource_group)
        if self.printing:
            print(product, 'requested', resource.resource_group, ' id ', resource.id, 'at', self.env.now)
        return resource

    def product(self, p, priority):

        # FIRST DO THE REQUESTING
        activities = self.plan.PRODUCTS[p].ACTIVITIES
        durations = []
        resources_required = {}
        resources_names = {}
        for i in range(0, 1):
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
                        resource_name = self.RESOURCE_NAMES[r]
                        resources_required_act.append(self.env.process(self.resource_request(product=p, resource_group=resource_name)))
                        resources_names_act.append(resource_name)
            resources_required[i] = resources_required_act
            resources_names[i] = resources_names_act

        request_time = self.env.now
        yield self.env.all_of(resources_required[i])
        self.env.process(self.activity_processing(i=i, p=p, delay=0,
                                                  duration=durations[i],
                                                  resources_required=resources_required[i],
                                                  resources_names=resources_names[i], request_time=request_time ))

        for i in range(1, len(activities)):
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
                        resource_name = self.RESOURCE_NAMES[r]
                        resources_required_act.append(self.env.process(self.resource_request(product=p, resource_group=resource_name)))
                        resources_names_act.append(resource_name)
            resources_required[i] = resources_required_act
            resources_names[i] = resources_names_act

        for i in range(1, len(activities)):
            delay_factor = self.plan.PRODUCTS[p].TEMPORAL_RELATIONS[(0, i)]
            yield self.env.timeout(0)

            self.env.process(self.activity_processing(i=i, p=p, delay=delay_factor, duration=durations[i],
                                                      resources_required=resources_required[i], resources_names=resources_names[i], request_time=request_time
                                                      ))

    def activity_processing(self, i, p, delay, duration, resources_required, resources_names, request_time):
        if i > 0:
            yield self.env.timeout(delay)
            request_time = self.env.now
            yield self.env.all_of(resources_required)
        else:
            yield self.env.timeout(0)

        retrieve_time = self.env.now

        if self.printing:
            print(f'Product {p}, activity {i}, retrieved resources: {resources_names} at time: {retrieve_time}')

        start_time = self.env.now
        # NOW START WITH THE ACTUAL PROCESSING
        yield self.env.timeout(duration)
        end_time = self.env.now

        # NOW RELEASE ALL RESOURCES THAT WERE NEEDED
        for j in range(0, len(resources_required)):
            r = resources_required[j].value
            yield self.factory.put(r)
            resource_name = resources_names[j]
            if self.printing:
                print(f'Product {p} released resources: {resource_name} at time: {end_time}')

            self.resource_usage.append({"Activity": i,
                                        "Product": p,
                                        "Resource": resource_name,
                                        "Check_resource_type": r.resource_group,
                                        "Machine_id": r.id,
                                        "Request moment": request_time,
                                        "Retrieve moment": retrieve_time,
                                        "Start": start_time,
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
            yield self.env.timeout(self.delay_between_products)

    def simulate(self, SIM_TIME, RANDOM_SEED, write=False, output_location="Results.csv"):

        self.plan.SEQUENCE = [int(i) for i in self.plan.SEQUENCE]
        if self.printing:
            print(f'START Factory simulation for seed {RANDOM_SEED}')
        random.seed(RANDOM_SEED)
        # Reset environment
        self.env = simpy.Environment()
        self.resource_usage = []

        # TO DO: REPLACE WITH FACTORY STORE TYPE
        self.factory = simpy.FilterStore(self.env, capacity=sum(self.CAPACITY))
        Resource = namedtuple('Machine', 'resource_group, id')
        items = []
        for r in range(0, self.NR_RESOURCES):
            for j in range(0, self.CAPACITY[r]):
                resource = Resource(self.RESOURCE_NAMES[r], j)
                items.append(copy.copy(resource))
        self.factory.items = items
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
            print(f"The lateness corresponding to this schedule is {tardiness}")
        if write:
            self.resource_usage.to_csv(output_location)

        return makespan, tardiness

