import copy
import simpy
import random
import pandas as pd


class Activity:
    def __init__(self, ID, PROCESSING_TIME, PRODUCT, PRODUCT_ID, NEEDS):
        self.ID = ID
        self.PRODUCT = PRODUCT
        self.PRODUCT_ID = PRODUCT_ID
        self.PROCESSING_TIME = PROCESSING_TIME
        self.NEEDS = NEEDS
        self.SEQUENCE_ID = int()


class Product:
    def __init__(self, ID, NAME, TEMPORAL_RELATIONS):
        self.ID = ID
        self.NAME = NAME
        self.DEADLINE = int()
        self.ACTIVITIES = []
        self.TEMPORAL_RELATIONS = TEMPORAL_RELATIONS

    def add_activity(self, activity):
        """
        Add a product to the product
        :param product: Class Product
        """
        self.ACTIVITIES.append(activity)

    def set_temporal_relations(self):
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
    def __init__(self, ID, FACTORY, PRODUCT_IDS, DEADLINES):
        self.ID = ID
        self.FACTORY = FACTORY
        self.PRODUCT_IDS = PRODUCT_IDS
        self.DEADLINES = DEADLINES
        self.SEQUENCE = []
        self.ACTIVITIES = []
        self.TEMPORAL_RELATIONS = {}
        self.PRODUCTS = []
        self.PREDECESSORS = []
        self.SUCCESSORS = []

    def list_products(self):
        """
        Add a product to the production plan
        :param product: Class Product
        """
        for i in range(0, len(self.PRODUCT_IDS)):
            product = copy.copy(self.FACTORY.PRODUCTS[self.PRODUCT_IDS[i]])
            product.DEADLINE = self.DEADLINES[i]
            self.PRODUCTS.append(product)

    def set_sequence(self, sequence):
        """
        Give the sequence in which the products will be processed
        :param sequence: list of integers
        """
        self.SEQUENCE = sequence


class Simulator:
    def __init__(self, plan):
        self.plan = plan
        self.RESOURCE_NAMES = plan.FACTORY.RESOURCE_NAMES
        self.NR_RESOURCES = len(self.RESOURCE_NAMES)
        self.CAPACITY = plan.FACTORY.CAPACITY
        self.ACTIVITIES = range(0, len(plan.ACTIVITIES))
        self.TEMPORAL_RELATIONS = plan.TEMPORAL_RELATIONS
        self.PREDECESSORS = plan.PREDECESSORS
        self.SUCCESSORS = plan.SUCCESSORS
        self.TEMPORAL_RELATIONS = plan.TEMPORAL_RELATIONS
        self.RESOURCES = []
        self.env = simpy.Environment()
        self.resource_usage = []
        self.printing = False

    def activity(self, activity, p, delay=0):
        """An activity arrives at the factory for processing
        It requests one of the resources. If this resource is
        occupied it has to wait.

        """
        resources_required = []
        resources_names = []
        needs = activity.NEEDS
        name = f'{p}_{activity.ID}'
        duration = random.randint(*activity.PROCESSING_TIME)
        yield self.env.timeout(delay)
        for r in range(0, self.NR_RESOURCES):
            need = needs[r]
            if need > 0:
                for _ in range(0, need):
                    resource = self.RESOURCES[r]
                    resource_name = self.RESOURCE_NAMES[r]
                    resources_required.append(resource.request())
                    resources_names.append(resource_name)
        request_time = self.env.now
        if self.printing:
            print(f'activity: {name} requested resources: {resources_names} at time: {request_time}')
        yield self.env.all_of(resources_required)
        start_time = self.env.now
        if self.printing:
            print(f'activity: {name} retrieved resources: {resources_names} at time: {start_time}')
        yield self.env.timeout(duration)
        end_time = self.env.now
        for r in resources_required:
            r.resource.release(r)
        if self.printing:
            print(f'activity: {name} released resources: {resources_names} at time: {end_time}')

        for resource_name in resources_names:
            self.resource_usage.append({"Activity": name,
                                        "Product": p,
                                        "Resource": resource_name,
                                        "Request moment": request_time,
                                        "Start": start_time,
                                        "Finish": end_time})

    def product(self, p):
        # Iterate through activites needed for this product
        activities = self.plan.PRODUCTS[p].ACTIVITIES
        temp_relations = self.plan.PRODUCTS[p].TEMPORAL_RELATIONS
        successors = self.plan.PRODUCTS[p].SUCCESSORS

        # Keep track of which activities are still unscheduled
        UNSCHEDULED = [0 for _ in activities]

        for i in range(0, len(activities)):
            # Activate activity process
            if UNSCHEDULED[i] == 0:
                self.env.process(self.activity(activities[i], p))
                UNSCHEDULED[i] = 1

                # Schedule successors for this activity according to temporal relations
                for j in successors[i]:
                    if UNSCHEDULED[j] == 0:
                        self.env.process(self.activity(activities[j], p, delay=temp_relations[(i, j)]))
                    UNSCHEDULED[j] = 1

        yield self.env.timeout(0)

    def product_generator(self):
        """Generate activities that arrive at the factory. For certain activities there are temporal relations,
        this means that there are fixed time intervals between the request times for the two activities."""
        print(f"The products are processed according to the production sequence {self.plan.SEQUENCE}.")
        # Schedule activities with priority ordering
        for p in self.plan.SEQUENCE:
            self.env.process(self.product(p))
            yield self.env.timeout(0)

    def simulate(self, SIM_TIME, RANDOM_SEED, write=False):
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

        print(f"The makespan corresponding to this schedule is {makespan}")
        print(f"The tardiness corresponding to this schedule is {tardiness}")
        if write:
            self.resource_usage.to_csv(f"Schedule_seed={RANDOM_SEED}.csv")

        return makespan, tardiness

