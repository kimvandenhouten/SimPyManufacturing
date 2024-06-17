# Import
import numpy as np
import pandas as pd

import general
from general.logger import get_logger
from rcpsp.solvers.RCPSP_CP_benchmark import RCPSP_CP_Benchmark
from rcpsp.solvers.check_feasibility import check_feasibility_rcpsp_max

logger = general.logger.get_logger(__name__)

# Import reactive approach

# GENERAL SETTINGS
SEED = 1
DIRECTORY_INSTANCES = 'rcpsp/rcpsp_max'
INSTANCE_FOLDERS = ["ubo50", "ubo100"]
INSTANCE_IDS = range(1, 91)
nb_scenarios_test = 10
time_limit = 10

# RUN REACTIVE EXPERIMENTS

# Run the experiments
results = []

for instance_folder in INSTANCE_FOLDERS:
    for instance_id in INSTANCE_IDS:
        rcpsp_max = RCPSP_CP_Benchmark.parsche_file(DIRECTORY_INSTANCES, instance_folder, instance_id)

        # Solve very conservative schedule
        upper_bound = rcpsp_max.get_bound()
        logger.info(f'Start solving upper bound schedule {upper_bound}')
        res, data = rcpsp_max.solve(upper_bound, time_limit=time_limit, mode="Quiet")

        if res:
            start_times = data['start'].tolist()
            logger.info(f'Robust start times are {start_times}')
        else:
            logger.info(f'No robust schedule exists')

        if res:
            np.random.seed(SEED)
            test_durations_samples = rcpsp_max.sample_durations(nb_scenarios_test)

            for i, sample in enumerate(test_durations_samples):

                # Check feasibility
                finish_times = [start_times[i] + sample[i] for i in range(len(start_times))]
                check_feasibility = check_feasibility_rcpsp_max(start_times, finish_times, sample, rcpsp_max.capacity,
                                            rcpsp_max.needs, rcpsp_max.temporal_constraints)
                if check_feasibility:
                    logger.info(f'With sample {sample} still feasible')
                    feasibility = True
                else:
                    logger.warning(f'NOT FEASIBLE: for {sample}')
                    feasibility = False

                results.append({
                    "instance_folder": rcpsp_max.instance_folder,
                    "instance_id": rcpsp_max.instance_id,
                    "method": "robust",
                    "time_limit": time_limit,
                    "feasibility": feasibility
                })

                results_df = pd.DataFrame(results)
                results_df.to_csv(f"experiments/aaai25_experiments/feasibility_experiments/results_{instance_folder}.csv")








