import json
from classes.classes import ProductionPlan
import numpy as np
import pandas as pd
from stn.floyd_warshall import floyd_warshall

EVENT_START = "start"
EVENT_FINISH = "finish"

instance_size = 10
instance_id = 1
instance_name = f"{instance_size}_{instance_id}_factory_1"
my_productionplan = ProductionPlan(
    **json.load(open('factory_data/development/instances_type_2/instance_' + instance_name + '.json')))

# Set-up nodes and edges
nodes, edges = [], []

# We use indices for the nodes in the network
idx = 0

# We keep track of two translation dictionaries to connect indices to the events
translation_dict = {}
translation_dict_reversed = {}

# We create a simple temporal network only for one product (we select p)
for p in my_productionplan.products:
    for a in p.activities:
        # Add node that refers to start of activity
        a_start = idx
        idx += 1
        nodes.append(a_start)
        translation_dict[a_start] = {"product_index": p.product_index,
                                 "activity_index": a.id,
                                 "event": EVENT_START}
        translation_dict_reversed[(p.product_index, a.id, EVENT_START)] = a_start

        # Add finish node
        a_finish = idx
        idx += 1
        nodes.append(a_finish)
        translation_dict[a_finish] = {"product_index": p.product_index,
                                 "activity_index": a.id,
                                 "event": EVENT_FINISH}
        translation_dict_reversed[(p.product_index, a.id, EVENT_FINISH)] = a_finish

        # Add edge between start and finish with processing time
        edges.append((a_start, a_finish, a.processing_time[0]))
        edges.append((a_finish, a_start, -a.processing_time[0]))

# For every temporal relation in temporal relations, add edge between nodes with min and max lag
for p in my_productionplan.products: # Again we now only do it for product p
    for i, j in p.temporal_relations:
        min_lag = p.temporal_relations[(i, j)].min_lag
        max_lag = p.temporal_relations[(i, j)].max_lag
        i_idx = translation_dict_reversed[(p.product_index, i, EVENT_START)]
        j_idx = translation_dict_reversed[(p.product_index, j, EVENT_START)]
        edges.append((i_idx, j_idx, max_lag))
        edges.append((j_idx, i_idx, -min_lag))

print(f'edges {edges}')

print(f'Apply Floyd-Warshall to STN without resource constraints')
shortest_distances = floyd_warshall(nodes=nodes, edges=edges)

# Load cp output and make production plan and convert to edges that must be added to STN
from construct_resource_edges import construct_resource_edges
cp_output = pd.read_csv(f"results/cp_model/development/instances_type_2/start times {instance_name}.csv")
earliest_start = cp_output.to_dict('records')  # Convert to earliest start times
# Run deterministic simulation with earliest start times and obtain resource predecence constraints
edges_stn = construct_resource_edges(production_plan=my_productionplan, earliest_start=earliest_start)

# Now add the edges with the correct edge weights to the STN
for pred, suc in edges_stn:
    # The finish of the predecessor should precede the start of the successor
    pred_idx = translation_dict_reversed[pred]  # Get translation index from finish of predecessor
    suc_idx = translation_dict_reversed[suc]  # Get translation index from start of successor
    edges.append((pred_idx, suc_idx, np.inf))  # Max difference is infinity
    edges.append((suc_idx, pred_idx, 0))  # Difference is at least 0

print(f'Apply Floyd-Warshall to STN WITH resource constraints')
# Compute shortest distance graph path for this graph
shortest_distances = floyd_warshall(nodes=nodes, edges=edges)
