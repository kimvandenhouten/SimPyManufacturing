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


def produce_json_data(source_path, output_path):
    production_plan = pd.read_pickle(source_path)
    default_variance = 2
    for i in range(len(production_plan.factory.products)):
        activities = []
        for activity in production_plan.factory.products[i].activities:
            processing_time = activity.processing_time[0]
            distribution = NormalDistribution(processing_time, default_variance)
            activity_stoch = Activity(activity.id, activity.processing_time, activity.product, activity.product_id,
                                      activity.needs, distribution, activity.sequence_id)
            activities.append(activity_stoch)
        production_plan.factory.products[i].activities = activities
        production_plan.list_products()

    json_str = production_plan.to_json()
    instance_name = source_path.split('/')[-1].split('.')[0]

    file_name = output_path + instance_name + '.json'
    with open(file_name, 'w+') as file:
        file.write(json_str)


if __name__ == '__main__':
    base_path = 'factory_data/instances_new/'
    output_path = f'factory_data/stochastic/json_instances/'

    source_instances = os.listdir(base_path)
    error_count = 0
    for instance in source_instances:
        try:
            produce_json_data(base_path + instance, output_path)
        except Exception as error:
            print("Could not convert instance:" + instance, error)
            error_count += 1
    print("Percent error of conversion", error_count * 100 / len(source_instances))
