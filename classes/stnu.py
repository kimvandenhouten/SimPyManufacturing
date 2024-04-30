from bs4 import BeautifulSoup, Tag
from classes.classes import ProductionPlan, Product
from classes.general import get_logger
import re
import numpy as np

logger = get_logger(__name__)

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
    ORIGIN_NAME = "ORIGIN"
    HORIZON_NAME = "HORIZON"
    nodes: set[int]
    edges: dict[int, dict[int, float]]
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
        self.node_types = [STNU.EXECUTABLE_TP, STNU.EXECUTABLE_TP] if origin_horizon else []
        self.edges = {node: {} for node in self.nodes}

        self.contingent_links = {}
        self.labels = {}

        # We use indices for the nodes in the network
        self.index = max(self.nodes) + 1 if origin_horizon else 0

        # We keep track of two translation dictionaries to connect indices to the events
        self.translation_dict = {self.ORIGIN_IDX: self.ORIGIN_NAME, self.HORIZON_IDX: self.HORIZON_NAME} if origin_horizon else {}
        self.translation_dict_reversed = {self.ORIGIN_NAME: self.ORIGIN_IDX, self.HORIZON_NAME: self.HORIZON_IDX} if origin_horizon else {}

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
    def from_rcpsp_instance(cls, durations, needs, capacity, successors):

        stnu = cls(origin_horizon=False)
        for task, duration in enumerate(durations):
            task_start = stnu.add_node(f'{task}_{STNU.EVENT_START}')
            task_finish = stnu.add_node(f'{task}_{STNU.EVENT_FINISH}')
            if duration == 0:
                stnu.add_tight_constraint(task_start, task_finish, 0)
            else:
                lower_bound = int(max(0, duration - np.sqrt(duration)))
                upper_bound = int(duration + np.sqrt(duration))
                stnu.add_contingent_link(task_start, task_finish, lower_bound, upper_bound)

        for (task, task_successors) in enumerate(successors):
            for suc in task_successors:
                i_idx = stnu.translation_dict_reversed[f'{task}_{STNU.EVENT_FINISH}']
                j_idx = stnu.translation_dict_reversed[f'{suc}_{STNU.EVENT_START}']
                stnu.set_ordinary_edge(j_idx, i_idx, 0)

        return stnu

    @classmethod
    def from_rcpsp_max_instance(cls, durations, temporal_constraints, sink_source=1):
        stnu = cls(origin_horizon=False)
        for task, duration in enumerate(durations):
            task_start = stnu.add_node(f'{task}_{STNU.EVENT_START}')

            if duration == 0 and sink_source == 1:
                logger.debug(f'This is a sink/source node from RCPSP/max, we add only a start event')
                #stnu.add_tight_constraint(task_start, task_finish, 0)
                #stnu.set_ordinary_edge(task_finish, task_start, 0)
            elif duration == 0 and sink_source == 2:
                logger.debug(f'This is a sink/source node from RCPSP/max, we add both a start event and a finish event')
                task_finish = stnu.add_node(f'{task}_{STNU.EVENT_FINISH}')
                stnu.add_tight_constraint(task_start, task_finish, 0)
            else:
                task_finish = stnu.add_node(f'{task}_{STNU.EVENT_FINISH}')
                lower_bound = int(max(0, duration - np.sqrt(duration)))
                upper_bound = int(duration + np.sqrt(duration))
                stnu.add_contingent_link(task_start, task_finish, lower_bound, upper_bound)

        for (pred, lag, suc) in temporal_constraints:
            i_idx = stnu.translation_dict_reversed[f'{pred}_{STNU.EVENT_START}']
            j_idx = stnu.translation_dict_reversed[f'{suc}_{STNU.EVENT_START}']
            # FIXME: check if this is correct
            stnu.set_ordinary_edge(j_idx, i_idx, -lag)

        return stnu

    @classmethod
    def from_production_plan(cls, production_plan: ProductionPlan, max_time_lag=True, origin_horizon=True) -> 'STNU':
        def get_name(product: Product, activity_id: int, event_type: str):
            """
            Return a unique string representation of the given product, activity, and event type.
            """
            return f"{product.product_index}_{activity_id}_{event_type}"

        stnu = cls(origin_horizon=origin_horizon)
        for product in production_plan.products:
            for activity in product.activities:
                # Add nodes that refer to start and end of activity
                a_start = stnu.add_node(get_name(product, activity.id, cls.EVENT_START))
                a_finish = stnu.add_node(get_name(product, activity.id, cls.EVENT_FINISH))

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
                i_idx = stnu.translation_dict_reversed[get_name(product, i, cls.EVENT_START)]
                j_idx = stnu.translation_dict_reversed[get_name(product, j, cls.EVENT_START)]

                # TODO: make sure that the simulator - operator also works when max_time_lag = True
                if max_time_lag:
                    if max_lag is not None:
                        stnu.add_interval_constraint(i_idx, j_idx, min_lag, max_lag)
                    else:
                        stnu.set_ordinary_edge(j_idx, i_idx, -min_lag)
                else:
                    stnu.set_ordinary_edge(j_idx, i_idx, -min_lag)
        return stnu

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

            # FIXME: is this a problem?
            #if value and labeled_value:
                #raise ValueError(f"Edge {edge_id} has both unlabeled and labeled value")
            if value:
                value = value.text.strip()
                if edge_type not in ('requirement', 'derived'):
                    raise ValueError(f"Unexpected edge type {edge_type} for unlabeled edge {edge_id}")
                try:
                    stnu.set_ordinary_edge(node_from, node_to, int(value))
                except ValueError:
                    raise ValueError(f"Unexpected value {value} for requirement edge {edge_id}")
            elif labeled_value:
                labeled_value = labeled_value.text.strip()
                if edge_type not in ('contingent', 'derived'):
                    logger.debug(f"WARNING: Unexpected edge type {edge_type} for labeled edge {edge_id}")
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
                            stnu.contingent_links[(node_to, node_from)] = {'lc_value': 'lb', 'uc_value': -int(m['distance'])}
                    elif int(m['distance']) >= 0 and m['label_type'] == STNU.LC_LABEL:
                        stnu.node_types[node_from] = STNU.ACTIVATION_TP
                        stnu.node_types[node_to] = STNU.CONTINGENT_TP
                        if (node_from, node_to) in stnu.contingent_links:
                            stnu.contingent_links[(node_from, node_to)]["lc_value"] = int(m['distance'])
                        else:
                            stnu.contingent_links[(node_from, node_to)] = {'uc_value': 'ub',
                                                                           'lc_value': int(m['distance'])}
                    else:
                        raise ValueError(f"Unexpected distance and label type combination for contingent edge {edge_id}")
            else:
                raise ValueError(f"Edge {edge_id} has no value")

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

    def sample_contingent_weights(self):
        sample = {}
        for (A, C) in self.contingent_links:
            duration_sample = np.random.randint(self.contingent_links[(A, C)]["lc_value"],
                                                self.contingent_links[(A, C)]["uc_value"])
            sample[C] = duration_sample
        return sample

