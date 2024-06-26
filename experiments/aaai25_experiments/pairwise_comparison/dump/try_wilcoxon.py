import scipy.stats as stats
import pandas as pd
import numpy as np
import itertools
from scipy.stats import ranksums

inf_mode = "99999"

for instance_folder in ["j10"]:
    # Read the CSV files into DataFrames
    df1 = pd.read_csv(f'experiments/aaai25_experiments/results/new_results_stnu_{instance_folder}_robust.csv')
    df2 = pd.read_csv(f'experiments/aaai25_experiments/results/new_results_reactive_{instance_folder}_quantile_0.9.csv')
    data = [df1, df2]


data = pd.concat(data, ignore_index=True)

objectives = data["obj"].tolist()
objectives = [i for i in objectives if i < np.inf]
if inf_mode == "inf":
    inf_value = np.inf
elif inf_mode == "99999":
    inf_value = 999
else:
    inf_value = max(objectives) * 1.5

print(f'inf value is {inf_value}')
data.replace([np.inf], inf_value, inplace=True)
print(data["obj"].tolist())


# Generate all possible pairs of methods
methods = data['method'].unique()
method_pairs = list(itertools.combinations(methods, 2))

# Dictionary to store test results

# Loop over each problem domain
for problem in data['instance_folder'].unique():

    # Filter data for the current problem domain
    domain_data = data[data['instance_folder'] == problem]

    for (method1, method2) in method_pairs:

        # Filter data for both methods
        data1 = domain_data[domain_data['method'] == method1]
        data2 = domain_data[domain_data['method'] == method2]

        # Remove infeasible by both methods
        at_least_one_feasible_indices = []
        for i in range(len(data1['obj'].tolist())):
            if data1['obj'].tolist()[i] < inf_value or data2['obj'].tolist()[i] < inf_value:
                # print(f'Double hit for {data1_list[i]} and {data2_list[i]}')
                at_least_one_feasible_indices.append(i)
        print(f'number of at least one feasible pairs {len(at_least_one_feasible_indices)}')

        data1_at_least_one_feasible = data1.iloc[at_least_one_feasible_indices]
        data1_at_least_one_feasible = data1_at_least_one_feasible.reset_index(drop=True)
        data2_at_least_one_feasible = data2.iloc[at_least_one_feasible_indices]
        data2_at_least_one_feasible = data2_at_least_one_feasible.reset_index(drop=True)

        data_1_obs = data1_at_least_one_feasible['obj'].tolist()
        data_2_obs = data2_at_least_one_feasible['obj'].tolist()

        print(f'data 1 is {data_1_obs}')
        print(f'data 2 is {data_2_obs}')

        # Calculate differences and then ranks
        differences = [after - before for after, before in zip(data_2_obs, data_1_obs)]
        print(f'differences is {differences}')
        ranks = stats.rankdata([abs(x) for x in differences])
        signed_ranks = [rank if diff > 0 else -rank for diff, rank in zip(differences, ranks)]

        # Sum of positive and negative ranks
        sum_positive_ranks = sum(rank for rank in signed_ranks if rank > 0)
        sum_negative_ranks = sum(-rank for rank in signed_ranks if rank < 0)

        # Calculate T (the smaller sum of ranks)
        T = min(sum_positive_ranks, sum_negative_ranks)

        # Perform the Wilcoxon signed-rank test
        statistic, p_value = stats.wilcoxon(data_1_obs, data_2_obs)

        print(f"Sum of positive ranks: {sum_positive_ranks}")
        print(f"Sum of negative ranks: {sum_negative_ranks}")
        print(f"T statistic: {T}")
        print(f"Wilcoxon test statistic: {statistic}")
        print(f"p-value: {p_value}")

        print(f'\nNow redo with scipy package')
        stat_obj, p_obj = ranksums(data1_at_least_one_feasible['obj'], data2_at_least_one_feasible['obj'])
        print(f'stat {stat_obj} and p {p_obj}')