from temporal_networks.stn import STN

import general.logger
logger = general.logger.get_logger(__name__)
import numpy as np

from factory_simulator.classes import ProductionPlan, Product


class FACTORY_STNU(STN):
    def __init__(self, origin_horizon=True):

        super().__init__(origin_horizon)

    @classmethod
    def from_production_plan(cls, production_plan: ProductionPlan, stochastic=False, max_time_lag=True) -> 'STN':
        stn = cls()
        for product in production_plan.products:
            for activity in product.activities:
                # Add nodes that refer to start and end of activity
                a_start = stn.add_node(product.product_index, activity.id, cls.EVENT_START)
                a_finish = stn.add_node(product.product_index, activity.id, cls.EVENT_FINISH)

                # Add edge between start and finish with processing time
                if stochastic is False:
                    stn.add_tight_constraint(a_start, a_finish, activity.processing_time[0])
                else:
                    # Possibly add function to distribution to convert distribution to uncertainty set
                    if activity.distribution.type == "UNIFORMDISCRETE":
                        lower_bound = activity.distribution.lb
                        upper_bound = activity.distribution.ub
                        stn.add_interval_constraint(a_start, a_finish, lower_bound, upper_bound)
                    elif activity.distribution.type == "NORMAL":
                        lower_bound = max(round(activity.distribution.mean - 5 * activity.distribution.variance), 0)
                        upper_bound = round(activity.distribution.mean + 10 * activity.distribution.variance)
                        stn.add_interval_constraint(a_start, a_finish, lower_bound, upper_bound)
                    else:
                        ValueError("Uncertainty set not implemented for this distribution")

            # For every temporal relation in this product's temporal_relations, add edge between nodes with min and max lag
            for i, j in product.temporal_relations:
                min_lag = product.temporal_relations[(i, j)].min_lag
                max_lag = product.temporal_relations[(i, j)].max_lag
                i_idx = stn.translation_dict_reversed[(product.product_index, i, cls.EVENT_START)]
                j_idx = stn.translation_dict_reversed[(product.product_index, j, cls.EVENT_START)]

                # TODO: make sure that the simulator - operator also works when max_time_lag = True
                if max_time_lag:
                    if max_lag is not None:
                        stn.add_interval_constraint(i_idx, j_idx, min_lag, max_lag)
                    else:
                        stn.add_interval_constraint(i_idx, j_idx, min_lag, np.inf)
                else:
                    stn.add_interval_constraint(i_idx, j_idx, min_lag, np.inf)
        return stn


import numpy as np

from factory_simulator.operator import Operator
from factory_simulator.simulator_7 import Simulator
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
            if len(resource_activities) > 1:  # Check if there are multiple activities assigned to the same resource
                # Sort by start time
                resource_activities = sorted(resource_activities, key=lambda x: x["Start"])

                # To do keep track of edges that should be added to STN
                for i in range(1, len(resource_activities)):
                    predecessor = resource_activities[i - 1]
                    successor = resource_activities[i]
                    resource_chains.append((predecessor["ProductIndex"], predecessor["Activity"],
                                            successor["ProductIndex"], successor["Activity"]))
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