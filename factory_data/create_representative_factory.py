from classes import Product, Factory, Activity
import pandas as pd
import pickle

# Initialize factory
resource_groups = pd.read_csv("factory_data/resource_groups.csv", delimiter=";")
factory = Factory(NAME="RepresentativeFactory", RESOURCE_NAMES=resource_groups["Resource_group"].tolist(),
                  CAPACITY=resource_groups["Capacity"].tolist())


# TO DO: add a product to the factory, using the recipes table
recipes = pd.read_csv("factory_data/recipes.csv")
unique_products = recipes.drop_duplicates(subset=["Enzyme name", "Fermenter"])

for index, row in unique_products.iterrows():
    product_id = 0
    enzyme_name = row["Enzyme name"]
    fermenter = row["Fermenter"]

    # Select recipe for this product
    recipe = recipes[recipes["Enzyme name"] == enzyme_name]
    recipe = recipe[recipe["Fermenter"] == fermenter]
    product = Product(ID=product_id, NAME=f'{enzyme_name}_{fermenter}')

    # Separate into fermentation and downstream processing
    df_fermentation = recipe[recipe["Equipment_type"] == "Fermenter"]
    df_downstream = recipe[recipe["Equipment_type"] != "Fermenter"]

    # Preprocess fermentation activity
    task_id = 0
    machine_types = df_fermentation["Equipment_type"].tolist()
    machines = df_fermentation["Machine"].tolist()
    durations = df_fermentation["Duration claim"].tolist()
    durations = [round(i) for i in durations]
    start_claim = df_fermentation["Claim time"].tolist()
    end_claim = df_fermentation["Release time"].tolist()
    resource_use = [0 for _ in range(0, resource_groups .shape[0])]
    resource_use_index = resource_groups["Resource_group"].tolist().index(machines[0])
    resource_use[resource_use_index] += 1
    start_fermentation = start_claim[0]
    task_dur_ferm = int(durations[0])
    task_id_ferm = task_id
    activity = Activity(ID=task_id, PRODUCT=f'{enzyme_name}_{fermenter}', PRODUCT_ID="0", PROCESSING_TIME=[task_dur_ferm, task_dur_ferm], NEEDS=resource_use)
    product.add_activity(activity)
    task_id += 1

    # Now iterate through the remaining activities (downstream processing)
    machine_types = df_downstream["Equipment_type"].tolist()
    machines = df_downstream["Machine"].tolist()
    durations = df_downstream["Duration claim"].tolist()
    durations = [round(i) for i in durations]
    start_claim = df_downstream["Claim time"].tolist()

    temporal_relations = {}
    for i in range(0, len(machines)):
        resource_use = [0 for _ in range(0, resource_groups.shape[0])]
        resource_use_index = resource_groups["Resource_group"].tolist().index(machine_types[i])
        resource_use[resource_use_index] += 1
        duration = durations[i]
        temp_dif_ferm = round(start_claim[i] - start_fermentation)

        activity = Activity(ID=task_id, PRODUCT=f'{enzyme_name}_{fermenter}', PRODUCT_ID="0",
                            PROCESSING_TIME=[duration, duration], NEEDS=resource_use)
        product.add_activity(activity)
        temporal_relations[(task_id_ferm, task_id)] = temp_dif_ferm
        task_id += 1

    product.set_temporal_relations(TEMPORAL_RELATIONS=temporal_relations)
    factory.add_product(product)
    product_id += 1

file_name = 'factory_data/RepresentativeFactory.pkl'
with open(file_name, 'wb') as file:
    pickle.dump(factory, file)
    print(f'Object successfully saved to "{file_name}"')