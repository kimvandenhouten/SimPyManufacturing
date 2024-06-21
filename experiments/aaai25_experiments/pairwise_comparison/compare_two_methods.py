import pandas as pd
from scipy.stats import wilcoxon
import itertools
import numpy as np
import networkx as nx
import matplotlib.pyplot as plt
from scipy.stats import ttest_ind
import ast

data = []
# Compare two methods based on quality
for instance_folder in ["j10", "j20", "j30", "ubo50", "ubo100"]:
    # Read the CSV files into DataFrames
    df1 = pd.read_csv(f'experiments/aaai25_experiments/results/results_reactive_{instance_folder}_quantile_0.9.csv')
    df2 = pd.read_csv(f'experiments/aaai25_experiments/results/results_proactive_{instance_folder}_quantile_0.9.csv')
    df3 = pd.read_csv(f'experiments/aaai25_experiments/results/results_stnu_{instance_folder}_robust.csv')
    #df3 = pd.read_csv(f'experiments/aaai25_experiments/results/results_reactive_{instance_folder}.csv')
    data = data + [df1, df2, df3]
    # Combine the DataFrames


data = pd.concat(data, ignore_index=True)

data['rel_regret'] = (data['obj'] - data['obj_pi']) / data['obj_pi']

print(f'regret')
print(f'data relative regret {data["rel_regret"].tolist()}')

objectives = data["rel_regret"].tolist()
objectives = [i for i in objectives if i < np.inf]
inf_value = max(objectives) * 1.5
data.replace([np.inf], inf_value, inplace=True)
#print(data["obj"].tolist())


# List of all methods

methods = data['method'].unique()
method_pairs = list(itertools.combinations(methods, 2))

# Dictionary to store test results
test_results = {}
test_results_double_hits = {}
test_results_magnitude = {}
test_results_proportion = {}
# Loop over each problem domain
for problem in data['instance_folder'].unique():
    test_results[problem] = {}
    test_results_double_hits[problem] = {}
    test_results_magnitude[problem] = {}
    test_results_proportion[problem] = {}
    # Filter data for the current problem domain
    domain_data = data[data['instance_folder'] == problem]

    for (method1, method2) in method_pairs:
        test_results[problem][(method1, method2)] = {}

        # Filter data for both methods
        data1 = domain_data[domain_data['method'] == method1]
        data2 = domain_data[domain_data['method'] == method2]

        data1_list = data1["rel_regret"].tolist()
        data2_list = data2["rel_regret"].tolist()

        # Remove infeasible by both methods
        at_least_one_feasible_indices = []
        for i in range(len(data1_list)):
            if data1_list[i] < inf_value or data2_list[i] < inf_value:
                # print(f'Double hit for {data1_list[i]} and {data2_list[i]}')
                at_least_one_feasible_indices.append(i)
        print(f'number of at least one feasible pairs {len(at_least_one_feasible_indices)}')

        data1_at_least_one_feasible = data1.iloc[at_least_one_feasible_indices]
        data1_at_least_one_feasible = data1_at_least_one_feasible.reset_index(drop=True)
        data2_at_least_one_feasible = data2.iloc[at_least_one_feasible_indices]
        data2_at_least_one_feasible = data2_at_least_one_feasible.reset_index(drop=True)

        # Wilcoxon rank-sum test for 'obj'
        data1_list = data1_at_least_one_feasible["rel_regret"].tolist()
        print(f'{method1} list with length {len(data1_list)} is {data1_list}')
        inf_count = sum(1 for item in data1_list if item == inf_value)
        print(f'number of inf in {method1}: {inf_count}')

        data2_list = data2_at_least_one_feasible['obj'].tolist()
        print(f'{method2} list with length {len(data2_list)} is {data2_list}')
        inf_count = sum(1 for item in data2_list if item == inf_value)
        print(f'number of inf in {method2}: {inf_count}')

        # TODO: what we could do before running this test is excluding all the double failures
        stat_obj, p_obj = wilcoxon(data1_at_least_one_feasible['obj'], data2_at_least_one_feasible['obj'])
        print(f'stat_obj: {stat_obj}, p_obj is {p_obj}')

        # Store results
        test_results[problem][(method1, method2)] = {
            'obj': {'statistic': stat_obj, 'p-value': p_obj, "n_pairs": len(data1_at_least_one_feasible['obj'].tolist())}
        }

        # Now we will only use double hits.
        data1_list = data1["rel_regret"].tolist()
        data2_list = data2["rel_regret"].tolist()

        double_hits_indices = []
        for i in range(len(data1_list)):
            if data1_list[i] < inf_value and data2_list[i] < inf_value:
                #print(f'Double hit for {data1_list[i]} and {data2_list[i]}')
                double_hits_indices.append(i)
        print(f'number of double hits {len(double_hits_indices)}')

        # Select only double hits
        data1_double_hits = data1.iloc[double_hits_indices]
        data1_double_hits = data1_double_hits.reset_index(drop=True)
        data2_double_hits = data2.iloc[double_hits_indices]
        data2_double_hits = data2_double_hits.reset_index(drop=True)

        # Do the Wilcoxon rank-sum tests on doulbe hits only
        stat_obj, p_obj = wilcoxon(data1_double_hits['obj'], data2_double_hits['obj'])
        print(f'double hits: stat_obj: {stat_obj}, p_obj is {p_obj}')

        # Store results
        test_results_double_hits[problem][(method1, method2)] = {
            'obj': {'statistic': stat_obj, 'p-value': p_obj, "n_pairs": len(data1_double_hits['obj'].tolist())}
        }
        print(test_results_double_hits)

        # Now do the magnitude test on the double hits
        data1_list = data1_double_hits["rel_regret"].tolist()
        data2_list = data2_double_hits["rel_regret"].tolist()

        normalized_data1 = []
        normalized_data2 = []
        for i in range(len(data1_list)):
            mean = (data1_list[i] + data2_list[i]) / 2
            if mean > 0:
                normalized_data1.append(data1_list[i] / mean)
                normalized_data2.append(data2_list[i] / mean)
            else:
                normalized_data1.append(1)
                normalized_data2.append(1)
        print(f'normalized data 1 {normalized_data1}')
        print(f'normalized data 2 {normalized_data2}')

        stat_obj, p_obj = ttest_ind(normalized_data1, normalized_data2)

        test_results_magnitude[problem][(method1, method2)] = {
        'obj': {'statistic': stat_obj, 'p-value': p_obj, "n_pairs": len(normalized_data1)}}

        # Now do a proportion test
        num_wins_1, num_trials, ties = 0, 0, 0
        for i in range(len(data1_list)):
            if data1_list[i] == data2_list[i]:
                ties += 1
                #print(f'WARNING THIS IS A TIE, EXCLUDE FROM TEST')
            else:
                num_trials += 1
                if data1_list[i] < data2_list[i]:
                    num_wins_1 += 1

        from scipy.stats import binom_test

        # Probability under the null hypothesis
        p = 0.5
        sample_proportion = num_wins_1 / num_trials

        # Perform the binomial test
        p_value_proportion = binom_test(num_wins_1, num_trials, p)

        test_results_proportion[problem][(method1, method2)] = {
            'obj': {'sample_proportion': sample_proportion, 'p-value': p_obj, 'n_pairs': num_trials, 'ties': ties}}


