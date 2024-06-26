import pandas as pd
from scipy.stats import wilcoxon
import itertools
import numpy as np
import networkx as nx
import matplotlib.pyplot as plt
from scipy.stats import ttest_ind
import ast
from general.latex_table_from_list import generate_latex_table_from_lists

data = []
# Compare two methods based on quality
for instance_folder in ["j10", "j20", "j30", "ubo50", "ubo100"]:
    # Read the CSV files into DataFrames
    df1 = pd.read_csv(f'experiments/aaai25_experiments/results/results_reactive_{instance_folder}_quantile_0.9.csv')
    df2 = pd.read_csv(f'experiments/aaai25_experiments/results/results_proactive_{instance_folder}_quantile_0.9.csv')
    df3 = pd.read_csv(f'experiments/aaai25_experiments/results/results_stnu_{instance_folder}_robust.csv')
    df4 = pd.read_csv(f'experiments/aaai25_experiments/results/results_proactive_{instance_folder}_SAA_smart.csv')
    data = data + [df1, df2, df3, df4]
    # Combine the DataFrames


data = pd.concat(data, ignore_index=True)

objectives = data["time_offline"].tolist()
objectives = [i for i in objectives if i < np.inf]
inf_value = max(objectives) * 5
data.replace([np.inf], inf_value, inplace=True)


methods = ["proactive_quantile_0.9", "STNU_robust", "reactive_quantile_0.9", "proactive_SAA_smart"]


method_pairs = [("reactive_quantile_0.9", "proactive_quantile_0.9"), ("reactive_quantile_0.9", "STNU_robust"),
                ("reactive_quantile_0.9", "proactive_SAA_smart"), ("proactive_quantile_0.9", "STNU_robust"),
                ("proactive_quantile_0.9", "proactive_SAA_smart"), ("proactive_SAA_smart", "STNU_robust")]



method_pairs_problems = {}
for prob in ["j10"]:
    method_pairs_problems[prob] = method_pairs

for prob in ["j20", "j30", "ubo50", "ubo100"]:
    method_pairs_problems[prob] = [("reactive_quantile_0.9", "proactive_quantile_0.9"), ("reactive_quantile_0.9", "STNU_robust"),
                ("reactive_quantile_0.9", "proactive_SAA_smart"), ("proactive_quantile_0.9", "STNU_robust"),
                ("proactive_quantile_0.9", "proactive_SAA_smart"), ("STNU_robust", "proactive_SAA_smart"), ]


