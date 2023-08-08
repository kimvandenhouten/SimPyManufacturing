import json
import random

import numpy as np

from classes.classes import Factory, Activity, ProductionPlan
from classes.distributions import NormalDistribution

# We set the seed fixed such that we can regenerate the instances more easily
# These instances won't have a max time lag constraint.
random.seed(1)


def create_stochastic_plan(production_plan):
    for i in range(len(production_plan.factory.products)):
        activities = []
        for activity in production_plan.factory.products[i].activities:
            processing_time = activity.processing_time[0]
            default_variance = np.sqrt(processing_time)
            distribution = NormalDistribution(processing_time, default_variance)
            activity_stoch = Activity(activity.id, activity.processing_time, activity.product, activity.product_id,
                                      activity.needs, distribution, activity.sequence_id, activity.constraints)
            activities.append(activity_stoch)
        production_plan.factory.products[i].activities = activities
        production_plan.list_products()
    return production_plan


fp = open('factory_data/development/data.json', 'r')
factory = Factory(**json.load(fp))
nr_products = len(factory.products)
rowids = range(0, nr_products)
months = range(1, 13)
month_deadlines = [744, 1416, 2160, 2880, 3624, 4344, 5088, 5832, 6552, 7296, 8016, 8760]
deadline_assignment = [deadline for deadline in month_deadlines for _ in range(0, 20)]
month_assignment = [month for month in months for _ in range(0, 20)]

general_id = 0
for instance_size in [10, 20, 40, 60, 120, 240]:
    for id in range(1, 11):
        product_list = []
        for i in range(0, instance_size):
            product_type = random.choice(rowids)
            product_list.append(product_type)

        deadlines = month_assignment[:instance_size]
        plan = ProductionPlan(id=general_id, size=instance_size, name=f'{instance_size}_{id}_{factory.name}',
                              product_ids=product_list,
                              deadlines=deadline_assignment[:instance_size],
                              factory=factory)
        plan = create_stochastic_plan(plan)
        json_str = plan.to_json()

        file_name = f'factory_data/development/instances_type_1/instance_{plan.name}.json'
        print(file_name, ' created')

        with open(file_name, 'w+') as file:
            file.write(json_str)
