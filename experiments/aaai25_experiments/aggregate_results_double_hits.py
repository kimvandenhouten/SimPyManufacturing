import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns



for instance_folder in ["j10"]:
    # Read the CSV files into DataFrames
    df1 = pd.read_csv(f'experiments/aaai25_experiments/results/new_results_proactive_{instance_folder}_robust.csv')
    df2 = pd.read_csv(f'experiments/aaai25_experiments/results/new_results_stnu_{instance_folder}_quantile_0.9.csv')
    df3 = pd.read_csv(f'experiments/aaai25_experiments/results/new_results_stnu_{instance_folder}_robust.csv')
    df4 = pd.read_csv(f'experiments/aaai25_experiments/results/new_results_reactive_{instance_folder}_quantile_0.9.csv')
    df5 = pd.read_csv(f'experiments/aaai25_experiments/results/new_results_proactive_{instance_folder}_quantile_0.9.csv')


    # TODO: only keep double hits (solved by all methods, yes this is tricky)
    df1_list = df1["obj"].tolist()
    df2_list = df2["obj"].tolist()
    df3_list = df1["obj"].tolist()
    df4_list = df2["obj"].tolist()
    df5_list = df1["obj"].tolist()

    double_hits_indices = []
    for i in range(len(df1_list)):
        if df1_list[i] < np.inf and df2_list[i] < np.inf and df3_list[i] < np.inf and df4_list[i] < np.inf and df5_list[i] < np.inf:
            # print(f'Double hit for {data1_list[i]} and {data2_list[i]}')
            double_hits_indices.append(i)
    print(f'number of double hits {len(double_hits_indices)}')
    df1 = df1.iloc[double_hits_indices]
    df2 = df2.iloc[double_hits_indices]
    df3 = df3.iloc[double_hits_indices]
    df4 = df4.iloc[double_hits_indices]
    df5 = df5.iloc[double_hits_indices]

    combined_df = pd.concat([df1, df2, df3, df4, df5], ignore_index=True)
    combined_df['total_time'] = combined_df['time_offline'] + combined_df['time_online']
    print(f'Total number of experiments for instance folder {instance_folder} {len(combined_df)}')

    combined_df = combined_df[combined_df['instance_id'] < 37]
    # Group by "instance" and "method" and calculate the average "rel_regret"
    aggregated_df = combined_df.groupby(['method']).agg(
        obj=('obj', 'mean'),
    ).reset_index()

    # Group by "instance" and "method" and calculate the average "rel_regret"
    combined_df_only_feasible = combined_df[combined_df['obj'] != np.inf]
    combined_df_only_feasible = combined_df_only_feasible[combined_df_only_feasible['obj'] != np.inf]
    aggregated_df = combined_df_only_feasible.groupby(['instance_id', 'method', 'real_durations']).agg(
        rel_regret=('obj', 'mean'),
    ).reset_index()

    # Plotting the results on relative regret
    plt.figure(figsize=(12, 6))
    plt.rcParams.update({'font.size': 20})
    sns.boxplot(x='method', y='obj', data=combined_df)
    plt.title(f'RCPSP\max {instance_folder} Objective')
    plt.xlabel('Method')
    plt.ylabel('Average Objective (Makespan)')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(f'experiments/aaai25_experiments/figures/double_hits_objective_{instance_folder}.png')

    # Plotting the results on offline runtime
    plt.figure(figsize=(12, 6))
    plt.rcParams.update({'font.size': 20})
    sns.boxplot(x='method', y='time_offline', data=combined_df)
    plt.title(f'RCPSP\max {instance_folder} time offline')
    plt.xlabel('Method')
    plt.ylabel('Time offline (seconds)')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(f'experiments/aaai25_experiments/figures/double_hits_time_offline_{instance_folder}.png')

    # Plotting the results on online runtime
    plt.figure(figsize=(12, 6))
    plt.rcParams.update({'font.size': 20})
    sns.boxplot(x='method', y='time_online', data=combined_df)
    plt.title(f'RCPSP\max {instance_folder} time online')
    plt.xlabel('Method')
    plt.ylabel('Time offline (seconds)')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(f'experiments/aaai25_experiments/figures/double_hits_time_online_{instance_folder}.png')

    # Plotting the results on total time
    plt.figure(figsize=(12, 6))
    plt.rcParams.update({'font.size': 20})
    sns.boxplot(x='method', y='total_time', data=combined_df)
    plt.title(f'RCPSP\max {instance_folder} total time')
    plt.xlabel('Method')
    plt.ylabel('Total time (seconds)')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(f'experiments/aaai25_experiments/figures/double_hits_total_time_{instance_folder}.png')

    filtered_df = combined_df[combined_df['obj'] != np.inf]
    aggregated_df = filtered_df.groupby(['method']).agg(
        obj_count=('obj', 'count'),
    ).reset_index()

    # Plotting the results
    plt.figure(figsize=(12, 6))
    sns.barplot(x='method', y='obj_count', data=aggregated_df)

    # Adding titles and labels
    plt.title(f'RCPSP\max {instance_folder} Feasible Solutions')
    plt.ylabel('Count feasible objectives')

    # Display the plot
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(f'experiments/aaai25_experiments/figures/double_hits_feasible_solutions_{instance_folder}.png')

