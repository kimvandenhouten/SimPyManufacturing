import json
from classes.classes import ProductionPlan
import classes.general
from classes.stnu import STNU
from rcpsp.solvers.check_feasibility import check_feasibility
from stnu.java_comparison.stnu_to_xml_function import stnu_to_xml
from stnu.algorithms.call_java_cstnu_tool import run_dc_algorithm
from stnu.algorithms.rte_star import rte_star
from stnu.get_resource_chains_reservations import get_resource_chains, add_resource_chains
from rcpsp.solvers.RCPSP_CP import RCPSP_CP
import numpy as np
import pandas as pd

logger = classes.general.get_logger(__name__)
collected_data = []
n_sim = 10
results_location = f'stnu/experiments/results/results_DSM_instances_infeasible.csv'
for (instance_size, instance_id) in [(20, 1), (40, 1), (40, 2), (40, 3), (40, 5)]:
        for instance_type in [2]:
            # Specify instance name

            instance_name = f"{instance_size}_{instance_id}_factory_1"

            # Read production plan
            my_productionplan = ProductionPlan(
                **json.load(open(f'factory_data/development/instances_type_{instance_type}_uniform/instance_' + instance_name + '.json')))

            # Make STNU from production plan
            # Solve deterministic CP and data
            rcpsp = RCPSP_CP(my_productionplan)
            res, _, cp_output = rcpsp.solve(None, None, 1, 0)
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
                        # TODO: make this within a function maybe
                        sample = {}
                        for (A, C) in estnu.contingent_links:
                            duration_sample = np.random.randint(estnu.contingent_links[(A, C)]["lc_value"],
                                                                estnu.contingent_links[(A, C)]["uc_value"])
                            sample[C] = duration_sample
                        logger.info(f'Sample that will be given to RTE_star: {sample}')

                        ## Run RTE algorithm with alternative oracle and store makespan
                        rte_data = rte_star(estnu, oracle="sample", sample=sample)

                        if rte_data:
                            # TODO: feasibility check on the output schedule
                            makespan_stnu = max(rte_data.f.values())
                            logger.info(f'The makespan obtained with the STNU algorithm is {makespan_stnu}')

                            ## Compute makespan lower bound by computing perfect information optimum with CP solver
                            durations = []
                            start_times = []
                            finish_times = []
                            for product in my_productionplan.products:
                                for activity in product.activities:
                                    key_start = f'{product.product_index}_{activity.id}_start'
                                    key_finish = f'{product.product_index}_{activity.id}_finish'
                                    node_idx_start = estnu.translation_dict_reversed[key_start]
                                    node_idx_finish = estnu.translation_dict_reversed[key_finish]
                                    weight = sample[node_idx_finish]
                                    start_times.append(rte_data.f[node_idx_start])
                                    finish_times.append(rte_data.f[node_idx_finish])
                                    durations.append(weight)

                            feasibility = check_feasibility(start_times, finish_times, durations, rcpsp.capacity, rcpsp.successors,
                                                 rcpsp.resources, rcpsp.min_lag, rcpsp.max_lag)
                            if feasibility:
                                print(f'The schedule generate with the STNU pipeline is feasible')
                            else:
                                Warning(f'The schedule generated with the STNU pipeline is not feasible')

                            assert feasibility

                            rcpsp = RCPSP_CP(my_productionplan)
                            print(len(rcpsp.durations))
                            res, _, cp_output = rcpsp.solve(durations,None, 1, 0)
                            if res:
                                gap_pi = res.get_objective_gaps()[0]
                                makespan_pi = max(cp_output["end"].tolist())
                                assert makespan_pi <= makespan_stnu
                            else:
                                gap_pi = np.inf
                                makespan_pi = np.inf

                            logger.info(f'makespan under perfect information is {makespan_pi}, makespan obtained with STNU is {makespan_stnu}, '
                                        f'regret is {makespan_stnu-makespan_pi}')
                            collected_data.append({"instance": instance_name, "it": i,  "makespan_lb": makespan_pi, "gap_lb": gap_pi , "makespan_stnu": makespan_stnu,
                                                   "regret": makespan_stnu-makespan_pi, "rel_regret": (makespan_stnu-makespan_pi)/makespan_pi,
                                                  "instance_type": instance_type, "status": "feasible_and_dc"})

                            ## Compute makespan upper bound by using heuristic and
                            #TODO: this heuristic is not yet implemented

                            # Store experiment data
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