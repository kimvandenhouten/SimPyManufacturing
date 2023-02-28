import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

budget = 1000
simulator = "SimPy"
for inst in ["10_1", "20_1", "40_1", "60_1"]:
    for method, color in [("random_search", "blue"), ("local_search", "red"), ("iterated_greedy", "green")]:
        fitness = []
        best_fitness = []
        run_time = []
        for seed in range(1, 2):
            data = pd.read_csv(f'results/{method}_simulator={simulator}_budget={budget}_seed={seed}_instance_{inst}.txt')
            fitness.append(data['Best_fitness'].tolist())

        length = len(fitness[0])
        fitness = np.asarray(fitness)
        y = np.mean(fitness, axis=0)
        std = np.std(fitness, axis=0)
        if method == "iterated_greedy":
            x = data["Number of evaluations"]
        else:
            x = [i for i in range(0, length)]
        plt.plot(x, y, color=color, label=method)
        plt.xlabel("Function evaluations")
        plt.ylabel("Makespan")
        plt.legend()
        plt.fill_between(x, y - std, y + std, alpha=0.2, edgecolor='#FF9848', facecolor='#FF9848')
    plt.savefig(f'plots/simulator={simulator}_budget={budget}_seed={seed}_instance_{inst}.png')
    plt.close()
