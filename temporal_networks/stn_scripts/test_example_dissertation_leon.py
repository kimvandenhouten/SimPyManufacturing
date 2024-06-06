import numpy as np

# Set-up nodes and edges
nodes, edges = [], []

# We use indices for the nodes in the network
nodes = [0, 1, 2, 3, 4, 5]
translation_dict = {0: "z", 1: "e1", 2: "e3", 3: "c1", 4: "c2", 5: "b"}
edges = [(1, 0, 0), (3, 0, 0),
         (1, 2, 5), (2, 1, -4),
         (3, 4, 3), (4, 3, -2),
         (2, 5, 8), (5, 2, 0),
         (4, 5, 5), (5, 4, 0),
         (0, 5, 15)]

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

print(w)
D = [np.full((n, n), np.inf) for _ in range(n+1)]
D[0] = w
for k in range(1, n+1):
    for i in range(n):
        for j in range(n):
            D[k][i, j] = min(D[k-1][i, j], D[k-1][i, k-1] + D[k-1][k-1, j])
if any(np.diag(D[n]) < 0):
    print("The graph contains negative cycles.")
print(D[n])

print(f'A valid schedule is {D[n][0]}')
