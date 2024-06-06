import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

for instance_folder in ["j10", "j30"]:
    # Read the CSV files into DataFrames
    df1 = pd.read_csv(f'aaai25_experiments/results/results_saa_{instance_folder}.csv')
    df2 = pd.read_csv(f'aaai25_experiments/results/results_stnu_{instance_folder}.csv')
    df3 = pd.read_csv(f'aaai25_experiments/results/reactive_approach_{instance_folder}.csv')
    # Combine the DataFrames
    combined_df = pd.concat([df1, df2, df3])


    print(len(combined_df))
    combined_df['rel_regret'] = pd.to_numeric(combined_df['rel_regret'], errors='coerce')
    print(len(combined_df))
    combined_df = combined_df.dropna(subset=['rel_regret'])

    print(len(combined_df))
    # Group by "instance" and "method" and calculate the average "rel_regret"
    aggregated_df = combined_df.groupby(['method']).agg(
        rel_regret=('rel_regret', 'mean'),
    ).reset_index()

    # Save the aggregated results to a new CSV file (optional)
    aggregated_df.to_csv(f'aaai25_experiments/results/aggregated_results_{instance_folder}.csv', index=False)

    # Print the aggregated DataFrame
    print(aggregated_df)

    # Plotting the results
    plt.figure(figsize=(12, 6))
    plt.rcParams.update({'font.size': 20})
    sns.barplot(x='method', y='rel_regret', data=combined_df)

    # Adding titles and labels
    plt.title(f'RCPSP\max {instance_folder} Relative Regret')
    plt.xlabel('Method')
    plt.ylabel('Average Relative Regret')

    # Display the plot
    plt.legend(title='Method')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(f'aaai25_experiments/results/relative_regret_{instance_folder}.png')

    filtered_df = combined_df[combined_df['obj'] != np.inf]
    print(filtered_df)
    aggregated_df = filtered_df.groupby(['method']).agg(
        obj_count=('obj', 'count'),
    ).reset_index()

    print(aggregated_df)

    # Plotting the results
    plt.figure(figsize=(12, 6))
    sns.barplot(x='method', y='obj_count', data=aggregated_df)

    # Adding titles and labels
    plt.title(f'RCPSP\max {instance_folder} Feasible Solutions')
    plt.xlabel('Method')
    plt.ylabel('Count feasible objectives')

    # Display the plot
    plt.legend(title='Method')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(f'aaai25_experiments/results/feasible_solutions_{instance_folder}.png')


# Plot relative regret when not including the infeasible ones:
filtered_df = combined_df[combined_df['obj'] != np.inf]
aggregated_df = filtered_df.groupby(['method']).agg(
    rel_regret=('rel_regret', 'mean'),
).reset_index()

# Plotting the results
plt.figure(figsize=(12, 6))
sns.barplot(x='method', y='rel_regret', data=filtered_df)

# Adding titles and labels
plt.title(f'RCPSP\max {instance_folder} Rel Regret on Feasible Solutions')
plt.xlabel('Instance')
plt.ylabel('Relative regret on feasible solutions')

# Display the plot
plt.legend(title='Method')
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig(f'aaai25_experiments/results/filtered_relative_regret_{instance_folder}.png')