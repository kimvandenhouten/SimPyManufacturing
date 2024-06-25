import time
import copy
import numpy as np

from general.logger import get_logger
from rcpsp.solvers.check_feasibility import check_feasibility_rcpsp_max

logger = get_logger(__name__)
# TODO: synchronize this with other methods


def run_reactive_offline(rcpsp_max, time_limit_initial=60, mode="mean"):

    # TODO: the offline procedure can be done once per instance id
    start_offline = time.time()
    # Initialization
    if mode == "mean":
        durations = rcpsp_max.durations
    elif mode == "robust":
        durations = rcpsp_max.get_bound()
    elif mode == "quantile_0.25":
        lb = rcpsp_max.get_bound(mode="lower_bound")
        ub = rcpsp_max.get_bound(mode="upper_bound")
        durations = [int(lb[i] + 0.9 * (ub[i] - lb[i] + 1) - 1) for i in range(len(lb))]
    elif mode == "quantile_0.75":
        lb = rcpsp_max.get_bound(mode="lower_bound")
        ub = rcpsp_max.get_bound(mode="upper_bound")
        durations = [int(lb[i] + 0.9 * (ub[i] - lb[i] + 1) - 1) for i in range(len(lb))]
    elif mode == "quantile_0.5":
        lb = rcpsp_max.get_bound(mode="lower_bound")
        ub = rcpsp_max.get_bound(mode="upper_bound")
        durations = [int(lb[i] + 0.9 * (ub[i] - lb[i] + 1) - 1) for i in range(len(lb))]
    elif mode == "quantile_0.9":
        lb = rcpsp_max.get_bound(mode="lower_bound")
        ub = rcpsp_max.get_bound(mode="upper_bound")
        durations = [int(lb[i] + 0.9 * (ub[i] - lb[i] + 1) - 1) for i in range(len(lb))]
    else:
        raise NotImplementedError

    # Initialize data
    data_dict = {"instance_folder": rcpsp_max.instance_folder,
                 "instance_id": rcpsp_max.instance_id,
                 "obj": np.inf,
                 "method": f"reactive_{mode}",
                 "time_limit_rescheduling": None,
                 "time_limit_initial": time_limit_initial,
                 "solver_calls": 1,
                 "feasibility": False,
                 "real_durations": None,
                 "estimated_start_times": None,
                 "start_times": None,
                 "time_offline": np.inf,
                 "time_online": np.inf,
                 "mode": mode,
                 "estimated_durations": durations
                 }

    infeasible = False
    current_time = 0
    solver_calls = 1
    scheduled_start_times = [-1 for i in range(len(durations))]

    # Find Initial Estimated Schedule
    logger.debug(f'Making initial schedule with durations {durations}')
    res, data = rcpsp_max.solve(durations, time_limit=time_limit_initial, mode="Quiet")
    if res:
        start_times = data['start'].tolist()
        finish_offline = time.time()
        data_dict["estimated_start_times"] = start_times
        data_dict["time_offline"] = finish_offline - start_offline

    return data_dict


def run_reactive_online(rcpsp_max, duration_sample, data_dict, time_limit_rescheduling):

    data_dict = copy.deepcopy(data_dict)
    data_dict["time_limit_rescheduling"] = time_limit_rescheduling
    real_durations = duration_sample
    data_dict["real_durations"] = duration_sample

    logger.debug(f'real durations is {real_durations}')
    infeasible = True
    if data_dict["estimated_start_times"] is not None:
        estimated_start_times = data_dict["estimated_start_times"]

        start_online = time.time()
        solver_calls = 1

        logger.debug(f'Initial schedule is {estimated_start_times}')
        start_times = estimated_start_times
        estimated_durations = data_dict["estimated_durations"]

        infeasible = False
        current_time = 0
        solver_calls = 1
        scheduled_start_times = [-1 for _ in range(len(estimated_durations))]
        completed_jobs = set()
        while True:
            # Grabbing data and calculating the real completion times
            estimated_completion_times = np.array(
                [estimated_start_times[i] + estimated_durations[i] for i in range(len(estimated_start_times))])
            real_completion_times = np.array(
                [estimated_start_times[i] + real_durations[i] for i in range(len(estimated_start_times))])

            # Find the next completed task
            for i in np.argsort(real_completion_times):
                if i not in completed_jobs:
                    next_completed_job = i
                    curr_time = real_completion_times[i]
                    completed_jobs.add(i)
                    logger.debug(f'Next decision moment is at {curr_time} when {i} finishes')
                    break

            # Fix the starting times of tasks that already have started
            for i, t in enumerate(start_times):
                if t < curr_time:
                    scheduled_start_times[i] = t
                    #logger.debug(f'We started job {i} at {t}')
            logger.debug(f'Scheduled start times so far are {scheduled_start_times}')
            logger.debug(f'Job {next_completed_job} finished at {curr_time}, with duration '
                         f'{real_durations[next_completed_job]}')

            if len(completed_jobs) >= len(estimated_durations):  # If all jobs completed -> break
                break

            # Update the real values into the data
            new_duration = real_durations[next_completed_job]
            estimated_durations[next_completed_job] = new_duration

            # Run the updated problem again
            # TODO:
            logger.debug(
                f'Start rescheduling procedure with processing times {estimated_durations} and scheduled start times {scheduled_start_times}')
            if estimated_completion_times[next_completed_job] != real_completion_times[next_completed_job]:
                estimated_start_times, estimated_makespan = rcpsp_max.solve_reactive(estimated_durations, scheduled_start_times,
                                                                                current_time, time_limit=time_limit_rescheduling)
                solver_calls += 1

                if estimated_start_times is None:
                    infeasible = True
                    break
                logger.debug(f'Rescheduling leads to {estimated_start_times}')
            else:
                logger.debug(f'No rescheduling required')

    finish_online = time.time()
    if infeasible:
        feasibility, start_times = False, None
        makespan = np.inf
        logger.info(
            f'{rcpsp_max.instance_folder}_PSP{rcpsp_max.instance_id} is INFEASIBLE with true durations {real_durations} ')
        data_dict["time_offline"] = np.inf

    else:
        # TODO assert feasibility
        feasibility = True
        start_times = estimated_start_times
        finish_times = [start_times[i] + real_durations[i] for i in range(len(start_times))]

        # TODO: model this in RCPSP_max object
        check_feasibility = check_feasibility_rcpsp_max(start_times, finish_times, real_durations, rcpsp_max.capacity,
                                                        rcpsp_max.needs, rcpsp_max.temporal_constraints)

        assert check_feasibility
        makespan = max(finish_times)
        logger.info(f'{rcpsp_max.instance_folder}_PSP{rcpsp_max.instance_id} is FEASIBLE with makespan {makespan} with true durations {real_durations} ')
        logger.info(f'With {solver_calls} solver calls')

        data_dict["time_online"] = finish_online - start_online

    data_dict["feasibility"] = feasibility
    data_dict["start_times"] = start_times
    data_dict["obj"] = makespan

    return [data_dict]


