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



def dc_checking(stnu):
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

    def DCbackprop(source):
        # TODO: if ancestor call with same source return false

        # TODO: if prior terminated call with same source return true

        # TODO: implement backward propagation procedure
        random_int = random.randint(0, 1)
        print(random_int)
        if random_int == 0:
            return False
        else:
            return True

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

    for node, negative in enumerate(negative_nodes):
        if negative:
            if DCbackprop(node) is False:
                print(f'Network is not DC')
                return False

    print(f'Network is DC')
    return True





