import sys
import numpy as np
import pandas as pd
from rcpsp.solvers.RCPSP_CP_benchmark import RCPSP_CP_Benchmark
from rcpsp.rcpsp_max.process_file import parse_sch_file
from rcpsp.solvers.check_feasibility import check_feasibility_rcpsp_max
from general.logger import get_logger

logger = get_logger(__name__)
# TODO: synchronize this with other methods

def randomize_real_durations(durations, distribution="uniform"):
    random_durations =[]
    for t in durations:
        if t == 0:
            random_durations.append(t)
        elif distribution == "normal":
            t = max(round(np.random.normal(t, t)), 1)
            random_durations.append(t)
        else:
            t = max(np.random.randint(round(t - 1 * np.sqrt(t)), round(t + 1 * np.sqrt(t))), 1)
            #t = max(np.random.randint(t - 2, t + 2), 1)
            random_durations.append(t)
    return random_durations


def run_reactive_approach(instance_id, instance_folder, time_limit_rescheduling=10, time_limit_pi=60):

    # Read information from RCPSP\max instance
    capacity, det_durations, needs, temporal_constraints = parse_sch_file(f'rcpsp/rcpsp_max/{instance_folder}/PSP{instance_id}.SCH')
    rcpsp_max = RCPSP_CP_Benchmark(capacity, det_durations, None, needs, temporal_constraints, "RCPSP_max")

    # Initialization
    durations = det_durations
    infeasible = False
    current_time = 0
    solver_calls = 0
    scheduled_start_times = [-1 for i in range(len(durations))]
    real_durations = randomize_real_durations(durations, distribution="uniform")
    logger.debug(f'real durations is {real_durations}')

    # Find Initial Estimated Schedule
    logger.debug(f'Making initial schedule with durations {durations}')

    estimated_result, estimated_makespan = rcpsp_max.solve_reactive(durations, scheduled_start_times, current_time)
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
                    logger.debug(f'First decision moment is at {curr_time} when {i} finishes')

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
            logger.debug(
                f'Start rescheduling procedure with processing times {durations} and scheduled start times {scheduled_start_times}')
            estimated_result, estimated_makespan = rcpsp_max.solve_reactive(durations, scheduled_start_times,
                                                                            current_time, time_limit=time_limit_rescheduling)
            solver_calls += 1

            if estimated_result is None:
                infeasible = True
                break
            logger.debug(f'Rescheduling leads to {estimated_result}')

    if infeasible:
        feasibility = False
        makespan = np.inf
        logger.info(f'Instance {instance_id} PSP{instance_id} with true durations {real_durations} is INFEASIBLE')
    else:
        # TODO assert feasibility
        feasibility = True
        start_times = estimated_result
        finish_times = [start_times[i] + real_durations[i] for i in range(len(start_times))]
        check_feasibility = check_feasibility_rcpsp_max(start_times, finish_times, real_durations, capacity, needs,
                                                        temporal_constraints)
        logger.info(f'Instance {instance_id} PSP{instance_id} with true durations {real_durations} is INFEASIBLE')
        assert check_feasibility
        makespan = estimated_makespan
        logger.info(f'Instance {instance_id} PSP{instance_id} with true durations {real_durations} is FEASIBLE with makespan {makespan}')

    # Run the updated problem again
    logger.debug(f'Start scheduling under perfect information with processing times {durations} '
                 f'which should match {real_durations}')
    current_time = 0
    scheduled_start_times = [-1 for i in range(len(durations))]
    result_pi, makespan_pi = rcpsp_max.solve_reactive(durations, scheduled_start_times, current_time, time_limit=time_limit_pi)

    if result_pi is None:
        feasibility_pi = False
        logger.debug(f'Result under perfect information is INFEASIBLE')

    else:
        feasibility_pi = True
        logger.debug(f'Result under perfect information is {result_pi} with makespan {makespan_pi}')

    if makespan == np.inf and makespan_pi == np.inf:
        relative_regret = 0
    elif makespan == np.inf and makespan_pi < np.inf:
        relative_regret = 100
    else:
        relative_regret = 100 * (makespan - makespan_pi) / makespan_pi

    logger.debug(f'Relative regret (%) is {relative_regret}')

    data = {"instance_folder": instance_folder, "instance_id": instance_id,
            "sample": sample, "rel_regret": relative_regret,
            "obj": makespan, "obj_pi": makespan_pi, "method": "reactive",
            "real_durations": real_durations, "start_times": start_times,
            "time_limit_pi": time_limit_pi, "time_limit_rescheduling": time_limit_rescheduling,
            "solver_calls": solver_calls, "feasibility": feasibility, "feasibility_pi": feasibility_pi}
    return [data]


data = []
np.random.seed(1)
instance_folder = "j10"
for instance_id in range(1, 100):
    for sample in range(10):
        data += run_reactive_approach(instance_id, instance_folder)
        data_df = pd.DataFrame(data)
        data_df.to_csv(f'experiments/aaai25_experiments/results/results_resactive_{instance_folder}.csv')