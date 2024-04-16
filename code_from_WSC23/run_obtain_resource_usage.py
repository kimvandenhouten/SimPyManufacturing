from classes.general import Settings
import pandas as pd
"""
This script can be used to obtain the resource usage of a solution to a problem instance
obtained by one of the search algorithms
"""

results = []
settings_list = []
l1=0.5
l2=0.5
seed=1
setting = Settings(method="local_search", stop_criterium="Budget", budget=200 * (20 / 20),
                   instance=f'20_1_factory_1', size=120, simulator="simulator_3",
                   objective=f'l1={l1}_l2={l2}', init="random", seed=seed, l1=l1, l2=l2)
settings_list.append(setting)

file_name = setting.make_file_name()

for setting in settings_list:
    # determine file name
    if setting.simulator == "simulator_1":
        from classes.simulator_1 import Simulator
    elif setting.simulator == "simulator_2":
        from classes.simulator_2 import Simulator
    elif setting.simulator == "simulator_3":
        from classes.simulator_3 import Simulator

    # read in best sequence
    data = pd.read_csv(f'results/results_algorithm/{file_name}.txt')
    data_x = data["Best_sequence"].tolist()[-1]
    data_x = data_x[1:-1].split(", ")
    data_x = [int(i) for i in data_x]

    plan = pd.read_pickle(f"factory_data/instances_legacy/instances_new/instance_{setting.instance}.pkl")
    sequence = data_x
    for seed in range(1, 2):
        plan.set_sequence(sequence)
        simulator = Simulator(plan, printing=True)
        makespan, tardiness = simulator.simulate(sim_time=300000, random_seed=seed, write=True,
                                                 output_location=f"results/resource_usage/{file_name}.csv")