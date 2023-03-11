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
    factory_name = "factory_1"
    for simulator in ["simulator_1", "simulator_2", "simulator_3"]:
        for seed in range(1, 2):
            for size in [20]:
                for id in range(1, 2):
                    for method in ["iterated_greedy"]:
                        for init in ["random"]:
                            for (l1, l2) in [(1, 0)]:
                                setting = Settings(method=method, stop_criterium="Budget", budget=10000 * (size / 20),
                                                   instance=f'{size}_{id}_{factory_name}', size=size, simulator=simulator,
                                                   objective=f'l1={l1}_l2={l2}', init=init, seed=seed, l1=l1, l2=l2)
                                settings_list.append(setting)

    for setting in settings_list:
        print(f"Start new instance {setting.instance}")
        # Set seed
        random.seed(setting.seed)
        np.random.seed(setting.seed)
        instance = pd.read_pickle(f"factory_data/instances/instance_{setting.instance}.pkl")
        file_name = setting.make_file_name()

        f_eval = lambda x, i: evaluator_simpy(plan=instance, sequence=x, setting=setting, sim_time=size*1000000,
                                              printing=False)

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
            print(f"The budget was {setting.budget}")
            print(f'The number of evaluations used is {nr_iterations}')

        elif setting.method == "UMM":
            nr_iterations, best_sequence = UMM(n=setting.size, f_eval=f_eval, budget=setting.budget, stop_criterium=setting.stop_criterium,
                                           time_limit=setting.time_limit, writing=True, output_file=f'results/{file_name}.txt')

        # Save output in resource usage table
        if setting.simulator == "SimPyClaimFromBegin":
            from classes import Simulator
        elif setting.simulator == "SimPyClaimOneByOneWithDelay":
            from classes.simulator_3 import Simulator
        else:
            from classes.simulator_2 import Simulator
        plan = pd.read_pickle(f"factory_data/instances/instance_{setting.instance}.pkl")
        sequence = best_sequence
        for SEED in range(1, 2):
            plan.set_sequence(sequence)
            simulator = Simulator(plan, printing=False)
            makespan, tardiness = simulator.simulate(SIM_TIME=300000, RANDOM_SEED=SEED, write=True,
                                                     output_location=f"results/resource_usage/{file_name}.csv")




