import pandas as pd
import json

from classes.classes import Activity, Product, Factory

if __name__ == '__main__':

    # Initialize factory
    factory_name = "factory_1"
    resource_groups = pd.read_csv("./factory_data/resource_groups.csv",
                                  delimiter=";")
    recipes = pd.read_csv("./factory_data/recipes.csv", delimiter=";")

    production = {'FACTORIES': []}
    factory = {
                'NAME': factory_name,
                'RESOURCE_NAMES': list(resource_groups.to_dict()['Resource_group'].values()),
                'CAPACITY': list(resource_groups.to_dict()['Capacity'].values())

                }

    unique_products = recipes.drop_duplicates(subset=["Enzyme name", "Fermenter"])

    factory['PRODUCTS'] = []
    product_id = 0
    for index, row in unique_products.iterrows():
        product = {'ID': product_id}
        enzyme_name = row["Enzyme name"]
        fermenter = row["Fermenter"]

        # Select recipe for this product
        recipe = recipes[recipes["Enzyme name"] == enzyme_name]
        recipe = recipe[recipe["Fermenter"] == fermenter]
        product['NAME'] = f'{enzyme_name}_{fermenter}'

        product['ACTIVITIES'] = []

        # Select recipe for this product
        recipe = recipes[recipes["Enzyme name"] == enzyme_name]
        recipe = recipe[recipe["Fermenter"] == fermenter]

        recipe["Claim time"] = round(recipe["Claim time"] / 1)
        recipe["Release time"] = round(recipe["Release time"] / 1)
        recipe["Duration claim"] = recipe["Release time"] - recipe["Claim time"]

        # Separate into fermentation and downstream processing
        df_fermentation = recipe[recipe["Equipment_type"] == "Fermenter"]
        df_downstream = recipe[recipe["Equipment_type"] != "Fermenter"]

        # Preprocess fermentation activity
        task_id: int = 0
        machine_types = df_fermentation["Equipment_type"].tolist()
        machines = df_fermentation["Machine"].tolist()
        durations = df_fermentation["Duration claim"].tolist()
        durations = [round(i) for i in durations]
        start_claim = df_fermentation["Claim time"].tolist()
        end_claim = df_fermentation["Release time"].tolist()
        resource_use = [0 for _ in range(0, resource_groups.shape[0])]
        resource_use_index = resource_groups["Resource_group"].tolist().index(machines[0])
        resource_use[resource_use_index] += 1
        start_fermentation = start_claim[0]
        task_dur_ferm = int(durations[0])
        task_id_ferm = task_id
        processing_time = [task_dur_ferm, task_dur_ferm]
        activity = {
            "ID": task_id,
            "PRODUCT": product['NAME'],
            "PRODUCT_ID": product_id,
            "PROCESSING_TIME": processing_time,
            "NEEDS": resource_use

        }
        product['ACTIVITIES'].append(activity)

        task_id += 1

        # Downstream processing
        df_downstream = df_downstream.groupby(["Equipment_type", "Machine"]).aggregate(
            {'Claim time': 'min', 'Release time': 'max'}).reset_index()
        df_downstream["Duration claim"] = df_downstream["Release time"] - df_downstream["Claim time"]
        df_downstream = df_downstream.sort_values(by=['Release time'])

        # Now iterate through the remaining activities (downstream processing)
        machine_types = df_downstream["Equipment_type"].tolist()
        machines = df_downstream["Machine"].tolist()
        durations = df_downstream["Duration claim"].tolist()
        durations = [round(i) for i in durations]
        release_time = df_downstream["Release time"].tolist()
        start_claim = df_downstream["Claim time"].tolist()

        temporal_relations = []

        for i in range(0, len(machines)):
            resource_use = [0 for _ in range(0, resource_groups.shape[0])]
            resource_use_index = resource_groups["Resource_group"].tolist().index(machine_types[i])
            resource_use[resource_use_index] += 1
            claim = start_claim[i]
            release = release_time[i]

            duration = round(release - claim)
            temp_rel = claim - start_fermentation
            processing_time = [duration, duration]
            activity = {
                "ID": task_id,
                "PRODUCT": product['NAME'],
                "PRODUCT_ID": product_id,
                "PROCESSING_TIME": processing_time,
                "NEEDS": resource_use

            }
            product['ACTIVITIES'].append(activity)
            relation = {"PREDECESSOR": task_id_ferm, "SUCCESSOR": task_id, "REL": round(temp_rel)}
            temporal_relations.append(relation)
            task_id += 1

        product['TEMPORAL_RELATIONS'] = temporal_relations
        factory['PRODUCTS'].append(product)
        product_id += 1
    production['FACTORIES'].append(factory)

    json.dump(production, open('./factory_data/data.json', 'w+'))
