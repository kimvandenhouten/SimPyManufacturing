# Import
import numpy as np
import pandas as pd
from rcpsp.solvers.RCPSP_CP_benchmark import RCPSP_CP_Benchmark

from general.logger import get_logger
logger = get_logger(__name__)

# GENERAL SETTINGS
SEED = 1
DIRECTORY_INSTANCES = 'rcpsp/rcpsp_max'
INSTANCE_FOLDERS = ["j10", "j20", "j30", "ubo50", "ubo100"]
INSTANCE_IDS = range(1, 11)
nb_scenarios_test = 10
perfect_information = True
noise_factor = 2

if perfect_information:
    # Settings perfect information
    time_limit = 10

    # Start solving the instances with perfect information
    for instance_folder in INSTANCE_FOLDERS:
        data = []
        for instance_id in INSTANCE_IDS:
            np.random.seed(SEED)
            rcpsp_max = RCPSP_CP_Benchmark.parsche_file(DIRECTORY_INSTANCES, instance_folder, instance_id)
            test_durations_samples = rcpsp_max.sample_durations(nb_scenarios_test, noise_factor=2)

            for i, sample in enumerate(test_durations_samples):
                logger.info(f'Start {instance_folder}_PSP{instance_id} timelimit {time_limit} and sample {sample}')
                res, _ = rcpsp_max.solve(sample, time_limit=time_limit, mode="Quiet")
                if res:
                    logger.info(f'Res objective gap is {res.get_objective_gaps()[0]}')
                    logger.info(f'Res objective value is {res.get_objective_values()[0]}')
                    logger.info(f'Res solve time is {res.get_solve_time()}')
                    logger.info(f'Res solver status {res.get_solve_status()}')

                    data.append({"instance_folder": instance_folder, "instance_id": instance_id, "noise_factor": noise_factor,
                                 "sample": i, "sample_durations": sample, "time_limit": time_limit,
                                 "obj_gap": res.get_objective_gaps()[0], "obj_value": res.get_objective_values()[0],
                                 "solve_time": res.get_solve_time(), "solver_status": res.get_solve_status()})
                else:
                    logger.info(f'Res solve time is {res.get_solve_time()}')
                    logger.info(f'Res solver status {res.get_solve_status()}')

                    data.append({"instance_folder": instance_folder, "instance_id": instance_id, "noise_factor": noise_factor,
                                 "sample": i, "sample_durations": sample, "time_limit": time_limit,
                                     "solve_time": res.get_solve_time(), "solver_status": res.get_solve_status()})

                data_df = pd.DataFrame(data)
                data_df.to_csv(f"experiments/aaai25_experiments/results/results_pi_{instance_folder}_{noise_factor}.csv")

