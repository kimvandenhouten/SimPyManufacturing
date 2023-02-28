from general import Settings
import pandas as pd

results = []
settings_list = []
for size in [120, 240]:
    for id in range(1, 6):
        instance = f'{size}_{id}'
        for method in ["random_search", "local_search", 'iterated_greedy']:
            setting = Settings(method=method, instance=instance, stop_criterium="Budget", budget=400*(size/20), simulator="SimPy")
            settings_list.append(setting)

for setting in settings_list:
    # determine file name
    file_name = setting.make_file_name()

    # read in best sequence
    data = pd.read_csv(f'results/{file_name}.txt')
    #data_x = data["Best_sequence"].tolist()[-1]
    #data_x = data_x.replace("[ ", "[")
    #data_x = data_x.replace("  ", " ")
    #data_x = data_x.replace(".", "")
    #data_x = [int(i) + 1 for i in data_x]
    data_y = data["Best_fitness"].tolist()[-1]

    if setting.stop_criterium == "Time":
        runtime = setting.time_limit
        total_budget = data.shape[0]
    elif setting.stop_criterium == "Budget":
        runtime = data["Time"].tolist()[-1]
        total_budget = setting.budget

    print(f'The best sequence for instance {setting.instance} using {setting.method} is {data_x} with fitness {data_y}')
    results.append({"simulator": setting.simulator,
                    "instance": setting.instance,
                    "method": setting.method,
                    "stop_criterium": setting.stop_criterium,
                    "time": runtime,
                    "budget": total_budget,
                    "seed": setting.seed,
                    "fitness": data_y})

results = pd.DataFrame(results)
results.to_csv("results/summary_table.csv")


