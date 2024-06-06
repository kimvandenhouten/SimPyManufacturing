import copy
import pickle
import numpy as np

# This file is created to experiment with the logic when a STN is not consistent due to a max time lag

# START INFORMATION
# Import snapshot stn
pickle_file_path = "snapshot_stn.pkl"
with open(pickle_file_path, 'rb') as file:
    stn = pickle.load(file)

# Current time simulator
current_time = 272

# Obtain upper bounds from origin to all other nodes
origin_to_ub = stn.shortest_distances[0]
print("Upper bounds from origin to other nodes", origin_to_ub)

# Obtain indices from events that are already fixed
indices_past_events = np.where(np.array(origin_to_ub) <= current_time)[0]
print("Indices of past events", indices_past_events)

# Obtain indices from events that are already fixed
indices_future_events = np.where(np.array(origin_to_ub) > current_time)[0]
print("Indices of future events", indices_future_events)

#TODO: per node gaat het nog niet efficient genoeg,
# probeer per geheel product te verwijderen
product_to_del = 9
nodes_corresponding_to_product = [stn.translation_dict_reversed[key] for key in stn.translation_dict_reversed.keys() if key[0] == product_to_del]
print("Nodes corresponding to product", nodes_corresponding_to_product)

common_values = list(set(nodes_corresponding_to_product) & set(indices_future_events))
print("Common values", common_values)
print(len(common_values),len(nodes_corresponding_to_product))

# Loop through the inputs and apply your function
copy_stn = copy.deepcopy(stn)
print(f'before product delete {len(copy_stn.nodes)} nodes')

for node in common_values:
    copy_stn.remove_node(node)
print(f'after product delete {len(copy_stn.nodes)} nodes')

copy_stn.floyd_warshall()
output = copy_stn.add_interval_constraint(0, 43, 272, 272)
