import json
from classes.classes import ProductionPlan
import classes.general
from classes.stnu import STNU
from stnu.java_comparison.stnu_to_xml_function import stnu_to_xml
from stnu.algorithms.call_java_dc_checking import run_dc_algorithm
from stnu.algorithms.rte_star import rte_star
from stnu.get_resource_chains_reservations import get_resource_chains, add_resource_chains
from solvers.RCPSP_CP import RCPSP_CP
import numpy as np
import pandas as pd

logger = classes.general.get_logger(level="INFO")
collected_data = []
n_sim = 5
for instance_size in [20, 40]:
    for instance_id in [1]:
        for instance_type in [1, 2]:
            # Specify instance name

            instance_name = f"{instance_size}_{instance_id}_factory_1"

            # Read production plan
            my_productionplan = ProductionPlan(
                **json.load(open(f'factory_data/development/instances_type_{instance_type}_uniform/instance_' + instance_name + '.json')))

            # Make STNU from production plan
            # Solve deterministic CP and data
            rcpsp = RCPSP_CP(my_productionplan)
            _, _, cp_output = rcpsp.solve(None, None, 1, 0)
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

            # For i in nr_samples:

            for i in range(n_sim):
                # TODO: make this within a function maybe
                sample = {}
                for (A, C) in estnu.contingent_links:
                    duration_sample = np.random.randint(estnu.contingent_links[(A, C)]["lc_value"],
                                                        estnu.contingent_links[(A, C)]["uc_value"])
                    sample[C] = duration_sample
                logger.info(f'Sample that will be given to RTE_star: {sample}')

                ## Run RTE algorithm with alternative oracle and store makespan
                rte_data = rte_star(estnu, oracle="sample", sample=sample)

                # TODO: feasibility check on the output schedule
                makespan_stnu = max(rte_data.f.values())
                logger.info(f'The makespan obtained with the STNU algorithm is {makespan_stnu}')

                ## Compute makespan lower bound by computing perfect information optimum with CP solver
                durations = []
                for product in my_productionplan.products:
                    for activity in product.activities:
                        key = f'{product.product_index}_{activity.id}_finish'
                        node_idx = estnu.translation_dict_reversed[key]
                        weight = sample[node_idx]
                        durations.append(weight)

                rcpsp = RCPSP_CP(my_productionplan)
                print(len(rcpsp.durations))
                _, _, cp_output = rcpsp.solve(durations,None, 1, 0)
                makespan_pi = max(cp_output["end"].tolist())
                assert makespan_pi <= makespan_stnu
                logger.info(f'makespan under perfect information is {makespan_pi}, makespan obtained with STNU is {makespan_stnu}, '
                            f'regret is {makespan_stnu-makespan_pi}')
                collected_data.append({"instance": instance_name, "it": i,  "makespan_lb": makespan_pi, "makespan_stnu": makespan_stnu,
                                       "regret": makespan_stnu-makespan_pi, "instance_type": instance_type})

                ## Compute makespan upper bound by using heuristic and
                #TODO: this heuristic is not yet implemented

                # Store experiment data
                collected_data_df = pd.DataFrame(collected_data)
                collected_data_df.to_csv('stnu/experiments/results.csv')