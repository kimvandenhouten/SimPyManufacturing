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
logger = classes.general.get_logger(level="info")

data = []
nr_samples = 10

for instance_id in [1]:
    capacity, durations, needs, temporal_constraints = parse_sch_file(f'benchmark_rcpsp/rcpsp_max/j10/PSP{instance_id}.SCH')
    start = time.time()
    rcpsp_max = RCPSP_CP_Benchmark(capacity, durations, None, needs, temporal_constraints, "RCPSP_max")
    time_cp_solving = time.time() - start
    res, schedule = rcpsp_max.solve()

    if res:
        schedule = schedule.to_dict('records')
        start = time.time()
        resource_chains, resource_assignments = get_resource_chains(schedule, capacity, needs, complete=True)
        stnu = STNU.from_rcpsp_max_instance(durations, temporal_constraints)
        stnu = add_resource_chains(stnu, resource_chains)
        stnu_to_xml(stnu, f"example_rcpsp_max_stnu", "stnu/java_comparison/xml_files")
        time_build_stnu = time.time() - start

        # Run the DC algorithm using the Java CSTNU tool, the result is written to a xml file
        start = time.time()
        dc, output_location = run_dc_algorithm("stnu/java_comparison/xml_files", f"example_rcpsp_max_stnu")
        logger.debug(f'dc is {dc} and output location {output_location}')
        time_dc_checking = time.time() - start
        # TODO: track time of DC-checking step

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
                rte_data = rte_star(estnu, oracle="sample", sample=sample)
                time_rte = time.time() - start
                logger.debug(f'Final schedule is {rte_data.f}')
                makespan_stnu = max(rte_data.f.values())
                logger.info(f'The makespan obtained with the STNU algorithm is {makespan_stnu}')
        else:
            print(f'The network is not dynamically controllable')

    else:
        print(f'The model has no solution for instance id {instance_id}')


