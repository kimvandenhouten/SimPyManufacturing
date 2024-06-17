from copy import deepcopy
import heapq

from typing import Any, List
from temporal_networks.stnu import STNU, Edge

import general.logger

logger = general.logger.get_logger(__name__)


def convert_to_normal_form(stnu: STNU):
    """
    Convert to normal form STNU according to Morris'14 paper
    Code structure based on repository "Temporal-Networks"
    https://github.com/sudaismoorad/temporal-networks
    :param stnu: regular stnu
    :return: stnu in normal form
    """
    contingent_links = deepcopy(stnu.contingent_links)
    for (node_from, node_to) in contingent_links:
        x = contingent_links[(node_from, node_to)]['lc_value']
        y = contingent_links[(node_from, node_to)]['uc_value']
        if x > 0:
            new_node_index = stnu.add_node(stnu.translation_dict[node_to] + "_act")

            if not stnu.remove_edge(node_from, node_to, type=STNU.LC_LABEL):
                raise ValueError(f"Removing nonexistent LC edge in convert_to_normal_form: {node_from}->{node_to}")
            if not stnu.remove_edge(node_to, node_from, type=STNU.UC_LABEL):
                raise ValueError(f"Removing nonexistent UC edge in convert_to_normal_form: {node_from}->{node_to}")

            stnu.node_types[node_from] = STNU.EXECUTABLE_TP
            stnu.add_tight_constraint(node_from, new_node_index, x)
            stnu.add_contingent_link(new_node_index, node_to, 0, y - x)
            stnu.contingent_links.pop((node_from, node_to), None)

    return stnu


def apply_reduction_rule(network, source, u, v, type_u_source, type_v_u, weight_u_source, weight_v_u, label_u_source,
                         label_v_u, new_distance):
    # TODO: can we make use of input variables cleaner
    # TODO: split up this function into separate functions for each "case" reduction
    new_type = "NotImplemented"
    new_label = "NotImplemented"

    # Upper-case reduction
    # noinspection PySetFunctionToLiteral
    if set([type_v_u, type_u_source]) == set([STNU.UC_LABEL, STNU.ORDINARY_LABEL]):
        logger.debug(f'upper-case reduction')
        new_type = STNU.UC_LABEL
        if type_v_u == STNU.UC_LABEL:
            new_label = label_v_u
        else:
            assert type_u_source == STNU.UC_LABEL
            new_label = label_u_source

    # Lower-case reduction
    elif {type_v_u, type_u_source} == {STNU.LC_LABEL, STNU.ORDINARY_LABEL}:
        logger.debug(f'lower-case reduction')
        new_type = STNU.ORDINARY_LABEL
        if type_u_source == STNU.LC_LABEL:
            assert type_v_u == STNU.ORDINARY_LABEL
            if weight_v_u > 0:
                logger.debug(f'WARNING: lower-case reduction but weight ordinary edge > 0')
            else:
                new_label = None

        else:
            assert type_u_source == STNU.ORDINARY_LABEL and type_v_u == STNU.LC_LABEL
            if weight_u_source > 0:
                logger.debug(f'WARNING: lower-case reduction but weight ordinary edge > 0')
            else:
                new_label = None

    # No-case reduction
    elif (type_v_u, type_u_source) == (STNU.ORDINARY_LABEL, STNU.ORDINARY_LABEL):
        logger.debug(f'no-case reduction')
        new_type = STNU.ORDINARY_LABEL
        new_label = None

    # Cross-case reduction
    elif (type_v_u, type_u_source) == (STNU.LC_LABEL, STNU.UC_LABEL) or (type_v_u, type_u_source) == (
            STNU.UC_LABEL, STNU.LC_LABEL):
        logger.debug(f'cross-case reduction')
        new_type = STNU.UC_LABEL
        if label_v_u == label_u_source:
            logger.debug(f'WARNING: but from the same contingent link')
        if type_v_u == STNU.UC_LABEL:
            if weight_v_u < 0:
                new_label = label_v_u
            else:
                logger.debug(f'WARNING: but x > 0 (UC labeled weight)')
        else:
            if weight_u_source > 0:
                logger.debug(f'WARNING: cross-case but x > 0 (UC labeled weight)')
            else:
                new_label = label_u_source

    if "NotImplemented" in [new_type, new_label]:
        logger.debug(
            f'WARNING: no reduction rule can be applied edge v to u {network.translation_dict[v]} -- {type_v_u} {label_v_u}: {weight_v_u} --> {network.translation_dict[u]}')
        logger.debug(
            f'and u to source edge {network.translation_dict[u]} -- {type_u_source} {label_u_source}: {weight_u_source} --> {network.translation_dict[source]}')
        raise NotImplementedError

    # Label removal
    # TODO: check if we also need the original label removal reduction rule
    if new_type == STNU.UC_LABEL and new_distance >= 0:
        logger.debug(f'label removal applies')
        new_type = STNU.ORDINARY_LABEL
        new_label = None

    return new_distance, v, new_type, new_label


