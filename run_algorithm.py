import numpy as np
import random
import pandas as pd
from general import Settings, evaluator_simpy
from methods.UMM import UMM
from methods.local_search import local_search
from methods.random_search import random_search
from methods.iterated_greedy import iterated_greedy


if __name__ == '__main__':
    printing = False
    settings_list = []
    for seed in range(0, 10):
        for size in [120, 240]:
            for id in range(1, 10):
                for objective in ["Makespan_Lateness", "Makespan_Average_Lateness"]:
                    for method in ["local_search"]:
                            for init in ["random", "sorted"]:
                                    setting = Settings(method=method, stop_criterium="Budget", budget=100*size,
                                                       instance=f'{size}_{id}', size=size, simulator="SimPy",
                                                       objective=objective, init=init, seed=seed)
                                    settings_list.append(setting)

                    for method in ["random_search"]:
                        setting = Settings(method=method, stop_criterium="Budget", budget=200*size, instance=f'{size}_{id}',
                                           size=size, simulator="SimPy", objective=objective, init="random", seed=seed)
                        settings_list.append(setting)



    for setting in settings_list:
        print(f"Start new instance {setting.instance}")
        # Set seed
        random.seed(setting.seed)
        np.random.seed(setting.seed)
        instance = pd.read_pickle(f"factory_data/instances/instance_{setting.instance}.pkl")
        file_name = setting.make_file_name()

        f_eval = lambda x, i: evaluator_simpy(plan=instance, sequence=x, seed=setting.seed, objective=setting.objective,
                                              sim_time=size*1000000)

        if setting.init == "random":
            init = None
        elif setting.init == "sorted":
            init = [i for i in range(0, setting.size)]

        if setting.method == "local_search":
            nr_iterations, best_sequence = local_search(n=setting.size, stop_criterium=setting.stop_criterium, budget=setting.budget, f_eval=f_eval,
                                                        time_limit=setting.time_limit, output_file=f'results/{file_name}.txt', write=True,
                                                        printing=printing, init=init)
        elif setting.method == "random_search":
            nr_iterations, best_sequence = random_search(n=setting.size, stop_criterium=setting.stop_criterium,
                                                        budget=setting.budget, f_eval=f_eval,
                                                        output_file=f'results/{file_name}.txt', write=True,
                                                        printing=printing)
        elif setting.method == "iterated_greedy":
            nr_iterations, best_sequence = iterated_greedy(n=setting.size, stop_criterium=setting.budget, budget=setting.budget,
                                                           f_eval=f_eval, printing=False, output_file=f'results/{file_name}.txt')

        elif setting.method == "UMM":
            nr_iterations, best_sequence = UMM(n=setting.size, f_eval=f_eval, budget=setting.budget, stop_criterium=setting.stop_criterium,
                                           time_limit=setting.time_limit, writing=True, output_file=f'results/{file_name}.txt')

        evaluator_simpy(plan=instance, sequence=best_sequence, seed=setting.seed, objective=setting.objective, printing=True)




