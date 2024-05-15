from rcpsp.rcpsp_max.process_file import parse_sch_file
from rcpsp.solvers.RCPSP_CP_benchmark import RCPSP_CP_Benchmark
import pandas as pd
from stnu.algorithms.call_java_cstnu_tool import run_dc_algorithm, run_rte_algorithm
from stnu.get_resource_chains_reservations_benchmark import get_resource_chains, add_resource_chains
from classes.stnu import STNU
from stnu.java_comparison.stnu_to_xml_function import stnu_to_xml
import time
import classes.general
logger = classes.general.get_logger(__name__)
from rcpsp.solvers.check_feasibility import check_feasibility_rcpsp_max
import numpy as np

data = []
results_location = "stnu/experiments/results/debugging_minimal_example.csv"
nr_samples = 1
instance_folder = "j10"


def run_minimal_example(capacity, durations, needs, temporal_constraints):


    row = {"instance": f"minimal_example", "status": "infeasible", "sample": 0,
           "rcpsp/max_feasible": "NotApplicable"}
    rows = []

    start = time.time()
    rcpsp_max = RCPSP_CP_Benchmark(capacity, durations, None, needs, temporal_constraints, "RCPSP_max")
    res, schedule = rcpsp_max.solve(time_limit=60)
    time_cp_solving = time.time() - start

    if not res:
        rows.append(row)
    else:
        schedule = schedule.to_dict('records')
        start = time.time()
        resource_chains, resource_assignments = get_resource_chains(schedule, capacity, needs, complete=False)

        stnu = STNU.from_rcpsp_max_instance(durations, temporal_constraints, sink_source=1)
        stnu = add_resource_chains(stnu, resource_chains)
        stnu_to_xml(stnu, f"example_rcpsp_max_stnu_java", "stnu/java_comparison/xml_files")
        time_build_stnu = time.time() - start # Track time to build up STNU

        # Run the DC algorithm using the Java CSTNU tool, the result is written to a xml file
        start = time.time()
        dc, output_location = run_dc_algorithm("stnu/java_comparison/xml_files", f"example_rcpsp_max_stnu_java")
        logger.debug(f'dc is {dc} and output location {output_location}')
        time_dc_checking = time.time() - start  # track time of DC-checking step

        if not dc:
            row['status'] = "feasible_but_not_dc"
            rows.append(row)
        else:
            for sample in range(nr_samples):
                # Construct a row dict to append to the list of rows at the end of each iteration
                row = {"instance": "min_example", "status": "feasible_and_dc_but_rte_error", "sample": sample,
                       "rcpsp/max_feasible": "NotApplicable"}
                # Read ESTNU xml file into Python object that was the output from the previous step
                schedule = run_rte_algorithm(output_location)
                if schedule:
                    true_durations, start_times, finish_times = [], [], []
                    for (task, dur) in enumerate(durations):
                        start = schedule[f"{task}_{STNU.EVENT_START}"]
                        start_times.append(start)
                        if dur == 0:  # For the sink and source for the time being
                            finish = schedule[f"{task}_{STNU.EVENT_START}"]
                        else:
                            finish = schedule[f"{task}_{STNU.EVENT_FINISH}"]

                        finish_times.append(finish)
                        true_durations.append(finish-start)

                    logger.debug(f'start times {start_times} finish times {finish_times}, durations {true_durations}')

                    makespan_rte_star = max(schedule.values())

                    check_feasibility = check_feasibility_rcpsp_max(start_times, finish_times, true_durations, capacity, needs, temporal_constraints)

                    if check_feasibility:
                        start = time.time()
                        rcpsp_max = RCPSP_CP_Benchmark(capacity, true_durations, None, needs, temporal_constraints,
                                                       "RCPSP_max")
                        res, schedule = rcpsp_max.solve(time_limit=60)

                        time_perfect_information = time.time() - start
                        makespan_pi = max(schedule["end"].tolist())
                        gap_pi = res.get_objective_gaps()[0]
                        if makespan_pi > makespan_rte_star:
                            logger.info(f"WARNING: Makespan under perfect information is larger than rte star makespan")

                        logger.info(
                            f'makespan under perfect information is {makespan_pi}, makespan obtained with STNU is {makespan_rte_star}, '
                            f'regret is {makespan_rte_star - makespan_pi}')
                        row.update({"status": "feasible_and_dc", "sample": sample, "rcpsp/max_feasible": True,
                                    "makespan_pi": makespan_pi, "makespan_rte_star": makespan_rte_star})

                    else:
                        print(f'WARNING: feasibility check false')
                        row.update({"status": "feasible_and_dc", "sample": sample, "rcpsp/max_feasible": False,
                                     "makespan_rte_star": makespan_rte_star})

                rows.append(row)
    return rows


capacity = [3, 4, 5, 5, 5]
durations = [0, 5, 3, 1, 4, 9, 3, 4, 7, 3, 4, 0]
temporal_constraints = [(0, 0, 1), (1, 8, 2), (1, 11, 8), (1, 11, 7), (2, -2, 3), (3, 0, 5), (3, 0, 9), (4, 4, 6), (4, -4, 5), (5, 3, 10), (5, 9, 11), (5, -4, 4), (6, 3, 11), (7, 4, 11), (8, 7, 11), (9, 3, 11), (10, 4, 11)]
needs = [[0, 0, 0, 0, 0], [0, 3, 3, 0, 0], [0, 0, 5, 0, 0], [0, 0, 5, 0, 0], [3, 4, 2, 2, 4], [0, 0, 2, 0, 0], [3, 0, 5, 0, 0], [0, 3, 3, 0, 0], [1, 0, 5, 4, 0], [3, 1, 2, 0, 1], [1, 2, 4, 2, 0], [0, 0, 0, 0, 0]]
logger.debug(f'Start STNU pipeline with for minimal example with {capacity}, durations {durations}, needs {needs}, '
             f'temporal_constraints {temporal_constraints}')

data += run_minimal_example(capacity, durations, needs, temporal_constraints)
data_df = pd.DataFrame(data=data)
data_df.to_csv(results_location)
