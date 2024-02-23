from random import randint
from copy import deepcopy
import random

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
        name = stnu.translation_dict[node_to]
        new_node_name = name + "".join([chr(randint(97,123)) for _ in range(9)])
        stnu.add_node(new_node_name)
        stnu.remove_edge(node_from, node_to)
        stnu.remove_edge(node_to, node_from)
        stnu.add_tight_constraint(node_from, new_node_name, x)
        stnu.add_contingent_link(new_node_name, node_to, 0, y-x)
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

    print(f'Network converted to Normal Form')
    print(network)
    N = len(network.nodes)

    def dc_backprop(source):
        print(f'start backprop from {source}')
        print(f'at beginning of backprop from {source} prior is {prior}')
        # LINE 00 - 01 FROM DCBACKPROP MORRIS'14 PSEUDOCODE
        # The whole algorithm terminates if the same source node is repeated in the recursion; thus an infinite
        # recursion is prevented. We will show that this condition occurs if and only if the STNU has a semi - reducible
        # negative cycle.
        print(f'ancestor {ancestor}')
        if ancestor[source] == source:
            print(f'ancestor of source {source} is source')
            return False  # Network is not DC

        # LINE 02 - 03 FROM DCBACKPROP MORRIS'14 PSEUDOCODE
        if prior[source]:
            print(f'prior backprop call of source {source} terminated')
            return True  # Network can still be DC, but this node has already been checked

        # LINE 04 - 06 FROM DCBACKPROP MORRIS'14 PSEUDOCODE
        distances = [0 if i == node else float("inf") for i in range(N)]

        # LINE 07 FROM DBACKPROP MORRIS'14 PSEUDOCODE
        queue = [] # Instantiate priority queue

        # LINE 08 - 11 FROM DBBACKPROP MORRIS'14 PSEUDOCODE
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
                    queue.append(pred_node)

            # Find incoming edges for this source from OL graph
            if source in network.ol_edges[pred_node]:
                weight = network.ol_edges[pred_node][source]
                if pred_node not in incoming_edges:  # If ordinary link the edges is now already in the dictionary
                    incoming_edges[pred_node] = weight
                    # LINE 10
                    distances[pred_node] = weight
                    # LINE 11
                    queue.append(pred_node)
        print(f'The incoming edges of source {source} are {incoming_edges}')
        print(f'The priority queue is now {queue}')

        # LINE 12 - 18
        while len(queue) > 0:
            u = queue.pop(0)
            print(f'pop u {u}')
            if distances[u] >= 0:
                print(f'distance u is {distances[u]}')
                network.set_edge(u, source, distances[u])  # backward prop so u is predecessor of source
                print(f'Now we continue')
                continue

            # LINE 19 - 21
            # Check if u is a negative node
            if negative_nodes[u]:
                print(f'u {u} is a negative node')
                ancestor[u] = source  # Here, we start backprop(u) for which reason the source is the ancestor of u
                if dc_backprop(u) is False:
                    return False

                # LINE 22: find InEdges(U)
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

                print(f'incoming edges of u {u} are {incoming_edges}')
                # LINE 23 - 24
                for v in incoming_edges:  # all nodes from (v) to (u) with weight (weight)
                    weight = incoming_edges[v]
                    if weight < 0:
                        print(f'the weight from v {v} to u {u} is negative ({weight}), so we can continue')
                        continue

                    # LINE 25 - 26
                    # MORRIS'14: unsuitability occurs if the source edge is unusable for e (they are from the same contingent link)
                    # MORRIS It is useful to think of the  distance  calculation as taking place in the projection  where
                    # any initial  contingent   link takes  on its maximum  duration and every other contingent link has
                    # its minimum. An unsuitable edge does not belong to that  projection.
                    # FIXME: check if this edge is unsuitable, this is currently not implemented yet
                    print(network.contingent_links)

                    # LINE 27 - 35 (numbering in pseudocode is a bit odd)
                    new_distance = distances[u] + weight
                    if new_distance < distances[v]:
                        print(f'We found a smaller distance of v {v} to u {u}, which changed from {distances[v]} to {new_distance}')
                        distances[v] = new_distance
                        queue.append(v)
                        print(f'The priority queue is now {queue}')

            print(f'Return true for backprop from {source}, backprop terminated')
            # Store that backprop procedure wrt source has terminated, this is needed to prevent infinite loops
            prior[source] = True
            print(prior)
            # Line 36
            return True

    # Determine which nodes are negative by looping through the OU-graph and OL-graph
    negative_nodes = [False for _ in range(N)]
    for node in range(N):
        for pred_node in range(N):
            if node in network.ou_edges[pred_node]:
                weight = network.ou_edges[pred_node][node]
                if weight < 0:
                    print(f'Node {node} ({network.translation_dict[node]}) is a negative node because it has an incoming OU edge from node {pred_node} with weight {weight}')
                    negative_nodes[node] = True

            if node in network.ol_edges[pred_node]:
                weight = network.ol_edges[pred_node][node]
                if weight < 0:
                    print(f'Node {node} ({network.translation_dict[node]}) is a negative node because it has an incoming OL edge from node {pred_node} with weight {weight}')
                    negative_nodes[node] = True

    print(f'Negative nodes are {negative_nodes}')
    prior = [False for i in range(N)]
    # Apply backpropagation procedure to all nodes
    for node, negative in enumerate(negative_nodes):
        if negative:

            ancestor = [float("inf") for i in range(N)]
            if dc_backprop(node) is False:
                print(f'Network is not DC')
                return False

    print(f'Network is DC')
    return True





