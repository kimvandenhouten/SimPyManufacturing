from random import randint
from copy import deepcopy
import heapq
import classes.general
from typing import Any, List
from classes.stnu import STNU, Edge
logger = classes.general.get_logger()


def convert_to_normal_form(stnu):
    """
    Convert to normal form STNU according to Morris'14 paper
    Code structure based on repository "Temporal-Networks"
    https://github.com/sudaismoorad/temporal-networks
    :param stnu: regular stnu
    :return: stnu in normal form
    """
    contingent_links = deepcopy(stnu.contingent_links)
    for (node_from, node_to, x, y) in contingent_links:
        if x > 0:
            name = stnu.translation_dict[node_to]
            # FIXME: this is quite an ugly implementation to distinguish between tuple and str descriptions
            if isinstance(name, tuple):
                new_node_name = "activation".join([chr(randint(97,123)) for _ in range(3)])
                (prod, act, event) = name
                stnu.add_node(prod, act, new_node_name)
                new_node_index = stnu.translation_dict_reversed[(prod, act, new_node_name)]
            else:
                new_node_name = name + "".join([chr(randint(97, 123)) for _ in range(9)])
                stnu.add_node(new_node_name)
                new_node_index = stnu.translation_dict_reversed[new_node_name]
            stnu.remove_edge(node_from, node_to, type=STNU.LC_LABEL)
            stnu.remove_edge(node_to, node_from, type=STNU.UC_LABEL)
            stnu.add_tight_constraint(node_from, new_node_index, x)
            stnu.add_contingent_link(new_node_index, node_to, 0, y-x)
            stnu.contingent_links.remove((node_from, node_to, x, y))

    return stnu


