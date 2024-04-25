import pandas as pd

data = pd.read_csv(f'stnu/experiments/results/rcpsp_stnu.csv')
data['regret'] = data['makespan_stnu'] - data['makespan_lb']
data['relative_regret'] = data['regret'] / data['makespan_lb']
data['instance_set'] = data['instance_name'].str.slice(0, 3)
print(data['instance_set'])

selected_columns = data[['instance_name', 'regret', 'relative_regret', 'makespan_lb', 'makespan_stnu']]

# Group by 'instance_name' and calculate mean and std
aggregated_data = selected_columns.groupby('instance_name').agg(['mean', 'std']).reset_index()

for column in ['regret', 'relative_regret', 'makespan_lb', 'makespan_stnu']:
    aggregated_data[(column, 'mean')] = aggregated_data[(column, 'mean')].round(2)
    aggregated_data[(column, 'std')] = aggregated_data[(column, 'std')].round(3)

# Optional: Flatten the columns for easier handling
aggregated_data.columns = ['_'.join(col).strip() if col[1] else col[0] for col in aggregated_data.columns.values]
print(aggregated_data)
# Save the aggregated data to a new CSV (optional)
aggregated_data.to_csv('stnu/experiments/results/aggregated_data_rcpsp_stnu.csv', index=False)


# Aggregate on instance set level

selected_columns = data[['instance_set', 'regret', 'relative_regret']]

# Group by 'instance_name' and calculate mean and std
aggregated_data = selected_columns.groupby('instance_set').agg(['mean', 'std']).reset_index()

for column in ['regret', 'relative_regret']:
    aggregated_data[(column, 'mean')] = aggregated_data[(column, 'mean')].round(2)
    aggregated_data[(column, 'std')] = aggregated_data[(column, 'std')].round(3)

# Optional: Flatten the columns for easier handling
aggregated_data.columns = ['_'.join(col).strip() if col[1] else col[0] for col in aggregated_data.columns.values]
print(aggregated_data)
# Save the aggregated data to a new CSV (optional)
aggregated_data.to_csv('stnu/experiments/results/aggregated_data_rcpsp_stnu_per_instance_set.csv', index=False)

# Aggregate runtime information
selected_columns = data[['instance_set', "time_initial_cp", "time_build_stnu", "time_dc_checking", "time_rte", "time_cp_lb"]]

# Group by 'instance_name' and calculate mean and std
aggregated_data = selected_columns.groupby('instance_set').agg(['mean', 'std']).reset_index()

for column in ["time_initial_cp", "time_build_stnu", "time_dc_checking", "time_rte", "time_cp_lb"]:
    aggregated_data[(column, 'mean')] = aggregated_data[(column, 'mean')].round(1)
    aggregated_data[(column, 'std')] = aggregated_data[(column, 'std')].round(1)

# Optional: Flatten the columns for easier handling
aggregated_data.columns = ['_'.join(col).strip() if col[1] else col[0] for col in aggregated_data.columns.values]
print(aggregated_data)
# Save the aggregated data to a new CSV (optional)
aggregated_data.to_csv('stnu/experiments/results/aggregated_data_rcpsp_stnu_per_instance_set_runtime.csv', index=False)