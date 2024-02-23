from typing import Any, Iterable, Union
import numpy as np

class STNU:
    EVENT_START = "start"
    EVENT_FINISH = "finish"
    ORIGIN_IDX = 0
    HORIZON_IDX = 1

    nodes: set[int]
    edges: dict[int, dict[int, float]]
    index: int
    translation_dict: dict[int, Any]
    translation_dict_reversed: dict[Any, int]

    def __init__(self):
        # Set-up nodes and edges
        self.nodes = {self.ORIGIN_IDX, self.HORIZON_IDX}
        self.ou_edges = {node: {} for node in self.nodes}
        self.ol_edges = {node: {} for node in self.nodes}
        self.contingent_links = []

        # We use indices for the nodes in the network
        self.index = max(self.nodes) + 1

        # We keep track of two translation dictionaries to connect indices to the events
        self.translation_dict = {}
        self.translation_dict_reversed = {}

        #self.set_edge(self.HORIZON_IDX, self.ORIGIN_IDX, 0)

    def __str__(self):
        """
        ----------------------------------------
        Print method for an STNU object
        ----------------------------------------
        Output:  String representation of the STNU
        ----------------------------------------
        """
        stringy = "STNU:\n"
        stringy += f"Number of nodes in network: {len(self.nodes)}\n"
        stringy += f"Dictionary of names -> index: {self.translation_dict}\n"
        stringy += f"Ordinary Lower Case Edges: {self.ol_edges}\n"
        stringy += f"Ordinary Upper Case Edges: {self.ou_edges}\n"
        stringy += f"Contingent links (node_from, node_to, x, y): {self.contingent_links}\n"
        return stringy

    def add_node(self, description):

        node_idx = self.index
        self.index += 1

        self.nodes.add(node_idx)
        self.ou_edges[node_idx] = {}
        self.ol_edges[node_idx] = {}
        self.translation_dict[node_idx] = description
        self.translation_dict_reversed[description] = node_idx

        # This node / event must occur between ORIGIN and HORIZON
        #self.set_edge(node_idx, self.ORIGIN_IDX, 0)
        #self.set_edge(self.HORIZON_IDX, node_idx, 0)
        return node_idx

    def set_edge(self, node_from, node_to, distance):

        node_from = self.translation_dict_reversed[node_from] if type(node_from) == str else node_from
        node_to = self.translation_dict_reversed[node_to] if type(node_to) == str else node_to

        self.ol_edges[node_from][node_to] = distance
        self.ou_edges[node_from][node_to] = distance

    def remove_edge(self, node_from, node_to):
        if node_to in self.ou_edges[node_from]:
            del self.ou_edges[node_from][node_to]
        if node_to in self.ol_edges[node_from]:
            del self.ol_edges[node_from][node_to]

    def add_interval_constraint(self, node_from, node_to, min_distance, max_distance):
        node_from = self.translation_dict_reversed[node_from] if type(node_from) == str else node_from
        node_to = self.translation_dict_reversed[node_to] if type(node_to) == str else node_to
        self.set_edge(node_from, node_to, max_distance)
        self.set_edge(node_to, node_from, -min_distance)

    def add_tight_constraint(self, node_from, node_to, distance):
        node_from = self.translation_dict_reversed[node_from] if type(node_from) == str else node_from
        node_to = self.translation_dict_reversed[node_to] if type(node_to) == str else node_to
        self.add_interval_constraint(node_from, node_to, distance, distance)

    def add_contingent_link(self, node_from, node_to, x, y):
        node_from = self.translation_dict_reversed[node_from] if type(node_from) == str else node_from
        node_to = self.translation_dict_reversed[node_to] if type(node_to) == str else node_to
        self.ou_edges[node_to][node_from] = -y
        self.ol_edges[node_from][node_to] = x
        self.contingent_links.append((node_from, node_to, x, y))

