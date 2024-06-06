import re
import general.logger
logger = general.logger.get_logger(__name__)
def parse_sch_file(filename):
    with open(filename, 'r') as file:
        lines = file.readlines()

    # Extract the header information
    header = lines[0].strip().split()
    n_tasks = int(header[0])
    n_res = int(header[1])

    # Initialize structures
    durations = [0] * (n_tasks + 2)  # Assuming tasks are numbered from 0 to n_tasks + 1
    needs = []
    temporal_relations = []

    # Parse each task line
    for line in lines[1:n_tasks+2]:
        parts = line.strip().split()
        task_id = int(parts[0])
        num_successors = int(parts[2])
        successors = parts[3: 3 +num_successors]
        lags = parts[3 +num_successors:]
        for i, suc in enumerate(successors):
            eval_lags = lags[i]
            eval_lags = eval_lags.strip('[]').split(',')
            eval_lags = [int(i) for i in eval_lags]
            for lag in eval_lags:
                temporal_relations.append((task_id, int(lag), int(suc)))

    for line in lines[n_tasks+3:-1]:
        parts = line.strip().split()
        task_id = int(parts[0])
        duration = int(parts[2])
        durations[task_id] = duration
        resource_needs = parts[3:]
        resource_needs = [int(i) for i in resource_needs ]
        needs.append(resource_needs)

    # Resource capacities and the last resource line
    capacity = list(map(int, lines[-1].strip().split()))

    # Outputs for MiniZinc
    logger.info("Resource capacities:", capacity)
    logger.info("Durations:", durations)
    logger.info("Temporal relations:", temporal_relations)
    logger.info("Resource needs:",  needs)

    return capacity, durations, needs, temporal_relations
