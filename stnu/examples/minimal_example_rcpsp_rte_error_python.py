from rcpsp.rcpsp_max.process_file import parse_sch_file
from rcpsp.solvers.RCPSP_CP_benchmark import RCPSP_CP_Benchmark
import pandas as pd
from stnu.algorithms.call_java_cstnu_tool import run_dc_algorithm
from stnu.algorithms.rte_star import rte_star
from stnu.get_resource_chains_reservations_benchmark import get_resource_chains, add_resource_chains
from classes.stnu import STNU, SampleStrategy
from stnu.java_comparison.stnu_to_xml_function import stnu_to_xml
import time
import classes.general
logger = classes.general.get_logger(__name__)
from rcpsp.solvers.check_feasibility import check_feasibility_rcpsp_max
import numpy as np
sample_mode = "sample"
data = []
results_location = "stnu/experiments/results/debugging_rcpsp_minimal_random_oracle_python_rte_error.csv"
nr_samples = 1


capacity = [7, 7, 7, 6, 7]
durations = [0, 7, 7, 6, 10, 1, 9]
needs = [[0, 0, 0, 0, 0], [5, 2, 0, 0, 2], [1, 4, 3, 1, 1], [2, 4, 5, 3, 3], [3, 1, 2, 1, 3], [3, 2, 2, 0, 3], [0, 0, 4, 5, 0]]
temporal_constraints = [(0, 0, 2), (0, 0, 3), (0, 0, 4), (0, 0, 5), (0, 0, 1), (1, 0, 6), (2, 10, 6), (3, -3, 6), (5, 0, 6)]

start = time.time()
rcpsp_max = RCPSP_CP_Benchmark(capacity, durations, None, needs, temporal_constraints, "RCPSP_max")
time_cp_solving = time.time() - start
res, schedule = rcpsp_max.solve(time_limit=60)

time_cp_solving = time.time() - start

if res:
    schedule = schedule.to_dict('records')
    start = time.time()
    resource_chains, resource_assignments = get_resource_chains(schedule, capacity, needs, complete=True)
    resource_chains = [(2, 3), (2, 6), (3, 6), (4, 1), (4, 6), (5, 3), (5, 1)]
    for i, dur in enumerate(durations):
        for (pred, lag, suc) in temporal_constraints:
            if pred == i:
                if lag >= 0:
                    print(f'MIN LAG: The start of task {pred} + {lag} <= the start of task {suc}')
                else:
                    print(f'MAX LAG: The start of task {pred} <= the start of task {suc} + {-lag}')
            if suc == i:
                print(f'LAG: the start of task {suc} >= the start of task {pred} + {lag}')

        for (pred, suc) in resource_chains:
            if pred == i:
                print(f'The finish of task {pred} <= the start of task {suc}')

    stnu = STNU.from_rcpsp_max_instance(durations, temporal_constraints, sink_source=1)
    stnu = add_resource_chains(stnu, resource_chains)
    stnu_to_xml(stnu, f"example_rcpsp_max_stnu_python", "stnu/java_comparison/xml_files")
    time_build_stnu = time.time() - start # Track time to build up STNU

    # Run the DC algorithm using the Java CSTNU tool, the result is written to a xml file
    start = time.time()
    dc, output_location = run_dc_algorithm("stnu/java_comparison/xml_files", f"example_rcpsp_max_stnu_python")
    logger.info(f'dc is {dc} and output location {output_location}')
    time_dc_checking = time.time() - start  # track time of DC-checking step

    # Read ESTNU xml file into Python object that was the output from the previous step
    # FIXME: Can we avoid this intermediate writing and reading step?
    estnu = STNU.from_graphml(output_location)
    if dc:
        # For i in nr_samples:
        for i in range(nr_samples):
            np.random.seed(i)
            # Sample a realisation for the contingent weights
            sample = estnu.sample_contingent_weights(strategy=SampleStrategy.RANDOM_EXECUTION_STRATEGY)
            logger.info(f'Sample that will be given to RTE_star: {sample}')

            # Run RTE algorithm with alternative oracle and store makespan
            start = time.time()
            if sample_mode == "standard":
                rte_data = rte_star(estnu, oracle="standard")
            else:
                rte_data = rte_star(estnu, oracle="sample", sample=sample)
            time_rte = time.time() - start
            if rte_data:
                logger.info(f'Final schedule is {rte_data.f}')
                makespan_stnu = max(rte_data.f.values())

                # TODO: check if the outcome schedule is feasible
                # Compute makespan lower bound by computing perfect information optimum with CP solver
                true_durations, start_times, finish_times = [], [], []
                for (task, dur) in enumerate(durations):

                    if task > 0 and task < len(durations) - 1:
                        node_idx_start = estnu.translation_dict_reversed[f'{task}_{STNU.EVENT_START}']
                        node_idx_finish = estnu.translation_dict_reversed[f'{task}_{STNU.EVENT_FINISH}']
                        start_times.append(rte_data.f[node_idx_start])
                        finish_times.append(rte_data.f[node_idx_finish])
                        if sample_mode == "standard":
                            true_durations.append(rte_data.f[node_idx_finish] - rte_data.f[node_idx_start])
                        else:
                            true_durations.append(sample[node_idx_finish])
                    else:
                        node_idx_start = estnu.translation_dict_reversed[f'{task}_{STNU.EVENT_START}']
                        node_idx_finish = estnu.translation_dict_reversed[f'{task}_{STNU.EVENT_START}']
                        start_times.append(rte_data.f[node_idx_start])
                        finish_times.append(rte_data.f[node_idx_finish])
                        true_durations.append(0)

                check_feasibility = check_feasibility_rcpsp_max(start_times, finish_times, true_durations, capacity, needs,
                                           temporal_constraints)
                logger.debug(
                    f'start times {start_times} finish times {finish_times}, durations {true_durations}')
                assert check_feasibility
                logger.info(f'The makespan obtained with the STNU algorithm is {makespan_stnu}')

                start = time.time()
                rcpsp_max = RCPSP_CP_Benchmark(capacity, true_durations, None, needs, temporal_constraints, "RCPSP_max")
                res, schedule = rcpsp_max.solve(time_limit=60)

                time_perfect_information = time.time() - start
                makespan_pi = max(schedule["end"].tolist())
                gap_pi = res.get_objective_gaps()[0]
                assert makespan_pi <= makespan_stnu
                logger.info(
                    f'makespan under perfect information is {makespan_pi}, makespan obtained with STNU is {makespan_stnu}, '
                    f'regret is {makespan_stnu - makespan_pi}')

            else:
                makespan_stnu = "inf"

                logger.info(f'For some reason the RTE start could not finish')




