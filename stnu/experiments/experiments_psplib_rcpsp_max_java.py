from rcpsp.rcpsp_max.process_file import parse_sch_file
from rcpsp.solvers.RCPSP_CP_benchmark import RCPSP_CP_Benchmark
import pandas as pd
from stnu.algorithms.call_java_dc_checking import run_dc_algorithm, run_rte_algorithm
from stnu.get_resource_chains_reservations_benchmark import get_resource_chains, add_resource_chains
from classes.stnu import STNU
from stnu.java_comparison.stnu_to_xml_function import stnu_to_xml
import time
import classes.general
logger = classes.general.get_logger(__name__)
from rcpsp.solvers.check_feasibility import check_feasibility_rcpsp_max

data = []
results_location = "stnu/experiments/results/rcpsp_max_results_java.csv"
nr_samples = 1
instance_folder = "j10"
for instance_id in range(1, 271):
    logger.debug(f'Start STNU pipeline with java for instance {instance_id}')
    capacity, durations, needs, temporal_constraints = parse_sch_file(f'rcpsp/rcpsp_max/{instance_folder}/PSP{instance_id}.SCH')
    start = time.time()
    rcpsp_max = RCPSP_CP_Benchmark(capacity, durations, None, needs, temporal_constraints, "RCPSP_max")
    time_cp_solving = time.time() - start
    res, schedule = rcpsp_max.solve(time_limit=60)
    time_cp_solving = time.time() - start

    if res:
        schedule = schedule.to_dict('records')
        start = time.time()
        resource_chains, resource_assignments = get_resource_chains(schedule, capacity, needs, complete=True)
        stnu = STNU.from_rcpsp_max_instance(durations, temporal_constraints, sink_source=2)
        stnu = add_resource_chains(stnu, resource_chains)
        stnu_to_xml(stnu, f"example_rcpsp_max_stnu_java", "stnu/java_comparison/xml_files")
        time_build_stnu = time.time() - start # Track time to build up STNU

        # Run the DC algorithm using the Java CSTNU tool, the result is written to a xml file
        start = time.time()
        dc, output_location = run_dc_algorithm("stnu/java_comparison/xml_files", f"example_rcpsp_max_stnu_java")
        logger.debug(f'dc is {dc} and output location {output_location}')
        time_dc_checking = time.time() - start  # track time of DC-checking step

        if dc:
            for sample in range(nr_samples):
                # Read ESTNU xml file into Python object that was the output from the previous step
                schedule = run_rte_algorithm(output_location)
                if schedule:
                    # TODO: compute makespan lower bound by computing perfect information optimum with CP solver
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

                    start = time.time()
                    rcpsp_max = RCPSP_CP_Benchmark(capacity, true_durations, None, needs, temporal_constraints,
                                                   "RCPSP_max")
                    res, schedule = rcpsp_max.solve(time_limit=60)

                    time_perfect_information = time.time() - start
                    makespan_pi = max(schedule["end"].tolist())
                    gap_pi = res.get_objective_gaps()[0]
                    assert makespan_pi <= makespan_rte_star

                    if check_feasibility:

                        data.append({"instance": f"{instance_folder}/PSP{instance_id}",
                                     "status": "feasible_and_dc", "sample": sample, "rcpsp/max_feasible": True,
                                     "makespan_rte_star": makespan_rte_star, "makespan_pi": makespan_pi,
                                     "gap_pi": gap_pi})
                        data_df = pd.DataFrame(data=data)
                        data_df.to_csv(results_location)

                    else:
                        data.append({"instance": f"{instance_folder}/PSP{instance_id}",
                                     "status": "feasible_and_dc", "sample": sample, "rcpsp/max_feasible": False,
                                     "makespan_pi": makespan_pi,"gap_pi": gap_pi
                                     })
                        data_df = pd.DataFrame(data=data)
                        data_df.to_csv(results_location)

                else:
                    data.append({"instance": f"{instance_folder}/PSP{instance_id}",
                                 "status": "feasible_and_dc_but_rte_error",
                                 "sample": sample, "rcpsp/max_feasible": "NotApplicable"})
                    data_df = pd.DataFrame(data=data)
                    data_df.to_csv(results_location)
        else:
            data.append({"instance": f"{instance_folder}/PSP{instance_id}",
                         "status": "feasible_but_not_dc", "sample": 0, "rcpsp/max_feasible": "NotApplicable"})
            data_df = pd.DataFrame(data=data)
            data_df.to_csv(results_location)
    else:
        data.append({"instance": f"{instance_folder}/PSP{instance_id}",
                     "status": "infeasible", "sample": 0, "rcpsp/max_feasible": "NotApplicable"})
        data_df = pd.DataFrame(data=data)
        data_df.to_csv(results_location)




