import json
from classes.classes import ProductionPlan, STN
import numpy as np

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


print(f'nodes {nodes}')
print(f'edges {edges}')
print(f'translation dict {translation_dict}')
print(f'reversed translation dict {translation_dict_reversed}')

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

# The following is equivalent code using the STN class:
stn = STN.from_production_plan(my_productionplan)
matrix = stn.floyd_warshall()

# Check if the output is the same:
print(f'nodes equal? {stn.nodes == nodes}')
print(f'edges equal? {sorted(stn.edges) == sorted(edges)}')
print(f'floyd-warshall equal? {np.array_equal(D[n], matrix)}')
