from classes.stnu import STNU
from rcpsp.solvers.RCPSP_CP_benchmark import RCPSP_CP_Benchmark
from rcpsp.solvers.check_feasibility import check_feasibility
from stnu.get_resource_chains_reservations_benchmark import get_resource_chains, add_resource_chains
from stnu.java_comparison.stnu_to_xml_function import stnu_to_xml
from stnu.algorithms.call_java_cstnu_tool import run_dc_algorithm
import time
from stnu.algorithms.rte_star import rte_star
import classes.general
from rcpsp.rcpsp.process_file import process_file
import pandas as pd
logger = classes.general.get_logger(__name__)

# Set experimental settings
nr_samples = 10

data = []
for instance_folder in [30]:
    for a in range(1, 49):
        for b in range(1, 11):
            # Read instance from PSPlib
            instance_name = f"j{instance_folder}{a}_{b}"
            activities, precedence_relations, resources, durations, capacity, needs, successors = process_file(f"benchmark_rcpsp/rcpsp/j{instance_folder}/",f"{instance_name}.sm", sink_source=False)

            # Create RCPSP_CP_Benchmark Object to solve the CP model with these inputs
            start = time.time()
            rcpsp = RCPSP_CP_Benchmark(capacity, durations, successors, needs)
            res, schedule = rcpsp.solve()  # Solve the CP model, res contains the CP results, schedule as Pandas DF
            schedule = schedule.to_dict('records')
            time_cp_solving = time.time() - start
            # TODO: track time of first step

            # Run the greedy algorithm to obtain resource chains based on the schedule from the CP output
            start = time.time()
            resource_chains, resource_assignments = get_resource_chains(schedule, capacity, needs, complete=True)

            # Build STNU from RCPSP instance and add resource chains and save as XML
            stnu = STNU.from_rcpsp_instance(durations, needs, capacity, successors)
            stnu = add_resource_chains(stnu, resource_chains)
            stnu_to_xml(stnu, f"example_rcpsp_stnu", "stnu/java_comparison/xml_files")
            time_build_stnu = time.time() - start
            # TODO: track time of building STNU step

            # Run the DC algorithm using the Java CSTNU tool, the result is written to a xml file
            start = time.time()
            dc, output_location = run_dc_algorithm("stnu/java_comparison/xml_files", f"example_rcpsp_stnu")
            logger.debug(f'dc is {dc} and output location {output_location}')
            time_dc_checking = time.time() - start
            #TODO: track time of DC-checking step

            # Read ESTNU xml file into Python object that was the output from the previous step
            # FIXME: Can we avoid this intermediate writing and reading step?
            estnu = STNU.from_graphml(output_location)

            # For i in nr_samples:
            for i in range(nr_samples):
                # Sample a realisation for the contingent weights
                sample = estnu.sample_contingent_weights()
                logger.debug(f'Sample that will be given to RTE_star: {sample}')

                # Run RTE algorithm with alternative oracle and store makespan
                start = time.time()
                rte_data = rte_star(estnu, oracle="sample", sample=sample)
                time_rte = time.time() - start
                logger.debug(f'Final schedule is {rte_data.f}')
                makespan_stnu = max(rte_data.f.values())
                logger.info(f'The makespan obtained with the STNU algorithm is {makespan_stnu}')

                # Compute makespan lower bound by computing perfect information optimum with CP solver
                true_durations = []
                start_times = []
                finish_times = []
                for (task, dur) in enumerate(durations):
                    key_start = f'{task}_{STNU.EVENT_START}'
                    key_finish = f'{task}_{STNU.EVENT_FINISH}'
                    node_idx_start = estnu.translation_dict_reversed[key_start]
                    node_idx_finish = estnu.translation_dict_reversed[key_finish]
                    weight = sample[node_idx_finish]
                    start_times.append(rte_data.f[node_idx_start])
                    finish_times.append(rte_data.f[node_idx_finish])
                    true_durations.append(weight)

                check_feasible = check_feasibility(start_times, finish_times, true_durations, rcpsp.capacity, rcpsp.successors,
                                  rcpsp.needs)
                if check_feasible:
                    logger.info(f'The schedule generate with the STNU pipeline is feasible')

                assert check_feasibility

                start = time.time()
                rcpsp = RCPSP_CP_Benchmark(capacity, true_durations, successors, needs)
                logger.info(len(rcpsp.durations))
                res, schedule = rcpsp.solve()
                time_perfect_information = time.time() - start
                makespan_pi = max(schedule["end"].tolist())
                assert makespan_pi <= makespan_stnu
                logger.info(f'makespan under perfect information is {makespan_pi}, makespan obtained with STNU is {makespan_stnu}, '
                            f'regret is {makespan_stnu - makespan_pi}')

                data.append({"instance_name": instance_name, "iteration": i, "makespan_stnu": makespan_stnu, "makespan_lb": makespan_pi,
                "time_initial_cp": time_cp_solving, "time_build_stnu": time_build_stnu, "time_dc_checking": time_dc_checking, "time_rte": time_rte,
                "time_cp_lb": time_perfect_information})
                data_df = pd.DataFrame(data)
                data_df.to_csv("stnu/experiments/results/rcpsp_stnu_more_instances_fromj609_1.csv")

