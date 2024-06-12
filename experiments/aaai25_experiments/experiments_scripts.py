# Import
import numpy as np
import pandas as pd
from rcpsp.solvers.RCPSP_CP_benchmark import RCPSP_CP_Benchmark

# Import reactive approach
from experiments.aaai25_experiments.run_reactive_approach import run_reactive_approach

# Import proactive approach
from experiments.aaai25_experiments.run_proactive_approach import run_saa, evaluate_saa

# GENERAL SETTINGS
SEED = 1
DIRECTORY_INSTANCES = 'rcpsp/rcpsp_max'
INSTANCE_FOLDERS = ["j10"]
INSTANCE_IDS = range(1, 11)

# RUN REACTIVE EXPERIMENTS
# Settings reactive approach
np.random.seed(SEED)
nb_scenarios_test = 10

data = []
for instance_folder in INSTANCE_FOLDERS:
    for instance_id in INSTANCE_IDS:
        rcpsp_max = RCPSP_CP_Benchmark.parsche_file(DIRECTORY_INSTANCES, instance_folder, instance_id)
        test_durations_samples = rcpsp_max.sample_durations(nb_scenarios_test)

        for duration_sample in test_durations_samples:
            data += run_reactive_approach(rcpsp_max, duration_sample)
            data_df = pd.DataFrame(data)
            data_df.to_csv(f'experiments/aaai25_experiments/results/results_reactive.csv')

# RUN PROACTIVE EXPERIMENTS
# Settings proactive approach
np.random.seed(SEED)
nb_scenarios_test = 10
time_limit_saa = 600

data = []
for nb_scenarios_saa in [10]:
    for instance_folder in INSTANCE_FOLDERS:
        for instance_id in INSTANCE_IDS:
            rcpsp_max = RCPSP_CP_Benchmark.parsche_file(DIRECTORY_INSTANCES, instance_folder, instance_id)
            test_durations_sample = rcpsp_max.sample_durations(nb_scenarios_test)
            res, start_times = run_saa(rcpsp_max, nb_scenarios_saa, time_limit_saa)
            data += evaluate_saa(rcpsp_max, res, start_times, test_durations_sample, nb_scenarios_saa, time_limit_saa)
            data_df = pd.DataFrame(data)
            data_df.to_csv("experiments/aaai25_experiments/results/results_proactive.csv")