import time

import numpy as np

from general.logger import get_logger
from rcpsp.solvers.check_feasibility import check_feasibility_rcpsp_max

logger = get_logger(__name__)
# TODO: synchronize this with other methods


def run_reactive_approach(rcpsp_max, duration_sample, time_limit_rescheduling=10, time_limit_initial=60, mode="mean"):

    start_offline = time.time()
    # Initialization
    if mode == "mean":
        durations = rcpsp_max.durations
    elif mode == "robust":
        durations = rcpsp_max.get_bound()
    else:
        raise NotImplementedError
    infeasible = False
    current_time = 0
    solver_calls = 0
    scheduled_start_times = [-1 for i in range(len(durations))]

    real_durations = duration_sample

    logger.debug(f'real durations is {real_durations}')

    # Find Initial Estimated Schedule
    logger.debug(f'Making initial schedule with durations {durations}')

    estimated_result, estimated_makespan = rcpsp_max.solve_reactive(durations, scheduled_start_times, current_time,
                                                                    time_limit=time_limit_initial)
    finish_offline = time.time()
    start_online = time.time()
    solver_calls += 1

    if estimated_result is None:
        infeasible = True
    logger.debug(f'Initial schedule is {estimated_result}')
    start_times = estimated_result

    if infeasible is False:
        curr_time = 0
        completed_jobs = set()
        while True:
            # Grabbing data and calculating the real completion times
            estimated_completion_times = np.array(
                [estimated_result[i] + durations[i] for i in range(len(estimated_result))])
            real_completion_times = np.array(
                [estimated_result[i] + real_durations[i] for i in range(len(estimated_result))])

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
                if t <= curr_time:
                    scheduled_start_times[i] = t
                    logger.debug(f'We started job {i} at {t}')

            logger.debug(f'Job {next_completed_job} finished at {curr_time}, with duration '
                         f'{real_durations[next_completed_job]}')

            if len(completed_jobs) >= len(durations):  # If all jobs completed -> break
                break

            # Update the real values into the data
            new_duration = real_durations[next_completed_job]
            durations[next_completed_job] = new_duration

            # Run the updated problem again
            # TODO:
            logger.debug(
                f'Start rescheduling procedure with processing times {durations} and scheduled start times {scheduled_start_times}')
            estimated_result, estimated_makespan = rcpsp_max.solve_reactive(durations, scheduled_start_times,
                                                                            current_time, time_limit=time_limit_rescheduling)
            solver_calls += 1

            if estimated_result is None:
                infeasible = True
                break
            logger.debug(f'Rescheduling leads to {estimated_result}')

    finish_online = time.time()
    if infeasible:
        feasibility = False
        makespan = np.inf
        logger.info(
            f'Instance PSP{rcpsp_max.instance_id} is INFEASIBLE with true durations {real_durations} ')


    else:
        # TODO assert feasibility
        feasibility = True
        start_times = estimated_result
        finish_times = [start_times[i] + real_durations[i] for i in range(len(start_times))]

        # TODO: model this in RCPSP_max object
        check_feasibility = check_feasibility_rcpsp_max(start_times, finish_times, real_durations, rcpsp_max.capacity,
                                                        rcpsp_max.needs, rcpsp_max.temporal_constraints)

        assert check_feasibility
        makespan = estimated_makespan
        logger.info(f'Instance PSP{rcpsp_max.instance_id} is FEASIBLE with makespan {makespan} with true durations {real_durations} ')

    data = {"instance_folder": rcpsp_max.instance_folder,
            "instance_id": rcpsp_max.instance_id,
            "obj": makespan,
            "method": "reactive",
            "time_limit_rescheduling": time_limit_rescheduling,
            "time_limit_initial": time_limit_initial,
            "solver_calls": solver_calls,
            "feasibility": feasibility,
            "real_durations": real_durations,
            "start_times": start_times,
            "time_offline": finish_offline - start_offline,
            "time_online": finish_online - start_online,
            "mode": mode
            }

    return [data]


