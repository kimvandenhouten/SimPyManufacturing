import json
import pandas as pd
from classes.classes import Scenario, ProductionPlan, STN
from classes.operator import OperatorSTN
from classes.simulator_8 import Simulator
from stn.get_resource_chains_reservations import get_resource_chains, add_resource_chains
from stn.get_compatibility_chains import get_compatibility_chains
import numpy as np
from solvers.RCPSP_CP import RCPSP_CP

"""
In this script we test the instances type 2 that do have a max time lag
"""

# Settings
printing = True
printing_output = True
compatibility = True
max_time_lag = False
seed = 3
reservation_factor = 0.7
read_cp_output = False

for instance_size in [10]:
    for instance_id in range(1, 2):
        instance_name = f"{instance_size}_{instance_id}_factory_1"
        my_productionplan = ProductionPlan(
            **json.load(open('factory_data/development/instances_type_1_uniform/instance_' + instance_name + '.json')))
        my_productionplan.set_sequence(sequence=np.arange(instance_size))
        if read_cp_output:
            cp_output = pd.read_csv(f"results/cp_model/development/instances_type_2/start times {instance_name}.csv")
        else:
            rcpsp = RCPSP_CP(my_productionplan)
            solution, callback, data_df = rcpsp.solve(time_limit=60, l1=1, l2=0, output_file=f"start times {instance_name}.csv")
            cp_output = data_df

        makespan_cp_output = max(cp_output["end"].tolist())
        print(f'Makespan according to CP output is {makespan_cp_output}')
        earliest_start = cp_output.to_dict('records')

        # Set up operator and initial STN
        stn = STN.from_production_plan(my_productionplan, stochastic=True, max_time_lag=max_time_lag)

        # Add resource constraints between incompatible pairs using sequencing decision from CP
        resource_chains, resource_use = get_resource_chains(production_plan=my_productionplan, earliest_start=earliest_start, complete=True)
        stn = add_resource_chains(stn=stn, resource_chains=resource_chains, reservation_factor=reservation_factor)
        print('resource chains added')

        # Add compatibility constraints between incompatible pairs using sequencing decision from CP:
        if compatibility:
            stn = get_compatibility_chains(stn=stn, productionplan=my_productionplan, cp_output=cp_output)
            print(f'Compatibility chains added')
        stn.floyd_warshall()   # Perform initial computation of shortest paths
        print(f'floyd warshall finished')
        operator = OperatorSTN(my_productionplan, stn, printing=printing, resource_use_cp=resource_use)

        # Create
        scenario_1 = my_productionplan.create_scenario(seed=seed)

        # TODO: make it also work when check_max_time_lag=True
        my_simulator = Simulator(plan=scenario_1.production_plan, operator=operator, printing=printing, check_max_time_lag=max_time_lag)

        # Run simulation
        makespan, lateness, nr_unfinished = my_simulator.simulate(sim_time=25000, write=False)

        distances = my_simulator.operator.stn.shortest_distances  # is this really using the stn that is updated from the operator?
        # Check that the incremental method is correct
        assert np.array_equal(distances, my_simulator.operator.stn.floyd_warshall())

        # Can we also check what the true optimal makespan would have been with perfect information?
        rcpsp = RCPSP_CP(scenario_1.production_plan)
        solution, callback, cp_output = rcpsp.solve(time_limit=60, l1=1, l2=0,
                                                  output_file=f"start times {instance_name}.csv")
        makespan_cp_output = max(cp_output["end"].tolist())

        print(f'makespan under perfect information for this scenario is {makespan_cp_output}')

