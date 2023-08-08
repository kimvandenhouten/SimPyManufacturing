from matplotlib import pyplot as plt
import pandas as pd

for instance_size in [10, 20]:
    for instance_id in range(1, 10):
        instance_name = f'{instance_size}_{instance_id}_factory_1'
        policy_type = 2
        evaluation = pd.read_csv(f"simulators/simulator7/outputs/evaluation_table_{instance_name}_policy={policy_type}.csv")
        cp_output = pd.read_csv(f"results/instances_development/start times {instance_name}.csv", delimiter=",")
        n = evaluation.shape[0]
        print(f'Makespan according to CP outout is {max(cp_output["end"].tolist())}')
        average_makespan = evaluation["makespan"].mean()
        std_makespan = evaluation["makespan"].std()
        plt.rcParams.update({'font.size': 14})
        plt.rc('axes', titlesize=14)
        plt.rc('axes', labelsize=14)
        plt.hist(evaluation["makespan"], 20)

        plt.title(f'n = {n}, mean = {round(average_makespan,1)}, std = {round(std_makespan,1)}')
        plt.savefig(f"simulators/simulator7/outputs/makespan_histogram_{instance_name}.png")
        plt.close()

        print(f"Based on {evaluation.shape[0]} scenarios, the average makespan is {average_makespan}")
        print(f"Based on {evaluation.shape[0]}  scenarios, the std makespan is {std_makespan}")