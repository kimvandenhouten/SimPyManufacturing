import json
from classes.classes import ProductionPlan
import classes.general
from classes.stnu import STNU

from stnu.get_resource_chains_reservations import get_resource_chains, add_resource_chains
from solvers.RCPSP_CP import RCPSP_CP
from stnu.dc_checking import determine_dc

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
    **json.load(open('factory_data/development/instances_type_1_uniform/instance_' + instance_name + '.json')))

# Solve deterministic CP and data
rcpsp = RCPSP_CP(my_productionplan)
print(len(rcpsp.durations))
_, _, cp_output = rcpsp.solve(1800, 1, 0)
makespan_cp_output = max(cp_output["end"].tolist())
logger.info(f'makespan according to CP output is {makespan_cp_output}')
earliest_start = cp_output.to_dict('records')
resource_chains, resource_use = get_resource_chains(my_productionplan, earliest_start, True)

# Set up stn and run floyd warshall
stnu = STNU.from_production_plan(my_productionplan, max_time_lag=max_time_lag)
stnu = add_resource_chains(stnu=stnu, resource_chains=resource_chains)

determine_dc(stnu)

