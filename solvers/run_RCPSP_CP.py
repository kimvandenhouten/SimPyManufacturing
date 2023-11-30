import pandas as pd
import time
import json
from classes.classes import ProductionPlan
from solvers.RCPSP_CP import solve_rcpsp_cp, convert_instance_to_cp_input

# read instance
output_file_name = "Results instances SimPy Manufacturing"
results = []
l1 = 1
l2 = 0

for size in [20]:
    for id in range(1, 2):
        instance_name = f"{size}_{id}_factory_1"
        instance = ProductionPlan(**json.load(open('factory_data/development/instances_type_2/instance_' + instance_name + '.json')))
        resources, capacity, durations, successors, min_lag, max_lag, durations, capacity,  deadlines,\
        product_index_translation, product_id_translation, activity_id_translation, incompatible_tasks\
            = convert_instance_to_cp_input(instance)
        print(f'number of tasks is {len(durations)}')
        start = time.time()
        if True:
            solution, callback, data_df = solve_rcpsp_cp(demands=resources, capacities=capacity, durations=durations, successors=successors,
                                                min_lag=min_lag, max_lag=max_lag, nb_tasks=len(durations), nb_resources=len(capacity),
                                                deadlines=deadlines, product_index_translation=product_index_translation,
                                                product_id_translation=product_id_translation, activity_id_translation=activity_id_translation,
                                                incompatible_tasks=incompatible_tasks, time_limit=3600*5, l1=l1, l2=l2,
                                                output_file=f"start times {instance_name}.csv")

            results.append({"instance": instance_name,
                            "act.": len(durations),
                            "l1": l1,
                            "l2": l2,
                            "objective": solution.get_objective_value() if solution else "inf",
                            "solve time": solution.get_process_infos().get_total_solve_time() if solution else "timeout",
                            "total time": time.time() - start,
                            "method": "CP solver",
                            "Optimality": solution.solve_status if solution else "inf"
                               #,
                            #"anytime-solutions": callback.anytimeData["anytime-solutions"],
                            #"anytime-bounds": callback.anytimeData["anytime-bounds"]
                           })

            results_df = pd.DataFrame(results)
            results_df.to_csv(f"{output_file_name}.csv")

