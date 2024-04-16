import json
from classes.classes import ProductionPlan
import classes.general
from classes.stnu import STNU
from stnu.java_comparison.stnu_to_xml_function import stnu_to_xml
import pandas as pd
from stnu.get_resource_chains_reservations import get_resource_chains, add_resource_chains
from solvers.RCPSP_CP import RCPSP_CP

"""
In this script we test the simulation that use the STNU together with the morris14 algorithm
"""

logger = classes.general.get_logger()

# Settings
printing_output = True
compatibility = True
max_time_lag = False

# Load instance data
instance_size = 10
instance_id = 1
instance_name = f"{instance_size}_{instance_id}_factory_1"
my_productionplan = ProductionPlan(
    **json.load(open('factory_data/development/instances_type_2_uniform/instance_' + instance_name + '.json')))

# Read in schedule that is output from stnu algorithms
schedule = pd.read_csv(f"stnu/examples/schedules/schedule_production_plan_{instance_size}_{instance_id}_makespan=1408.csv")

# Obtain realizations of uncertain links
sampled_weights = pd.read_csv(f"stnu/examples/schedules/sampled_weights_production_plan_{instance_size}_{instance_id}_makespan=1408.csv")
keys = sampled_weights["description"].tolist()
weights = sampled_weights["weight"].tolist()

# FIXME: this is all very ugly and inefficient
durations = []
for product in my_productionplan.products:
    for activity in product.activities:
        key = f'{product.product_index}_{activity.id}_finish'
        index = keys.index(key)
        weight = weights[index]
        durations.append(weight)

# Solve under perfect information
rcpsp = RCPSP_CP(my_productionplan)
print(len(rcpsp.durations))
# TODO: set durations obtained from
_, _, cp_output = rcpsp.solve(durations,1800, 1, 0)
makespan_cp_output = max(cp_output["end"].tolist())
logger.info(f'makespan under perfect information is {makespan_cp_output}, makespan obtained with STNU is 1408, regret is {1408-makespan_cp_output}')



