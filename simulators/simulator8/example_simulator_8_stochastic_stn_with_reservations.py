import json
from classes.classes import ProductionPlan
import classes.general
from classes.stn import STN
from classes.operator import OperatorSTN
from classes.simulator_8 import Simulator
from stn.get_resource_chains_reservations import get_resource_chains, add_resource_chains
from stn.get_compatibility_chains import get_compatibility_chains
from solvers.RCPSP_CP import RCPSP_CP
import copy
"""
In this script we test the simulation that use the STN to run send activitites
"""

logger = classes.general.get_logger()

# Settings
printing = False
printing_output = True
compatibility = True
max_time_lag = False
reservation_factor = 0.0
use_p3c = True

# Load instance data
instance_size = 10
instance_id = 1
instance_name = f"{instance_size}_{instance_id}_factory_1"
my_productionplan = ProductionPlan(
    **json.load(open('factory_data/development/instances_type_1_uniform/instance_' + instance_name + '.json')))

# Solve deterministic CP and data
rcpsp = RCPSP_CP(my_productionplan)
_, _, cp_output = rcpsp.solve(60, 1, 0)
makespan_cp_output = max(cp_output["end"].tolist())
logger.info(f'makespan according to CP output is {makespan_cp_output}')
earliest_start = cp_output.to_dict('records')
resource_chains, resource_use = get_resource_chains(my_productionplan, earliest_start, True)

# Set up stn and run floyd warshall
stn = STN.from_production_plan(my_productionplan, stochastic=True, max_time_lag=max_time_lag)
stn = add_resource_chains(stn=stn, resource_chains=resource_chains, reservation_factor=reservation_factor)
stn = get_compatibility_chains(stn=stn, productionplan=my_productionplan, cp_output=cp_output)

if use_p3c:
    logger.info('start p3c')
    stn.p3c()   # Perform initial computation of shortest paths
    logger.info('p3c finished')
else:
    logger.info(f'start floyd warshall')
    stn.floyd_warshall()   # Perform initial computation of shortest paths
    logger.info(f'floyd warshall finished')

# Create
for seed in range(0, 200):
    logger.info(f'start scenario {seed}')
    stn_copy = copy.deepcopy(stn)  # FIXME: could we avoid deepcopy
    productionplan_copy = copy.deepcopy(my_productionplan)  # FIXME: could we avoid deepcopy
    operator = OperatorSTN(productionplan_copy, stn_copy, resource_use, printing=printing)

    # run simulation for this scenario seed
    # TODO: make it also work when check_max_time_lag=True
    scenario_1 = productionplan_copy.create_scenario(seed)
    my_simulator = Simulator(scenario_1.production_plan, operator, max_time_lag, printing)
    makespan, lateness, nr_unfinished = my_simulator.simulate(sim_time=25000, write=False)
    logger.info(f'makespan obtained by simulation is {makespan}')
    if nr_unfinished > 0:
        logger.warning('not all products finished')
    # check that the incremental method is correct
    distances = my_simulator.operator.stn.shortest_distances  # is this really using the stn that is updated from the operator?
    # assert np.array_equal(distances, my_simulator.operator.stn.floyd_warshall())

    # find optimal makespan under perfect inforation
    rcpsp = RCPSP_CP(scenario_1.production_plan)
    _, _, cp_output = rcpsp.solve(60, 1, 0)
    makespan_cp_output = max(cp_output["end"].tolist())
    logger.info(f'makespan under perfect information is {makespan_cp_output}\n')

