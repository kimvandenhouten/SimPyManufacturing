import copy
import json
import time

import pandas as pd
import numpy as np

from enum import Enum

from classes.distributions import Distribution, get_distribution


class CompatibilityConstraint:
    def __init__(self, product_id=None, activity_id=None):
        self.activity_id = activity_id
        self.product_id = product_id


class TemporalRelation:
    def __init__(self, min_lag=None, max_lag=None):
        self.min_lag = min_lag
        self.max_lag = max_lag


class Activity:
    def __init__(self, id, processing_time, product, product_id, needs, distribution=None, sequence_id=int(),
                 constraints=[]):
        self.distribution = None
        self.id = id
        self.product = product
        self.product_id = product_id
        self.processing_time = processing_time
        self.needs = needs
        self.sequence_id = sequence_id
        self.constraints = []
        self._set_constraints(constraints)
        self.set_distribution(distribution)

    def sample_processing_time(self):
        return self.distribution.sample()

    def sample_and_set_scenario(self):
        sample = self.sample_processing_time()
        self.processing_time = [sample, sample]

    def set_distribution(self, distribution):
        if isinstance(distribution, Distribution):
            self.distribution = distribution
        elif distribution is None:
            self.distribution = Distribution(self.processing_time[0])
        elif isinstance(distribution, dict):
            try:
                args = copy.copy(distribution)
                del args['type']
                self.distribution = get_distribution(distribution["type"], args)
            except:
                self.distribution = get_distribution(distribution["type"], distribution["args"])
        else:
            return TypeError("Illegal distribution type: ", type(distribution))

    def _set_constraints(self, constraints):
        for constr in constraints:
            self._set_constraint(constr)

    def _set_constraint(self, constraint):
        if isinstance(constraint, CompatibilityConstraint):
            self.constraints.append(constraint)
        elif isinstance(constraint, dict):
            self.constraints.append(CompatibilityConstraint(**constraint))
        else:
            return TypeError("Illegal distribution type: ", type(constraint))


class Product:
    def __init__(self, id, name, activities=None, temporal_relations=None, deadline=int(), predecessors=None,
                 successors=None, product_index=None):
        self.id = id
        self.name = name
        self.deadline = deadline
        self.successors = successors
        self.predecessors = predecessors
        self._set_activities(activities)
        self._set_temporal_relations(temporal_relations)
        self.product_index = product_index

    def add_activity(self, activity):
        """
        Add a product to the product
        :param product: Class product
        """
        self.activities.append(activity)

    def set_temporal_relations(self, temporal_relations):
        self.temporal_relations = temporal_relations
        self.predecessors = [[] for _ in self.activities]
        self.successors = [[] for _ in self.activities]
        for (i, j) in self.temporal_relations.keys():
            self.predecessors[j].append(i)
            self.successors[i].append(j)

    def _set_activities(self, activities):
        activities_obj = []
        if activities:
            for activity in activities:
                if isinstance(activity, dict):
                    activities_obj.append(Activity(**activity))
                elif isinstance(activity, Activity):
                    activities_obj.append(activity)
                else:
                    raise TypeError("Invalid type of data provided needed: Activity or dict provided:", type(activity))

        self.activities = activities_obj

    def _set_temporal_relations(self, relations):
        temporal_relations = {}
        if relations:
            for relation in relations:
                if (isinstance(relation, dict)):
                    temporal_relations[(relation['predecessor'], relation['successor'])] = TemporalRelation(
                        relation['min_lag'], relation['max_lag'] if 'max_lag' in relation.keys() else None)
                elif (isinstance(relation, tuple)):
                    temporal_relations[relation] = relations[relation]
                else:
                    raise TypeError("Unknown temporal relation type:", type(relations))

        self.temporal_relations = temporal_relations
        self.predecessors = [[] for _ in self.activities]
        self.successors = [[] for _ in self.activities]
        for (i, j) in self.temporal_relations.keys():
            self.predecessors[j].append(i)
            self.successors[i].append(j)


class Factory:
    def __init__(self, name, resource_names, capacity, compatibility_constraints=[], products=None):
        self.name = name
        self._set_products(products)
        self.resource_names = resource_names
        self.capacity = capacity
        self.compatibility_constraints = compatibility_constraints
        self.set_compatibility_constraints()

    def add_product(self, product):
        """
        Add a product to the production plan
        :param product: Class product
        """
        self.products.append(product)

    def set_compatibility_constraints(self):
        for constraint in self.compatibility_constraints:
            if isinstance(constraint[0],CompatibilityConstraint) and isinstance(constraint[1],CompatibilityConstraint):
                self.products[constraint[0]["product_id"]].activities[constraint[0]["activity_id"]].constraints.append(constraint[1])
                self.products[constraint[1]["product_id"]].activities[constraint[1]["activity_id"]]._set_constraint(
                    CompatibilityConstraint(constraint[0]))
            elif isinstance(constraint[0],dict) and isinstance(constraint[1],dict):
                self.products[constraint[0]["product_id"]].activities[constraint[0]["activity_id"]]._set_constraint(
                    CompatibilityConstraint(**constraint[1]))
                self.products[constraint[1]["product_id"]].activities[constraint[1]["activity_id"]]._set_constraint(
                    CompatibilityConstraint(**constraint[0]))

    def _set_products(self, products):
        products_obj = []
        if products:
            for product in products:
                if isinstance(product, dict):
                    products_obj.append(Product(**product))
                elif isinstance(product, Product):
                    products_obj.append(product)
                else:
                    raise TypeError("Invalid type of data provided needed: product or dict provided:", type(product))

        self.products = products_obj


