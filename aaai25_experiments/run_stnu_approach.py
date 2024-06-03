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

data_agg = []
results_location = "aaai25_experiments/results/results_stnu.csv"


def get_true_durations(estnu, rte_data, durations, sample):
    true_durations, start_times, finish_times = [], [], []
    for (task, dur) in enumerate(durations):
        if task > 0 and task < len(durations) - 1:
            node_idx_start = estnu.translation_dict_reversed[f'{task}_{STNU.EVENT_START}']
            node_idx_finish = estnu.translation_dict_reversed[f'{task}_{STNU.EVENT_FINISH}']
            start_times.append(rte_data.f[node_idx_start])
            finish_times.append(rte_data.f[node_idx_finish])
            true_durations.append(sample[node_idx_finish])
        else:
            node_idx_start = estnu.translation_dict_reversed[f'{task}_{STNU.EVENT_START}']
            node_idx_finish = estnu.translation_dict_reversed[f'{task}_{STNU.EVENT_START}']
            start_times.append(rte_data.f[node_idx_start])
            finish_times.append(rte_data.f[node_idx_finish])
            true_durations.append(0)
    return true_durations, start_times, finish_times


def run_stnu_experiment(instance_folder, instance_id, nr_samples):
    data = []
    logger.info(f'Start instance {instance_id}')

    # Read instance and set up deterministic RCPSP/max CP model and solve (this will be used for the resource chain)
    capacity, durations, needs, temporal_constraints = parse_sch_file(f'rcpsp/rcpsp_max/{instance_folder}/PSP{instance_id}.SCH')
    rcpsp_max = RCPSP_CP_Benchmark(capacity, durations, None, needs, temporal_constraints, "RCPSP_max")
    res, schedule = rcpsp_max.solve(time_limit=60)

    if res:
        # Build the STNU using the instance information and the resource chains
        schedule = schedule.to_dict('records')
        resource_chains, resource_assignments = get_resource_chains(schedule, capacity, needs, complete=True)
        stnu = STNU.from_rcpsp_max_instance(durations, temporal_constraints)
        stnu = add_resource_chains(stnu, resource_chains)
        stnu_to_xml(stnu, f"example_rcpsp_max_stnu", "stnu/java_comparison/xml_files")

        # Run the DC algorithm using the Java CSTNU tool, the result is written to a xml file
        dc, output_location = run_dc_algorithm("stnu/java_comparison/xml_files", f"example_rcpsp_max_stnu")
        logger.info(f'dc is {dc} and output location {output_location}')

        # Read ESTNU xml file into Python object that was the output from the previous step
        estnu = STNU.from_graphml(output_location)
        if dc:
            # For i in nr_samples:
            for i in range(nr_samples):
                np.random.seed(i)
                # Sample a realisation for the contingent weights
                sample = estnu.sample_contingent_weights(strategy=SampleStrategy.RANDOM_EXECUTION_STRATEGY)
                logger.info(f'Sample that will be given to RTE_star: {sample}')

                # Run RTE algorithm with alternative oracle and store makespan
                rte_data = rte_star(estnu, oracle="sample", sample=sample)

                if rte_data:
                    objective = max(rte_data.f.values())

                    # Obtain true durations and start and finish times and verify feasibility
                    true_durations, start_times, finish_times = get_true_durations(estnu, rte_data, durations, sample)
                    check_feasibility = check_feasibility_rcpsp_max(start_times, finish_times, true_durations, capacity, needs,
                                               temporal_constraints)
                    assert check_feasibility

                    # Solve with perfect information
                    rcpsp_max = RCPSP_CP_Benchmark(capacity, true_durations, None, needs, temporal_constraints, "RCPSP_max")
                    res, schedule = rcpsp_max.solve(time_limit=60)

                    objective_pi = max(schedule["end"].tolist())
                    assert objective_pi <= objective
                    rel_regret = 100 * (objective - objective_pi) / objective_pi

                else:
                    objective = np.inf
                    logger.info(f'For some reason the RTE start could not finish')
                    objective_pi = "NotImplemented"
                    rel_regret = "NotImplemented"

                # Store data
                data.append({
                    "instance_name": f'{instance_folder}_{instance_id}',
                    "method": "STNU",
                    "test_sample_id": i,
                    "obj": objective,
                    "obj_pi": objective_pi,
                    "rel_regret": rel_regret})

                logger.info(
                    f'objective under perfect information is {objective_pi}, makespan obtained with STNU scheduling is {objective}, '
                    f'relative regret is {rel_regret}, and')

        else:  # In this situation the STNU approach cannot find a schedule because the network was not DC
            print(f'The network is not dynamically controllable')
            objective = np.inf
            feasibility = False

    else:  # In this situation the STNU approach cannot find a schedule because the network was not DC
        objective = np.inf
        feasibility = False

    if objective == np.inf and feasibility == False:
        # For the situations that we did not find a feasibile schedule we should still need to simulate and evaluate
        # perfect information schedules.
        feasibilities, objectives = [], []
        rel_regrets = []
        test_durations_sample = rcpsp_max.sample_durations(nr_samples)

        for i, duration_sample in enumerate(test_durations_sample):
            feasibilities.append(False)
            objectives.append(np.inf)

            # Solve with perfect information
            rcpsp_max = RCPSP_CP_Benchmark(capacity, duration_sample, None, needs, temporal_constraints,
                                           "RCPSP_max")
            res, schedule = rcpsp_max.solve(time_limit=60)

            if res:
                objective_pi = max(schedule["end"].tolist())
            else:
                objective_pi = np.inf

            if objective_pi == np.inf:
                rel_regret = 0
            else:
                rel_regret = 100

            rel_regrets.append(rel_regret)

            # Store data
            data.append({
                "instance_name": f'{instance_folder}_{instance_id}',
                "method": "STNU",
                "test_sample_id": i,
                "obj": np.inf,
                "obj_pi": objective_pi,
                "rel_regret": rel_regret})

            logger.info(
                f'objective under perfect information is {objective_pi}, makespan obtained with STNU scheduling is {np.inf}, '
                f'relative regret is {rel_regret}, and')
    return data


nb_scenarios_test = 50
for instance_folder in ["j10"]:
    for instance_id in range(1, 271):
        data_agg += run_stnu_experiment(instance_folder, instance_id, nb_scenarios_test)
        df = pd.DataFrame(data_agg)
        df.to_csv(results_location, index=False)