trans_dict = {"STNU_robust": "stnu",
              "reactive_quantile_0.9": "reactive",
              "proactive_quantile_0.9": "proactive$_{0.9}$",
               "proactive_SAA_smart": "proactive$_{SAA}$"}

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
    method_pairs = method_pairs_problems[problem]
    for (method1, method2) in method_pairs:
        test_results[problem][(method1, method2)] = {}

        # Filter data for both methods
        data1 = domain_data[domain_data['method'] == method1]
        data2 = domain_data[domain_data['method'] == method2]

        data1_list = data1["time_offline"].tolist()
        data2_list = data2["time_offline"].tolist()

        # Remove infeasible by both methods
        at_least_one_feasible_indices = []
        for i in range(len(data1_list)):
            if data1_list[i] < inf_value or data2_list[i] < inf_value:
                # print(f'Double hit for {data1_list[i]} and {data2_list[i]}')
                at_least_one_feasible_indices.append(i)

        data1_at_least_one_feasible = data1.iloc[at_least_one_feasible_indices]
        data1_at_least_one_feasible = data1_at_least_one_feasible.reset_index(drop=True)
        data2_at_least_one_feasible = data2.iloc[at_least_one_feasible_indices]
        data2_at_least_one_feasible = data2_at_least_one_feasible.reset_index(drop=True)

        # Wilcoxon rank-sum test for 'obj'
        data1_list = data1_at_least_one_feasible["time_offline"].tolist()
        inf_count = sum(1 for item in data1_list if item == inf_value)

        data2_list = data2_at_least_one_feasible['time_offline'].tolist()
        print(f'{method2} list with length {len(data2_list)} is {data2_list}')
        inf_count = sum(1 for item in data2_list if item == inf_value)

        # TODO: what we could do before running this test is excluding all the double failures
        res = wilcoxon(data1_at_least_one_feasible['time_offline'], data2_at_least_one_feasible['time_offline'],
                       method="approx", zero_method="pratt")

        differences = np.array(data1_at_least_one_feasible['time_offline'].tolist()) - np.array(data2_at_least_one_feasible['time_offline'].tolist())
        import scipy
        ranks = scipy.stats.rankdata([abs(x) for x in differences])
        signed_ranks = []
        for diff, rank in zip(differences, ranks):
            # Pratt method ignores zero ranks, although there were included in the ranking process
            if diff > 0:
                signed_ranks.append(rank)
            elif diff < 0:
                signed_ranks.append(-rank)

        # Sum of positive and negative ranks
        sum_positive_ranks = sum(rank for rank in signed_ranks if rank > 0)
        sum_negative_ranks = sum(-rank for rank in signed_ranks if rank < 0)

        if sum_positive_ranks > sum_negative_ranks:
            print(f'{method2} is probably better')
        else:
            print(f'{method1} is probably better')

        stat_obj = res.statistic
        p_obj = res.pvalue
        z_obj = res.zstatistic

        # Store results
        test_results[problem][(method1, method2)] = {
            'obj': {'statistic': stat_obj, 'p-value': p_obj, 'z-statistic': z_obj,
                    "n_pairs": len(data1_at_least_one_feasible['time_offline'].tolist()),
                    "sum_pos_ranks": sum_positive_ranks, 'sum_neg_ranks': sum_negative_ranks}
        }

        # Now we will only use double hits.
        data1_list = data1["time_offline"].tolist()
        data2_list = data2["time_offline"].tolist()

        double_hits_indices = []
        for i in range(len(data1_list)):
            if data1_list[i] < inf_value and data2_list[i] < inf_value:
                #print(f'Double hit for {data1_list[i]} and {data2_list[i]}')
                double_hits_indices.append(i)

        # Select only double hits
        data1_double_hits = data1.iloc[double_hits_indices]
        data1_double_hits = data1_double_hits.reset_index(drop=True)
        data2_double_hits = data2.iloc[double_hits_indices]
        data2_double_hits = data2_double_hits.reset_index(drop=True)

        # Do the Wilcoxon rank-sum tests on doulbe hits only
        res = wilcoxon(data1_double_hits['time_offline'], data2_double_hits['time_offline'], method="approx", zero_method="pratt")
        stat_obj = res.statistic
        p_obj = res.pvalue
        z_obj = res.zstatistic

        # Store results
        test_results_double_hits[problem][(method1, method2)] = {
            'obj': {'statistic': stat_obj, 'p-value': p_obj, "z-statistic": z_obj, "n_pairs": len(data1_double_hits['time_offline'].tolist())}
        }

        # Now do the magnitude test on the double hits
        data1_list = data1_double_hits['time_offline'].tolist()
        data2_list = data2_double_hits['time_offline'].tolist()

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

        stat_obj, p_obj = ttest_ind(normalized_data1, normalized_data2)

        test_results_magnitude[problem][(method1, method2)] = {
        'obj': {'statistic': stat_obj, 'p-value': p_obj, "n_pairs": len(normalized_data1),
                "mean_method1": np.mean(normalized_data1), "mean_method2": np.mean(normalized_data2)}}

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

        from scipy.stats import binomtest

        # Probability under the null hypothesis
        p = 0.5
        sample_proportion = num_wins_1 / num_trials

        # Perform the binomial test
        result = binomtest(num_wins_1, num_trials, p)
        p_value_proportion = result.pvalue
        statistic = result.statistic
        z_value = (num_wins_1 - num_trials * p) / np.sqrt(num_trials * p * (1 - p))
        test_results_proportion[problem][(method1, method2)] = {
            'obj': {'sample_proportion': sample_proportion, 'p-value': p_obj, 'n_pairs': num_trials, 'ties': ties, 'z-statistic': z_value}}


# Significance level
alpha_consistent = 0.001
alpha_magnitude = 0.05
alpha_proportion = 0.05

rows = []

