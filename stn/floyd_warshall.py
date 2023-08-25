import numpy as np


def floyd_warshall(nodes, edges):
    n = len(nodes)
    w = np.full((n, n), np.inf)
    np.fill_diagonal(w, 0)
    for edge in edges:
        u, v, weight = edge
        w[u, v] = weight

    D = [np.full((n, n), np.inf) for _ in range(n + 1)]
    D[0] = w
    for k in range(1, n + 1):
        for i in range(n):
            for j in range(n):
                D[k][i, j] = min(D[k - 1][i, j], D[k - 1][i, k - 1] + D[k - 1][k - 1, j])
    if any(np.diag(D[n]) < 0):
        print("The graph contains negative cycles.")
    return D[n]