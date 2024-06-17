import heapq
import itertools
import pickle
from abc import ABC
from collections import Counter
from typing import Any, Iterable, Union

import numpy as np

import general.logger

logger = general.logger.get_logger(__name__)



class VertexOrdering(Iterable[int], ABC):
    """Abstract base class for vertex orderings"""

    def __init__(self, stn: "STN"):
        self.stn = stn


class StaticMinDegree(VertexOrdering):
    order: list[int]

    def __init__(self, stn: "STN"):
        super().__init__(stn)
        self.order = sorted(stn.nodes, key=lambda x: len(stn.edges[x]))

    def __iter__(self):
        return iter(self.order)


class DynamicMinDegree(VertexOrdering):
    def __init__(self, stn: "STN"):
        super().__init__(stn)
        self.sorted_nodes = sorted(stn.nodes, key=lambda x: len(stn.edges[x]))
        self.running = False

    def __iter__(self):
        if self.running:
            raise Exception("already iterating")
        self.running = True
        return self._generator()

    def _generator(self):
        eliminated = set()

        def active(nodes):
            return (x for x in nodes if x not in eliminated)

        def degree(v):
            return sum(1 for _ in active(edges[v].keys()))

        edges = self.stn.edges
        if not self.running:
            raise Exception("must be invoked through __iter__")
        while self.sorted_nodes:
            v = self.sorted_nodes[0]
            yield v
            eliminated.add(v)
            to_update = sorted(active(edges[v].keys()), key=degree)
            remainder = (x for x in self.sorted_nodes[1:] if x not in to_update)
            self.sorted_nodes = list(heapq.merge(to_update, remainder, key=degree))
        self.running = False


