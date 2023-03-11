from general import Settings
import pandas as pd

results = []
settings_list = []
for factory_name in ["factory_1"]:
    for seed in range(1, 2):
        for size in [120]:
            for id in range(1, 2):
                for method in ["local_search"]:
                    for init in ["sorted"]:
                        for (l1, l2) in [(0, 1), (1, 1)]:
                            setting = Settings(method=method, stop_criterium="Budget", budget=100 * (size / 20),
                                               instance=f'{size}_{id}_{factory_name}', size=size, simulator="SimPyClaimOneByOneWithDelay",
                                               objective=f'l1={l1}_l2={l2}', init=init, seed=seed, l1=l1, l2=l2)
                            settings_list.append(setting)


for setting in settings_list:
    # determine file name
    if setting.simulator == "SimPyClaimFromBegin":
        from classes import Simulator
    elif setting.simulator == "SimPyClaimOneByOneWithDelay":
        from classes.simulator_3 import Simulator
    else:
        from classes.simulator_2 import Simulator
    file_name = setting.make_file_name()
    print(file_name)

    # read in best sequence
    data = pd.read_csv(f'results/{file_name}.txt')
    data_x = data["Best_sequence"].tolist()[-1]
    data_x = data_x[1:-1].split(", ")
    data_x = [int(i) for i in data_x]

    plan = pd.read_pickle(f"factory_data/instances/instance_{setting.instance}.pkl")
    sequence = data_x
    for SEED in range(1, 2):
        plan.set_sequence(sequence)
        simulator = Simulator(plan, printing=True)
        makespan, tardiness = simulator.simulate(SIM_TIME=300000, RANDOM_SEED=SEED, write=True,
                                                 output_location=f"results/resource_usage/{file_name}.csv")