import copy
import simpy
import random
import pandas as pd
from collections import namedtuple


class Simulator:
    def __init__(self, plan, printing=False):
        self.plan = plan
        self.resource_name = plan.factory.resource_name
        self.nr_resources = len(self.resource_name)
        self.capacity = plan.factory.capacity
        self.resources = []
        self.env = simpy.Environment()
        self.resource_usage = []
        self.printing = printing

    def resource_request(self, product, resource_group):
        resource = yield self.factory.get(lambda resource: resource.resource_group == resource_group)
        if self.printing:
            print(product, 'requested', resource.resource_group, ' id ', resource.id, 'at', self.env.now)
        return resource

    def product(self, p, priority):

        #TODO: adjust such that machines in the store are requested instead of resources

        # FIRST DO THE REQUESTING
        activities = self.plan.products[p].activities
        durations = []
        resources_required = {}
        resources_names = {}
        for i in range(0, len(activities)):
            activity = activities[i]
            needs = activity.needs
            duration = random.randint(*activity.processing_time)
            durations.append(duration)
            resources_required_act = []
            resources_names_act = []
            for r in range(0, self.nr_resources):
                need = needs[r]
                if need > 0:
                    for _ in range(0, need):
                        resource_name = self.resource_name[r]
                        resources_required_act.append(self.env.process(self.resource_request(product=p, resource_group=resource_name)))
                        resources_names_act.append(resource_name)
            resources_required[i] = resources_required_act
            resources_names[i] = resources_names_act
        request_time = self.env.now
        if self.printing:
            print(f'Product {p} requested resources: {resources_names} at time: {request_time}')

        for i in range(0, len(activities)):
            yield self.env.all_of(resources_required[i])
            retrieve_time = self.env.now
            if self.printing:
                print(f'Product {p}, activity {i}, retrieved resources: {resources_names[i]} at time: {retrieve_time}')

        for i in range(0, len(activities)):
            if i == 0:
                delay_factor = 0
            else:
                delay_factor = self.plan.products[p].temporal_relations[(0, i)]
            self.env.process(self.activity_processing(i=i, p=p, delay=delay_factor, duration=durations[i], resources_required=resources_required[i],
                                                      resources_names=resources_names[i], request_time=request_time,
                                                      retrieve_time=retrieve_time))

    def activity_processing(self, i, p, delay, duration, resources_required, resources_names, request_time, retrieve_time):

        # TODO: adjust such that the tuples in the factory are released instead of the resource types
        yield self.env.timeout(delay)
        start_time = self.env.now
        # NOW START WITH THE ACTUAL PROCESSING
        yield self.env.timeout(duration)
        end_time = self.env.now

        # NOW RELEASE ALL resources THAT WERE NEEDED
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
            print(f"The products are processed according to the production sequence {self.plan.sequence}.")
        # Schedule activities with priority ordering
        priority = 0
        for p in self.plan.sequence:
            self.env.process(self.product(p, priority=priority))
            priority += 1
            yield self.env.timeout(3)

    def simulate(self, SIM_TIME, random_seed, write=False, output_location="Results.csv"):
        if self.printing:
            print(f'START factory simulation for seed {random_seed}')
        random.seed(random_seed)
        # Reset environment
        self.env = simpy.Environment()
        self.resource_usage = []

        # TO DO: REPLACE WITH factory STORE TYPE
        self.factory = simpy.FilterStore(self.env, capacity=sum(self.capacity))
        Resource = namedtuple('Machine', 'resource_group, id')
        items = []
        for r in range(0, self.nr_resources):
            for j in range(0, self.capacity[r]):
                resource = Resource(self.resource_name[r], j)
                items.append(copy.copy(resource))
        self.factory.items = items
        self.env.process(self.product_generator())

        # Execute!
        self.env.run(until=SIM_TIME)

        # Process results
        self.resource_usage = pd.DataFrame(self.resource_usage)
        makespan = max(self.resource_usage["Finish"])
        tardiness = 0

        for p in self.plan.sequence:
            schedule = self.resource_usage[self.resource_usage["Product"] == p]
            finish = max(schedule["Finish"])
            if self.printing:
                print(f'Product {p} finished at time {finish}, while the dealine was {self.plan.products[p].dealine}.')
            tardiness += max(0, finish - self.plan.products[p].dealine)

        if self.printing:
            print(f"The makespan corresponding to this schedule is {makespan}")
            print(f"The tardiness corresponding to this schedule is {tardiness}")
        if write:
            self.resource_usage.to_csv(output_location)

        return makespan, tardiness

