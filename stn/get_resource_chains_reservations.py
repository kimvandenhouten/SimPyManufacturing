from classes.operator import Operator
from classes.simulator_7 import Simulator
from classes.classes import STN
import numpy as np


def get_resource_chains(production_plan, earliest_start, complete=False):
    production_plan.set_earliest_start_times(earliest_start)
    
    # Set printing to True if you want to print all events
    policy_type = 2
    operator = Operator(plan=production_plan, policy_type=policy_type, printing=False)
    my_simulator = Simulator(plan=production_plan, operator=operator, printing=False)
    
    # Run simulation
    makespan, lateness, nr_unfinished = my_simulator.simulate(sim_time=2000, write=False)
    logger = my_simulator.logger.info.to_df()

    resource_use = {}
    for index, row in logger.iterrows():
        for resource in row["Resources"]:
            users = resource_use.setdefault((resource.resource_group, resource.id), [])
            users.append({"ProductIndex": row["ProductIndex"], "Activity": row["Activity"], "Start": row["Start"]})
    resource_chains = []
    if complete:
        for resource_activities in resource_use.values():
            if len(resource_activities) > 1:  # Check if there are multiple activities assigned to the same resource
                # Sort by start time
                resource_activities = sorted(resource_activities, key=lambda x: x["Start"])
                # To do keep track of edges that should be added to STN
                for i in range(1, len(resource_activities)):
                    for j in range(0, i):
                        predecessor = resource_activities[j]
                        successor = resource_activities[i]
                        resource_chains.append((predecessor["ProductIndex"], predecessor["Activity"],
                                                successor["ProductIndex"], successor["Activity"]))
    else:
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


def add_resource_chains(stn, resource_chains):
    for pred_p, pred_a, succ_p, succ_a in resource_chains:
        # The finish of the predecessor should precede the start of the successor
        pred_idx = stn.translation_dict_reversed[
            (pred_p, pred_a, STN.EVENT_FINISH)]  # Get translation index from finish of predecessor
        suc_idx = stn.translation_dict_reversed[
            (succ_p, succ_a, STN.EVENT_START)]  # Get translation index from start of successor

        # TODO: is this really the best modelling choice having the 0 as lowerbound instead of the 1?
        stn.add_interval_constraint(pred_idx, suc_idx, 1, np.inf)
    return stn