def determine_dc(stnu, dispatchability=True):
    """
    Implements the DC-checking algorithm by Morris'14
    Code structure based on repository "Temporal-Networks"
    https://github.com/sudaismoorad/temporal-networks
    :param stnu:
    :return:
    """
    network = deepcopy(stnu)
    network = convert_to_normal_form(network)

    logger.debug(f'Network converted to Normal Form')
    logger.debug(network)
    N = len(network.nodes)

    def dc_backprop(source):
        logger.debug(f'start backprop from {source}')
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
        distances = [0 if i == node else float("inf") for i in range(N)]

        # LINE 07 FROM DBACKPROP MORRIS'14 PSEUDOCODE
        # Set up a priority queue. We use heapq from the python standard library, but note that a fibonacci heap
        # guarantees better asymptotic complexity. But because it is more complex, it is in practice often slower than
        # heapq. See for example: https://github.com/danielborowski/fibonacci-heap-python
        # TODO: Check if we need to use a fibonacci heap
        p_queue: list[Any] = []   # Instantiate priority queue

        # LINE 08 - 11 FROM DBBACKPROP MORRIS'14 PSEUDOCODE
        logger.debug(f'FIND INCOMING EDGES TO THE SOURCE')
        # Find incoming edges for this source from OU graph
        incoming_edges = network.get_incoming_ou_edges(source)
        for (weight, pred_node, type, label) in incoming_edges:
            heapq.heappush(p_queue, (weight, pred_node, type, label))
            distances[pred_node] = weight

        logger.debug(f'The incoming OU edges of source {source} are {incoming_edges}')
        logger.debug(f'The priority queue is now {p_queue}')

        # LINE 12 - 18
        logger.debug(f'START POPPING FROM PRIORITY QUEUE (BACKWARD PROP)')
        while len(p_queue) > 0:
            (weight_u_source, u, type_u_source, label_u_source) = heapq.heappop(p_queue)
            if weight_u_source > distances[u]:
                # This is a stale heap entry for a node that has been popped before
                logger.debug(f'Ignoring stale heap entry {(weight_u_source, u, type_u_source)}')
                continue
            assert weight_u_source == distances[u]
            logger.debug(f'pop u {u} ({network.translation_dict[u]})')
            if distances[u] >= 0:
                logger.debug(f'distance from u {u} ({network.translation_dict[u]}) '
                             f' to source ({source}) ({network.translation_dict[source]}) is {distances[u]}')

                # FIXME: here we should properly make a new edge
                # TODO: first check if this edge object already exists
                # TODO: check which reduction rule applies based on the predecessor edge and source edge
                # TODO: add the correct edge with the correct label
                # LINE 17
                network.set_ordinary_edge(u, source, distances[u])  # backward prop so u is predecessor of source

                logger.debug(f'we set a new edge from from u {u} ({network.translation_dict[u]}) '
                             f' to source ({source}) ({network.translation_dict[source]}) is {distances[u]}')
                logger.debug(f'Now we continue')
                continue

            # TODO: also insert edge if it is negative if we want to implement dispatchablility (return extended form)

            # LINE 19 - 21
            # Check if u is a negative node
            logger.debug(f'CHECK IF U {u} ({network.translation_dict[u]}) IS A NEGATIVE NODE')
            if negative_nodes[u]:
                logger.debug(f'u {u} ({network.translation_dict[u]}) is a negative node')
                ancestor[u] = source  # Here, we start backprop(u) for which reason the source is the ancestor of u
                if dc_backprop(u) is False:
                    logger.debug(f'dc backprop of {u} ({network.translation_dict[u]}) is false')
                    return False

            # LINE 22: find InEdges(U)
            logger.debug(F'FIND INCOMING EDGES OF U {u} ({network.translation_dict[u]})')

            incoming_edges = network.get_incoming_edges(u)

            logger.debug(f'incoming edges of u {u} ({network.translation_dict[u]}) are {incoming_edges}')
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
                logger.debug(f'CHECK UNSUITABILITY')
                unsuitability = False
                logger.debug(f'here we should check the unsuitability of {(network.translation_dict[v], network.translation_dict[u])}'
                             f' and {(network.translation_dict[u], network.translation_dict[source])}, i.e. whether they '
                             f'are from the same contingent link')
                for (node_from, node_to, x, y) in network.contingent_links:
                    if u == node_from and source == node_to and v == node_to:
                        unsuitability = True
                    elif v == node_from and source == node_from and u == node_to:
                        unsuitability = True
                if unsuitability:
                    logger.debug(f'{(network.translation_dict[v], network.translation_dict[u])} and '
                          f'{(network.translation_dict[u], network.translation_dict[source])}'
                          f' are from the same contingent link')
                    continue

                # FIXME Comment Kim: this is the part of the code where we should keep track of which labels belong
                #  to possible new edges. If we properly use heapq.heappush(p_queue, (new_distance, v, new_type, new_label))
                #  we can use that while popping from the priority queue and executing LINE 17 from the morris'14 pseudo
                #  currently we don't cover all possible reduction cases or have a mistake in our normal form transformation
                #  perhaps we can try to understand this with the example in test_uncontrollable from morris_14_unit_test.py
                # LINE 27 - 35 (numbering in pseudocode is a bit odd)
                new_distance = distances[u] + weight_v_u
                if new_distance < distances[v]:
                    logger.debug(f'We found a smaller distance from v {v} ({network.translation_dict[v]})'
                                 f' to source ({network.translation_dict[source]}), which changed from {distances[v]} to {new_distance}')
                    distances[v] = new_distance

                    if (type_v_u, type_u_source) == (STNU.UC_LABEL, STNU.ORDINARY_LABEL) or (type_v_u, type_u_source) == (STNU.ORDINARY_LABEL, STNU.UC_LABEL):
                        logger.debug(f'Upper-case Reduction')
                        new_type = STNU.UC_LABEL
                        if type_v_u == STNU.UC_LABEL:
                            new_label = label_v_u
                        else:
                            new_label = label_u_source
                    elif (type_v_u, type_u_source) == (STNU.LC_LABEL, STNU.ORDINARY_LABEL) or (type_v_u, type_u_source) == (STNU.ORDINARY_LABEL, STNU.LC_LABEL):
                        logger.debug(f'Lower-case Reduction')
                        new_type = STNU.LC_LABEL
                        if type_v_u == STNU.LC_LABEL:
                            new_label = label_v_u
                        else:
                            new_label = label_u_source
                    elif (type_v_u, type_u_source) == (STNU.ORDINARY_LABEL, STNU.ORDINARY_LABEL):
                        logger.debug(f'No-case Reduction')
                        new_type = STNU.ORDINARY_LABEL
                        new_label = None

                    elif (type_v_u, type_u_source) == (STNU.LC_LABEL, STNU.UC_LABEL) or (type_v_u, type_u_source) == (STNU.UC_LABEL, STNU.LC_LABEL):
                        logger.debug(f'Cross-case Reduction')
                        new_type = STNU.UC_LABEL
                        if type_v_u == STNU.UC_LABEL:
                            new_label = label_v_u
                        else:
                            new_label = label_u_source
                    else:
                        logger.debug(f'Reduction rule not implemented yet')
                        logger.debug(f'type v_u {type_v_u} with label {label_v_u} type u source {type_u_source} with label {label_u_source}')
                        raise NotImplementedError

                    heapq.heappush(p_queue, (new_distance, v, new_type, new_label))
                    logger.debug(f'The priority queue is now {p_queue}')

        logger.debug(f'Return true for backprop from {source}, backprop terminated')
        # Store that backprop procedure wrt source has terminated, this is needed to prevent infinite loops
        prior[source] = True
        logger.debug(prior)
        # Line 36
        return True

    negative_nodes = network.find_negative_nodes()

    logger.debug(f'Negative nodes are {negative_nodes}')
    # to keep track of whether a prior backprop call with this source terminated (global) and defined beforehand
    prior = [False for i in range(N)]

    # Apply backpropagation procedure to all nodes
    for node, negative in enumerate(negative_nodes):
        if negative:
            # To keep track of within the backprop loop started from this source the same source is repeated in the
            # recursion, this can be reset for every backprop call (Kim's assumption), global variable
            ancestor = [float("inf") for i in range(N)]
            if dc_backprop(node) is False:
                logger.debug(f'Network after dc-checking \n{network}')
                logger.debug(f'Network is not DC')
                return False

    logger.debug(f'Network is DC')
    logger.debug(f'Network after dc-checking \n{network}')
    if dispatchability:
        return network
    else:
        return True





