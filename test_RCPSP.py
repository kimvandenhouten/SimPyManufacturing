import pandas as pd

# read instance
for instance_name in ["5_1_factory_1", "5_2_factory_1", "5_3_factory_1", "5_4_factory_1", "5_5_factory_1"]:
    instance = pd.read_pickle(f"factory_data/instances/instance_{instance_name}.pkl")

    # convert to RCPSP instance
    capacity = instance.FACTORY.CAPACITY
    durations = []
    num_tasks = 0
    num_resources = len(capacity)
    resources = []
    successors = []
    temporal_relations = {}

    resource_translation = instance.FACTORY.RESOURCE_NAMES
    task_translation = []

    activity_counter = 0
    product_counter = 0

    # loop over all products
    for p in instance.PRODUCTS:
        for (i, j) in p.TEMPORAL_RELATIONS:
            temporal_relations[(i+activity_counter, j+activity_counter)] = p.TEMPORAL_RELATIONS[(i, j)]
            successors.append((i+activity_counter, j+activity_counter))

        nr_activities = len(p.ACTIVITIES)
        for act in range(0, nr_activities):
            task_translation.append(product_counter)
        print(f'number of activities {nr_activities}')

        for a in p.ACTIVITIES:
            durations.append(a.PROCESSING_TIME[0])
            resources.append(a.NEEDS)

        activity_counter += nr_activities
        product_counter += 1


    from methods.RCPSP import RCPSP

    MILP = RCPSP(capacity=capacity, durations=durations, num_tasks=activity_counter, num_resources=num_resources,
                 resources=resources, temporal_relations=temporal_relations, successors=successors)

    MILP.model(temp_relation="time_lag")
    MILP.solve()
    MILP.get_start_times()
    gannt = MILP.make_resource_usage_table(resource_translation=resource_translation, task_translation=task_translation)
    gannt.to_csv(f'results/milp_output/instance_{instance_name}.csv')

    # Compare with simulator
    from classes.simulator_3 import Simulator
    plan = pd.read_pickle(f"factory_data/instances/instance_{instance_name}.pkl")
    plan.set_sequence([0])
    simulator = Simulator(plan, delay=0, printing=False)
    makespan, lateness = simulator.simulate(SIM_TIME=1000, RANDOM_SEED=1, write=True,
                                            output_location=f"results/milp_output/simulator_check_instance_{instance_name}.csv")
    print(f'Makespan obtained with simulator is {makespan}')