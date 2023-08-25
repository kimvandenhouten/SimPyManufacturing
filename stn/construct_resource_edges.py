import json
import pandas as pd
from classes.classes import Scenario, ProductionPlan
from classes.operator import Operator
from classes.simulator_7 import Simulator
import numpy as np

def construct_resource_edges(production_plan, earliest_start):

    production_plan.set_earliest_start_times(earliest_start)
    
    # Which resources are in the factory?
    resources = {}
    for i, resource in enumerate(production_plan.factory.resource_names):
        nr_resources = production_plan.factory.capacity[i]
        for r in range(nr_resources):
            resources[(resource, r)] = []
    
    # Set printing to True if you want to print all events
    policy_type = 2
    operator = Operator(plan=production_plan, policy_type=policy_type, printing=False)
    my_simulator = Simulator(plan=production_plan, operator=operator, printing=False)
    
    # Run simulation
    makespan, lateness, nr_unfinished = my_simulator.simulate(sim_time=2000, write=False)
    logger = my_simulator.logger.info.to_df()
    
    for index, row in logger.iterrows():
        for resource in row["Resources"]:
            resources[(resource.resource_group, resource.id)].append({"ProductIndex": row["ProductIndex"], "Activity": row["Activity"], "Start": row["Start"]})
    
    edges_stn = []
    EVENT_START = "start"
    EVENT_FINISH = "finish"
    for key in resources:
        resource_activities = resources[key]
        if len(resource_activities) > 1: # Check if there are multiple activities assigned to the same resource
            # Sort by start time
            resource_activities = sorted(resource_activities, key=lambda x: x["Start"])
    
            # To do keep track of edges that should be added to STN
            for i in range(1, len(resource_activities)):
                if i > 0:
                    predecessor = resource_activities[i-1]
                    successor = resource_activities[i]
                    edges_stn.append(((predecessor["ProductIndex"], predecessor["Activity"], EVENT_FINISH),
                                     (successor["ProductIndex"], successor["Activity"], EVENT_START))
                                     )
    return edges_stn
        









