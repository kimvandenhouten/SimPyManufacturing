from copy import deepcopy
from typing import Union, Any

from rcpsp.rcpsp_max.process_file import parse_sch_file
from rcpsp.solvers.RCPSP_CP_benchmark import RCPSP_CP_Benchmark
from stnu.algorithms.call_java_cstnu_tool import run_dc_algorithm
from stnu.algorithms.rte_star import rte_star
from stnu.get_resource_chains_reservations_benchmark import get_resource_chains, add_resource_chains
from classes.stnu import STNU, SampleStrategy, Edge
from stnu.java_comparison.stnu_to_xml_function import stnu_to_xml
import time
import classes.general
from rcpsp.solvers.check_feasibility import check_feasibility_rcpsp_max
import numpy as np

logger = classes.general.get_logger(__name__)

BUILD_FROM_RCPSP = True


def rcpsp_to_stnu(capacity, durations, needs, temporal_constraints) -> STNU:
    logger.info(f'Start instance {instance_id}')
    rcpsp_max = RCPSP_CP_Benchmark(capacity, durations, None, needs, temporal_constraints, "RCPSP_max")
    res, schedule = rcpsp_max.solve(time_limit=60)

    if not res:
        return None

    schedule = schedule.to_dict('records')
    resource_chains, resource_assignments = get_resource_chains(schedule, capacity, needs, complete=True)
    stnu = STNU.from_rcpsp_max_instance(durations, temporal_constraints, sink_source=1)
    stnu = add_resource_chains(stnu, resource_chains)
    return stnu


def check_rte_problem():
    stnu_to_xml(stnu, f"example_rcpsp_max_stnu_python", "stnu/java_comparison/xml_files")

    # Run the DC algorithm using the Java CSTNU tool, the result is written to a xml file
    dc, output_location = run_dc_algorithm("stnu/java_comparison/xml_files", f"example_rcpsp_max_stnu_python")
    logger.info(f'dc is {dc} and output location {output_location}')

    if not dc:
        return False

    # Read ESTNU xml file into Python object that was the output from the previous step
    # FIXME: Can we avoid this intermediate writing and reading step?
    estnu = STNU.from_graphml(output_location)
    if dc:
        np.random.seed(1)
        # Sample a realisation for the contingent weights
        sample = estnu.sample_contingent_weights(strategy=SampleStrategy.RANDOM_EXECUTION_STRATEGY)
        logger.info(f'Sample that will be given to RTE_star: {sample}')

        # Run RTE algorithm with alternative oracle and store makespan
        if sample_mode == "standard":
            rte_data = rte_star(estnu, oracle="standard")
        else:
            rte_data = rte_star(estnu, oracle="sample", sample=sample)
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
            if not check_feasibility:
                return False
            logger.info(f'The makespan obtained with the STNU algorithm is {makespan_stnu}')

            rcpsp_max = RCPSP_CP_Benchmark(capacity, true_durations, None, needs, temporal_constraints, "RCPSP_max")
            res, schedule = rcpsp_max.solve(time_limit=60)

            makespan_pi = max(schedule["end"].tolist())
            gap_pi = res.get_objective_gaps()[0]
            assert makespan_pi <= makespan_stnu
            logger.info(
                f'makespan under perfect information is {makespan_pi}, makespan obtained with STNU is {makespan_stnu}, '
                f'regret is {makespan_stnu - makespan_pi}')
            return False
        else:
            logger.info(f'For some reason the RTE star could not finish')
            return True

    else:
        print(f'The network is not dynamically controllable')
        # TODO: for these instances, should we analyze whether with perfect information they were solvable?
        return False


sample_mode = "sample"

instance_folder, instance_id = "j10", 138
capacity, durations, needs, temporal_constraints = parse_sch_file(
    f'rcpsp/rcpsp_max/{instance_folder}/PSP{instance_id}.SCH')

if BUILD_FROM_RCPSP:
    stnu = rcpsp_to_stnu(capacity, durations, needs, temporal_constraints)
else:
    stnu = STNU.from_graphml('stnu/java_comparison/xml_files/example_rcpsp_max_stnu_python.stnu')
if not stnu:
    print(f'The model has no solution for instance id {instance_id}')
    raise Exception("infeasible rcpsp instance")

removed_edges: list[Any] = []
removed_nodes: set[Any] = set()

for node in stnu.edges:
    for edge in stnu.edges[node].values():
        if edge.uc_label:
            e2 = stnu.edges[edge.node_to][edge.node_from]
            assert e2 is not None and e2.lc_label
        elif edge.lc_label:
            e2 = stnu.edges[edge.node_to][edge.node_from]
            assert e2 is not None and e2.uc_label


def find_edge_to_remove() -> bool:
    # for e, t in removed_edges:
    #    stnu2.remove_edge(e.node_from, e.node_to, t)
    found = False

    for node in stnu.edges:
        for edge in list(stnu.edges[node].values()):
            e2 = deepcopy(edge)
            for type in [STNU.ORDINARY_LABEL, STNU.LC_LABEL]:
                if stnu.remove_edge(edge.node_from, edge.node_to, type):
                    if type == STNU.LC_LABEL:
                        e3 = deepcopy(stnu.edges[edge.node_to][edge.node_from])
                        assert e3 is not None and e3.uc_label
                        removed = stnu.remove_edge(e3.node_from, e3.node_to, STNU.UC_LABEL)
                        assert removed
                    else:
                        e3 = None

                    try:
                        problem_persists = check_rte_problem()
                    except:
                        problem_persists = False

                    if problem_persists:
                        found = True
                        removed_edges.append((e2, type))
                        if e3 is not None:
                            assert type == STNU.LC_LABEL
                            removed_edges.append((e3, STNU.UC_LABEL))
                        else:
                            assert type == STNU.ORDINARY_LABEL

                        print(f'can remove edge {edge.node_from}, {edge.node_to}, {type}')
                    else:
                        # re-add the edge
                        if type == STNU.ORDINARY_LABEL:
                            assert e3 is None
                            stnu.set_ordinary_edge(e2.node_from, e2.node_to, e2.weight)
                        else:
                            assert type == STNU.LC_LABEL
                            assert (e3 is not None
                                    and e3.node_from == e2.node_to
                                    and e2.node_from == e3.node_to)
                            stnu.set_labeled_edge(e2.node_from, e2.node_to,
                                                  e2.lc_weight, e2.lc_label,
                                                  STNU.LC_LABEL)
                            stnu.set_labeled_edge(e3.node_from, e3.node_to,
                                                  e3.uc_weight, e3.uc_label,
                                                  STNU.UC_LABEL)
    return found


while True:
    if not find_edge_to_remove():
        break
for node in stnu.edges:
    if len(stnu.edges[node]) == 0:
        if all(node not in edge_set for
               edge_set in stnu.edges.values()):
            removed_nodes.add(node)
for node in removed_nodes:
    stnu.remove_node(node)

stnu_to_xml(stnu, f"example_rcpsp_max_stnu_python", "stnu/java_comparison/xml_files")

print(f"{len(removed_edges)} edges can be removed: "
      f"{[(e.node_from, e.node_to, t) for (e, t) in removed_edges]}")
print(f"{len(removed_nodes)} nodes can be removed: {removed_nodes}")
