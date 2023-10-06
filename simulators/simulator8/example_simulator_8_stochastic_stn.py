import json
import pandas as pd
from classes.classes import Scenario, ProductionPlan, STN
from classes.operator import OperatorSTN
from classes.simulator_8 import Simulator
from stn.get_resource_chains import get_resource_chains
import numpy as np
from numpy import random
from matplotlib import pyplot as plt

"""
In this script we test the instances type 2 that do have a max time lag
"""

# Settings
policy_type = 1
printing = True
printing_output = True
compatibility = True
max_time_lag = False
seed = 3

for instance_size in [10]:
    for instance_id in range(1, 2):
        # Read CP output and convert
        instance_name = f"{instance_size}_{instance_id}_factory_1"
        file_name = instance_name

        # Deterministic check:
        # Read CP output and instance
        my_productionplan = ProductionPlan(
            **json.load(open('factory_data/development/instances_type_2/instance_' + instance_name + '.json')))
        my_productionplan.set_sequence(sequence=np.arange(instance_size))
        cp_output = pd.read_csv(f"results/cp_model/development/instances_type_2/start times {file_name}.csv")
        makespan_cp_output = max(cp_output["end"].tolist())
        print(f'Makespan according to CP output is {makespan_cp_output}')
        earliest_start = cp_output.to_dict('records')

        # Set up operator and initial STN
        stn = STN.from_production_plan(my_productionplan, stochastic=True, max_time_lag=max_time_lag)

        # Add resource constraints between incompatible pairs using sequencing decision from CP
        resource_chains = get_resource_chains(production_plan=my_productionplan, earliest_start=earliest_start, complete=True)

        # Now add the edges with the correct edge weights to the STN
        for pred_p, pred_a, succ_p, succ_a in resource_chains:
            # The finish of the predecessor should precede the start of the successor
            pred_idx = stn.translation_dict_reversed[
                (pred_p, pred_a, STN.EVENT_FINISH)]  # Get translation index from finish of predecessor
            suc_idx = stn.translation_dict_reversed[
                (succ_p, succ_a, STN.EVENT_START)]  # Get translation index from start of successor

            # TODO: is this really the best modelling choice having the 0 as lowerbound instead of the 1?
            stn.add_interval_constraint(pred_idx, suc_idx, 1, np.inf)

        # Add compatibility constraints between incompatible pairs using sequencing decision from CP:
        if compatibility:
            for constraint in my_productionplan.factory.compatibility_constraints:
                constraint_0_activities = cp_output[(cp_output['product_id'] == constraint[0]['product_id']) & (cp_output['activity_id'] == constraint[0]['activity_id'])]
                constraint_1_activities = cp_output[(cp_output['product_id'] == constraint[1]['product_id']) & (cp_output['activity_id'] == constraint[1]['activity_id'])]
                if len(constraint_0_activities) > 0 and len(constraint_1_activities) > 0:
                    for index, row in constraint_0_activities.iterrows():
                        product_index_0 = row["product_index"]
                        activity_id_0 = row["activity_id"]
                        start_0 = row['earliest_start']

                        for index, row in constraint_1_activities.iterrows():
                            product_index_1 = row["product_index"]
                            activity_id_1 = row["activity_id"]
                            start_1 = row['earliest_start']

                        if start_0 < start_1:
                            pred_idx = stn.translation_dict_reversed[(product_index_0, activity_id_0, STN.EVENT_FINISH)]
                            suc_idx = stn.translation_dict_reversed[(product_index_1, activity_id_1, STN.EVENT_START)]

                        else:
                            pred_idx = stn.translation_dict_reversed[(product_index_1, activity_id_1, STN.EVENT_FINISH)]
                            suc_idx = stn.translation_dict_reversed[(product_index_0, activity_id_0, STN.EVENT_START)]

                        stn.add_interval_constraint(pred_idx, suc_idx, 0, np.inf)

        stn.floyd_warshall()   # Perform initial computation of shortest paths

        operator = OperatorSTN(my_productionplan, stn, printing=printing)

        # Create
        scenario_1 = my_productionplan.create_scenario(seed=seed)

        # TODO: make it also work when check_max_time_lag=True
        my_simulator = Simulator(plan=scenario_1.production_plan, operator=operator, printing=printing, check_max_time_lag=max_time_lag)

        # Run simulation
        makespan, lateness, nr_unfinished = my_simulator.simulate(sim_time=25000, write=False)

        distances = my_simulator.operator.stn.shortest_distances  # is this really using the stn that is updated from the operator?
        # Check that the incremental method is correct
        assert np.array_equal(distances, my_simulator.operator.stn.floyd_warshall())
