from rcpsp.rcpsp_max.process_file import parse_sch_file
from rcpsp.solvers.RCPSP_CP_benchmark import RCPSP_CP_Benchmark
import time
import classes.general
logger = classes.general.get_logger(__name__)
from rcpsp.solvers.check_feasibility import check_feasibility_rcpsp_max
import numpy as np
sample_mode = "sample"
data = []
results_location = "aaai25_experiments/results/results_saa.csv"
nr_samples = 10
for instance_folder in ["j10"]:
    for instance_id in range(1, 2):
        logger.info(f'Start instance {instance_id}')
        capacity, durations, needs, temporal_constraints = parse_sch_file(f'rcpsp/rcpsp_max/{instance_folder}/PSP{instance_id}.SCH')
        start = time.time()
        rcpsp_max = RCPSP_CP_Benchmark(capacity, durations, None, needs, temporal_constraints, "RCPSP_max")

        # TODO: implement the sampling strategy to sample scenarios
        train_durations_sample = rcpsp_max.sample_durations(10)
        print(train_durations_sample)

        # TODO: solve the SAA approach
        res, start_times = rcpsp_max.solve_saa(train_durations_sample, 120)
        print(f'start times are {start_times}')

        # TODO: evaluate on test scenarios (simulation)
        test_durations_sample = rcpsp_max.sample_durations(100)

        feasibilities, makespans = [], []
        for duration_sample in test_durations_sample:
            finish_times = [start_times[i] + duration_sample[i] for i in range(len(duration_sample))]
            feasibility = check_feasibility_rcpsp_max(start_times, finish_times, duration_sample, capacity, needs,
                                        temporal_constraints)
            feasibilities.append(feasibility)
            makespan= max(finish_times)
            makespans.append(makespan)

            rcpsp_max = RCPSP_CP_Benchmark(capacity, duration_sample, None, needs, temporal_constraints, "RCPSP_max")
            res, schedule = rcpsp_max.solve(time_limit=60)

            time_perfect_information = time.time() - start
            makespan_pi = max(schedule["end"].tolist())
            gap_pi = res.get_objective_gaps()[0]
            assert makespan_pi <= makespan
            logger.info(
                f'makespan under perfect information is {makespan_pi}, makespan obtained with proactive schedule is {makespan}, '
                f'regret is {makespan- makespan_pi}')

        print(f'{sum(feasibilities)} feasible solutions')
        print(f'average makespan is {np.mean(makespans)}')


