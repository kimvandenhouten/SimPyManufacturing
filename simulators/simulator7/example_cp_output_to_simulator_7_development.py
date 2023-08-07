import json
import pandas as pd
from classes.classes import Scenario, ProductionPlan
from classes.operator import Operator
from classes.simulator_7 import Simulator
import numpy as np
from numpy import random
from matplotlib import pyplot as plt

# Settings
nr_scenarios = 1000
scenario_seeds = random.randint(100000, size=nr_scenarios)
policy_type = 2
printing = False

for instance_size in [10]:
    for instance_id in range(1, 10):
        # Read CP output and convert
        instance_name = f"{instance_size}_{instance_id}_factory_1"
        file_name = instance_name
        cp_output = pd.read_csv(f"results/instances_development/start times {file_name}.csv")
        makespan_cp_output = max(cp_output["end"].tolist())
        print(f'Makespan according to CP outout is {makespan_cp_output}')
        earliest_start = cp_output.to_dict('records')
        evaluation = []

        # deterministic check:
        # Read input instance
        my_productionplan = ProductionPlan(
            **json.load(open('factory_data/development/instances/instance_' + instance_name + '.json')))
        my_productionplan.set_earliest_start_times(earliest_start)
        my_productionplan.set_sequence(sequence=np.arange(instance_size))

        # Set printing to True if you want to print all events
        operator = Operator(plan=my_productionplan, policy_type=policy_type, printing=False)
        my_simulator = Simulator(plan=my_productionplan, operator=operator, printing=False)

        # Run simulation
        makespan, lateness, nr_unfinished = my_simulator.simulate(sim_time=2000, write=False, output_location=f""
        f"simulators/simulator7/outputs/example_cp_output_to_simulator.csv")

        print(f'According to the deterministic simulation, the makespan is {makespan}')
        print(f'The number of unfinished products {nr_unfinished}')
        print(f'The number of clashes (i.e. activities that could not be processed) is {my_simulator.nr_clashes}')

        for seed in scenario_seeds:
            # Read input instance
            my_productionplan = ProductionPlan(
                **json.load(open('factory_data/development/instances/instance_' + instance_name + '.json')))
            my_productionplan.set_earliest_start_times(earliest_start)
            my_productionplan.set_sequence(sequence=np.arange(instance_size))
            scenario_1 = my_productionplan.create_scenario(seed)

            # Set printing to True if you want to print all events
            operator = Operator(plan=scenario_1.production_plan, policy_type=policy_type, printing=False)
            my_simulator = Simulator(plan=scenario_1.production_plan, operator=operator, printing=False)

            # Run simulation
            makespan, lateness, nr_unfinished = my_simulator.simulate(sim_time=2000, write=False, output_location=f""
            f"simulators/simulator7/outputs/example_cp_output_to_simulator.csv")

            if printing:
                print(f'According to the simulation, the makespan is {makespan} and the lateness is {lateness}')
                print(f'The number of unfinished products {nr_unfinished}')
                print(f'The number of clashes (i.e. activities that could not be processed) is {my_simulator.nr_clashes}')

            evaluation.append({"seed": seed,
                               "makespan": makespan,
                               "lateness": lateness,
                               "nr_unfinished_products": nr_unfinished})

        evaluation = pd.DataFrame(evaluation)
        evaluation.to_csv(f"simulators/simulator7/outputs/evaluation_table_{instance_name}_policy={policy_type}.csv")
