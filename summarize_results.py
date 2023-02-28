from general import Settings
import pandas as pd
from classes import Simulator
import numpy as np

results = []
settings_list = []
for size in [120, 240]:
    for id in range(1, 10):
        for method in ["random_search"]:
            for objective in ["Makespan_Lateness", "Makespan_Average_Lateness"]:
                for seed in range(0, 10):
                    setting = Settings(method=method, stop_criterium="Budget", budget=2*size, instance=f'{size}_{id}', size=size, simulator="SimPy",
                                       objective=objective, init="random", seed=seed)
                    settings_list.append(setting)

for size in [120, 240]:
    for id in range(1, 10):
        for method in ["local_search"]:
            for objective in ["Makespan_Lateness", "Makespan_Average_Lateness"]:
                for init in ["random", "sorted"]:
                    for seed in range(0, 10):
                        setting = Settings(method=method, stop_criterium="Budget", budget=200*size, instance=f'{size}_{id}', size=size, simulator="SimPy",
                                           objective=objective, init=init, seed=seed)
                        settings_list.append(setting)

for setting in settings_list:
    # determine file name
    file_name = setting.make_file_name()
    print(file_name)

    # read in best sequence
    data = pd.read_csv(f'results/{file_name}.txt')
    data_x = data["Best_sequence"].tolist()[-1]
    data_x = data_x[1:-1].split(", ")
    data_x = [int(i) for i in data_x]
    sequence = [i + 1 for i in data_x]
    assert len(data_x) == setting.size
    # read in fitness
    data_y = data["Best_fitness"].tolist()[-1]

    # read runtime and fitness evaluations
    if setting.stop_criterium == "Time":
        runtime = setting.time_limit
        total_budget = data.shape[0]
    elif setting.stop_criterium == "Budget":
        runtime = data["Time"].tolist()[-1]
        total_budget = setting.budget

    # evaluate to find all KPIs
    instance = pd.read_pickle(f"factory_data/instances/instance_{setting.instance}.pkl")
    instance.set_sequence(data_x)
    simulator = Simulator(instance, printing=False)
    makespan, tardiness = simulator.simulate(SIM_TIME=10000000000, RANDOM_SEED=setting.seed, write=False)

    print(f'The best sequence for instance {setting.instance} using {setting.method} has fitness {data_y}')
    results.append({"simulator": setting.simulator,
                    "instance": setting.instance,
                    "method": setting.method,
                    "init": setting.init,
                    "objective": setting.objective,
                    "stop_criterium": setting.stop_criterium,
                    "time": round(runtime),
                    "budget": total_budget,
                    "seed": setting.seed,
                    "sequence": sequence,
                    "makespan": makespan,
                    "tardiness": tardiness,
                    "average_tardiness": tardiness/setting.size,
                    "fitness": data_y})

results = pd.DataFrame(results)
results.to_csv("results/summary_table.csv")


