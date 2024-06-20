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
    df6 = pd.read_csv(f'experiments/aaai25_experiments/results/new_results_reactive_{instance_folder}_robust.csv')

    # Combine the DataFrames
    combined_df = pd.concat([df1, df2, df3, df4, df5, df6], ignore_index=True)
    # Save the aggregated results to a new CSV file (optional)
    combined_df.to_csv(f'experiments/aaai25_experiments/results/results_meeting_{instance_folder}.csv',
                         index=False)
