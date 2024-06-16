from rcpsp.solvers.RCPSP_CP_benchmark import RCPSP_CP_Benchmark
from rcpsp.solvers.check_feasibility import check_feasibility_rcpsp_max
from rcpsp.temporal_networks.stnu_rcpsp import RCPSP_STNU, get_resource_chains, add_resource_chains

from temporal_networks.cstnu_tool.call_java_cstnu_tool import run_dc_algorithm
from temporal_networks.rte_star import rte_star
from temporal_networks.stnu import STNU, SampleStrategy
from temporal_networks.cstnu_tool.stnu_to_xml_function import stnu_to_xml

import time
import pandas as pd
import numpy as np
import general

logger = general.logger.get_logger(__name__)


def get_start_and_finish(estnu, rte_data, num_tasks):
    """
    This function can be used to link the start times and finish times from the rte_dta
    to the RCPSP_max starts and finish times
    """
    true_durations, start_times, finish_times = [], [], []
    for task in range(num_tasks):
        if task > 0 and task < num_tasks - 1:
            node_idx_start = estnu.translation_dict_reversed[f'{task}_{STNU.EVENT_START}']
            node_idx_finish = estnu.translation_dict_reversed[f'{task}_{STNU.EVENT_FINISH}']
            start_times.append(rte_data.f[node_idx_start])
            finish_times.append(rte_data.f[node_idx_finish])
        else:
            node_idx_start = estnu.translation_dict_reversed[f'{task}_{STNU.EVENT_START}']
            node_idx_finish = estnu.translation_dict_reversed[f'{task}_{STNU.EVENT_START}']
            start_times.append(rte_data.f[node_idx_start])
            finish_times.append(rte_data.f[node_idx_finish])
    return start_times, finish_times


def get_true_durations(estnu, rte_data, num_tasks):
    """
    This function can be used to return the durations according to the RTE schedule
    related to the RCPSP_max
    """
    start_times, finish_times = get_start_and_finish(estnu, rte_data, num_tasks)
    true_durations = [finish_times[i] - start_times[i] for i in range(num_tasks)]

    return true_durations


