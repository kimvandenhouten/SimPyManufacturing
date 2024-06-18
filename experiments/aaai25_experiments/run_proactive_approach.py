import time
import copy
import numpy as np

import general.logger
from rcpsp.solvers.check_feasibility import check_feasibility_rcpsp_max

logger = general.logger.get_logger(__name__)


def run_saa(rcpsp_max, nb_scenarios_saa, time_limit_saa):

    # Initialize results dict.
    data_dict = {
        "instance_folder": rcpsp_max.instance_folder,
        "instance_id": rcpsp_max.instance_id,
        "method": "proactive",
        "nr_samples": nb_scenarios_saa,
        "obj": np.inf,
        "time_limit_SAA": time_limit_saa,
        "feasibility": False,
        "real_durations": None,
        "start_times": None,
        "time_offline": np.inf,
        "time_online": np.inf
    }

    start_offline = time.time()
    logger.debug(f'Start solving SAA instance {rcpsp_max.instance_id} with {nb_scenarios_saa} scenarios')

    # Sample scenarios for Sample Average Approximation
    train_durations_sample = rcpsp_max.sample_durations(nb_scenarios_saa)

    logger.debug(train_durations_sample)

    #  Solve the SAA approach
    res, start_times = rcpsp_max.solve_saa(train_durations_sample, time_limit_saa)
    finish_offline = time.time()
    if res:
        data_dict['time_offline'] = finish_offline - start_offline
        data_dict['start_times'] = start_times

    return data_dict


def evaluate_saa(rcpsp_max, data_dict, duration_sample):

    data_dict = copy.deepcopy(data_dict)
    start_times = data_dict['start_times']
    data_dict['real_durations'] = duration_sample
    feasibility = False

    if start_times is not None:
        logger.debug(f'SAA found a solution, start times are {start_times}')

        # Evaluate on duration sample
        start_online = time.time()
        finish_times = [start_times[i] + duration_sample[i] for i in range(len(duration_sample))]
        feasibility = check_feasibility_rcpsp_max(start_times, finish_times, duration_sample, rcpsp_max.capacity,
                                                  rcpsp_max.needs, rcpsp_max.temporal_constraints)
        objective = max(finish_times) if feasibility else np.inf
        finish_online = time.time()
        data_dict["time_online"] = finish_online - start_online
        data_dict["obj"] = objective
        data_dict["feasibility"] = feasibility

    if feasibility:
        logger.info(f'Instance PSP{rcpsp_max.instance_id} is FEASIBLE with makespan {objective} with true durations {duration_sample} ')
    else:
        logger.info(f'Instance PSP{rcpsp_max.instance_id} is INFEASIBLE with true durations {duration_sample} ')
    return [data_dict]






