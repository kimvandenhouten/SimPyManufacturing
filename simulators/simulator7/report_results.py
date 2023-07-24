from matplotlib import pyplot as plt
import pandas as pd

instance_name = "10_1_factory_1"
policy_type = 1
evaluation = pd.read_csv(f"simulators/simulator7/outputs/evaluation_table_{instance_name}_policy={policy_type}.csv")
cp_output = pd.read_csv(f"results/cp_model/{instance_name}.csv", delimiter=";")
print(f'Makespan according to CP outout is {max(cp_output["End"].tolist())}')

plt.hist(evaluation["makespan"], 20)
plt.savefig(f"simulators/simulator7/outputs/makespan_histogram_{instance_name}.png")
average_makespan = evaluation["makespan"].mean()
std_makespan = evaluation["makespan"].std()

print(f"Based on 1000 scenarios, the average makespan is {average_makespan}")
print(f"Based on 1000 scenarios, the std makespan is {std_makespan}")