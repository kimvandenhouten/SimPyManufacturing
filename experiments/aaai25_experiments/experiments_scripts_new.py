# Import
import numpy as np
import pandas as pd
from rcpsp.solvers.RCPSP_CP_benchmark import RCPSP_CP_Benchmark

# Import reactive approach
from experiments.aaai25_experiments.run_reactive_approach import run_reactive_approach

# Import proactive approach
from experiments.aaai25_experiments.run_proactive_approach import run_saa, evaluate_saa

# Import STNU approach
from experiments.aaai25_experiments.run_stnu_approach import run_stnu, evaluate_stnu

from general.logger import get_logger
logger = get_logger(__name__)

# GENERAL SETTINGS
SEED = 1
DIRECTORY_INSTANCES = 'rcpsp/rcpsp_max'
INSTANCE_FOLDERS = ["j10"]
INSTANCE_IDS = range(1, 10)
nb_scenarios_test = 10
perfect_information = False
reactive = False
proactive = False
stnu = True


if perfect_information:
    # Settings perfect information
    time_limit = 600

    # Start solving the instances with perfect information
    for instance_folder in INSTANCE_FOLDERS:
        data = []
        for instance_id in INSTANCE_IDS:
            rcpsp_max = RCPSP_CP_Benchmark.parsche_file(DIRECTORY_INSTANCES, instance_folder, instance_id)

            np.random.seed(SEED)
            test_durations_samples = rcpsp_max.sample_durations(nb_scenarios_test)

            for i, sample in enumerate(test_durations_samples):
                logger.info(f'Start {instance_folder}_PSP{instance_id} timelimit {time_limit}')
                res, _ = rcpsp_max.solve(sample, time_limit=time_limit, mode="Quiet")
                if res:
                    logger.info(f'Res objective gap is {res.get_objective_gaps()[0]}')
                    logger.info(f'Res objective value is {res.get_objective_values()[0]}')
                    logger.info(f'Res solve time is {res.get_solve_time()}')
                    logger.info(f'Res solver status {res.get_solve_status()}')

                    data.append({"instance_folder": instance_folder, "instance_id": instance_id, "sample": i,
                                 "sample_durations": sample, "time_limit": time_limit,
                                 "obj_gap": res.get_objective_gaps()[0], "obj_value": res.get_objective_values()[0],
                                 "solve_time": res.get_solve_time(), "solver_status": res.get_solve_status()})
                else:
                    logger.info(f'Res solve time is {res.get_solve_time()}')
                    logger.info(f'Res solver status {res.get_solve_status()}')

                    data.append({"instance_folder": instance_folder, "instance_id": instance_id, "sample": i,
                                     "sample_durations": sample, "time_limit": time_limit,
                                     "solve_time": res.get_solve_time(), "solver_status": res.get_solve_status()})

                data_df = pd.DataFrame(data)
                data_df.to_csv(f"experiments/aaai25_experiments/results/results_pi_{instance_folder}.csv")

if reactive:
    # RUN REACTIVE EXPERIMENTS
    # Settings reactive approach
    np.random.seed(SEED)

    # Run the experiments
    for instance_folder in INSTANCE_FOLDERS:
        data = []
        for instance_id in INSTANCE_IDS:
            rcpsp_max = RCPSP_CP_Benchmark.parsche_file(DIRECTORY_INSTANCES, instance_folder, instance_id)
            test_durations_samples = rcpsp_max.sample_durations(nb_scenarios_test)

            for duration_sample in test_durations_samples:
                data += run_reactive_approach(rcpsp_max, duration_sample)
                data_df = pd.DataFrame(data)
                data_df.to_csv(f'experiments/aaai25_experiments/results/results_reactive_{instance_folder}.csv', index=False)

if proactive:
    # RUN PROACTIVE EXPERIMENTS
    # Settings proactive approach
    np.random.seed(SEED)
    nb_scenarios_saa = 10
    time_limit_saa = 600

    # Run the experiments
    for instance_folder in INSTANCE_FOLDERS:
        data = []
        for instance_id in INSTANCE_IDS:
            rcpsp_max = RCPSP_CP_Benchmark.parsche_file(DIRECTORY_INSTANCES, instance_folder, instance_id)
            test_durations_sample = rcpsp_max.sample_durations(nb_scenarios_test)
            res, start_times, time_offline = run_saa(rcpsp_max, nb_scenarios_saa, time_limit_saa)
            data += evaluate_saa(rcpsp_max, res, start_times, time_offline, test_durations_sample, nb_scenarios_saa,
                                 time_limit_saa)
            data_df = pd.DataFrame(data)
            data_df.to_csv(f"experiments/aaai25_experiments/results/results_proactive_{instance_folder}.csv", index=False)

if stnu:
    # RUN STNU EXPERIMENTS
    # Settings stnu approach
    np.random.seed(SEED)

    # Run the experiments
    for instance_folder in INSTANCE_FOLDERS:
        data = []
        for instance_id in INSTANCE_IDS:
            rcpsp_max = RCPSP_CP_Benchmark.parsche_file(DIRECTORY_INSTANCES, instance_folder, instance_id)
            test_durations_sample = rcpsp_max.sample_durations(nb_scenarios_test)

            for duration_sample in test_durations_sample:
                dc, estnu, data_dict = run_stnu(rcpsp_max)
                data += evaluate_stnu(dc, estnu, duration_sample, rcpsp_max, data_dict)
                df = pd.DataFrame(data)
                df.to_csv(f"experiments/aaai25_experiments/results/results_stnu_new_{instance_folder}.csv", index=False)

