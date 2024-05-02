import json
from classes.classes import ProductionPlan
import classes.general
from classes.stnu import STNU
from rcpsp.solvers.check_feasibility import check_feasibility
from stnu.java_comparison.stnu_to_xml_function import stnu_to_xml
from stnu.algorithms.call_java_cstnu_tool import run_dc_algorithm, run_rte_algorithm
from stnu.algorithms.rte_star import rte_star
from stnu.get_resource_chains_reservations import get_resource_chains, add_resource_chains
from rcpsp.solvers.RCPSP_CP import RCPSP_CP
import numpy as np
import pandas as pd

logger = classes.general.get_logger(__name__)
collected_data = []
results_location = 'stnu/experiments/results/results_DSM_instances_java.csv'
n_sim = 1
for instance_size in [10, 20]:
    for instance_id in [1, 2, 3]:
        for instance_type in [1, 2]:
            # Specify instance name

            instance_name = f"{instance_size}_{instance_id}_factory_1"

            # Read production plan
            my_productionplan = ProductionPlan(
                **json.load(open(f'factory_data/development/instances_type_{instance_type}_uniform/instance_' + instance_name + '.json')))

            # Make STNU from production plan
            # Solve deterministic CP and data
            rcpsp = RCPSP_CP(my_productionplan)
            res, _, cp_output = rcpsp.solve(None, 60, 1, 0)
            if res:
                makespan_cp_output = max(cp_output["end"].tolist())
                logger.info(f'makespan according to CP output is {makespan_cp_output}')
                earliest_start = cp_output.to_dict('records')
                resource_chains, resource_use = get_resource_chains(my_productionplan, earliest_start, True)

                # Set up STNU and write to xml
                stnu = STNU.from_production_plan(my_productionplan, max_time_lag=True, origin_horizon=False)
                stnu = add_resource_chains(stnu=stnu, resource_chains=resource_chains)
                stnu_to_xml(stnu, f"input_production_plan_{instance_size}_{instance_id}", "stnu/java_comparison/xml_files")

                # Run DC-checking and store ESTNU in xml
                dc, output_location = run_dc_algorithm("stnu/java_comparison/xml_files", f"input_production_plan_{instance_size}_{instance_id}")
                logger.info(f'dc is {dc} and output location {output_location}')

                # Read ESTNU xml file into Python object
                estnu = STNU.from_graphml(output_location)

                if dc:
                    for i in range(n_sim):
                        # Run RTE algorithm with Java tool
                        schedule = run_rte_algorithm(output_location)
                        if schedule:
                            true_durations, start_times, finish_times = [], [], []
                            for product in my_productionplan.products:
                                for activity in product.activities:
                                    key_start = f'{product.product_index}_{activity.id}_start'
                                    key_finish = f'{product.product_index}_{activity.id}_finish'
                                    start = schedule[key_start]
                                    start_times.append(start)
                                    finish = schedule[key_finish]
                                    finish_times.append(finish)
                                    true_durations.append(finish - start)

                            logger.debug(
                                f'start times {start_times} finish times {finish_times}, durations {true_durations}')

                            makespan_stnu = max(schedule.values())

                            feasibility = check_feasibility(start_times, finish_times, true_durations, rcpsp.capacity, rcpsp.successors,
                                                 rcpsp.resources, rcpsp.min_lag, rcpsp.max_lag)
                            if feasibility:
                                print(f'The schedule generate with the STNU pipeline is feasible')
                            else:
                                Warning(f'The schedule generated with the STNU pipeline is not feasible')

                            assert feasibility

                            rcpsp = RCPSP_CP(my_productionplan)
                            print(len(rcpsp.durations))
                            _, _, cp_output = rcpsp.solve(true_durations,None, 1, 0)
                            makespan_pi = max(cp_output["end"].tolist())
                            assert makespan_pi <= makespan_stnu
                            logger.info(f'makespan under perfect information is {makespan_pi}, makespan obtained with STNU is {makespan_stnu}, '
                                        f'regret is {makespan_stnu-makespan_pi}')

                            # Store data
                            collected_data.append({"instance": instance_name, "it": i,  "makespan_lb": makespan_pi, "makespan_stnu": makespan_stnu,
                                                   "regret": makespan_stnu-makespan_pi, "rel_regret": (makespan_stnu-makespan_pi)/makespan_pi,
                                                  "instance_type": instance_type, "status": "feasible_and_dc"})
                            collected_data_df = pd.DataFrame(collected_data)
                            collected_data_df.to_csv(results_location)
                        else:
                            collected_data.append(
                                {"instance": instance_name, "instance_type": instance_type,
                                 "status": "feasible_and_dc_but_rte_error"})
                            collected_data_df = pd.DataFrame(collected_data)
                            collected_data_df.to_csv(results_location)

                else:
                    collected_data.append(
                        {"instance": instance_name, "instance_type": instance_type, "status": "feasible_but_not_dc"})
                    collected_data_df = pd.DataFrame(collected_data)
                    collected_data_df.to_csv(results_location)
            else:
                collected_data.append(
                    {"instance": instance_name, "instance_type": instance_type, "status": "infeasible"})
                collected_data_df = pd.DataFrame(collected_data)
                collected_data_df.to_csv(results_location)