import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

for instance_folder in ["j10", "j20", "j30", "ubo50", "ubo100"]:
    # Read the CSV files into DataFrames
    df = pd.read_csv(f'experiments/aaai25_experiments/results/results_proactive_{instance_folder}_quantile_0.9.csv')
    print(f'Number of experiments {instance_folder} proactive {len(df)}')
    df = df[df['obj'] != np.inf]
    print(f'Number of feasible instances {instance_folder} robust {len(df)}')
    nr_proactive = len(df)

    df = pd.read_csv(f'experiments/aaai25_experiments/results/results_reactive_{instance_folder}_quantile_0.9.csv')
    print(f'Number of experiments {instance_folder} reactive {len(df)}')
    df = df[df['obj'] != np.inf]
    print(f'Number of feasible instances {instance_folder} reactive {len(df)} ')
    nr_reactive = len(df)

    df = pd.read_csv(f'experiments/aaai25_experiments/results/results_stnu_{instance_folder}_robust.csv')
    print(f'Number of experiments {instance_folder} stnu {len(df)}')
    df = df[df['obj'] != np.inf]
    print(f'Number of feasible instances {instance_folder} stnu {len(df)}')
    nr_stnu = len(df)

    print(f'Overleaf: {instance_folder} & {nr_proactive} & {nr_reactive} & {nr_stnu}')




for instance_folder in []:
    # Read the CSV files into DataFrames
    df1 = pd.read_csv(f'experiments/aaai25_experiments/results/new_results_proactive_{instance_folder}_robust.csv')
    df2 = pd.read_csv(f'experiments/aaai25_experiments/results/new_results_stnu_{instance_folder}_quantile_0.9_60.csv')
    df3 = pd.read_csv(f'experiments/aaai25_experiments/results/new_results_stnu_{instance_folder}_robust.csv')
    df4 = pd.read_csv(f'experiments/aaai25_experiments/results/new_results_reactive_{instance_folder}_quantile_0.9_60.csv')
    df5 = pd.read_csv(f'experiments/aaai25_experiments/results/new_results_proactive_{instance_folder}_quantile_0.9.csv')
    #df4 = pd.read_csv(f'experiments/aaai25_experiments/results/new_results_proactive_{instance_folder}.csv')
    # Combine the DataFrames
    combined_df = pd.concat([df1, df2, df4, df3, df5], ignore_index=True)
    combined_df['total_time'] = combined_df['time_offline'] + combined_df['time_online']

    print(f'Total number of experiments for instance folder {instance_folder} {len(combined_df)}')

    # Remove the instances for which the PI problem was infeasible
    #combined_df = combined_df[combined_df['obj_pi'] != np.inf]
    #print(f'Total number of experiments after removing non-pi-feasible instances {len(combined_df)}')

    print(len(combined_df))
    combined_df = combined_df[combined_df['instance_id'] < 37]
    # Group by "instance" and "method" and calculate the average "rel_regret"
    aggregated_df = combined_df.groupby(['method']).agg(
        obj=('obj', 'mean'),
    ).reset_index()

    # Save the aggregated results to a new CSV file (optional)
    aggregated_df.to_csv(f'experiments/aaai25_experiments/results/new_aggregated_results_{instance_folder}.csv',
                         index=False)

    # Group by "instance" and "method" and calculate the average "rel_regret"
    combined_df_only_feasible = combined_df[combined_df['obj'] != np.inf]
    combined_df_only_feasible = combined_df_only_feasible[combined_df_only_feasible['obj'] != np.inf]
    aggregated_df = combined_df_only_feasible.groupby(['instance_id', 'method', 'real_durations']).agg(
        rel_regret=('obj', 'mean'),
    ).reset_index()

    # Save the aggregated results to a new CSV file (optional)
    aggregated_df.to_csv(f'experiments/aaai25_experiments/results/new_aggregated_results_per_instance_{instance_folder}.csv', index=False)

    # Print the aggregated DataFrame
    print(aggregated_df)

    # Plotting the results on relative regret
    plt.figure(figsize=(12, 6))
    plt.rcParams.update({'font.size': 20})
    sns.boxplot(x='method', y='obj', data=combined_df)
    plt.title(f'RCPSP\max {instance_folder} Objective')
    plt.xlabel('Method')
    plt.ylabel('Average Objective (Makespan)')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(f'experiments/aaai25_experiments/figures/objective_{instance_folder}.png')

    # Plotting the results on offline runtime
    plt.figure(figsize=(12, 6))
    plt.rcParams.update({'font.size': 20})
    sns.boxplot(x='method', y='time_offline', data=combined_df)
    plt.title(f'RCPSP\max {instance_folder} time offline')
    plt.xlabel('Method')
    plt.ylabel('Time offline (seconds)')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(f'experiments/aaai25_experiments/figures/time_offline_{instance_folder}.png')

    # Plotting the results on online runtime
    plt.figure(figsize=(12, 6))
    plt.rcParams.update({'font.size': 20})
    sns.boxplot(x='method', y='time_online', data=combined_df)
    plt.title(f'RCPSP\max {instance_folder} time online')
    plt.xlabel('Method')
    plt.ylabel('Time offline (seconds)')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(f'experiments/aaai25_experiments/figures/time_online_{instance_folder}.png')

    # Plotting the results on total time
    plt.figure(figsize=(12, 6))
    plt.rcParams.update({'font.size': 20})
    sns.boxplot(x='method', y='total_time', data=combined_df)
    plt.title(f'RCPSP\max {instance_folder} total time')
    plt.xlabel('Method')
    plt.ylabel('Total time (seconds)')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(f'experiments/aaai25_experiments/figures/total_time_{instance_folder}.png')

    filtered_df = combined_df[combined_df['obj'] != np.inf]
    print(filtered_df)
    aggregated_df = filtered_df.groupby(['method']).agg(
        obj_count=('obj', 'count'),
    ).reset_index()

    aggregated_df.to_csv(
        f'experiments/aaai25_experiments/results/feasible_solutions_{instance_folder}.csv', index=False)

    # Plotting the results
    plt.figure(figsize=(12, 6))
    sns.barplot(x='method', y='obj_count', data=aggregated_df)

    # Adding titles and labels
    plt.title(f'RCPSP\max {instance_folder} Feasible Solutions')
    plt.ylabel('Count feasible objectives')

    # Display the plot
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(f'experiments/aaai25_experiments/figures/feasible_solutions_{instance_folder}.png')

    # Plot total time not including the infeasible ones
    plt.figure(figsize=(12, 6))
    plt.rcParams.update({'font.size': 20})
    sns.boxplot(x='method', y='total_time', data=filtered_df)
    plt.title(f'RCPSP\max {instance_folder} total time filtered')
    plt.xlabel('Method')
    plt.ylabel('Total time (seconds)')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(f'experiments/aaai25_experiments/figures/total_time_{instance_folder}_filtered.png')

    # Plot relative regret when not including the infeasible ones:
    filtered_df = combined_df[combined_df['obj'] != np.inf]
    aggregated_df = filtered_df.groupby(['method']).agg(
        obj=('obj', 'mean'),
    ).reset_index()
    plt.figure(figsize=(12, 6))
    sns.boxplot(x='method', y='obj', data=filtered_df)
    plt.title(f'RCPSP\max {instance_folder} Objective on Feasible Solutions')
    plt.xlabel('Instance')
    plt.ylabel('Objective on feasible solutions')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(f'experiments/aaai25_experiments/figures/filtered_objective_{instance_folder}.png')
