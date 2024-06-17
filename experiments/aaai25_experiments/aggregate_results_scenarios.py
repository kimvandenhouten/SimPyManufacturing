import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

for instance_folder in ["j10", "j30"]:
    # Read the CSV files into DataFrames
    df = pd.read_csv(f'aaai25_experiments/results/results_saa_scenarios_{instance_folder}.csv')

    # Group by "instance" and "method" and calculate the average "rel_regret"
    aggregated_df = df.groupby(['nr_samples']).agg(
        rel_regret=('rel_regret', 'mean'),
    ).reset_index()

    # Plotting the results
    plt.figure(figsize=(12, 6))
    plt.rcParams.update({'font.size': 20})
    sns.barplot(x='nr_samples', y='rel_regret', data=df)

    # Adding titles and labels
    plt.title('SAA approach effect nr samples')
    plt.xlabel('Method')
    plt.ylabel('Average Relative Regret (%)')

    # Display the plot
    plt.legend(title='Method')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(f'aaai25_experiments/results/saa_nr_samples_{instance_folder}.png')