class ProductionPlan:
    def __init__(self, id, size, name, factory, product_ids, deadlines, products=[], sequence=[], earliest_start=None):
        self.id = id
        self.size = size
        self.name = name
        self.product_ids = product_ids
        self.deadlines = deadlines
        self.sequence = sequence
        self.earliest_start = earliest_start
        self._set_factory(factory, products)

    def list_products(self):
        """
        Add a product to the production plan
        :param product: Class product
        """
        self.products = []
        for i in range(0, len(self.product_ids)):
            product = copy.deepcopy(self.factory.products[self.product_ids[i]])
            product.deadline = self.deadlines[i]
            product.product_index = i
            self.products.append(product)
        self.size = len(self.product_ids)

    def set_sequence(self, sequence):
        """
        Give the sequence in which the products will be processed
        :param sequence: list of integers
        """
        self.sequence = sequence

    def convert_to_dataframe(self):
        df = pd.DataFrame()
        df["product_id"] = self.product_ids
        df["deadlines"] = self.deadlines
        return df

    def set_earliest_start_times(self, earliest_start):
        self.earliest_start = earliest_start

    def _set_factory(self, factory, products):
        if isinstance(factory, dict):
            self.factory = Factory(**factory)
        elif isinstance(factory, Factory):
            self.factory = factory
        else:
            raise TypeError("Invalid type of data provided needed: product or dict provided:",
                            type(factory))

        products_obj = []
        for product in products:
            if isinstance(product, dict):
                products_obj.append(Product(**product))
            elif isinstance(products, Product):
                products_obj.append(product)
            else:
                raise TypeError("Invalid type of data provided needed: product or dict provided:",
                                type(product))

        self.products = products_obj

        x = 1

    def to_json(self):
        plan = copy.deepcopy(self)
        for i in range(len(plan.factory.products)):
            temporal_relations = list(map(lambda rel: {
                "predecessor": rel[0],
                "successor": rel[1],
                "min_lag": plan.factory.products[i].temporal_relations[rel].min_lag,
                "max_lag": plan.factory.products[i].temporal_relations[rel].max_lag
            }, plan.factory.products[i].temporal_relations.keys()))
            plan.factory.products[i].temporal_relations = temporal_relations
        plan.list_products()
        return json.dumps(plan, default=lambda o: o.__dict__,
                          sort_keys=True, indent=4)

    def create_scenario(self, seed=None):
        plan = copy.deepcopy(self)
        if seed is not None:
            np.random.seed(seed)

        # sample only plan products
        for product in plan.products:
            for activity in product.activities:
                activity.sample_and_set_scenario()
        return Scenario(plan, seed)


class Scenario:
    def __init__(self, production_plan, seed=None):
        self._set_production_plan(production_plan)
        self.seed = seed

    def to_json(self):
        scenario = {'seed': self.seed, 'production_plan': json.loads(self.production_plan.to_json())}
        return json.dumps(scenario, default=lambda o: o.__dict__,
                          sort_keys=True, indent=4)

    def _set_production_plan(self, production_plan):
        if isinstance(production_plan, dict):
            self.production_plan = ProductionPlan(**production_plan)
        elif isinstance(production_plan, ProductionPlan):
            self.production_plan = production_plan
        else:
            raise TypeError("Invalid type of data provided needed: product or dict provided:",
                            type(production_plan))


class Action(Enum):
    START = "Start"
    END = "End"


class FailureCode(Enum):
    MIN_LAG = "Min_Lag"
    MAX_LAG = "Max_Lag"
    COMPATIBILITY = "Compatibility"
    PRECEDENCE = "Precedence"
    AVAILABILITY = "Availability"


class LogEntry:

    def __init__(self, product_id, activity_id, product_idx, action, timestamp):
        self.product_id = product_id
        self.activity_id = activity_id
        self.product_index = product_idx
        self.action = action
        self.timestamp = timestamp


class SimulatorLogger:

    def __init__(self, class_name):
        self.active_processes = []
        self.class_name = class_name
        self.log = []
        self.failure_code = None

    def log_activity(self, product_id, activity_id, product_index, action, timestamp=time.time()):
        self.log.append(LogEntry(product_id, activity_id, product_index, action, timestamp))
        if action == Action.START and (product_id, activity_id) not in self.active_processes:
            self.active_processes.append((product_id, activity_id))
        elif action == Action.END and (product_id, activity_id) in self.active_processes:
            self.active_processes.remove((product_id, activity_id))

    def fetch_latest_entry(self, product_index, activity_id, action):
        entries = list(filter(lambda
                                  entry: entry.product_index == product_index and entry.activity_id ==
                                         activity_id and entry.action == action,
                              self.log))
        if len(entries) > 0:
            return entries[-1]
        else:
            return None

