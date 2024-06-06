import json
from factory_simulator.classes import ProductionPlan
from temporal_networks.stn import STN
import numpy as np
import pandas as pd

instance_size = 10
instance_id = 1
instance_name = f"{instance_size}_{instance_id}_factory_1"
my_productionplan = ProductionPlan(
    **json.load(open('factory_data/development/instances_type_2/instance_' + instance_name + '.json')))

stn = STN.from_production_plan(my_productionplan)
# Load cp output and make production plan and convert to edges that must be added to STN
from dsm_experiments.temporal_networks.stn_factory import get_resource_chains
cp_output = pd.read_csv(f"results/cp_model/development/instances_type_2/start times {instance_name}.csv")
earliest_start = cp_output.to_dict('records')  # Convert to earliest start times
# Run deterministic simulation with earliest start times and obtain resource predecence constraints
resource_chains = get_resource_chains(production_plan=my_productionplan, earliest_start=earliest_start)

# Now add the edges with the correct edge weights to the STN
for pred_p, pred_a, succ_p, succ_a in resource_chains:
    # The finish of the predecessor should precede the start of the successor
    pred_idx = stn.translation_dict_reversed[(pred_p, pred_a, STN.EVENT_FINISH)]  # Get translation index from finish of predecessor
    suc_idx = stn.translation_dict_reversed[(succ_p, succ_a, STN.EVENT_START)]  # Get translation index from start of successor
    stn.add_interval_constraint(pred_idx, suc_idx, 0, np.inf)

print(f'Apply Floyd-Warshall to STN WITH resource constraints')
# Compute shortest distance graph path for this graph
shortest_distances = stn.floyd_warshall()

t = 0


def collect_activities_that_can_start(t):
    activities_that_can_start = []
    for i in stn.translation_dict:
        product_id, activity_id, event = stn.translation_dict[i]
        if event == "start":
            es = -shortest_distances[i][0]
            if es == t:
                print(f'Product {product_id}, {activity_id} can start now')
                activities_that_can_start.append((product_id, activity_id))
    return activities_that_can_start


for t in range(100):
    print(t)
    activities_that_can_start = collect_activities_that_can_start(t=t)
    # TODO in integration with simulator
    # Send all activities that can start to simulator
    # Move to t=1
    # Update STN if signals from finished product came back from simulator

print(f'Makespan: {-shortest_distances[stn.HORIZON_IDX, stn.ORIGIN_IDX]} \n')


# TODO: try to change a processing time once realisation becomes certain

# Input
product_index, activity_id, realized_processing_time = 0, 1, 50
# find node that corresponds to start
start_node = stn.translation_dict_reversed[(product_index, activity_id, "start")]
# find node that corresponds to finish
finish_node = stn.translation_dict_reversed[(product_index, activity_id, "finish")]

# update edge met real processing time
stn.set_edge(start_node, finish_node, realized_processing_time)
stn.set_edge(finish_node, start_node, -realized_processing_time)

# recompute shortest distances
shortest_distances = stn.floyd_warshall()
print(f'After updating processing time from product index {product_index}, activity {activity_id} '
      f'the updated makespan is : {-shortest_distances[stn.HORIZON_IDX, stn.ORIGIN_IDX]} \n')
