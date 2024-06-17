import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

for instance_id in range(1, 51):
    for instance_folder in ["j10", "j20", "j30"]:
        # Read the CSV files into DataFrames
        df1 = pd.read_csv(f'experiments/aaai25_experiments/results/results_proactive_{instance_folder}.csv')
        df2 = pd.read_csv(f'experiments/aaai25_experiments/results/results_stnu_{instance_folder}.csv')
        df3 = pd.read_csv(f'experiments/aaai25_experiments/results/results_reactive_{instance_folder}.csv')
        # Combine the DataFrames
        combined_df = pd.concat([df1, df2, df3])
        combined_df = combined_df[combined_df['obj_pi'] != np.inf]
        combined_df = combined_df[combined_df['instance_id'] == instance_id]

        if len(combined_df) > 0:

            aggregated_df = combined_df.groupby(['real_durations', 'method']).agg(
                obj=('rel_regret', 'mean'),
            ).reset_index()

            print(aggregated_df)
            problems = range(10)
            method1 = aggregated_df[aggregated_df['method'] == "proactive"]
            method1 = method1['obj'].tolist()
            print(method1)

            method2 = aggregated_df[aggregated_df['method'] == "reactive"]
            method2 = method2['obj'].tolist()
            print(method2)

            method3 = aggregated_df[aggregated_df['method'] == "STNU"]
            method3 = method3['obj'].tolist()
            print(method3)


            fig, ax = plt.subplots()
            plt.rcParams.update({'font.size': 12})
            # Using 'o' for success and 'X' for failures
            markers = {'Proactive': 'o', 'Reactive': 's', 'STNU': '^'}
            markers_failures = {'Proactive': 'X', 'Reactive': '+', 'STNU': '1'}
            colors = {'Proactive': 'b', 'Reactive': 'g', 'STNU': 'r'}
            data = {'Proactive': method1, 'Reactive': method2, 'STNU': method3}

            for method, values in data.items():
                x_vals = [i for i, v in enumerate(values) if v < 100]
                y_vals = [v for v in values if v < 100]
                ax.scatter(x_vals, y_vals, marker=markers[method], color=colors[method], label=method)

                # Adding X for failures
                fail_x_vals = [i for i, v in enumerate(values) if v == 100]
                fail_y_vals = [100 for _ in
                               fail_x_vals]  # Assuming 0.75 is within the y-axis limit and indicates failure level
                ax.scatter(fail_x_vals, fail_y_vals, marker=markers_failures[method], color='k', label=f'{method} Failure')

            ax.set_xlabel('Problem Index', fontsize=12)
            ax.set_ylabel('Relative regret, (100%) = infeasible', fontsize=12)
            ax.set_title(f'Comparison Across Methods for {instance_folder}_PSP{instance_id}')
            ax.legend()

            plt.savefig(f'experiments/aaai25_experiments/figures/plot_failures_{instance_folder}_{instance_id}.png')


for instance_id in range(1, 11):
    for instance_folder in ["ubo50", "ubo100"]:
        # Read the CSV files into DataFrames
        df1 = pd.read_csv(f'experiments/aaai25_experiments/results/results_proactive_{instance_folder}.csv')
        df2 = pd.read_csv(f'experiments/aaai25_experiments/results/results_stnu_{instance_folder}.csv')
        df3 = pd.read_csv(f'experiments/aaai25_experiments/results/results_reactive_{instance_folder}.csv')
        # Combine the DataFrames
        combined_df = pd.concat([df1, df2, df3])
        combined_df = combined_df[combined_df['obj_pi'] != np.inf]
        combined_df = combined_df[combined_df['instance_id'] == instance_id]

        if len(combined_df) > 0:

            aggregated_df = combined_df.groupby(['real_durations', 'method']).agg(
                obj=('rel_regret', 'mean'),
            ).reset_index()

            print(aggregated_df)
            problems = range(10)
            method1 = aggregated_df[aggregated_df['method'] == "proactive"]
            method1 = method1['obj'].tolist()
            print(method1)

            method2 = aggregated_df[aggregated_df['method'] == "reactive"]
            method2 = method2['obj'].tolist()
            print(method2)

            method3 = aggregated_df[aggregated_df['method'] == "STNU"]
            method3 = method3['obj'].tolist()
            print(method3)


            fig, ax = plt.subplots()
            # Using 'o' for success and 'X' for failures
            markers = {'Proactive': 'o', 'Reactive': 's', 'STNU': '^'}
            markers_failures = {'Proactive': 'X', 'Reactive': '+', 'STNU': '1'}
            colors = {'Proactive': 'b', 'Reactive': 'g', 'STNU': 'r'}
            data = {'Proactive': method1, 'Reactive': method2, 'STNU': method3}

            for method, values in data.items():
                x_vals = [i for i, v in enumerate(values) if v < 100]
                y_vals = [v for v in values if v < 100]
                ax.scatter(x_vals, y_vals, marker=markers[method], color=colors[method], label=method)

                # Adding X for failures
                fail_x_vals = [i for i, v in enumerate(values) if v == 100]
                fail_y_vals = [100 for _ in
                               fail_x_vals]  # Assuming 0.75 is within the y-axis limit and indicates failure level
                ax.scatter(fail_x_vals, fail_y_vals, marker=markers_failures[method], color='k', label=f'{method} Failure')

            ax.set_xlabel('Problem Index')
            ax.set_ylabel('Relative regret, (100%) indicates infeasible')
            ax.set_title(f'Comparison Across Methods for {instance_folder}_PSP{instance_id}')
            ax.legend()

            plt.savefig(f'experiments/aaai25_experiments/figures/plot_failures_{instance_folder}_{instance_id}.png')

