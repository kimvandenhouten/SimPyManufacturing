from typing import Any, Iterable, Union
import numpy as np
from classes.classes import ProductionPlan


class Edge:
    UC_LABEL = "UC"
    LC_LABEL = "LC"
    ORDINARY_LABEL = "ORDINARY"

    def __init__(self, node_from, node_to):
        self.node_from = node_from
        self.node_to = node_to
        self.weight = None
        self.uc_label = None
        self.uc_weight = None
        self.lc_label = None
        self.lc_weight = None

    def set_labeled_weight(self, labeled_weight, label, label_type):
        if label_type == self.UC_LABEL:
            self.uc_weight = labeled_weight
            self.uc_label = label
        elif label_type == self.LC_LABEL:
            self.lc_weight = labeled_weight
            self.lc_label = label
        else:
            ValueError(f'Type for labeled weight not specified')

    def set_weight(self, weight):
        self.weight = weight


class STNU:
    EVENT_START = "start"
    EVENT_FINISH = "finish"
    UC_LABEL = "UC"
    LC_LABEL = "LC"
    ORDINARY_LABEL = "ORDINARY"
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
        self.edges = {node: {} for node in self.nodes}

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
        stringy += f"Edges: {self.edges}\n"
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
        self.edges[node_idx] = {}

        # FIXME: this is quite an ugly implementation to distinguish between tuple and str descriptions
        description = description[0] if len(description) == 1 else description
        self.translation_dict[node_idx] = description
        self.translation_dict_reversed[description] = node_idx

        # This node / event must occur between ORIGIN and HORIZON
        #self.set_edge(node_idx, self.ORIGIN_IDX, 0)
        #self.set_edge(self.HORIZON_IDX, node_idx, 0)
        return node_idx

    def set_labeled_edge(self, node_from, node_to, distance, label, label_type):

        node_from = self.translation_dict_reversed[node_from] if type(node_from) == str else node_from
        node_to = self.translation_dict_reversed[node_to] if type(node_to) == str else node_to

        if node_to in self.edges[node_from]:
            edge = self.edges[node_from][node_to]
        else:
            edge = Edge(node_from, node_to)

        edge.set_labeled_weight(labeled_weight=distance, label=label, label_type=label_type)
        self.edges[node_from][node_to] = edge

    def set_ordinary_edge(self, node_from, node_to, distance):

        node_from = self.translation_dict_reversed[node_from] if type(node_from) == str else node_from
        node_to = self.translation_dict_reversed[node_to] if type(node_to) == str else node_to

        if node_to in self.edges[node_from]:
            edge = self.edges[node_from][node_to]
        else:
            edge = Edge(node_from, node_to)
        edge.set_weight(weight=distance)
        self.edges[node_from][node_to] = edge



    def remove_edge(self, node_from, node_to, type):
        """Removes edge of the given type (if it exists)

        :return: Whether an edge was succesfully removed
        """

        if node_to not in self.edges[node_from]:
            return False

        edge = self.edges[node_from][node_to]
        if type == self.LC_LABEL:
            if edge.lc_weight is None or edge.lc_label is None:
                assert edge.lc_weight is None and edge.lc_label is None
                return False
            edge.lc_weight = None
            edge.lc_label = None
        elif type == self.UC_LABEL:
            if edge.uc_weight is None or edge.uc_label is None:
                assert edge.uc_weight is None and edge.uc_label is None
                return False
            edge.uc_weight = None
            edge.uc_label = None
        elif type == self.ORDINARY_LABEL:
            if edge.weight is None:
                return False
            edge.weight = None
        else:
            raise ValueError("Unknown edge type")

        if edge.lc_weight is None and edge.uc_weight is None and edge.weight is None:
            del self.edges[node_from][node_to]

        return True

    def add_interval_constraint(self, node_from, node_to, min_distance, max_distance):
        node_from = self.translation_dict_reversed[node_from] if type(node_from) == str else node_from
        node_to = self.translation_dict_reversed[node_to] if type(node_to) == str else node_to
        self.set_ordinary_edge(node_from, node_to, max_distance)
        self.set_ordinary_edge(node_to, node_from, -min_distance)

    def add_tight_constraint(self, node_from, node_to, distance):
        node_from = self.translation_dict_reversed[node_from] if type(node_from) == str else node_from
        node_to = self.translation_dict_reversed[node_to] if type(node_to) == str else node_to
        self.add_interval_constraint(node_from, node_to, distance, distance)

    def add_contingent_link(self, node_from, node_to, x, y):
        node_from = self.translation_dict_reversed[node_from] if type(node_from) == str else node_from
        node_to = self.translation_dict_reversed[node_to] if type(node_to) == str else node_to

        label = self.translation_dict[node_to]

        if node_from in self.edges[node_to]:
            edge = self.edges[node_to][node_from]
        else:
            edge = Edge(node_to, node_from)

        edge.set_labeled_weight(labeled_weight=-y, label=label, label_type=self.UC_LABEL)
        self.edges[node_to][node_from] = edge

        if node_from in self.edges[node_from]:
            edge = self.edges[node_from][node_to]
        else:
            edge = Edge(node_from, node_to)
        edge.set_labeled_weight(labeled_weight=x, label=label, label_type=self.LC_LABEL)
        self.edges[node_from][node_to] = edge

        self.contingent_links.append((node_from, node_to, x, y))

    def get_incoming_edges(self, node_to):
        """
        :param u: node_to
        :return: all preceding edges of node u
        """
        N = len(self.nodes)
        incoming_edges = []  # I have chosen now to use a dictionary to keep track of the incoming edges
        # Find incoming edges of node u from OU graph
        for pred_node in range(N):
            if node_to in self.edges[pred_node]:
                edge = self.edges[pred_node][node_to]
                if edge.weight is not None:
                    incoming_edges.append((edge.weight, pred_node, STNU.ORDINARY_LABEL, None))
                if edge.uc_weight is not None:
                    incoming_edges.append((edge.uc_weight, pred_node, STNU.UC_LABEL, edge.uc_label))
                if edge.lc_weight is not None:
                    incoming_edges.append((edge.lc_weight, pred_node, STNU.LC_LABEL, edge.lc_label))

        return incoming_edges

    def get_incoming_ou_edges(self, node_to):
        """
        :param u: node_to
        :return: all preceding edges of node u
        """
        N = len(self.nodes)
        incoming_edges = []  # I have chosen now to use a dictionary to keep track of the incoming edges
        # Find incoming edges of node u from OU graph
        for pred_node in range(N):
            if node_to in self.edges[pred_node]:
                edge = self.edges[pred_node][node_to]
                if edge.weight is not None:
                    incoming_edges.append((edge.weight, pred_node, STNU.ORDINARY_LABEL, None))
                if edge.uc_weight is not None:
                    incoming_edges.append((edge.uc_weight, pred_node, STNU.UC_LABEL, edge.uc_label))

        return incoming_edges

    def find_negative_nodes(self):
        # Determine which nodes are negative by looping through the OU-graph and OL-graph
        N = len(self.nodes)
        negative_nodes = [False for _ in range(N)]
        for node in range(N):
            for pred_node in range(N):
                if node in self.edges[pred_node]:
                    # Check ordinary edges
                    weight = self.edges[pred_node][node].weight
                    if weight is not None:
                        if weight < 0:
                            negative_nodes[node] = True
                    # Check upper-case edges
                    weight = self.edges[pred_node][node].uc_weight
                    if weight is not None:
                        if weight < 0:
                            negative_nodes[node] = True
                    # Check lower-case edges
                    weight = self.edges[pred_node][node].lc_weight
                    if weight is not None:
                        if weight < 0:
                            negative_nodes[node] = True

        return negative_nodes




