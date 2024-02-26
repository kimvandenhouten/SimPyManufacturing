from typing import Any, Iterable, Union
import numpy as np
from classes.classes import ProductionPlan

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
        self.labels = {}

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

    @classmethod
    def from_production_plan(cls, production_plan: ProductionPlan, max_time_lag=True) -> 'STNU':
        stnu = cls()
        for product in production_plan.products:
            for activity in product.activities:
                # Add nodes that refer to start and end of activity
                a_start = stnu.add_node(product.product_index, activity.id, cls.EVENT_START)
                a_finish = stnu.add_node(product.product_index, activity.id, cls.EVENT_FINISH)

                # Add contingent link
                # Possibly add function to distribution to convert distribution to uncertainty set
                if activity.distribution.type == "UNIFORMDISCRETE":
                    lower_bound = activity.distribution.lb
                    upper_bound = activity.distribution.ub
                    stnu.add_contingent_link(a_start, a_finish, lower_bound, upper_bound)
                elif activity.distribution.type == "NORMAL":
                    lower_bound = max(round(activity.distribution.mean - 5 * activity.distribution.variance), 0)
                    upper_bound = round(activity.distribution.mean + 10 * activity.distribution.variance)
                    stnu.add_contingent_link(a_start, a_finish, lower_bound, upper_bound)
                else:
                    ValueError("Uncertainty set not implemented for this distribution")

            # For every temporal relation in this product's temporal_relations, add edge between nodes with min and max lag
            for i, j in product.temporal_relations:
                min_lag = product.temporal_relations[(i, j)].min_lag
                max_lag = product.temporal_relations[(i, j)].max_lag
                i_idx = stnu.translation_dict_reversed[(product.product_index, i, cls.EVENT_START)]
                j_idx = stnu.translation_dict_reversed[(product.product_index, j, cls.EVENT_START)]

                # TODO: make sure that the simulator - operator also works when max_time_lag = True
                if max_time_lag:
                    if max_lag is not None:
                        stnu.add_interval_constraint(i_idx, j_idx, min_lag, max_lag)
                    else:
                        stnu.set_edge(j_idx, i_idx, -min_lag)
                else:
                    stnu.set_edge(j_idx, i_idx, -min_lag)
        return stnu

    def add_node(self, *description):

        node_idx = self.index
        self.index += 1
        self.nodes.add(node_idx)
        self.ou_edges[node_idx] = {}
        self.ol_edges[node_idx] = {}

        # FIXME: this is quite an ugly implementation to distinguish between tuple and str descriptions
        description = description[0] if len(description) == 1 else description
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



