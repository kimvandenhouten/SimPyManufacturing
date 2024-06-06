import numpy as np

# Set-up nodes and edges
nodes, edges = [], []

# We use indices for the nodes in the network
nodes = [1, 2 , 3 ,4]
edges = [(1, 2, 3), (2, 1, 8),
         (1, 4, 7), (4, 1, 2),
         (3, 1, 5), (3, 4, 1),
         (2, 3, 2)]

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
    w[u-1, v-1] = weight
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
print(f'The minimum time needed to finish this product is {D[n][0][n-1]}')