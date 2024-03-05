from random import randint
from copy import deepcopy
import heapq
import classes.general
from typing import Any

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
                new_node_name = name + "".join([chr(randint(97,123)) for _ in range(9)])
                stnu.add_node(new_node_name)
                new_node_index = stnu.translation_dict_reversed[new_node_name]
            stnu.remove_edge(node_from, node_to)
            stnu.remove_edge(node_to, node_from)
            stnu.add_tight_constraint(node_from, new_node_index, x)
            stnu.add_contingent_link(new_node_index, node_to, 0, y-x)
            stnu.contingent_links.remove((node_from, node_to, x, y))

    return stnu


def determine_dc(stnu):
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
        incoming_edges = {}  # I have chosen now to use a dictionary to keep track of the incoming edges
        for pred_node in range(N):
            if source in network.ou_edges[pred_node]:
                weight = network.ou_edges[pred_node][source]
                if pred_node not in incoming_edges:
                    incoming_edges[pred_node] = weight
                    # LINE 10
                    distances[pred_node] = weight # Note that this distance is the distance from pred_node to source
                    # LINE 11
                    heapq.heappush(p_queue, (weight, pred_node))

            # Find incoming edges for this source from OL graph
            if source in network.ol_edges[pred_node]:
                weight = network.ol_edges[pred_node][source]
                if pred_node not in incoming_edges:  # If ordinary link the edges is now already in the dictionary
                    incoming_edges[pred_node] = weight
                    # LINE 10
                    distances[pred_node] = weight
                    # LINE 11
                    heapq.heappush(p_queue, (weight, pred_node))
        logger.debug(f'The incoming edges of source {source} are {incoming_edges}')
        logger.debug(f'The priority queue is now {p_queue}')

        # LINE 12 - 18
        logger.debug(f'START POPPING FROM PRIORITY QUEUE (BACKWARD PROP)')
        while len(p_queue) > 0:
            (d, u) = heapq.heappop(p_queue)
            if d > distances[u]:
                # This is a stale heap entry for a node that has been popped before
                logger.debug(f'Ignoring stale heap entry {(d,u)}')
                continue
            assert d == distances[u]
            logger.debug(f'pop u {u} ({network.translation_dict[u]})')
            if distances[u] >= 0:
                logger.debug(f'distance from u {u} ({network.translation_dict[u]}) '
                             f' to source ({source}) ({network.translation_dict[source]}) is {distances[u]}')
                network.set_edge(u, source, distances[u])  # backward prop so u is predecessor of source
                logger.debug(f'we set a new edge from from u {u} ({network.translation_dict[u]}) '
                             f' to source ({source}) ({network.translation_dict[source]}) is {distances[u]}')
                logger.debug(f'Now we continue')
                continue

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
            incoming_edges = {}  # I have chosen now to use a dictionary to keep track of the incoming edges
            # Find incoming edges of node u from OU graph
            for pred_node in range(N):
                if u in network.ou_edges[pred_node]:
                    weight = network.ou_edges[pred_node][u]
                    if pred_node not in incoming_edges:
                        incoming_edges[pred_node] = weight

                # Find incoming edges of node u from OL graph
                if u in network.ol_edges[pred_node]:
                    weight = network.ol_edges[pred_node][u]
                    if pred_node not in incoming_edges:  # If ordinary link the edges is now already in the dictionary
                        incoming_edges[pred_node] = weight

            logger.debug(f'incoming edges of u {u} ({network.translation_dict[u]}) are {incoming_edges}')
            # LINE 23 - 24
            for v in incoming_edges:  # all nodes from (v) to (u) with weight (weight)
                weight = incoming_edges[v]
                if weight < 0:
                    logger.debug(f'the weight from v {v} ({network.translation_dict[v]}) to u {u} '
                                 f'({network.translation_dict[u]}) is negative ({weight}), so we can continue')
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

                # LINE 27 - 35 (numbering in pseudocode is a bit odd)
                new_distance = distances[u] + weight
                if new_distance < distances[v]:
                    logger.debug(f'We found a smaller distance from v {v} ({network.translation_dict[v]})'
                                 f' to source ({network.translation_dict[source]}), which changed from {distances[v]} to {new_distance}')
                    distances[v] = new_distance

                    logger.debug(f'If DISPATCHABILITY is true, add UC edge {network.translation_dict[v]} '
                                 f'to {network.translation_dict[source]} with weight {new_distance}')
                    # TODO: if we want the algorithm to return an EF_STNU we should also keep track of negative edges
                    #  that are found along the way
                    heapq.heappush(p_queue, (new_distance, v))
                    logger.debug(f'The priority queue is now {p_queue}')

        logger.debug(f'Return true for backprop from {source}, backprop terminated')
        # Store that backprop procedure wrt source has terminated, this is needed to prevent infinite loops
        prior[source] = True
        logger.debug(prior)
        # Line 36
        return True

    # Determine which nodes are negative by looping through the OU-graph and OL-graph
    negative_nodes = [False for _ in range(N)]
    for node in range(N):
        for pred_node in range(N):
            if node in network.ou_edges[pred_node]:
                weight = network.ou_edges[pred_node][node]
                if weight < 0:
                    logger.debug(f'Node {node} ({network.translation_dict[node]}) is a negative node because it has an incoming OU edge from node {pred_node} with weight {weight}')
                    negative_nodes[node] = True

            if node in network.ol_edges[pred_node]:
                weight = network.ol_edges[pred_node][node]
                if weight < 0:
                    logger.debug(f'Node {node} ({network.translation_dict[node]}) is a negative node because it has an incoming OL edge from node {pred_node} with weight {weight}')
                    negative_nodes[node] = True

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
    return True





