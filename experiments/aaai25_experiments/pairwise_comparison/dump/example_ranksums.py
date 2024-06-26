import pandas as pd
from scipy.stats import ranksums
import itertools
import numpy as np
import networkx as nx
import matplotlib.pyplot as plt
from scipy.stats import ttest_ind

data = []
# Load data from a CSV file
for instance_folder in ["j10"]:
    # Read the CSV files into DataFrames
    df1 = pd.read_csv(f'experiments/aaai25_experiments/results/new_results_stnu_{instance_folder}_robust.csv')
    df2 = pd.read_csv(f'experiments/aaai25_experiments/results/new_results_reactive_{instance_folder}_quantile_0.9.csv')
    df3 = pd.read_csv(f'experiments/aaai25_experiments/results/new_results_robust_{instance_folder}.csv')
    df4 = pd.read_csv(f'experiments/aaai25_experiments/results/new_results_robust_{instance_folder}_quantile_0.9.csv')
    #df3 = pd.read_csv(f'experiments/aaai25_experiments/results/results_reactive_{instance_folder}.csv')
    data = data + [df1, df2, df3, df4]
    # Combine the DataFrames

data = pd.concat(data, ignore_index=True)

objectives = data["obj"].tolist()
objectives = [i for i in objectives if i < np.inf]
inf_value = max(objectives) * 1.25
print(inf_value)
data.replace([np.inf], inf_value, inplace=True)
print(data["obj"].tolist())

data['total_time'] = data['time_offline'] + data['time_online']

# List of all methods
# Initialize a directed graph
G = nx.DiGraph()
methods = data['method'].unique()
G.add_nodes_from(methods)

# Generate all possible pairs of methods
method_pairs = list(itertools.combinations(methods, 2))

# Dictionary to store test results
test_results = {}
test_results_double_hits = {}
test_results_magnitude = {}
# Loop over each problem domain
for problem in data['instance_folder'].unique():
    test_results[problem] = {}
    test_results_double_hits[problem] = {}
    test_results_magnitude[problem] = {}
    # Filter data for the current problem domain
    domain_data = data[data['instance_folder'] == problem]

    for (method1, method2) in method_pairs:
        test_results[problem][(method1, method2)] = {}

        # Filter data for both methods
        data1 = domain_data[domain_data['method'] == method1]
        data2 = domain_data[domain_data['method'] == method2]

        # Wilcoxon rank-sum test for 'obj'
        data1_list = data1["obj"].tolist()
        print(f'{method1} list with length {len(data1_list)} is {data1_list}')
        inf_count = sum(1 for item in data1_list if item == inf_value)
        print(f'number of inf in {method1}: {inf_count}')

        data2_list = data2["obj"].tolist()
        print(f'{method2} list with length {len(data2_list)} is {data2_list}')
        inf_count = sum(1 for item in data2_list if item == inf_value)
        print(f'number of inf in {method2}: {inf_count}')

        stat_obj, p_obj = ranksums(data1['obj'], data2['obj'])
        print(f'stat_obj: {stat_obj}, p_obj is {p_obj}')

        # Wilcoxon rank-sum test for 'total_time'
        stat_time, p_time = ranksums(data1['total_time'], data2['total_time'])
        print(f'stat_total_time: {stat_time}, p_time is {p_time}')

        # Store results
        test_results[problem][(method1, method2)] = {
            'obj': {'statistic': stat_obj, 'p-value': p_obj},
            'total_time': {'statistic': stat_time, 'p-value': p_time}
        }

        # Now we will only use double hits.
        data1_list = data1["obj"].tolist()
        data2_list = data2["obj"].tolist()
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
        stat_obj, p_obj = ranksums(data1_double_hits['obj'], data2_double_hits['obj'])
        print(f'double hits: stat_obj: {stat_obj}, p_obj is {p_obj}')

        # Wilcoxon rank-sum test for 'total_time'
        stat_time, p_time = ranksums(data1_double_hits['total_time'], data2_double_hits['total_time'])
        print(f'double hits: stat_total_time: {stat_time}, p_obj is {p_time}')

        # Store results
        test_results_double_hits[problem][(method1, method2)] = {
            'obj': {'statistic': stat_obj, 'p-value': p_obj},
            'total_time': {'statistic': stat_time, 'p-value': p_time}
        }
        print(test_results_double_hits)

        # Now do the magnitude test on the double hits
        data1_list = data1_double_hits["obj"].tolist()
        data2_list = data2_double_hits["obj"].tolist()

        normalized_data1 = []
        normalized_data2 = []
        for i in range(len(data1_list)):
            mean = (data1_list[i] + data2_list[i]) / 2
            normalized_data1.append(data1_list[i] / mean)
            normalized_data2.append(data2_list[i] / mean)

        stat_obj, p_obj = ttest_ind(normalized_data1, normalized_data2)

        data1_list = data1_double_hits["total_time"].tolist()
        data2_list = data2_double_hits["total_time"].tolist()

        normalized_data1 = []
        normalized_data2 = []
        for i in range(len(data1_list)):
            mean = (data1_list[i] + data2_list[i]) / 2
            normalized_data1.append(data1_list[i] / mean)
            normalized_data2.append(data2_list[i] / mean)

        stat_time, p_time = ttest_ind(normalized_data1, normalized_data2)

        test_results_magnitude[problem][(method1, method2)] = {
        'obj': {'statistic': stat_obj, 'p-value': p_obj},
        'total_time': {'statistic': stat_time, 'p-value': p_time}}