def run_stnu_experiment(rcpsp_max, test_durations_sample, time_limit_pi=60, time_limit_cp_stnu=60, mode="mean"):
    data = []
    logger.debug(f'Start instance {rcpsp_max.instance_id}')
    start_offline = time.time()

    upper_bound = rcpsp_max.get_bound()

    # Read instance and set up deterministic RCPSP/max CP model and solve (this will be used for the resource chain)
    if mode == "mean":
        res, schedule = rcpsp_max.solve(time_limit=time_limit_cp_stnu)
    elif mode == "robust":
        res, schedule = rcpsp_max.solve(upper_bound, time_limit=time_limit_cp_stnu)
    else:
        raise NotImplementedError(f'')

    if res:

        # Build the STNU using the instance information and the resource chains
        schedule = schedule.to_dict('records')
        resource_chains, resource_assignments = get_resource_chains(schedule, rcpsp_max.capacity, rcpsp_max.needs,
                                                                    complete=True)
        stnu = RCPSP_STNU.from_rcpsp_max_instance(rcpsp_max.durations, rcpsp_max.temporal_constraints)
        stnu = add_resource_chains(stnu, resource_chains)
        stnu_to_xml(stnu, f"example_rcpsp_max_stnu", "temporal_networks/cstnu_tool/xml_files")

        # Run the DC algorithm using the Java CSTNU tool, the result is written to a xml file
        dc, output_location = run_dc_algorithm("temporal_networks/cstnu_tool/xml_files",
                                               f"example_rcpsp_max_stnu")
        logger.debug(f'dc is {dc} and output location {output_location}')

        # Read ESTNU xml file into Python object that was the output from the previous step
        estnu = STNU.from_graphml(output_location)
        finish_offline = time.time()


        if dc:
            # For i in nr_samples:
            for sample_duration in test_durations_sample:
                start_online = time.time()
                # Transform the sample_duration to a dictionary and find the correct ESTNU node indices
                sample = {}
                for task, duration in enumerate(sample_duration):
                    if 0 >= task or task >= len(sample_duration) - 1:  # skip the source and sink node
                        continue
                    find_contingent_node = estnu.translation_dict_reversed[f'{task}_{STNU.EVENT_FINISH}']
                    sample[find_contingent_node] = duration

                logger.debug(f'Sample dict that will be given to RTE star is {sample_duration}')

                # Run RTE algorithm with alternative oracle and store makespan
                rte_data = rte_star(estnu, oracle="sample", sample=sample)

                if rte_data:
                    objective = max(rte_data.f.values())

                    # Obtain true durations and start and finish times and verify feasibility
                    start_times, finish_times = get_start_and_finish(estnu, rte_data, rcpsp_max.num_tasks)

                    feasibility = check_feasibility_rcpsp_max(start_times, finish_times, sample_duration, rcpsp_max.capacity, rcpsp_max.needs,
                                               rcpsp_max.temporal_constraints)

                    assert feasibility
                    finish_online = time.time()

                    # Solve with perfect information
                    res, schedule = rcpsp_max.solve(sample_duration, time_limit=time_limit_pi)

                    if res:
                        objective_pi = max(schedule["end"].tolist())
                        feasibility_pi = True
                    else:
                        feasibility_pi = False
                        objective_pi = np.inf
                        logger.info(f'Instance PSP{rcpsp_max.instance_id} with true durations {sample_duration} is INFEASIBLE under perfect information')
                    assert objective_pi <= objective
                    rel_regret = 100 * (objective - objective_pi) / objective_pi

                else:
                    raise ValueError(f'For some reason the RTE could not finish')

                # Store data
                data.append({
                    "instance_folder": rcpsp_max.instance_folder,
                    "instance_id": rcpsp_max.instance_id,
                    "method": "STNU",
                    "time_limit_pi": time_limit_pi,
                    "time_limit_cp_stnu": time_limit_cp_stnu,
                    "obj": objective,
                    "obj_pi": objective_pi,
                    "feasibility": feasibility,
                    "feasibility_pi": feasibility_pi,
                    "rel_regret": rel_regret,
                    "real_durations": sample_duration,
                    "start_times": start_times,
                    "time_offline": finish_offline - start_offline,
                    "time_online": finish_online - start_online,
                    "mode": mode
                })

                logger.debug(
                    f'objective under perfect information is {objective_pi}, makespan obtained with STNU scheduling is {objective}, '
                    f'relative regret is {rel_regret}, and')
                logger.info(
                    f'Instance PSP{rcpsp_max.instance_id} with true durations {sample_duration} is FEASIBLE with makespan {objective}')

        else:  # In this situation the STNU approach cannot find a schedule because the network was not DC
            objective = np.inf
            feasibility = False

    else:  # In this situation the STNU approach cannot find a schedule because the initial CP is infeasible
        objective = np.inf
        feasibility = False
        finish_offline = time.time()

    if objective == np.inf and feasibility == False:
        # For the situations that we did not find a feasible schedule we should still need to simulate and evaluate
        # perfect information schedules.
        feasibilities, objectives = [], []
        rel_regrets = []

        # TODO: this is sort of double now
        for i, sample_duration in enumerate(test_durations_sample):
            feasibilities.append(False)
            objectives.append(np.inf)

            # Solve with perfect information
            res, schedule = rcpsp_max.solve(sample_duration, time_limit=time_limit_pi)

            if res:
                objective_pi = max(schedule["end"].tolist())
                feasibility_pi = True
                logger.info(f'Instance PSP{rcpsp_max.instance_id} with true durations {sample_duration} is INFEASIBLE')
            else:
                objective_pi = np.inf
                feasibility_pi = False
                logger.info(
                    f'Instance PSP{rcpsp_max.instance_id} with true durations {sample_duration} is INFEASIBLE under perfect information')

            if objective_pi == np.inf:
                rel_regret = 0
            else:
                rel_regret = 100

            rel_regrets.append(rel_regret)

            # Store data
            data.append({
                "instance_folder": rcpsp_max.instance_folder,
                "instance_id": rcpsp_max.instance_id,
                "method": "STNU",
                "time_limit_pi": time_limit_pi,
                "time_limit_cp_stnu": time_limit_cp_stnu,
                "obj": np.inf,
                "obj_pi": objective_pi,
                "rel_regret": rel_regret,
                "feasibility": feasibility,
                "feasibility_pi": feasibility_pi,
                "real_durations": sample_duration,
                "start_times": None,
                "time_offline": finish_offline - start_offline,
                "time_online": 0,
                "mode": mode
            })

            logger.debug(
                f'objective under perfect information is {objective_pi}, makespan obtained with STNU scheduling is {np.inf}, '
                f'relative regret is {rel_regret}, and')
    return data
