from benchmark_rcpsp.rcpsp_max.process_file import parse_sch_file
from solvers.RCPSP_CP_benchmark import RCPSP_CP_Benchmark
import pandas as pd
from stnu.algorithms.call_java_dc_checking import run_dc_algorithm
from stnu.algorithms.rte_star import rte_star
from stnu.get_resource_chains_reservations_benchmark import get_resource_chains, add_resource_chains
from classes.stnu import STNU
from stnu.java_comparison.stnu_to_xml_function import stnu_to_xml
import time
import classes.general
logger = classes.general.get_logger(__name__)
from solvers.check_feasibility import check_feasibility_rcpsp_max

data = []
results_location = "stnu/experiments/results/rcpsp_max_results.csv"
nr_samples = 10
instance_folder = "j10"
for instance_id in range(1, 271):
    capacity, durations, needs, temporal_constraints = parse_sch_file(f'benchmark_rcpsp/rcpsp_max/{instance_folder}/PSP{instance_id}.SCH')
    start = time.time()
    rcpsp_max = RCPSP_CP_Benchmark(capacity, durations, None, needs, temporal_constraints, "RCPSP_max")
    time_cp_solving = time.time() - start
    res, schedule = rcpsp_max.solve(time_limit=60)
    time_cp_solving = time.time() - start

    if res:
        schedule = schedule.to_dict('records')
        start = time.time()
        resource_chains, resource_assignments = get_resource_chains(schedule, capacity, needs, complete=True)
        stnu = STNU.from_rcpsp_max_instance(durations, temporal_constraints)
        stnu = add_resource_chains(stnu, resource_chains)
        stnu_to_xml(stnu, f"example_rcpsp_max_stnu", "stnu/java_comparison/xml_files")
        time_build_stnu = time.time() - start # Track time to build up STNU

        # Run the DC algorithm using the Java CSTNU tool, the result is written to a xml file
        start = time.time()
        dc, output_location = run_dc_algorithm("stnu/java_comparison/xml_files", f"example_rcpsp_max_stnu")
        logger.debug(f'dc is {dc} and output location {output_location}')
        time_dc_checking = time.time() - start  # track time of DC-checking step

        # Read ESTNU xml file into Python object that was the output from the previous step
        # FIXME: Can we avoid this intermediate writing and reading step?
        estnu = STNU.from_graphml(output_location)
        if dc:
            # For i in nr_samples:
            for i in range(nr_samples):
                # Sample a realisation for the contingent weights
                sample = estnu.sample_contingent_weights()
                logger.debug(f'Sample that will be given to RTE_star: {sample}')

                # Run RTE algorithm with alternative oracle and store makespan
                start = time.time()
                #rte_data = rte_star(estnu, oracle="standard")
                rte_data = rte_star(estnu, oracle="sample", sample=sample)
                time_rte = time.time() - start
                if rte_data:
                    logger.debug(f'Final schedule is {rte_data.f}')
                    makespan_stnu = max(rte_data.f.values())

                    # TODO: check if the outcome schedule is feasible
                    # Compute makespan lower bound by computing perfect information optimum with CP solver
                    true_durations, start_times, finish_times = [], [], []
                    for (task, dur) in enumerate(durations):
                        node_idx_start = estnu.translation_dict_reversed[f'{task}_{STNU.EVENT_START}']
                        node_idx_finish = estnu.translation_dict_reversed[f'{task}_{STNU.EVENT_FINISH}']
                        start_times.append(rte_data.f[node_idx_start])
                        finish_times.append(rte_data.f[node_idx_finish])

                        if task > 0 and task < len(durations) - 1:
                            true_durations.append(sample[node_idx_finish])
                        else:
                            true_durations.append(0)

                    #check_feasibility = check_feasibility_rcpsp_max(start_times, finish_times, true_durations, capacity, needs,
                                               # temporal_constraints)
                    #assert check_feasibility
                    logger.info(f'The makespan obtained with the STNU algorithm is {makespan_stnu}')
                    makespan_pi = "NotImplementedYet"
                    time_perfect_information = "NotImplementedYet"

                    data.append({"instance_name": f'{instance_folder}_PSP_{instance_id}',
                                 "iteration": i, "makespan_stnu": makespan_stnu,
                                 "makespan_lb": makespan_pi,
                                 "time_initial_cp": time_cp_solving, "time_build_stnu": time_build_stnu,
                                 "time_dc_checking": time_dc_checking, "time_rte": time_rte,
                                 "time_cp_lb": time_perfect_information,
                                 "status": "feasible_and_dc"})
                    data_df = pd.DataFrame(data)
                    data_df.to_csv(results_location)
                else:
                    makespan_stnu = "inf"

                    logger.info(f'For some reason the RTE start could not finish')
                    makespan_pi = "NotImplementedYet"
                    time_perfect_information = "NotImplementedYet"

                    data.append({"instance_name": f'{instance_folder}_PSP_{instance_id}',
                                 "iteration": i, "makespan_stnu": makespan_stnu,
                                 "makespan_lb": makespan_pi,
                                 "time_initial_cp": time_cp_solving, "time_build_stnu": time_build_stnu,
                                 "time_dc_checking": time_dc_checking, "time_rte": time_rte,
                                 "time_cp_lb": time_perfect_information,
                                 "status": "feasible_and_dc_but_rte_error"})
                    data_df = pd.DataFrame(data)
                    data_df.to_csv(results_location)

        else:
            print(f'The network is not dynamically controllable')
            # TODO: for these instances, should we analyze whether with perfect information they were solvable?
            data.append({"instance_name": f'{instance_folder}_PSP_{instance_id}',
                         "iteration": 0, "makespan_stnu": "inf",
                         "makespan_lb": "inf",
                         "time_initial_cp": time_cp_solving, "time_build_stnu": time_build_stnu,
                         "time_dc_checking": time_dc_checking, "time_rte": 0,
                         "time_cp_lb": 0,
                         "status": "feasible_but_not_dc"})
            data_df = pd.DataFrame(data)
            data_df.to_csv(results_location)

    else:
        print(f'The model has no solution for instance id {instance_id}')
        data.append({"instance_name": f'{instance_folder}_PSP_{instance_id}',
                     "iteration": 0, "makespan_stnu": "inf",
                     "makespan_lb": "inf",
                     "time_initial_cp": time_cp_solving, "time_build_stnu": 0,
                     "time_dc_checking": 0, "time_rte": 0,
                     "time_cp_lb": 0, "status": "infeasible"})
        data_df = pd.DataFrame(data)
        data_df.to_csv(results_location)



