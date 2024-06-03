import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# Read the CSV files into DataFrames
df1 = pd.read_csv('aaai25_experiments/results/results_saa.csv')
print(len(df1))
df2 = pd.read_csv('aaai25_experiments/results/results_stnu.csv')
print(len(df2))
# Combine the DataFrames
combined_df = pd.concat([df1, df2])
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
aggregated_df.to_csv('aaai25_experiments/results/aggregated_results.csv', index=False)

# Print the aggregated DataFrame
print(aggregated_df)

# Plotting the results
plt.figure(figsize=(12, 6))
sns.barplot(x='method', y='rel_regret', data=aggregated_df)

# Adding titles and labels
plt.title('RCPSP\max J10 Relative Regret')
plt.xlabel('Instance')
plt.ylabel('Average Relative Regret')

# Display the plot
plt.legend(title='Method')
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig('aaai25_experiments/results/relative_regret.png')

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
plt.title('RCPSP\max J10 Feasible Solutions')
plt.xlabel('Instance')
plt.ylabel('Count feasible objectives')

# Display the plot
plt.legend(title='Method')
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig('aaai25_experiments/results/feasible_solutions.png')