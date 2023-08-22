import json
from classes.classes import ProductionPlan
import numpy as np

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
p = my_productionplan.products[0]
for a in p.activities:
    # Add node that refers to start of activity
    nodes.append(idx)
    translation_dict[idx] = {"product_index": p.product_index,
                             "activity_index": a.id,
                             "event": "start"}
    translation_dict_reversed[(p.product_index, a.id, "start")] = idx
    idx += 1

    # Add finish node
    nodes.append(idx)
    translation_dict[idx] = {"product_index": p.product_index,
                             "activity_index": a.id,
                             "event": "finish"}
    translation_dict_reversed[(p.product_index, a.id, "finish")] = idx
    idx += 1

    # Add edge between start and finish with processing time
    edges.append((idx - 2, idx - 1, a.processing_time[0]))
    edges.append((idx - 1, idx - 2, -a.processing_time[0]))


print(f'nodes {nodes}')
print(f'edges {edges}')
print(f'translation dict {translation_dict}')
print(f'reversed translation dict {translation_dict_reversed}')

# For every temporal relation in temporal relations, add edge between nodes with min and max lag
p = my_productionplan.products[0] # Again we now only do it for product p
for i, j in p.temporal_relations:
    min_lag = p.temporal_relations[(i, j)].min_lag
    max_lag = p.temporal_relations[(i, j)].max_lag
    i_idx = translation_dict_reversed[(p.product_index, i, "start")]
    j_idx = translation_dict_reversed[(p.product_index, j, "start")]
    edges.append((i_idx, j_idx, max_lag))
    edges.append((j_idx, i_idx, -min_lag))

print(f'edges {edges}')

'''
Floyd-Warshall algorithm
Compute a matrix of shortest-path weights (if the graph contains no negative cycles)
'''

# Compute shortest distance graph path for this graph
n = len(nodes)
w = np.full((n, n), np.inf)
np.fill_diagonal(w, 0)
for edge in edges:
    u, v, weight = edge
    w[u, v] = weight

D = [np.full((n, n), np.inf) for _ in range(n+1)]
D[0] = w
for k in range(1, n+1):
    for i in range(n):
        for j in range(n):
            D[k][i, j] = min(D[k-1][i, j], D[k-1][i, k-1] + D[k-1][k-1, j])
if any(np.diag(D[n]) < 0):
    print("The graph contains negative cycles.")

print(f'The minimum time needed to finish this product is {D[n][0][n-1]}')