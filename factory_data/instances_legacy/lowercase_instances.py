import os
import pickle

from classes.classes import Activity, Product, Factory, ProductionPlan


def convert_to_new_production_plan(data):
    products_new = []
    for product in data.FACTORY.PRODUCTS:
        activities_new = []
        for activity in product.ACTIVITIES:
            activity_new = Activity(activity.ID, activity.PROCESSING_TIME, activity.PRODUCT, activity.PRODUCT_ID,
                                    activity.NEEDS, None, activity.SEQUENCE_ID)
            activities_new.append(activity_new)
        products_new.append(
            Product(product.ID, product.NAME, activities_new, product.TEMPORAL_RELATIONS, product.DEADLINE,
                    product.PREDECESSORS, product.SUCCESSORS))
    factory_new = Factory(data.FACTORY.NAME, data.FACTORY.RESOURCE_NAMES, data.FACTORY.CAPACITY, products_new)
    production_plan = ProductionPlan(data.ID, data.SIZE, data.NAME, factory_new, data.PRODUCT_IDS, data.DEADLINES, [],
                                     data.SEQUENCE)
    production_plan.list_products()
    return production_plan


if __name__ == '__main__':
    base_path = 'factory_data/instances_legacy/instances/'
    target_path = 'factory_data/instances_legacy/instances_new/'
    files = os.listdir(base_path)

    for file in files:
        try:
            data = pickle.load(open(base_path + file, 'rb'))
            new_data = convert_to_new_production_plan(data)
            with open(target_path + file, 'wb') as f:
                pickle.dump(new_data, f)
                print(f'Object successfully saved to "{files}"')
        except Exception as e:
            print("could not convert file:", file)
            print(e)
