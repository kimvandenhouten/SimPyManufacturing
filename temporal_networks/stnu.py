import enum
import re

import numpy as np
from bs4 import BeautifulSoup

import general.logger

logger = general.logger.get_logger(__name__)


class SampleStrategy(enum.Enum):
    EARLY_EXECUTION_STRATEGY = enum.auto()
    LATE_EXECUTION_STRATEGY = enum.auto()
    RANDOM_EXECUTION_STRATEGY = enum.auto()


class Edge:
    UC_LABEL = "UC"
    LC_LABEL = "LC"
    ORDINARY_LABEL = "ORDINARY"

    node_from: int
    node_to: int

    def __init__(self, node_from: int, node_to: int):
        self.node_from = node_from
        self.node_to = node_to
        self.weight = None
        self.uc_label = None
        self.uc_weight = None
        self.lc_label = None
        self.lc_weight = None

    def set_labeled_weight(self, labeled_weight, label, label_type):
        if label_type == self.UC_LABEL:
            if self.uc_weight is not None:
                logger.warning(f'WARNING: we are overwriting UC edge with weight {self.uc_weight} and label {self.uc_label}')
            self.uc_weight = labeled_weight
            self.uc_label = label
        elif label_type == self.LC_LABEL:
            if self.lc_weight is not None:
                logger.warning(
                    f'WARNING: we are overwriting LC edge with weight {self.lc_weight} and label {self.lc_label}')
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
    ORIGIN_NAME = "ORIGIN"
    HORIZON_NAME = "HORIZON"
    nodes: set[int]
    removed_nodes: list[int]
    edges: dict[int, dict[int, Edge]]
    index: int
    translation_dict: dict[int, str]
    translation_dict_reversed: dict[str, int]
    EXECUTABLE_TP = "EXECUTABLE_TP"
    ACTIVATION_TP = "ACTIVATION_TP"
    CONTINGENT_TP = "CONTINGENT_TP"

    def __init__(self, origin_horizon=True):
        self.origin_horizon = origin_horizon
        # Set-up nodes and edges
        self.nodes = {self.ORIGIN_IDX, self.HORIZON_IDX} if origin_horizon else set()
        self.removed_nodes = []
        self.node_types = [STNU.EXECUTABLE_TP, STNU.EXECUTABLE_TP] if origin_horizon else []
        self.edges = {node: {} for node in self.nodes}

        self.contingent_links = {}
        self.labels = {}

        # We use indices for the nodes in the network
        self.index = max(self.nodes) + 1 if origin_horizon else 0

        # We keep track of two translation dictionaries to connect indices to the events
        self.translation_dict = {self.ORIGIN_IDX: self.ORIGIN_NAME,
                                 self.HORIZON_IDX: self.HORIZON_NAME} if origin_horizon else {}
        self.translation_dict_reversed = {self.ORIGIN_NAME: self.ORIGIN_IDX,
                                          self.HORIZON_NAME: self.HORIZON_IDX} if origin_horizon else {}

        if origin_horizon:
            self.set_ordinary_edge(self.HORIZON_IDX, self.ORIGIN_IDX, 0)

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
    def from_graphml(cls, file_name, origin_horizon=False) -> 'STNU':
        stnu = cls(origin_horizon=False)
        with open(file_name, 'r') as f:
            soup = BeautifulSoup(f, 'xml')
        for node in soup.find_all('node'):
            node_id = node.attrs.get('id', None)
            if not node_id:
                raise ValueError("node without id")
            stnu.add_node(node_id)
        cls.process_graphml_edges(soup, stnu)
        return stnu

    @classmethod
    def process_graphml_edges(cls, soup: BeautifulSoup, stnu: 'STNU'):
        lv_pattern = re.compile(r'(?P<label_type>UC|LC)\((?P<label>\w*)\):(?P<distance>-?\d+)', re.ASCII)
        for edge in soup.find_all('edge'):
            edge_id = edge.attrs.get('id', None)
            if not edge_id:
                raise ValueError("edge without id")
            source = edge.attrs.get('source', None)
            if not source:
                raise ValueError(f"edge {edge_id} has no source")
            node_from = stnu.translation_dict_reversed.get(source, None)
            if node_from is None:
                raise ValueError(f"unknown node {node_from} in edge {edge_id}")
            target = edge.attrs.get('target', None)
            if not target:
                raise ValueError(f"edge {edge_id} has no target")
            node_to = stnu.translation_dict_reversed.get(target, None)
            if node_to is None:
                raise ValueError(f"unknown node {node_to} in edge {edge_id}")

            edge_type = edge.find(key='Type').text.strip()
            value = edge.find(key='Value')
            labeled_value = edge.find(key='LabeledValue')

            if value and labeled_value:
                logger.info(f"Edge {edge_id} has both unlabeled and labeled value")
            if value:
                value = value.text.strip()
                if edge_type not in ('requirement', 'derived'):
                    raise ValueError(f"Unexpected edge type {edge_type} for unlabeled edge {edge_id}")
                try:
                    stnu.set_ordinary_edge(node_from, node_to, int(value))
                except ValueError:
                    raise ValueError(f"Unexpected value {value} for requirement edge {edge_id}")
            if labeled_value:
                labeled_value = labeled_value.text.strip()
                if edge_type not in ('contingent', 'derived'):
                    logger.warning(f"WARNING: Unexpected edge type {edge_type} for labeled edge {edge_id}")
                m = lv_pattern.match(labeled_value)
                if not m:
                    raise ValueError(f"Unexpected value {labeled_value} for {edge_type} edge {edge_id}")
                stnu.set_labeled_edge(node_from, node_to, int(m['distance']), m['label'], m['label_type'])
                if edge_type == "contingent":
                    if int(m['distance']) < 0 and m['label_type'] == STNU.UC_LABEL:
                        stnu.node_types[node_from] = STNU.CONTINGENT_TP
                        stnu.node_types[node_to] = STNU.ACTIVATION_TP
                        if (node_to, node_from) in stnu.contingent_links:
                            stnu.contingent_links[(node_to, node_from)]["uc_value"] = -int(m['distance'])
                        else:
                            stnu.contingent_links[(node_to, node_from)] = {'lc_value': 'lb',
                                                                           'uc_value': -int(m['distance'])}
                    elif int(m['distance']) >= 0 and m['label_type'] == STNU.LC_LABEL:
                        stnu.node_types[node_from] = STNU.ACTIVATION_TP
                        stnu.node_types[node_to] = STNU.CONTINGENT_TP
                        if (node_from, node_to) in stnu.contingent_links:
                            stnu.contingent_links[(node_from, node_to)]["lc_value"] = int(m['distance'])
                        else:
                            stnu.contingent_links[(node_from, node_to)] = {'uc_value': 'ub',
                                                                           'lc_value': int(m['distance'])}
                    else:
                        raise ValueError(
                            f"Unexpected distance and label type combination for contingent edge {edge_id}")
            if not value and not labeled_value:
                raise ValueError(f"Edge {edge_id} has no value and no labeled value")

    def add_node(self, description: str):
        if description in self.translation_dict_reversed:
            raise ValueError(f"Node with description {description} already exists")

        node_idx = self.index
        self.index += 1
        self.nodes.add(node_idx)
        self.node_types.append(STNU.EXECUTABLE_TP)
        self.edges[node_idx] = {}

        self.translation_dict[node_idx] = description
        self.translation_dict_reversed[description] = node_idx

        # This node / event must occur between ORIGIN and HORIZON
        if self.origin_horizon:
            self.set_ordinary_edge(node_idx, self.ORIGIN_IDX, 0)
            self.set_ordinary_edge(self.HORIZON_IDX, node_idx, 0)
        return node_idx

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

    def get_executable_time_points(self):
        return [node for node in self.nodes if self.node_types[node] in (STNU.EXECUTABLE_TP, STNU.ACTIVATION_TP)]

    def get_contingent_time_points(self):
        return [node for node in self.nodes if self.node_types[node] == STNU.CONTINGENT_TP]

    def set_labeled_edge(self, node_from: int, node_to: int, distance: int, label: str, label_type: str):
        if node_to in self.edges[node_from]:
            edge = self.edges[node_from][node_to]
        else:
            edge = Edge(node_from, node_to)

        edge.set_labeled_weight(labeled_weight=distance, label=label, label_type=label_type)
        self.edges[node_from][node_to] = edge

    def set_ordinary_edge(self, node_from: int, node_to: int, distance):
        if node_to in self.edges[node_from]:
            edge = self.edges[node_from][node_to]
        else:
            edge = Edge(node_from, node_to)
        edge.set_weight(weight=distance)
        self.edges[node_from][node_to] = edge

    def remove_edge(self, node_from: int, node_to: int, type):
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

    def add_interval_constraint(self, node_from: int, node_to: int, min_distance, max_distance):
        self.set_ordinary_edge(node_from, node_to, max_distance)
        self.set_ordinary_edge(node_to, node_from, -min_distance)

    def add_tight_constraint(self, node_from: int, node_to: int, distance):
        self.add_interval_constraint(node_from, node_to, distance, distance)

    def add_contingent_link(self, node_from: int, node_to: int, x, y):
        self.node_types[node_from] = STNU.ACTIVATION_TP
        self.node_types[node_to] = STNU.CONTINGENT_TP

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

        self.contingent_links[(node_from, node_to)] = {"lc_value": x, "uc_value": y}

    def get_incoming_edges(self, node_to: int, ordinary=True, uc=True, lc=True):
        """
        :return: all preceding edges of node u
        """
        N = len(self.nodes)
        incoming_edges = []  # I have chosen now to use a dictionary to keep track of the incoming edges
        # Find incoming edges of node u from OU graph
        for pred_node in range(N):
            if node_to in self.edges[pred_node]:
                edge = self.edges[pred_node][node_to]
                if ordinary:
                    if edge.weight is not None:
                        incoming_edges.append((edge.weight, pred_node, STNU.ORDINARY_LABEL, None))
                if uc:
                    if edge.uc_weight is not None:
                        incoming_edges.append((edge.uc_weight, pred_node, STNU.UC_LABEL, edge.uc_label))
                if lc:
                    if edge.lc_weight is not None:
                        incoming_edges.append((edge.lc_weight, pred_node, STNU.LC_LABEL, edge.lc_label))

        return incoming_edges

    def get_outgoing_edges(self, node_from: int, ordinary=True, uc=True, lc=True):
        """
        :param u: node_to
        :return: all preceding edges of node u
        """
        N = len(self.nodes)
        outgoing_edges = []  # I have chosen now to use a dictionary to keep track of the incoming edges
        # Find incoming edges of node u from OU graph
        for suc_node in range(N):
            if suc_node in self.edges[node_from]:
                edge = self.edges[node_from][suc_node]
                if ordinary:
                    if edge.weight is not None:
                        outgoing_edges.append((edge.weight, suc_node, STNU.ORDINARY_LABEL, None))
                if uc:
                    if edge.uc_weight is not None:
                        outgoing_edges.append((edge.uc_weight, suc_node, STNU.UC_LABEL, edge.uc_label))
                if lc:
                    if edge.lc_weight is not None:
                        outgoing_edges.append((edge.lc_weight, suc_node, STNU.LC_LABEL, edge.lc_label))

        return outgoing_edges

    def get_incoming_ou_edges(self, node_to: int):
        # FIXME: this method is not needed anymore, check if it is used and replace with get_incoming_edges(node_to: int)
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

    def get_wait_edges(self):
        """
        :return: all (derived) wait edges of the STNU
        """
        N = len(self.nodes)
        wait_edges = []  # I have chosen now to use a dictionary to keep track of the incoming edges
        # Find incoming edges of node u from OU graph
        for node_from in range(N):
            for node_to in range(N):
                if node_to in self.edges[node_from]:
                    edge = self.edges[node_from][node_to]
                    if edge.uc_weight is not None:
                        node_from_label = self.translation_dict[node_from]
                        node_to_label = self.translation_dict[node_to]
                        if edge.uc_label in (node_from_label, node_to_label):
                            continue
                        else:
                            wait_edges.append((node_from, edge.uc_label, edge.uc_weight, node_to))

        return wait_edges

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

    def sample_contingent_weights(self, strategy: SampleStrategy):
        sample = {}
        for (A, C) in self.contingent_links:
            if strategy == SampleStrategy.RANDOM_EXECUTION_STRATEGY:
                duration_sample = np.random.randint(self.contingent_links[(A, C)]["lc_value"],
                                                    self.contingent_links[(A, C)]["uc_value"])
                sample[C] = duration_sample
            elif strategy == SampleStrategy.LATE_EXECUTION_STRATEGY:
                sample[C] = self.contingent_links[(A, C)]["uc_value"]
            elif strategy == SampleStrategy.EARLY_EXECUTION_STRATEGY:
                sample[C] = self.contingent_links[(A, C)]["lc_value"]
            else:
                raise NotImplemented
        return sample
