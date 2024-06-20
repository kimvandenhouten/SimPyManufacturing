from copy import deepcopy
from typing import Any

import numpy as np

import general.logger
from rcpsp.rcpsp_max.process_file import parse_sch_file
from rcpsp.solvers.RCPSP_CP_benchmark import RCPSP_CP_Benchmark
from rcpsp.solvers.check_feasibility import check_feasibility_rcpsp_max
from rcpsp.temporal_networks.stnu_rcpsp import RCPSP_STNU, get_resource_chains, add_resource_chains
from temporal_networks.cstnu_tool.call_java_cstnu_tool import run_dc_algorithm
from temporal_networks.cstnu_tool.stnu_to_xml_function import stnu_to_xml
from temporal_networks.rte_star import rte_star
from temporal_networks.stnu import STNU, SampleStrategy

logger = general.logger.get_logger(__name__)


BUILD_FROM_RCPSP = True
REMOVE_NODES = False

def rcpsp_to_stnu(rcpsp_max) -> STNU:
    logger.info(f'Build STNU for {rcpsp_max.instance_folder} {rcpsp_max.instance_id}')
    upper_bound = rcpsp_max.get_bound()
    logger.info(f'Upper bound used for making the STNU is {upper_bound}')
    res, schedule = rcpsp_max.solve(upper_bound, time_limit=30)

    if not res:
        return None

    schedule = schedule.to_dict('records')
    resource_chains, resource_assignments = get_resource_chains(schedule, rcpsp_max.capacity, rcpsp_max.needs,
                                                                complete=True)
    stnu = RCPSP_STNU.from_rcpsp_max_instance(rcpsp_max.durations, rcpsp_max.temporal_constraints)
    stnu = add_resource_chains(stnu, resource_chains)
    return stnu


def check_rte_problem(sample_duration):
    stnu_to_xml(stnu, f"example_rcpsp_max_stnu_python", "temporal_networks/cstnu_tool/xml_files")

    # Run the DC algorithm using the Java CSTNU tool, the result is written to a xml file
    dc, output_location = run_dc_algorithm("temporal_networks/cstnu_tool/xml_files", f"example_rcpsp_max_stnu_python")
    logger.info(f'dc is {dc} and output location {output_location}')

    if not dc:
        return False

    # Read ESTNU xml file into Python object that was the output from the previous step
    # FIXME: Can we avoid this intermediate writing and reading step?
    estnu = STNU.from_graphml(output_location)
    logger.info(f'nodes estnu is {len(estnu.nodes)}')
    if dc:
        np.random.seed(1)
        # Sample a realisation for the contingent weights
        sample = {}
        for task, duration in enumerate(sample_duration):
            if 0 >= task or task >= len(sample_duration) - 1:  # skip the source and sink node
                continue
            if estnu.translation_dict_reversed[f'{task}_{STNU.EVENT_FINISH}']:
                find_contingent_node = estnu.translation_dict_reversed[f'{task}_{STNU.EVENT_FINISH}']
                sample[find_contingent_node] = duration

        logger.info(f'Sample dict that will be given to RTE star is {sample}')

        # Run RTE algorithm with alternative oracle and store makespan
        rte_data = rte_star(estnu, oracle="sample", sample=sample)
        if rte_data:
            logger.info(f'Final schedule is {rte_data.f}')
            makespan_stnu = max(rte_data.f.values())

            logger.info(f'The makespan obtained with the STNU algorithm is {makespan_stnu}')

            return False
        else:
            logger.info(f'For some reason the RTE star could not finish')
            return True

    else:
        print(f'The network is not dynamically controllable')
        return False


DIRECTORY_INSTANCES = 'rcpsp/rcpsp_max'

instance_folder, instance_id = "j30", 35
np.random.seed(1)
rcpsp_max = RCPSP_CP_Benchmark.parsche_file(DIRECTORY_INSTANCES, instance_folder, instance_id)
test_durations_samples = rcpsp_max.sample_durations(10)
sample_duration = test_durations_samples[0]

if BUILD_FROM_RCPSP:
    stnu = rcpsp_to_stnu(rcpsp_max)
else:
    stnu = RCPSP_STNU.from_graphml('stnu/java_comparison/xml_files/rte_error_example.stnu')

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


def find_edge_to_remove(sample_duration) -> bool:
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
                        problem_persists = check_rte_problem(sample_duration)
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
    logger.info(f'Start up')
    if not find_edge_to_remove(sample_duration):
        break

stnu_to_xml(stnu, f"rte_error_kim_with_nodes", "temporal_networks/cstnu_tool/xml_files")

for node in stnu.edges:

    if len(stnu.edges[node]) == 0:
        if all(node not in edge_set for
               edge_set in stnu.edges.values()):
            removed_nodes.add(node)
for node in removed_nodes:
    stnu.remove_node(node)

stnu_to_xml(stnu, f"rte_error_kim_without_nodes", "temporal_networks/cstnu_tool/xml_files")

print(f"{len(removed_edges)} edges can be removed: "
      f"{[(e.node_from, e.node_to, t) for (e, t) in removed_edges]}")
print(f"{len(removed_nodes)} nodes can be removed: {removed_nodes}")