# Significance level
alpha_consistent = 0.001
alpha_magnitude = 0.05
alpha_proportion = 0.05


# Go through results to form partial orders based on p-values
print(f'\n >> Pairwise comparison of Wilcoxon Matched-Pairs Rank-Sum Test with alpha {alpha_consistent}\n')

for problem, results in test_results.items():
    print(f"Problem Domain: {problem}")
    for pair, metrics in results.items():
        print(f"Methods {pair}:")
        for metric, result in metrics.items():
            print(f'Test is performed on {result["n_pairs"]} pairs')
            if result['p-value'] < alpha_consistent:
                if result['statistic'] < 0:
                    better = pair[0]
                else:
                    better = pair[1]

                print(f"  {metric.capitalize()}: {better} performs significantly better.\n")
            else:
                print(f"  {metric.capitalize()}: No significant difference.\n")

print(f'\n >> Pairwise comparison of Wilcoxon Matched-Pairs Rank-Sum Test with alpha {alpha_consistent} on double hits\n')

# Go through results to form partial orders based on p-values
for problem, results in test_results_double_hits.items():
    print(f"Problem Domain: {problem}")
    for pair, metrics in results.items():
        print(f"Methods {pair}:")
        for metric, result in metrics.items():
            print(f'Test is performed on {result["n_pairs"]} pairs')
            if result['p-value'] < alpha_consistent:
                if result['statistic'] < 0:
                    better = pair[0]
                else:
                    better = pair[1]
                print(f"  Double hits:  {metric.capitalize()}: {better} performs significantly better.")
            else:
                print(f"  Double hits:  {metric.capitalize()}: No significant difference.")

print(f'\n >> Proportion test, excluding ties, and alpha {alpha_proportion}\n')

# Go through results to form partial orders based on p-values
for problem, results in test_results_proportion.items():
    print(f"Problem Domain: {problem}")
    for pair, metrics in results.items():
        print(f"Methods {pair}:")
        for metric, result in metrics.items():
            print(f'Test is performed on {result["n_pairs"]} pairs excluding {result["ties"]} ties')
            if result['p-value'] < alpha_proportion:
                if result['sample_proportion'] >= 0.5:
                    better = pair[0]
                else:
                    better = pair[1]
                print(f"  There is a significant proportion of wins difference :  {metric.capitalize()}: {better} "
                      f"performs significantly better with proportion {result['sample_proportion']}.")
            else:
                print(f"  Double hits magnitude:  {metric.capitalize()}: No significant difference.")

print(f'\n >> Pair-wise t-test, on double hits, and alpha {alpha_magnitude}\n')

# Go through results to form partial orders based on p-values
for problem, results in test_results_magnitude.items():
    print(f"Problem Domain: {problem}")
    for pair, metrics in results.items():
        print(f"Methods {pair}:")
        for metric, result in metrics.items():
            print(f'Test is performed on {result["n_pairs"]} pairs')
            if result['p-value'] < alpha_magnitude:
                if result['statistic'] < 0:
                    better = pair[0]
                else:
                    better = pair[1]
                print(f"  Double hits magnitude:  {metric.capitalize()}: {better} performs significantly better.")
            else:
                print(f"  Double hits magnitude:  {metric.capitalize()}: No significant difference.")

