import json
from classes.classes import ProductionPlan, STN
import numpy as np

instance_size = 10
instance_id = 1
instance_name = f"{instance_size}_{instance_id}_factory_1"
my_productionplan = ProductionPlan(
    **json.load(open('factory_data/development/instances_type_2/instance_' + instance_name + '.json')))

stn = STN.from_production_plan(my_productionplan)
matrix = stn.floyd_warshall()

print(f'nodes {stn.nodes}')
print(f'edges {stn.edges}')
print(f'translation dict {stn.translation_dict}')
print(f'reversed translation dict {stn.translation_dict_reversed}')