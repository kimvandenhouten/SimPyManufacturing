import copy
import json
import time

import pandas as pd
import numpy as np

from enum import Enum
from typing import Union, Any

from IPython.core.display_functions import display

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
        sample = round(sample)
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
                        relation['min_lag'] if 'min_lag' in relation.keys() else None,
                        relation['max_lag'] if 'max_lag' in relation.keys() else None)
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
        #self.set_compatibility_constraints(compatibility_constraints)

    def add_product(self, product):
        """
        Add a product to the production plan
        :param product: Class product
        """
        self.products.append(product)

    def set_compatibility_constraints(self, compatibility_constraints):
        print(f'set compatibility constraints is activated')
        for constraint in compatibility_constraints:
            if isinstance(constraint[0], CompatibilityConstraint) and isinstance(constraint[1],
                                                                                 CompatibilityConstraint):
                self.products[constraint[0]["product_id"]].activities[constraint[0]["activity_id"]].constraints.append(
                    constraint[1])
                self.products[constraint[1]["product_id"]].activities[constraint[1]["activity_id"]]._set_constraint(
                    CompatibilityConstraint(constraint[0]))
            elif isinstance(constraint[0], dict) and isinstance(constraint[1], dict):
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
        self.list_products()

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
        constraints = []
        constraints_obj = []
        for i in range(len(plan.factory.products)):
            temporal_relations = list(map(lambda rel: {
                "predecessor": rel[0],
                "successor": rel[1],
                "min_lag": plan.factory.products[i].temporal_relations[rel].min_lag,
                "max_lag": plan.factory.products[i].temporal_relations[rel].max_lag
            }, plan.factory.products[i].temporal_relations.keys()))
            plan.factory.products[i].temporal_relations = temporal_relations
            for activity in plan.factory.products[i].activities:
                for constraint in activity.constraints:
                    if (plan.factory.products[i].id, activity.id) not in constraints:
                        constraints.append((constraint.product_id, constraint.activity_id))
                        constraints_obj.append([CompatibilityConstraint(constraint.product_id, constraint.activity_id),
                                                CompatibilityConstraint(plan.factory.products[i].id, activity.id)])
                del activity.constraints
            plan.factory.compatibility_constraints = constraints_obj
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


class LogInfoEntry:
    def __init__(self, product_id, activity_id, product_idx, needs, resources, request_time, retrieve_time, start_time,
                 end_time, pushback=False):
        self.product_id = product_id
        self.activity_id = activity_id
        self.product_idx = product_idx
        self.needs = needs
        self.resources = resources
        self.request_time = request_time
        self.retrieve_time = retrieve_time
        self.start_time = start_time
        self.end_time = end_time
        self.pushback = pushback


class LogInfo:
    def __init__(self):
        self.entries = []

    def log(self, product_id, activity_id, product_idx, needs, resources, request_time, retrieve_time, start_time,
            end_time, pushback):
        self.entries.append(
            LogInfoEntry(product_id, activity_id, product_idx, needs, resources, request_time, retrieve_time,
                         start_time,
                         end_time, pushback))

    '''Returns the latest entry with the given product ID, activity ID and product index, if any.'''

    def fetch_latest_entry(self, product_id, activity_id, product_idx):
        entries = list(filter(lambda
                                  entry: entry.product_id == product_id and entry.activity_id ==
                                         activity_id and entry.product_idx == product_idx,
                              self.entries))
        if len(entries) > 0:
            return entries[-1]
        else:
            return None

    def to_df(self):
        info_df = []
        for entry in self.entries:
            info_r = {"ProductIndex": entry.product_idx,
                      "ProductId": entry.product_id,
                      "Activity": entry.activity_id,
                      "Needs": entry.needs,
                      "Resources": entry.resources,
                      "Request": entry.request_time,
                      "Retrieve": entry.retrieve_time,
                      "Start": entry.start_time,
                      "Finish": entry.end_time,
                      "Pushback": entry.pushback}
            info_df.append(info_r)

        return pd.DataFrame(info_df)

    def to_csv(self, output_location):
        self.to_df().to_csv(output_location)

    def print(self):
        display(self.to_df().to_string())


