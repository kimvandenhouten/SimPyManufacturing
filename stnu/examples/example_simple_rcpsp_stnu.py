from classes.stnu import STNU
from rcpsp.solvers.RCPSP_CP_benchmark import RCPSP_CP_Benchmark
from rcpsp.solvers.check_feasibility import check_feasibility
from stnu.get_resource_chains_reservations_benchmark import get_resource_chains, add_resource_chains
from stnu.java_comparison.stnu_to_xml_function import stnu_to_xml
import numpy as np
from stnu.algorithms.call_java_dc_checking import run_dc_algorithm
from stnu.algorithms.rte_star import rte_star
import classes.general
logger = classes.general.get_logger(__name__)

durations = [10, 20, 4, 6]
resources = [[1, 0], [1, 0], [0, 1], [0, 1]]
capacity = [1, 2]
successors = [[2], [3], [], []]

rcpsp = RCPSP_CP_Benchmark(capacity, durations, successors, resources)
stnu = STNU.from_rcpsp_instance(durations, resources, capacity, successors)
res, schedule = rcpsp.solve()
schedule = schedule.to_dict('records')

resource_chains, resource_assignments = get_resource_chains(schedule, capacity, resources, complete=True)
logger.debug(f'resource chains {resource_chains}')
logger.debug(f'resource assignment {resource_assignments}')
stnu = add_resource_chains(stnu, resource_chains)
stnu_to_xml(stnu, f"example_rcpsp_stnu", "stnu/java_comparison/xml_files")

dc, output_location = run_dc_algorithm("stnu/java_comparison/xml_files", f"example_rcpsp_stnu")
logger.debug(f'dc is {dc} and output location {output_location}')

# Read ESTNU xml file into Python object
estnu = STNU.from_graphml(output_location)

# For i in nr_samples:
n_sim = 1
for i in range(n_sim):
    # TODO: make this within a function maybe
    sample = {}
    for (A, C) in estnu.contingent_links:
        duration_sample = np.random.randint(estnu.contingent_links[(A, C)]["lc_value"],
                                            estnu.contingent_links[(A, C)]["uc_value"])
        sample[C] = duration_sample
    logger.debug(f'Sample that will be given to RTE_star: {sample}')

    ## Run RTE algorithm with alternative oracle and store makespan
    rte_data = rte_star(estnu, oracle="sample", sample=sample)

    logger.debug(f'Final schedule is {rte_data.f}')
    makespan_stnu = max(rte_data.f.values())
    logger.info(f'The makespan obtained with the STNU algorithm is {makespan_stnu}')

    ## Compute makespan lower bound by computing perfect information optimum with CP solver
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

    if check_feasibility(start_times, finish_times, true_durations, rcpsp.capacity, rcpsp.successors, rcpsp.resources):
        print(f'The schedule generate with the STNU pipeline is feasible')
    else:
        Warning(f'The schedule generated with the STNU pipeline is not feasible')

    rcpsp = RCPSP_CP_Benchmark(capacity, true_durations, successors, resources)
    print(len(rcpsp.durations))
    res, schedule = rcpsp.solve()
    makespan_pi = max(schedule["end"].tolist())
    assert makespan_pi <= makespan_stnu
    logger.info(f'makespan under perfect information is {makespan_pi}, makespan obtained with STNU is {makespan_stnu}, '
                f'regret is {makespan_stnu - makespan_pi}')
