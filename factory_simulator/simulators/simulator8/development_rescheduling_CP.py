import json
from classes.classes import ProductionPlan
import numpy as np
from rcpsp.solvers.RCPSP_CP import RCPSP_CP
import pandas as pd
"""
This is a development file for a rescheduling module in the simulator, in which we use the simulation
logging up to a certain point (current time) and fix some decision variables that are already decided
"""

# Initial instance (deterministic)
instance_size = 10
instance_id = 1
instance_name = f"{instance_size}_{instance_id}_factory_1"
my_productionplan = ProductionPlan(
    **json.load(open('factory_data/development/instances_type_1_uniform/instance_' + instance_name + '.json')))
my_productionplan.set_sequence(sequence=np.arange(instance_size))

rcpsp = RCPSP_CP(my_productionplan)
solution, callback, cp_output = rcpsp.solve(time_limit=60, l1=1, l2=0, output_file=f"start times {instance_name}.csv")

# Information about "rescheduling point in time"
current_time = 163
logger_info = pd.read_csv(f'simulators/simulator8/logger_info.csv')

print(logger_info.columns)
# TODO, add constraints on start times and end times based on logger info
solution, callback, cp_output = rcpsp.reschedule(logger_info, time_limit=60, l1=1, l2=0, output_file=f"start times updated {instance_name}.csv")
