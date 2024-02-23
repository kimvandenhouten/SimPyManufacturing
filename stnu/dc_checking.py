from random import randint
from copy import deepcopy

def convert_to_normal_form(stnu):
    """
    Convert to normal form STNU according to Morris'14 paper
    :param stnu: regular stnu
    :return: stnu in normal form
    """
    contingent_links = deepcopy(stnu.contingent_links)
    for (node_from, node_to, x, y) in contingent_links:
        print(node_from, node_to, x, y)
        name = stnu.translation_dict[node_to]
        new_node_name = name + "".join([chr(randint(97,123)) for _ in range(9)])
        stnu.add_node(new_node_name)
        stnu.remove_edge(node_from, node_to)
        stnu.remove_edge(node_to, node_from)
        stnu.add_tight_constraint(node_from, new_node_name, x)
        stnu.add_contingent_link(new_node_name, node_to, 0, y-x)
        stnu.contingent_links.remove((node_from, node_to, x, y))

    return stnu