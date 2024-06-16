# Import
import numpy as np
import pandas as pd
from rcpsp.solvers.RCPSP_CP_benchmark import RCPSP_CP_Benchmark

# Import reactive approach
from experiments.aaai25_experiments.run_reactive_approach import run_reactive_approach

# Import proactive approach
from experiments.aaai25_experiments.run_proactive_approach import run_saa, evaluate_saa

# Import STNU approach
from experiments.aaai25_experiments.run_stnu_approach import run_stnu_experiment

# GENERAL SETTINGS
SEED = 1
DIRECTORY_INSTANCES = 'rcpsp/rcpsp_max'
INSTANCE_FOLDERS = ["ubo50", "ubo100"]
INSTANCE_IDS = range(1, 91)
nb_scenarios_test = 10

# RUN REACTIVE EXPERIMENTS
# Settings reactive approach
np.random.seed(SEED)

# Run the experiments

# RUN STNU EXPERIMENTS
# Settings stnu approach

# Run the experiments
for mode in ["robust", "mean"]:
    np.random.seed(SEED)
    data = []
    for instance_folder in INSTANCE_FOLDERS:
        for instance_id in INSTANCE_IDS:
            rcpsp_max = RCPSP_CP_Benchmark.parsche_file(DIRECTORY_INSTANCES, instance_folder, instance_id)
            test_durations_sample = rcpsp_max.sample_durations(nb_scenarios_test)
            data += run_stnu_experiment(rcpsp_max, test_durations_sample, time_limit_pi=10, time_limit_cp_stnu=10)
            df = pd.DataFrame(data)
            df.to_csv(f"experiments/aaai25_experiments/robust_experiments/results_stnu_mean_vs_robust_{instance_folder}.csv", index=False)

