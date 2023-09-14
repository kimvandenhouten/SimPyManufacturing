from classes.operator import Operator
from classes.simulator_7 import Simulator


def get_resource_chains(production_plan, earliest_start):
    production_plan.set_earliest_start_times(earliest_start)
    
    # Set printing to True if you want to print all events
    policy_type = 2
    operator = Operator(plan=production_plan, policy_type=policy_type, printing=True)
    my_simulator = Simulator(plan=production_plan, operator=operator, printing=True)
    
    # Run simulation
    makespan, lateness, nr_unfinished = my_simulator.simulate(sim_time=2000, write=False)
    logger = my_simulator.logger.info.to_df()

    resource_use = {}
    for index, row in logger.iterrows():
        for resource in row["Resources"]:
            users = resource_use.setdefault((resource.resource_group, resource.id), [])
            users.append({"ProductIndex": row["ProductIndex"], "Activity": row["Activity"], "Start": row["Start"]})
    
    resource_chains = []
    for resource_activities in resource_use.values():
        if len(resource_activities) > 1: # Check if there are multiple activities assigned to the same resource
            # Sort by start time
            resource_activities = sorted(resource_activities, key=lambda x: x["Start"])
    
            # To do keep track of edges that should be added to STN
            for i in range(1, len(resource_activities)):
                predecessor = resource_activities[i-1]
                successor = resource_activities[i]
                resource_chains.append((predecessor["ProductIndex"], predecessor["Activity"], successor["ProductIndex"], successor["Activity"]))
    return resource_chains
