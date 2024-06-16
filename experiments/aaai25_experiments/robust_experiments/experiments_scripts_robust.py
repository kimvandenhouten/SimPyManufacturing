# Import
import numpy as np
import pandas as pd
from rcpsp.solvers.RCPSP_CP_benchmark import RCPSP_CP_Benchmark

# Import reactive approach
from experiments.aaai25_experiments.run_reactive_approach import run_reactive_approach

# Import STNU approach
from experiments.aaai25_experiments.run_stnu_approach import run_stnu_experiment

# GENERAL SETTINGS
SEED = 1
DIRECTORY_INSTANCES = 'rcpsp/rcpsp_max'
INSTANCE_FOLDERS = ["j10", "j20", "j30", "ubo50", "ubo100"]
INSTANCE_IDS = range(1, 51)
nb_scenarios_test = 10


# RUN REACTIVE EXPERIMENTS
# Settings reactive approach
np.random.seed(SEED)

# Run the experiments
data = []
for instance_folder in INSTANCE_FOLDERS:
    for instance_id in INSTANCE_IDS:
        rcpsp_max = RCPSP_CP_Benchmark.parsche_file(DIRECTORY_INSTANCES, instance_folder, instance_id)
        test_durations_samples = rcpsp_max.sample_durations(nb_scenarios_test)

        for duration_sample in test_durations_samples:
            data += run_reactive_approach(rcpsp_max, duration_sample, mode="robust")
            data_df = pd.DataFrame(data)
            data_df.to_csv(f'experiments/aaai25_experiments/robust_experiments/results_reactive_{instance_folder}.csv', index=False)


# RUN STNU EXPERIMENTS
# Settings stnu approach
np.random.seed(SEED)

# Run the experiments
data = []
for instance_folder in INSTANCE_FOLDERS:
    for instance_id in INSTANCE_IDS:
        rcpsp_max = RCPSP_CP_Benchmark.parsche_file(DIRECTORY_INSTANCES, instance_folder, instance_id)
        test_durations_sample = rcpsp_max.sample_durations(nb_scenarios_test)
        data += run_stnu_experiment(rcpsp_max, test_durations_sample, mode="robust")
        df = pd.DataFrame(data)
        df.to_csv(f"experiments/aaai25_experiments/robust_experiments/results_stnu_{instance_folder}.csv", index=False)