class STN:
    EVENT_START = "start"
    EVENT_FINISH = "finish"
    EVENT_RESERVATION = "reservation"
    ORIGIN_IDX = 0
    HORIZON_IDX = 1
    SOLUTION_TYPE_FPC = "FPC"
    SOLUTION_TYPE_PPC = "PPC"

    nodes: set[int]
    edges: dict[int, dict[int, float]]
    solution_type: str
    removed_nodes: list[int]
    shortest_distances: Union[np.ndarray, dict[int, dict[int, float]], None]
    index: int
    translation_dict: dict[int, Any]
    translation_dict_reversed: dict[Any, int]


    def __init__(self):
        # Set-up nodes and edges
        self.nodes = {self.ORIGIN_IDX, self.HORIZON_IDX}
        self.edges = {node: {} for node in self.nodes}
        self.solution_type = None

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

    def log_graph_statistics(self):
        logger.debug(
            f"Running P3C on instance with {len(self.nodes)} nodes and {sum(1 for d in self.edges.values() for _ in d)} edges")

        rigid_count = 0
        degrees = Counter()
        for v in self.edges:
            degrees[len(self.edges[v])] += 1
            for w in self.edges[v]:
                if w < v:
                    continue
                elif w == v:
                    assert False
                if self.edges[v][w] + self.edges[w][v] == 0:
                    rigid_count += 1

        logger.debug(f"vertex degrees: {sorted(degrees.items(), reverse=True)}")
        logger.debug(f"# rigid constraints: {rigid_count}")

    def check_solution_type(self, solution_type: str):
        if self.solution_type not in (None, solution_type):
            raise Exception("Incompatible solution type")
        self.solution_type = solution_type

    def p3c(self, vertex_ordering_class: type[VertexOrdering] = DynamicMinDegree):
        """
        P3C algorithm

        Compute shortest paths only for the chordal graph induced by the given ordering
        """
        self.check_solution_type(self.SOLUTION_TYPE_PPC)

        def triangle(a, b, c):
            ab = self.shortest_distances[a].setdefault(b, self.edges[a][b])
            bc = self.shortest_distances[b].setdefault(c, self.edges[b][c])
            if ab + bc < self.shortest_distances[a].setdefault(c, self.edges[a][c]):
                self.shortest_distances[a][c] = ab + bc
                return True
            else:
                return False

        self.log_graph_statistics()

        vertex_ordering = vertex_ordering_class(self)

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

        logger.debug(f"P3C done.")
        self.log_graph_statistics()

    def floyd_warshall(self):
        """
        Floyd-Warshall algorithm

        Compute a matrix of shortest-path weights (if the graph contains no negative cycles)
        """
        self.check_solution_type(self.SOLUTION_TYPE_FPC)

        n = self.index
        logger.debug(
            f"Running Floyd-Warshall on instance with {n} nodes and {sum(1 for d in self.edges.values() for _ in d)} edges")

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
            self.incremental(node_from, node_to, max_distance)
        if self.set_edge(node_to, node_from, -min_distance) and propagate:
            self.incremental(node_to, node_from, -min_distance)

    def add_tight_constraint(self, node_from, node_to, distance, propagate=False):
        self.add_interval_constraint(node_from, node_to, distance, distance, propagate)

    def incremental(self, node_from, node_to, distance):
        if self.solution_type is None:
            raise Exception("please run Floyd-Warshall or P3C first")
        elif self.solution_type == self.SOLUTION_TYPE_FPC:
            return self.ifpc(node_from, node_to, distance)
        elif self.solution_type == self.SOLUTION_TYPE_PPC:
            return self.ippc(node_from, node_to, distance)
        else:
            raise Exception("unknown solution type")

    def ifpc(self, node_from, node_to, distance):
        self.check_solution_type(self.SOLUTION_TYPE_FPC)
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

    def ippc(self, node_a, node_b, dist_a_b):
        self.check_solution_type(self.SOLUTION_TYPE_PPC)

        if self.shortest_distances[node_a][node_b] <= dist_a_b:
            return
        self.shortest_distances[node_a][node_b] = dist_a_b

        tagged = {node_a, node_b}
        dist_to_a: dict[int] = {v: self.shortest_distances[v][node_a] for v in self.shortest_distances[node_a].keys()}
        dist_from_b: dict[int] = {v: d for (v, d) in self.shortest_distances[node_b].items()}
        tagged_neighbours = {}

        def tag(v):
            assert v not in tagged
            tagged.add(v)

            change = False

            for u in tagged_neighbours.pop(v):
                assert u in tagged
                assert u in dist_to_a and v in dist_to_a
                assert u in dist_from_b and v in dist_from_b
                assert u in self.shortest_distances and v in self.shortest_distances
                assert u in self.shortest_distances[v] and v in self.shortest_distances[u]

                d = dist_to_a[u] + dist_a_b + dist_from_b[v]
                if d < self.shortest_distances[u][v]:
                    self.shortest_distances[u][v] = d
                    change = True

                d = dist_to_a[v] + dist_a_b + dist_from_b[u]
                if d < self.shortest_distances[v][u]:
                    self.shortest_distances[v][u] = d
                    change = True

            if change:
                for u in self.edges[v]:
                    if u in tagged:
                        continue

                    d = self.shortest_distances[u].get(v, np.inf) + dist_to_a[v]
                    if d < dist_to_a.get(u, np.inf):
                        dist_to_a[u] = d

                    d = dist_from_b[v] + self.shortest_distances.get(v, np.inf)
                    if d < dist_from_b.get(u, np.inf):
                        dist_from_b[u] = d

                    nb_list = tagged_neighbours.get(u, [])
                    nb_list.append(v)
                    # TODO Here, keep track of the size of nb_list in an efficient data structure

        def max_count():
            # TODO this is a proof of concept.  Re-implement in an efficient way
            largest = None
            maxlen = 0

            for (v, nb_list) in tagged_neighbours.items():
                if len(nb_list) > maxlen:
                    largest, maxlen = v, len(nb_list)

            return largest, maxlen

        while True:
            v, maxlen = max_count()
            if v is None or maxlen < 2:
                break
            tag(v)


    def to_pickle(self, pickle_file_path):
        with open(pickle_file_path, 'wb') as file:
            # Use the pickle.dump() method to serialize and write the object to the file
            pickle.dump(self, file)

        print(f"Object saved to {pickle_file_path}")

    def bounds_check(self, node_from, node_to, min_distance, max_distance):
        if self.shortest_distances is not None:
            lower_bound = -self.shortest_distances[node_to][node_from]
            upper_bound = self.shortest_distances[node_from][node_to]
            if max_distance < lower_bound:
                #self.to_pickle("snapshot_stn.pkl")
                print(node_from, node_to, min_distance, max_distance)
                raise ValueError(f"Can't set upper bound of {max_distance} between node_{node_from} and "
                                 f"node_{node_to}: lower bound is {lower_bound}")
            if min_distance > upper_bound:
                #self.to_pickle("snapshot_stn.pkl")
                print(node_from, node_to, min_distance, max_distance)
                raise ValueError(f"Can't set lower bound of {min_distance} between node_{node_from} and "
                                 f"node_{node_to}: upper bound is {upper_bound}")
