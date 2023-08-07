from matplotlib import pyplot as plt
import pandas as pd

for instance_size in [10]:
    for instance_id in range(1, 10):
        instance_name = f'{instance_size}_{instance_id}_factory_1'
        policy_type = 2
        evaluation = pd.read_csv(f"simulators/simulator7/outputs/evaluation_table_{instance_name}_policy={policy_type}.csv")
        cp_output = pd.read_csv(f"results/instances_development/start times {instance_name}.csv", delimiter=",")
        n = evaluation.shape[0]
        print(f'Makespan according to CP outout is {max(cp_output["end"].tolist())}')
        average_makespan = evaluation["makespan"].mean()
        std_makespan = evaluation["makespan"].std()
        plt.hist(evaluation["makespan"], 20)
        plt.title(f'n = {n}, mean = {round(average_makespan,1)}, std = {round(std_makespan,1)}')
        plt.savefig(f"simulators/simulator7/outputs/makespan_histogram_{instance_name}.png")

        print(f"Based on {evaluation.shape[0]} scenarios, the average makespan is {average_makespan}")
        print(f"Based on {evaluation.shape[0]}  scenarios, the std makespan is {std_makespan}")