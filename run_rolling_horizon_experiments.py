import numpy as np
import copy
import random
from methods.local_search import local_search
from general import evaluator_simpy, Settings
import pandas as pd
import time


def combine_sequences(fixed, i):
    return list(np.concatenate([fixed, i]))


setting_list = []

simulator = "simulator_3"
factory_name = "factory_1"
init = "random"
for seed in range(1, 2):
    for id in range(6, 10):
        for size in [120, 240]:
            for l1 in [0.5]:
                l2 = 1 - l1
                for (k, m) in [(40, 10)]:
                    for search_method in ["local_search"]:
                        decompose = f'rolling_horizon_k={k}_m={m}'
                        instance_name = f'{size}_{id}'
                        setting = Settings(method=f"{decompose}_{search_method}",  instance=f'{size}_{id}_{factory_name}',
                                           size=size, simulator=simulator, stop_criterium="Budget", budget=(size/20)*100,
                                           objective=f'l1={l1}_l2={l2}', init=init, seed=seed, l1=l1, l2=l2, k=k, m=m)
                        setting_list.append(setting)

for seed in range(2, 4):
    for id in range(1, 10):
        for size in [120, 240]:
            for l1 in [0.5]:
                l2 = 1 - l1
                for (k, m) in [(40, 10)]:
                    for search_method in ["local_search"]:
                        decompose = f'rolling_horizon_k={k}_m={m}'
                        instance_name = f'{size}_{id}'
                        setting = Settings(method=f"{decompose}_{search_method}",  instance=f'{size}_{id}_{factory_name}',
                                           size=size, simulator=simulator, stop_criterium="Budget", budget=(size/20)*100,
                                           objective=f'l1={l1}_l2={l2}', init=init, seed=seed, l1=l1, l2=l2, k=k, m=m)
                        setting_list.append(setting)

for setting in setting_list:
    start = time.time()
    file_name = setting.make_file_name()
    instance = pd.read_pickle(f"factory_data/instances/instance_{setting.instance}.pkl")

    fixed = []
    # Important, the f_eval considers the previously solved subinstances
    f_eval = lambda x, i: evaluator_simpy(plan=instance, sequence=combine_sequences(fixed, x), setting=setting,
                                          sim_time=setting.size*300000, printing=False)

    k = setting.k
    m = setting.m
    n = setting.size
    productionplan = list(range(0, n))
    nr_iterations = n/m
    budget_per_iteration = round(setting.budget/nr_iterations)

    for i in range(0, round(nr_iterations)):
        x = copy.copy(productionplan[i*m:i*m+k])
        print(f'To optimize is {x}')
        nr_iterations, best_sequence = local_search(n=n, f_eval=f_eval, stop_criterium="Budget",
                                                    budget=budget_per_iteration,  printing=False, write=False, init=x)
        print(best_sequence)
        productionplan[i*m:i*m+k] = copy.copy(best_sequence)
        fixed = productionplan[0: (i+1) * m]
        print(f'We now fixed {fixed}')

    if setting.simulator == "simulator_1":
        from classes.simulator_1 import Simulator
    if setting.simulator == "simulator_2":
        from classes.simulator_2 import Simulator
    if setting.simulator == "simulator_3":
        from classes.simulator_3 import Simulator
    simulator = Simulator(instance, printing=False)
    makespan, lateness = simulator.simulate(SIM_TIME=setting.size*300000, RANDOM_SEED=setting.seed, write=True,
                                             output_location=f"results/resource_usage/{file_name}.csv")
    results = pd.DataFrame()
    results['Makespan'] = [makespan]
    results['Lateness'] = [lateness]
    results['Time'] = [time.time() - start]
    results['Fitness'] = [setting.l1 * makespan + setting.l2 * lateness]
    results['Sequence'] = [productionplan]
    results['Best_fitness'] = [setting.l1 * makespan + setting.l2 * lateness]
    results['Best_sequence'] = [productionplan]
    results.to_csv(f'results/{file_name}.txt', header=True, index=False)

