"""
For running this script set working directory to ~/SimPyManufacturing
"""
import os

import pandas as pd
import random
from classes.classes import ProductionPlan, Factory, Scenario, Activity
import pickle
import json

from classes.distributions import NormalDistribution

instance_name = 'instance_10_1_factory_1.pkl'
production_plan = pd.read_pickle('factory_data/instances/' + instance_name)
default_variance = 2
for i in range(len(production_plan.FACTORY.PRODUCTS)):
    activities = []
    for activity in production_plan.FACTORY.PRODUCTS[i].ACTIVITIES:
        processing_time = activity.PROCESSING_TIME[0]
        distribution = NormalDistribution(processing_time, default_variance)
        activity_stoch = Activity(activity.ID, activity.PROCESSING_TIME, activity.PRODUCT, activity.PRODUCT_ID,
                                  activity.NEEDS, distribution, activity.SEQUENCE_ID)
        activities.append(activity_stoch)
    production_plan.FACTORY.PRODUCTS[i].ACTIVITIES = activities
    production_plan.list_products()

file_name = f'factory_data/stochastic/instances/' + instance_name
with open(file_name, 'wb') as file:
    pickle.dump(production_plan, file)
    print(f'Object successfully saved to "{file_name}"')
