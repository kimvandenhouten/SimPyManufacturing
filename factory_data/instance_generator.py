"""
For running this script set working directory to ~/SimPyManufacturing
"""

import pandas as pd
import random
from classes.classes import ProductionPlan, Factory
import pickle
import json

#Load factory from new json file
fp = open('./factory_data/data.json', 'r')
factory = Factory(**json.load(fp))
nr_products = len(factory.PRODUCTS)
rowIDS = range(0, nr_products)
months = range(1, 13)
month_deadlines = [744, 1416, 2160, 2880, 3624, 4344, 5088, 5832, 6552, 7296, 8016, 8760]
deadline_assignment = [deadline for deadline in month_deadlines for _ in range(0, 20)]
month_assignment = [month for month in months for _ in range(0, 20)]

general_id = 0
for instance_size in [10, 20, 40, 60, 120, 240]:
    for id in range(6, 11):
        product_list = []
        for i in range(0, instance_size):
            product_type = random.choice(rowIDS)
            product_list.append(product_type)

        deadlines = month_assignment[:instance_size]
        plan = ProductionPlan(ID=general_id, SIZE=instance_size, NAME=f'{instance_size}_{id}_{factory.NAME}', PRODUCT_IDS=product_list,
                              DEADLINES=deadline_assignment[:instance_size],
                              FACTORY=factory)
        plan.list_products()
        file_name = f'factory_data/instances/instance_{plan.NAME}.pkl'
        with open(file_name, 'wb') as file:
            pickle.dump(plan, file)
            print(f'Object successfully saved to "{file_name}"')
        general_id += 1