for problem in data['instance_folder'].unique():
    print(f'\nStart evaluation for new problem set {problem}')

    # Obtain Wilcoxon-stats and make overleaf cell
    method_pairs = method_pairs_problems[problem]
    method_pairs_to_header = [f"{trans_dict[pair[0]]}-{trans_dict[pair[1]]}" for pair in method_pairs]
    header = [problem] + method_pairs_to_header
    rows.append(header)

    new_row = [""]
    for pair in method_pairs:
        result = test_results[problem][(pair[0], pair[1])]['obj']

        if result['p-value'] < alpha_consistent:
            if result['sum_pos_ranks'] > result['sum_neg_ranks']:
                better = pair[1]
                print(f'WARNING pair[1] is better {pair[1]}')
            else:
                better = pair[0]

            print(
                f"Wilcoxon objective {pair}: {better} performs significantly better with z-stat {np.round(result['z-statistic'], 3)} and p-value "
                f"{result['p-value']}")
            overleaf_string = f"[{result['n_pairs']}] {np.round(result['z-statistic'], 3)} (*)"
            print(f"Overleaf string: {overleaf_string}")
        else:
            print(
                f"Wilcoxon objective {pair}: No significant difference with z-stat {np.round(result['z-statistic'], 3)} and p-value "
                f"{result['p-value']}.")
            overleaf_string = f"[{result['n_pairs']}] {np.round(result['z-statistic'], 3)} ({np.round(result['p-value'], 3)})"
            print(f"Overleaf string: {overleaf_string}")
        new_row.append(overleaf_string)
    rows.append(new_row)

    new_row = [""]
    for pair in method_pairs:
        result = test_results_proportion[problem][(pair[0], pair[1])]['obj']

        if result['p-value'] < alpha_proportion:
            if result['sample_proportion'] >= 0.5:
                better = pair[0]
            else:
                better = pair[1]
                print(f'WARNING pair[1] is better {pair[1]}')
            print(f"  There is a significant proportion of wins in objective {better} "
                  f"performs significantly better with proportion {result['sample_proportion']} and p-value "
                  f"{result['p-value']} and z-value {np.round(result['z-statistic'], 3)}.")
            overleaf_string = f"[{result['n_pairs']}] {np.round(result['z-statistic'], 3)} (*)"
            print(f"Overleaf string: {overleaf_string}")
        else:
            print(f"  There is no significant proportion of wins in obj: No significant difference."
                  f"proportion {result['sample_proportion']} and p-value {result['p-value']} and z-value {np.round(result['z-statistic'], 3)}")
            overleaf_string = f"[{result['n_pairs']}] {np.round(result['z-statistic'], 3)} ({result['p-value']})"
            print(f"Overleaf string: {overleaf_string}")
        new_row.append(overleaf_string)
    rows.append(new_row)

print(rows)
caption = ("Pairwise comparison on time offline. Using a Wilcoxon test and a proportion test."
           " Including all instances for which at least one of the two methods found a feasible solution.")
latex_code = generate_latex_table_from_lists(rows, caption=caption, label="tab:offline_pairwise")
print(latex_code)


rows = []

for problem in data['instance_folder'].unique():
    method_pairs = method_pairs_problems[problem]
    method_pairs_to_header = [f"{trans_dict[pair[0]]}-{trans_dict[pair[1]]}" for pair in method_pairs]
    header = [problem] + method_pairs_to_header
    rows.append(header)
    print(f'\nStart evaluation for new problem set {problem}')
    new_row_1 = [""]
    new_row_2 = [""]
    new_row_3 = [""]
    # Obtain Wilcoxon-stats and make overleaf cell
    for pair in method_pairs:
        result = test_results_magnitude[problem][(pair[0], pair[1])]['obj']
        if result['p-value'] < alpha_magnitude:
            if result['statistic'] < 0:
                better = pair[0]
            else:
                better = pair[1]
                print(f'warning the second is better {pair[1]}')
            print(f"Double hits magnitude: {better} performs significantly better with"
                  f" stat {np.round(result['statistic'], 3)} and p-value {result['p-value']}.")
            overleaf_1 = f"[{result['n_pairs']}] {np.round(result['statistic'], 3)} (*) "
            overleaf_2 = f"{trans_dict[pair[0]]}: {np.round(result['mean_method1'], 2)}"
            overleaf_3 = f"{trans_dict[pair[1]]}: {np.round(result['mean_method2'], 2)}"
            print(overleaf_1)
            print(overleaf_2)
            print(overleaf_3)

        else:
            print(f"Double hits magnitude: No significant difference. With stat"
                  f" {np.round(result['statistic'], 3)} and p-value {result['p-value']}")
            overleaf_1 = f"[{result['n_pairs']}] {np.round(result['statistic'], 3)} ({result['p-value']})"
            overleaf_2 = f"{trans_dict[pair[0]]}: {np.round(result['mean_method1'], 2)}"
            overleaf_3 = f"{trans_dict[pair[1]]}: {np.round(result['mean_method2'], 2)}"
            print(overleaf_1)
            print(overleaf_2)
            print(overleaf_3)
        new_row_1.append(overleaf_1)
        new_row_2.append(overleaf_2)
        new_row_3.append(overleaf_3)
    rows.append(new_row_1)
    rows.append(new_row_2)
    rows.append(new_row_3)

caption = ("Magnitude test on time offline. Using a pairwise t-test, including all instances for which both methods found "
           "a feasible solution, and for which earlier tests indicated a significant consistent or proportional difference.")
latex_code = generate_latex_table_from_lists(rows, caption=caption, label="tab:offline_magnitude")
print(latex_code)