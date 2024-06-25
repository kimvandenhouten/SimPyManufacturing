# Import
import numpy as np
import pandas as pd
from rcpsp.solvers.RCPSP_CP_benchmark import RCPSP_CP_Benchmark
import ast

# Import reactive approach
from experiments.aaai25_experiments.run_reactive_approach import run_reactive_offline, run_reactive_online

# Import proactive approach
from experiments.aaai25_experiments.run_proactive_approach import run_proactive_offline, run_proactive_online

# Import STNU approach
from experiments.aaai25_experiments.run_stnu_approach import run_stnu_offline, run_stnu_online


from general.logger import get_logger
logger = get_logger(__name__)

# GENERAL SETTINGS
SEED = 1
DIRECTORY_INSTANCES = 'rcpsp/rcpsp_max'
INSTANCE_FOLDERS = ["j10", "j20", "j30", "ubo50", "ubo100"]
INSTANCE_IDS = range(1, 50)
nb_scenarios_test = 0
stnu = True


def check_pi_feasible(instance_folder, instance_id, sample_index, duration_sample):
    df = pd.read_csv(f'experiments/aaai25_experiments/results/results_pi_{instance_folder}.csv')
    filtered_df = df[(df['instance_id'] == instance_id) & (df['sample'] == sample_index)]
    assert len(filtered_df) == 1

    solve_result = filtered_df["solver_status"].tolist()[0]

    if solve_result in ["Infeasible", "Unknown"]:
        feasible = False
    else:
        feasible = True

    logger.debug(f'{instance_folder}_PSP{instance_id} with {duration_sample} PI feasibility is {feasible}')

    if np.random.randint(0, 100) < 100:
        real_duration = filtered_df["sample_durations"].tolist()[0]
        real_duration = ast.literal_eval(real_duration)
        logger.debug(f'pi duration {real_duration} and duration sample is {duration_sample}')
        assert real_duration == duration_sample

    if feasible:
        obj_pi = filtered_df['obj_value'].to_list()[0]
    else:
        obj_pi = np.inf
    return feasible, obj_pi


# RUN STNU EXPERIMENTS
# Settings stnu approach
time_limit_cp_stnu = 60

# Run the experiments
data = []
for mode in ["quantile_0.25", "mean", "quantile_0.75", "robust"]:
    for instance_folder in INSTANCE_FOLDERS:

        for instance_id in INSTANCE_IDS:
            rcpsp_max = RCPSP_CP_Benchmark.parsche_file(DIRECTORY_INSTANCES, instance_folder, instance_id)
            np.random.seed(SEED)
            test_durations_samples = rcpsp_max.sample_durations(nb_scenarios_test)
            dc, estnu, data_dict = run_stnu_offline(rcpsp_max, time_limit_cp_stnu=time_limit_cp_stnu, mode=mode)

            data.append({'instance_folder': instance_folder, 'instance_id': instance_id, 'mode': mode,
                         "dc": dc})

            data_df = pd.DataFrame(data)
            data_df.to_csv("experiments/aaai25_experiments/results/stnu/dc_checking.csv")
