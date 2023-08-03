import numpy as np
import random
import pandas as pd
from classes.general import Settings, evaluator_simpy
from methods.local_search import local_search
from methods.random_search import random_search
from methods.iterated_greedy import iterated_greedy


if __name__ == '__main__':
    printing = False
    save_resource_usage = False
    settings_list = []
    data_table = []
    factory_name = "factory_1"
    for simulator in ["simulator_3"]:
        for size in [20, 40]:
            for seed in [4]:
                budget = (size/20)*200
                for id in range(1, 10):
                    for l1 in [0.5]:
                        l2 = 1 - l1
                        for method in ["iterated_greedy"]:
                            for init in ["random", 'sorted']:
                                setting = Settings(method=method, stop_criterium="Budget", budget=budget,
                                                   instance=f'{size}_{id}_{factory_name}', size=size, simulator=simulator,
                                                   objective=f'l1={l1}_l2={l2}', init=init, seed=seed, l1=l1, l2=l2)
                                settings_list.append(setting)

        for size in [20, 120, 240]:
            for seed in [4]:
                budget = (size/20)*200
                for id in range(1, 10):
                    for l1 in [0.5]:
                        l2 = 1 - l1
                        for method in ["local_search"]:
                            for init in ["random", 'sorted']:
                                setting = Settings(method=method, stop_criterium="Budget", budget=budget,
                                                   instance=f'{size}_{id}_{factory_name}', size=size, simulator=simulator,
                                                   objective=f'l1={l1}_l2={l2}', init=init, seed=seed, l1=l1, l2=l2)
                                settings_list.append(setting)
                        for method in ["random_search"]:
                            for init in ["random"]:
                                setting = Settings(method=method, stop_criterium="Budget", budget=budget,
                                                   instance=f'{size}_{id}_{factory_name}', size=size, simulator=simulator,
                                                   objective=f'l1={l1}_l2={l2}', init=init, seed=seed, l1=l1, l2=l2)
                                settings_list.append(setting)

    for setting in settings_list:
        print(f"Start new instance {setting.instance}")
        # Set seed
        random.seed(setting.seed)
        np.random.seed(setting.seed)
        instance = pd.read_pickle(f"factory_data/instances_legacy/instances_new/instance_{setting.instance}.pkl")
        file_name = setting.make_file_name()

        f_eval = lambda x, i: evaluator_simpy(plan=instance, sequence=x, setting=setting, sim_time=size*1000000,
                                              printing=False)

        if setting.init == "random":
            init = None
        elif setting.init == "sorted":
            init = [i for i in range(0, setting.size)]

        if setting.method == "local_search":
            nr_iterations, best_sequence = local_search(n=setting.size, stop_criterium=setting.stop_criterium, budget=setting.budget, f_eval=f_eval,
                                                        time_limit=setting.time_limit, output_file=f'results/results_algorithm/{file_name}.txt', write=True,
                                                        printing=printing, init=init)
        elif setting.method == "random_search":
            nr_iterations, best_sequence = random_search(n=setting.size, stop_criterium=setting.stop_criterium,
                                                        budget=setting.budget, f_eval=f_eval,
                                                        output_file=f'results/results_algorithm/{file_name}.txt', write=True,
                                                        printing=printing)
        elif setting.method == "iterated_greedy":
            nr_iterations, best_sequence = iterated_greedy(n=setting.size, init=init, stop_criterium=setting.budget, budget=setting.budget,
                                                           f_eval=f_eval, printing=False, output_file=f'results/results_algorithm/{file_name}.txt')

        # Save output in resource usage table
        if setting.simulator == "simulator_1":
            from classes.simulator_1 import Simulator
        elif setting.simulator == "simulator_2":
            from classes.simulator_2 import Simulator
        elif setting.simulator == "simulator_3":
            from classes.simulator_3 import Simulator
        else:
            print('WARNING: simulator not defined')

        plan = pd.read_pickle(f"factory_data/instances_legacy/instances_new/instance_{setting.instance}.pkl")
        sequence = best_sequence
        plan.set_sequence(sequence)
        simulator = Simulator(plan, printing=False)
        makespan, lateness = simulator.simulate(sim_time=size*1000000, random_seed=setting.seed, write=True,
                                                         output_location=f"results/resource_usage/{file_name}.csv")

        data_table.append({"instance": setting.instance,
                           "method": setting.method,
                           "budget": setting.budget,
                           "fitness": setting.l1 * makespan + setting.l2 * lateness,
                           "makespan": makespan,
                           "lateness": lateness,
                           "costs": 0.5 * makespan + 0.5 * lateness,
                           "l1": setting.l1,
                           "l2": setting.l2,
                           "seed": setting.seed})
        dataframe = pd.DataFrame(data_table)
        dataframe.to_csv("results/summary_tables/global search.csv")