# Significance level
alpha_consistent = 0.05
alpha_magnitude = 0.05
# Go through results to form partial orders based on p-values
for problem, results in test_results.items():
    print(f"Problem Domain: {problem}")
    for pair, metrics in results.items():
        print(f"Methods {pair}:")
        for metric, result in metrics.items():
            if result['p-value'] < alpha_consistent:
                if result['statistic'] < 0:
                    better = pair[0]
                    if metric == "obj":
                        G.add_edge(pair[0], pair[1])
                else:
                    better = pair[1]
                    if metric == "obj":
                        G.add_edge(pair[1], pair[0])
                print(f"  {metric.capitalize()}: {better} performs significantly better.")
            else:
                print(f"  {metric.capitalize()}: No significant difference.")


# Go through results to form partial orders based on p-values
for problem, results in test_results_double_hits.items():
    print(f"Problem Domain: {problem}")
    for pair, metrics in results.items():
        print(f"Methods {pair}:")
        for metric, result in metrics.items():
            if result['p-value'] < alpha_consistent:
                if result['statistic'] < 0:
                    better = pair[0]
                else:
                    better = pair[1]
                print(f"  Double hits:  {metric.capitalize()}: {better} performs significantly better.")
            else:
                print(f"  Double hits:  {metric.capitalize()}: No significant difference.")


# Go through results to form partial orders based on p-values
for problem, results in test_results_magnitude.items():
    print(f"Problem Domain: {problem}")
    for pair, metrics in results.items():
        print(f"Methods {pair}:")
        for metric, result in metrics.items():
            if result['p-value'] < alpha_magnitude:
                if result['statistic'] < 0:
                    better = pair[0]
                else:
                    better = pair[1]
                print(f"  Double hits magnitude:  {metric.capitalize()}: {better} performs significantly better.")
            else:
                print(f"  Double hits magnitude:  {metric.capitalize()}: No significant difference.")

if False:
    # Check if the graph is a Directed Acyclic Graph (DAG)
    if nx.is_directed_acyclic_graph(G):
        # Get one possible topological order
        topo_sort = list(nx.topological_sort(G))
        print("One possible ordering of methods based on 'obj' metric:")
        print(topo_sort)
    else:
        print("No consistent ordering possible (the graph has cycles)")

        from networkx.drawing.nx_agraph import to_agraph

    # Convert the NetworkX graph to a Graphviz AGraph
    nx.draw(G, with_labels=True)
    plt.show()

# TODO: for the ones that have a pair-wise significant difference, also evaluate the magnitude significant difference