class SimulatorLogger:

    def __init__(self, class_name):
        self.active_processes = []
        self.class_name = class_name
        self.log = []
        self.failure_code = None
        self.info = LogInfo()

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


class STN:
    VERIFY_PROBABILITY = 0 # In 10% of cases, verify that computed distances were correct
    EVENT_START = "start"
    EVENT_FINISH = "finish"
    ORIGIN_IDX = 0
    HORIZON_IDX = 1

    nodes: set[int]
    edges: dict[int, dict[int, float]]
    removed_nodes: list[int]
    shortest_distances: Union[np.ndarray, None]
    index: int
    translation_dict: dict[int, Any]
    translation_dict_reversed: dict[Any, int]

    @classmethod
    def from_production_plan(cls, production_plan: ProductionPlan, stochastic=False, max_time_lag=True) -> 'STN':
        stn = cls()
        for product in production_plan.products:
            for activity in product.activities:
                # Add nodes that refer to start and end of activity
                a_start = stn.add_node(product.product_index, activity.id, cls.EVENT_START)
                a_finish = stn.add_node(product.product_index, activity.id, cls.EVENT_FINISH)

                # Add edge between start and finish with processing time
                if stochastic is False:
                    stn.add_tight_constraint(a_start, a_finish, activity.processing_time[0])
                else:
                    # Possibly add function to distribution to convert distribution to uncertainty set
                    lower_bound = max(round(activity.distribution.mean - 5 * activity.distribution.variance), 0)
                    upper_bound = round(activity.distribution.mean + 10 * activity.distribution.variance)
                    stn.add_interval_constraint(a_start, a_finish, lower_bound, upper_bound)

            # For every temporal relation in this product's temporal_relations, add edge between nodes with min and max lag
            for i, j in product.temporal_relations:
                min_lag = product.temporal_relations[(i, j)].min_lag
                max_lag = product.temporal_relations[(i, j)].max_lag
                i_idx = stn.translation_dict_reversed[(product.product_index, i, cls.EVENT_START)]
                j_idx = stn.translation_dict_reversed[(product.product_index, j, cls.EVENT_START)]

                # TODO: make sure that the simulator - operator also works when max_time_lag = True
                if max_time_lag:
                    stn.add_interval_constraint(i_idx, j_idx, min_lag, max_lag)
                else:
                    stn.add_interval_constraint(i_idx, j_idx, min_lag, np.inf)
        return stn

    def __init__(self):
        # Set-up nodes and edges
        self.nodes = {self.ORIGIN_IDX, self.HORIZON_IDX}
        self.edges = {node: {} for node in self.nodes}

        self.removed_nodes = []

        self.shortest_distances = None

        # We use indices for the nodes in the network
        self.index = max(self.nodes) + 1

        # We keep track of two translation dictionaries to connect indices to the events
        self.translation_dict = {}
        self.translation_dict_reversed = {}

        self.set_edge(self.HORIZON_IDX, self.ORIGIN_IDX, 0)

    '''
    Floyd-Warshall algorithm
    Compute a matrix of shortest-path weights (if the graph contains no negative cycles)
    '''
    def remove_node(self, node_idx):
        # Remove a certain node and corresponding edges from the dictionary
        self.nodes.remove(node_idx)
        self.removed_nodes.append(node_idx)

        edge_dict = self.edges.pop(node_idx)
        for key in edge_dict.keys():
            self.edges[key].pop(node_idx)
        assert not(any(node_idx in d for d in self.edges.values()))

        description = self.translation_dict.pop(node_idx)
        self.translation_dict_reversed.pop(description)

    def floyd_warshall(self):
        # Compute shortest distance graph path for this graph
        n = self.index
        assert n >= len(self.nodes)
        w = np.full((n, n), np.inf)
        np.fill_diagonal(w, 0)
        for u, edge_dict in self.edges.items():
            for v, weight in edge_dict.items():
                w[u, v] = weight

        for k in range(1, n + 1):
            w_old = w
            w = np.full((n, n), np.inf)
            for i in range(n):
                for j in range(n):
                    w[i, j] = min(w_old[i, j], w_old[i, k - 1] + w_old[k - 1, j])

        if any(np.diag(w) < 0):
            raise ValueError("The graph contains negative cycles.")

        self.shortest_distances = w
        return self.shortest_distances

    def add_node(self, *description):
        if self.removed_nodes:
            node_idx = self.removed_nodes.pop()
        else:
            node_idx = self.index
            self.index += 1

        self.nodes.add(node_idx)
        self.edges[node_idx] = {}
        self.translation_dict[node_idx] = description
        self.translation_dict_reversed[description] = node_idx

        # This node / event must occur between ORIGIN and HORIZON
        self.set_edge(node_idx, self.ORIGIN_IDX, 0)
        self.set_edge(self.HORIZON_IDX, node_idx, 0)
        return node_idx

    def set_edge(self, node_from, node_to, distance):
        if node_to not in self.edges[node_from]:
            assert node_from not in self.edges[node_to]
            self.edges[node_from][node_to] = self.edges[node_to][node_from] = np.inf
        prev = self.edges[node_from][node_to]
        reverse = np.inf if self.shortest_distances is None else self.shortest_distances[node_to][node_from]
        if reverse + distance < 0:
            raise ValueError(f"Introducing negative cycle: "
                             f"{-reverse} <= node_{node_to} - node_{node_from} <= {distance}")
        self.edges[node_from][node_to] = distance
        if prev > distance:
            return True
        elif prev == distance:
            return False
        else:
            assert prev < distance
            print(f"STN warning: loosening constraint edge {node_from}->{node_to} from {prev} to {distance}")
            return True

    def add_interval_constraint(self, node_from, node_to, min_distance, max_distance, propagate=False):
        self.bounds_check(node_from, node_to, min_distance, max_distance)

        if self.set_edge(node_from, node_to, max_distance) and propagate:
            self.ifpc(node_from, node_to, max_distance)
        if self.set_edge(node_to, node_from, -min_distance) and propagate:
            self.ifpc(node_to, node_from, -min_distance)

        assert self._verify_distances()

    def add_tight_constraint(self, node_from, node_to, distance, propagate=False):
        self.add_interval_constraint(node_from, node_to, distance, distance, propagate)

    def ifpc(self, node_from, node_to, distance):
        if self.shortest_distances[node_from][node_to] <= distance:
            return
        self.shortest_distances[node_from][node_to] = distance
        from_list = []
        to_list = []
        for idx in self.nodes:
            if idx in (node_from, node_to):
                continue
            d = self.shortest_distances[idx][node_from]
            new_d = d + distance
            if new_d < self.shortest_distances[idx][node_to]:
                self.shortest_distances[idx][node_to] = new_d
                from_list.append(idx)
            d = self.shortest_distances[node_to][idx]
            new_d = distance + d
            if new_d < self.shortest_distances[node_from][idx]:
                self.shortest_distances[node_from][idx] = new_d
                to_list.append(idx)

        for idx1 in from_list:
            d = self.shortest_distances[idx1][node_from]
            for idx2 in to_list:
                if idx2 == idx1:
                    continue
                new_d = d + self.shortest_distances[node_from][idx2]
                if new_d < self.shortest_distances[idx1][idx2]:
                    self.shortest_distances[idx1][idx2] = new_d

    def _verify_distances(self, force=False):
        if self.shortest_distances is None:
            return True
        elif not force and np.random.random() > STN.VERIFY_PROBABILITY:
            return True

        distances = self.shortest_distances
        return np.array_equal(distances, self.floyd_warshall())

    def bounds_check(self, node_from, node_to, min_distance, max_distance):
        if self.shortest_distances is not None:
            lower_bound = -self.shortest_distances[node_to][node_from]
            upper_bound = self.shortest_distances[node_from][node_to]
            if max_distance < lower_bound:
                raise ValueError(f"Can't set upper bound of {max_distance} between node_{node_from} and "
                                 f"node_{node_to}: lower bound is {lower_bound}")
            if min_distance > upper_bound:
                raise ValueError(f"Can't set lower bound of {min_distance} between node_{node_from} and "
                                 f"node_{node_to}: upper bound is {upper_bound}")