def determine_dc(stnu, dispatchability=False):
    """
    Implements the DC-checking algorithm by Morris'14
    Code structure based on repository "Temporal-Networks"
    https://github.com/sudaismoorad/temporal-networks
    :param stnu: STNU
    :param dispatchability: Boolean
    :return:
    """
    network = deepcopy(stnu)
    network = convert_to_normal_form(network)

    logger.debug(f'network converted to Normal Form')
    logger.debug(network)
    N = len(network.nodes)

    def dc_backprop(source):
        logger.debug(f'START BACKPROP FROM NEW SOURCE {source} ({network.translation_dict[source]})')
        logger.debug(f'at beginning of backprop from {source} prior is {prior}')
        # LINE 00 - 01 FROM DCBACKPROP MORRIS'14 PSEUDOCODE
        # Morris'14: "The whole algorithm terminates if the same source node is repeated in the recursion; thus an
        # infinite recursion is prevented. We will show that this condition occurs if and only if the STNU has a
        # semi - reducible negative cycle."
        logger.debug(f'ancestor {ancestor}')
        if ancestor[source] == source:
            logger.debug(f'ancestor of source {source} is source')
            logger.debug(f'negative cycle encountered')
            return False  # Network is not DC

        # LINE 02 - 03 FROM DCBACKPROP MORRIS'14 PSEUDOCODE
        if prior[source]:
            logger.debug(f'prior backprop call of source {source} terminated')
            return True  # Network can still be DC, but this node has already been checked

        # LINE 04 - 06 FROM DCBACKPROP MORRIS'14 PSEUDOCODE
        # the distances should be set within a dc_backprop call, see pseudocode
        # the distance[i] indicates the distance from i to the source
        distances = [0 if i == source else float("inf") for i in range(N)]
        logger.debug(f'set distances to {distances}')

        # LINE 07 FROM DBACKPROP MORRIS'14 PSEUDOCODE
        # Set up a priority queue. We use heapq from the python standard library, but note that a fibonacci heap
        # guarantees better asymptotic complexity. But because it is more complex, it is in practice often slower than
        # heapq. See for example: https://github.com/danielborowski/fibonacci-heap-python
        # TODO: Check if we need to use a fibonacci heap
        p_queue: list[Any] = []  # Instantiate priority queue

        # LINE 08 - 11 FROM DBBACKPROP MORRIS'14 PSEUDOCODE
        logger.debug(f'find incoming edges to the source')
        # Find incoming edges for this source from OU graph
        incoming_edges = network.get_incoming_ou_edges(source)
        for (weight, pred_node, type, label) in incoming_edges:
            heapq.heappush(p_queue, (weight, pred_node, type, label))
            distances[pred_node] = weight

        logger.debug(f'the incoming OU edges of source {source} ({network.translation_dict[source]}):')
        for (weight, pred_node, type, label) in incoming_edges:
            logger.debug(
                f'edge {network.translation_dict[pred_node]} -- {type} {label}: {weight} --> {network.translation_dict[source]}')
        logger.debug(f'the priority queue four edges to source {network.translation_dict[source]} is now'
                     f' (weight, pred_node, type_pred, label_pred) {p_queue}')

        # LINE 12 - 18
        logger.debug(f'start popping from priority queue (backward prop) ')
        while len(p_queue) > 0:
            (weight_u_source, u, type_u_source, label_u_source) = heapq.heappop(p_queue)
            if weight_u_source > distances[u]:
                # This is a stale heap entry for a node that has been popped before
                logger.debug(f'ignoring stale heap entry {(weight_u_source, u, type_u_source)}')
                continue
            assert weight_u_source == distances[u]
            logger.debug(
                f'pop u {u} ({network.translation_dict[u]}) that is edge {network.translation_dict[u]} -- {type_u_source} {label_u_source}: {weight_u_source} --> {network.translation_dict[source]}')

            if dispatchability:
                # In the extended form of the algorithm both negative and positive edges will be stored along the way
                # TODO: when we set a new edge use edge types as "derived" or "wait"
                if type_u_source == STNU.UC_LABEL or type_u_source == STNU.LC_LABEL:
                    logger.debug(f'we set a labeled edge from from u {u} ({network.translation_dict[u]}) '
                                 f' to source {source} ({network.translation_dict[source]}) with distance {distances[u]}')
                    logger.debug(
                        f'we should set this edge with  with type {type_u_source} and label {label_u_source}')
                    network.set_labeled_edge(node_from=u, node_to=source, distance=distances[u], label=label_u_source,
                                             label_type=type_u_source)

                else:
                    network.set_ordinary_edge(u, source,
                                              distances[u])  # backward prop so u is predecessor of source
                    logger.debug(f'we set an ordinary edge from from u {u} ({network.translation_dict[u]}) '
                                 f' to source {source} ({network.translation_dict[source]}) with distance {distances[u]}')

                if distances[u] >= 0:
                    logger.debug(f'now we continue')
                    continue

            else:
                # LINE 17
                if distances[u] >= 0:
                    logger.debug(f'distance from u {u} ({network.translation_dict[u]}) '
                                 f' to source ({source}) ({network.translation_dict[source]}) is {distances[u]}')
                    network.set_ordinary_edge(u, source, distances[u])  # backward prop so u is predecessor of source
                    logger.debug(f'we set an edge from from u {u} ({network.translation_dict[u]}) '
                                 f' to source {source} ({network.translation_dict[source]}) with distance {distances[u]}')

                    logger.debug(f'now we continue')
                    continue

            # LINE 19 - 21
            # Check if u is a negative node
            logger.debug(f'check if u {u} ({network.translation_dict[u]}) is a negative node')
            if negative_nodes[u]:
                logger.debug(f'u {u} ({network.translation_dict[u]}) is a negative node')
                ancestor[u] = source  # Here, we start backprop(u) for which reason the source is the ancestor of u
                if dc_backprop(u) is False:
                    logger.debug(f'dc backprop of {u} ({network.translation_dict[u]}) is false')
                    return False

            # LINE 22: find InEdges(U)
            logger.debug(F'find incoming edges of u {u} ({network.translation_dict[u]})')
            incoming_edges = network.get_incoming_edges(u)

            logger.debug(f'incoming edges of u {u} ({network.translation_dict[u]})')
            for (weight, pred_node, type, label) in incoming_edges:
                logger.debug(
                    f'edge {network.translation_dict[pred_node]} -- {type} {label}: {weight} --> {network.translation_dict[u]}')
            # LINE 23 - 24
            for (weight_v_u, v, type_v_u, label_v_u) in incoming_edges:  # all nodes from (v) to (u) with weight (weight)
                if weight_v_u < 0:
                    logger.debug(f'the weight from v {v} ({network.translation_dict[v]}) to u {u} '
                                 f'({network.translation_dict[u]}) is negative ({weight_v_u}), so we can continue')
                    continue

                # LINE 25 - 26
                # MORRIS'14: unsuitability occurs if the source edge is unusable for e (they are from the same contingent link)
                # MORRIS It is useful to think of the  distance  calculation as taking place in the projection  where
                # any initial  contingent   link takes  on its maximum  duration and every other contingent link has
                # its minimum. An unsuitable edge does not belong to that  projection.
                # TODO: write unit tests for unsuitability module
                unsuitability = False
                logger.debug(
                    f'here we should check the unsuitability of {(network.translation_dict[v], network.translation_dict[u])}'
                    f' and {(network.translation_dict[u], network.translation_dict[source])}, i.e. whether they '
                    f'are from the same contingent link')
                for (node_from, node_to) in network.contingent_links:
                    if u == node_from and source == node_to and v == node_to:
                        unsuitability = True
                    elif v == node_from and source == node_from and u == node_to:
                        unsuitability = True
                if unsuitability:
                    logger.debug(f'{(network.translation_dict[v], network.translation_dict[u])} and '
                                 f'{(network.translation_dict[u], network.translation_dict[source])}'
                                 f' are from the same contingent link')
                    continue

                # LINE 27 - 35 (numbering in pseudocode is a bit odd)
                new_distance = distances[u] + weight_v_u
                logger.debug(f'{distances}')
                if new_distance < distances[v]:
                    logger.debug(
                        f"Update distance from {network.translation_dict[v]} to {network.translation_dict[source]} "
                        f"using edge value {weight_v_u} and distance {distances[u]}: old value: {distances[v]} and new value {new_distance}")

                    distances[v] = new_distance

                    if dispatchability:
                        new_distance, v, new_type, new_label = apply_reduction_rule(network, source, u, v,
                                                                                    type_u_source, type_v_u,
                                                                                    weight_u_source, weight_v_u,
                                                                                    label_u_source, label_v_u,
                                                                                    new_distance)
                        heapq.heappush(p_queue, (new_distance, v, new_type, new_label))
                    else:
                        # This is the version if you would not have implemented the specific reduction rules
                        heapq.heappush(p_queue, (new_distance, v, "TypeNotImplemented", "LabelNotImplemented"))

                    logger.debug(f'the priority queue four edges to source {network.translation_dict[source]} is now'
                                 f' (weight, pred_node, type_pred, label_pred) {p_queue}')

        logger.debug(f'RETURN TRUE FOR BACKPROP FROM {source} ({network.translation_dict[source]}) BACKPROP TERMINATED')
        # Store that backprop procedure wrt source has terminated, this is needed to prevent infinite loops
        prior[source] = True
        logger.debug(prior)
        # Line 36
        return True

    negative_nodes = network.find_negative_nodes()

    logger.debug(f'negative nodes are {negative_nodes}')
    # to keep track of whether a prior backprop call with this source terminated (global) and defined beforehand
    prior = [False for i in range(N)]

    # Apply backpropagation procedure to all nodes
    for node, negative in enumerate(negative_nodes):
        if negative:
            # To keep track of within the backprop loop started from this source the same source is repeated in the
            # recursion, this can be reset for every backprop call (Kim's assumption), global variable
            ancestor = [float("inf") for i in range(N)]
            if dc_backprop(node) is False:
                logger.debug(f'network after dc-checking \n{network}')
                logger.debug(f'network is not DC')
                if dispatchability:
                    return False, network
                else:
                    return False

    logger.debug(f'network is DC')
    logger.debug(f'network after dc-checking \n{network}')
    if dispatchability:
        return True, network
    else:
        return True
