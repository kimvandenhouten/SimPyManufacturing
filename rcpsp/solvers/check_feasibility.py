import numpy as np

import general.logger

logger = general.logger.get_logger(__name__)

def check_resources_schedule(earliest_start, durations, capacity, needs):
    num_resources = len(capacity)
    num_jobs = len(durations)
    used = np.zeros((sum(durations), num_resources))

    for job in range(num_jobs):
        start_job = earliest_start[job]
        duration = durations[job]
        job_needs = needs[job]
        used[start_job:start_job + duration] += job_needs

    resource_feasible = True
    for t in range(sum(durations)):
        for r, resource_usage in enumerate(used[t]):
            if resource_usage > capacity[r]:
                resource_feasible = False
                logger.debug(f'At time {t} resource {r} exceeds capacity with {resource_usage} while max cap {capacity[r]}')
    if resource_feasible:
        logger.debug(f'These start times / durations are resource feasible')
    else:
        logger.debug(f'These start times / durations are not resource feasible')
    return resource_feasible


def check_precedence_schedule(start_times, finish_times, successors):
    # TODO: implement the one with min and max time lags
    precedence_feasible = True

    for (job, job_successors) in enumerate(successors):
        for suc in job_successors:
            if finish_times[suc] < start_times[job]:
                logger.debug(f'violated because the start of job {suc} is < the finish of job {job}')
                precedence_feasible = False

    if precedence_feasible:
        logger.debug(f'This schedule is precedence feasible')
    else:
        logger.debug(f'This schedule is not precedence feasible')
    return precedence_feasible


def check_duration_feasible(start_times, finish_times, durations):
    duration_feasible = True
    for (job, dur) in enumerate(durations):
        if finish_times[job] - start_times[job] != dur or dur < 0:
            logger.debug(f'Infeasibility for job {job}')
            logger.debug(f'Start time {start_times[job]} and finish time: {finish_times[job]}, diff is {finish_times[job]-start_times[job]} and duration {durations[job]}')
            duration_feasible = False
    if duration_feasible:
        logger.debug(f'This schedule is duration feasible')
    else:
        logger.debug(f'This schedule is not duration feasible')
    return duration_feasible


def check_feasibility(start_times, finish_times, durations, capacity, successors, needs):
    duration_feasible = check_duration_feasible(start_times, finish_times, durations)
    if not duration_feasible:
        return False
    precedence_feasible = check_precedence_schedule(start_times, finish_times, successors)
    if not precedence_feasible:
        return False
    resource_feasible = check_resources_schedule(start_times, durations, capacity, needs)
    if not resource_feasible:
        return False
    return True


def check_precedence_schedule_rcpsp_max(start_times, temporal_constraints):
    precedence_feasible = True
    for (pred, lag, suc) in temporal_constraints:
        if start_times[pred] + lag > start_times[suc]:
            logger.debug(f'Start of {pred} is {start_times[pred]} and start of {suc} is {start_times[suc]}, while lag is {lag}')
            precedence_feasible = False
    if precedence_feasible:
        logger.debug(f'This schedule is precedence feasible')
    else:
        logger.debug(f'This schedule is not precedence feasible')
    return precedence_feasible


def check_feasibility_rcpsp_max(start_times, finish_times, durations, capacity, needs, temporal_constraints):
    duration_feasible = check_duration_feasible(start_times, finish_times, durations)
    if not duration_feasible:
        return False
    precedence_feasible = check_precedence_schedule_rcpsp_max(start_times, temporal_constraints)
    if not precedence_feasible:
        return False
    resource_feasible = check_resources_schedule(start_times, durations, capacity, needs)
    if not resource_feasible:
        return False
    return True
