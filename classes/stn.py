import itertools
from abc import ABC
from typing import Any, Iterable, Union

import numpy as np

from classes.classes import ProductionPlan
import classes.general

logger = classes.general.get_logger()


class VertexOrdering(Iterable[int], ABC):
    """Abstract base class for vertex orderings"""
    def __init__(self, stn: "STN"):
        self.stn = stn


class StaticMinDegree(VertexOrdering):
    order: list[int]

    def __init__(self, stn: "STN"):
        super().__init__(stn)
        self.order = [x for x in stn.nodes]
        self.order.sort(key=lambda x: len(stn.edges[x]))

    def __iter__(self):
        return iter(self.order)


class STN:
    VERIFY_PROBABILITY = 0  # In 10% of cases, verify that computed distances were correct
    EVENT_START = "start"
    EVENT_FINISH = "finish"
    EVENT_RESERVATION = "reservation"
    ORIGIN_IDX = 0
    HORIZON_IDX = 1

    nodes: set[int]
    edges: dict[int, dict[int, float]]
    removed_nodes: list[int]
    shortest_distances: Union[np.ndarray, dict[int, dict[int, float]], None]
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
                    if activity.distribution.type == "UNIFORMDISCRETE":
                        lower_bound = activity.distribution.lb
                        upper_bound = activity.distribution.ub
                        stn.add_interval_constraint(a_start, a_finish, lower_bound, upper_bound)
                    elif activity.distribution.type == "NORMAL":
                        lower_bound = max(round(activity.distribution.mean - 5 * activity.distribution.variance), 0)
                        upper_bound = round(activity.distribution.mean + 10 * activity.distribution.variance)
                        stn.add_interval_constraint(a_start, a_finish, lower_bound, upper_bound)
                    else:
                        ValueError("Uncertainty set not implemented for this distribution")

            # For every temporal relation in this product's temporal_relations, add edge between nodes with min and max lag
            for i, j in product.temporal_relations:
                min_lag = product.temporal_relations[(i, j)].min_lag
                max_lag = product.temporal_relations[(i, j)].max_lag
                i_idx = stn.translation_dict_reversed[(product.product_index, i, cls.EVENT_START)]
                j_idx = stn.translation_dict_reversed[(product.product_index, j, cls.EVENT_START)]

                # TODO: make sure that the simulator - operator also works when max_time_lag = True
                if max_time_lag:
                    if max_lag is not None:
                        stn.add_interval_constraint(i_idx, j_idx, min_lag, max_lag)
                    else:
                        stn.add_interval_constraint(i_idx, j_idx, min_lag, np.inf)
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

    def remove_node(self, node_idx):
        # Remove a certain node and corresponding edges from the dictionary
        self.nodes.remove(node_idx)
        self.removed_nodes.append(node_idx)

        edge_dict = self.edges.pop(node_idx)
        for key in edge_dict.keys():
            self.edges[key].pop(node_idx)
        assert not (any(node_idx in d for d in self.edges.values()))

        description = self.translation_dict.pop(node_idx)
        self.translation_dict_reversed.pop(description)

    def p3c(self, vertex_ordering: VertexOrdering = None):
        """
        P3C algorithm

        Compute shortest paths only for the chordal graph induced by the given ordering
        """
        def triangle(a, b, c):
            ab = self.shortest_distances[a].setdefault(b, self.edges[a][b])
            bc = self.shortest_distances[b].setdefault(c, self.edges[b][c])
            if ab + bc > self.shortest_distances[a].setdefault(c, self.edges[a][c]):
                self.shortest_distances[a][c] = ab + bc
                return True
            else:
                return False

        logger.debug(f"Running P3C on instance with {len(self.nodes)} nodes and {sum(1 for d in self.edges.values() for _ in d)} edges")

        if not vertex_ordering:
            vertex_ordering = StaticMinDegree(self)

        self.shortest_distances = {v: {} for v in self.nodes}

        seen = set()
        order = []
        for u in vertex_ordering:
            order.append(u)
            neighbours = self.edges[u].keys() - seen
            for (v, w) in itertools.combinations(neighbours, 2):
                if w not in self.edges[v]:
                    # Insert fill edges
                    assert v not in self.edges[w]
                    self.edges[v][w] = np.inf
                    self.edges[w][v] = np.inf
                triangle(v, u, w)
                triangle(w, u, v)
            seen.add(u)

        for u in reversed(order):
            neighbours = self.edges[u].keys() - seen
            for (v, w) in itertools.combinations(neighbours, 2):
                assert w in self.edges[v] and v in self.edges[w]
                triangle(u, v, w)
                triangle(u, w, v)
                triangle(v, w, u)
                triangle(w, v, u)
            seen.remove(u)

        logger.debug(f" P3C done. New edge count: {sum(1 for d in self.edges.values() for _ in d)}")


    def floyd_warshall(self):
        """
        Floyd-Warshall algorithm

        Compute a matrix of shortest-path weights (if the graph contains no negative cycles)
        """
        n = self.index
        logger.debug(f"Running Floyd-Warshall on instance with {n} nodes and {sum(1 for d in self.edges.values() for _ in d)} edges")

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
