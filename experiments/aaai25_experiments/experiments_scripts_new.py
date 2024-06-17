# Import
import numpy as np
import pandas as pd
from rcpsp.solvers.RCPSP_CP_benchmark import RCPSP_CP_Benchmark
import ast

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
proactive = True
stnu = False


def check_pi_feasible(instance_folder, instance_id, sample_index, duration_sample):
    df = pd.read_csv(f'experiments/aaai25_experiments/results/results_pi_{instance_folder}.csv')
    filtered_df = df[(df['instance_id'] == instance_id) & (df['sample'] == sample_index)]

    assert len(filtered_df) == 1

    solve_result = filtered_df["solver_status"].tolist()[0]

    if solve_result in ["Infeasible", "Unknown"]:
        feasible = False
    else:
        feasible = True

    logger.info(f'{instance_folder}_PSP{instance_id} with {duration_sample} PI feasibility is {feasible}')

    if np.random.randint(0, 100) < 100:
        real_duration = filtered_df["sample_durations"].tolist()[0]
        real_duration = ast.literal_eval(real_duration)
        logger.info(f'pi duration {real_duration} and duration sample is {duration_sample}')
        assert real_duration == duration_sample
    return feasible


if reactive:
    # RUN REACTIVE EXPERIMENTS
    # Settings reactive approach


    # Run the experiments
    for instance_folder in INSTANCE_FOLDERS:
        data = []
        for instance_id in INSTANCE_IDS:
            np.random.seed(SEED)
            rcpsp_max = RCPSP_CP_Benchmark.parsche_file(DIRECTORY_INSTANCES, instance_folder, instance_id)
            test_durations_samples = rcpsp_max.sample_durations(nb_scenarios_test)

            for i, duration_sample in enumerate(test_durations_samples):
                pi_feasible = check_pi_feasible(instance_folder, instance_id, i, duration_sample)
                if pi_feasible:
                    data += run_reactive_approach(rcpsp_max, duration_sample)
                    data_df = pd.DataFrame(data)
                    data_df.to_csv(f'experiments/aaai25_experiments/results/results_reactive_{instance_folder}.csv', index=False)
                else:
                    logger.info(f'We can skip the reactive approach')

if proactive:
    # RUN PROACTIVE EXPERIMENTS
    # Settings proactive approach

    nb_scenarios_saa = 10
    time_limit_saa = 600

    # Run the experiments
    for instance_folder in INSTANCE_FOLDERS:
        data = []
        for instance_id in INSTANCE_IDS:
            np.random.seed(SEED)
            rcpsp_max = RCPSP_CP_Benchmark.parsche_file(DIRECTORY_INSTANCES, instance_folder, instance_id)
            test_durations_samples = rcpsp_max.sample_durations(nb_scenarios_test)

            for i, duration_sample in enumerate(test_durations_samples):
                pi_feasible = check_pi_feasible(instance_folder, instance_id, i, duration_sample)
                if pi_feasible:
                    data_dict = run_saa(rcpsp_max, nb_scenarios_saa, time_limit_saa)
                    data += evaluate_saa(rcpsp_max, data_dict, duration_sample)
                    data_df = pd.DataFrame(data)
                    data_df.to_csv(f"experiments/aaai25_experiments/results/results_proactive_new_{instance_folder}.csv", index=False)
                else:
                    logger.info(f'We can skip the proactive approach')

if stnu:
    # RUN STNU EXPERIMENTS
    # Settings stnu approach

    # Run the experiments
    for instance_folder in INSTANCE_FOLDERS:
        data = []
        for instance_id in INSTANCE_IDS:
            rcpsp_max = RCPSP_CP_Benchmark.parsche_file(DIRECTORY_INSTANCES, instance_folder, instance_id)
            np.random.seed(SEED)
            test_durations_samples = rcpsp_max.sample_durations(nb_scenarios_test)
            dc, estnu, data_dict = run_stnu(rcpsp_max)

            for i, duration_sample in enumerate(test_durations_samples):
                pi_feasible = check_pi_feasible(instance_folder, instance_id, i, duration_sample)
                if pi_feasible:
                    data += evaluate_stnu(dc, estnu, duration_sample, rcpsp_max, data_dict)
                    df = pd.DataFrame(data)
                    df.to_csv(f"experiments/aaai25_experiments/results/results_stnu_new_{instance_folder}.csv", index=False)
                else:
                    logger.info(f'We can skip the STNU approach')

