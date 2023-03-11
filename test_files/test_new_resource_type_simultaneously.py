import simpy
from collections import namedtuple
import pandas as pd
import copy
import random


print(f' \n \n Try out new Simpy Simulator')

### Now try to make something similar for the DSM data
resource_groups_df = pd.read_csv('../factory_data/resource_groups.csv', delimiter=";")
resources = resource_groups_df["Resource_group"].tolist()
capacity = resource_groups_df["Capacity"].tolist()

env = simpy.Environment()
factory = simpy.FilterStore(env, capacity=sum(capacity))
Resource = namedtuple('Machine', 'resource_group, id')
items = []
for i in range(0, len (resources)):
    for j in range(0, capacity[i]):
        r = Resource(resources[i], j)
        items.append(copy.copy(r))
print(items)
factory.items = items


def resource_request(product, env, factory, resource_group):
    resource = yield factory.get(lambda resource: resource.resource_group == resource_group)
    print(product, 'requested', resource.resource_group,' id ', resource.id, 'at', env.now)
    return resource


def process_activity(product, env, factory, resource, duration):
    print(f'user {product} started processing at {env.now} on {resource.resource_group} id {resource.id}')
    yield env.timeout(duration)
    yield factory.put(resource)
    print(product, 'released', resource.resource_group, ' id ', resource.id, 'at',
          env.now)


def generate_products():
    # Iterate through sequence
    for product in range(0, 5):
        print(f' new product {product}')
        resource_requests = []
        for activity in range(0, 4):
            # Retrieving of resources
            resource_requests.append(env.process(resource_request(product=product, env=env, factory=factory, resource_group=resources[activity])))
        yield env.all_of(resource_requests)

        for activity in range(0, 4):
            env.process(process_activity(product=product, env=env, factory=factory, resource=resource_requests[activity].value, duration=random.randint(0, 5)))


        # Processing of activities on resources
        #yield env.timeout(10)
        #for i in range(5):
            #yield factory.put(resource_requests[i].value)
            #print(user, 'released', resource_requests[i].value.resource_group, ' id ', resource_requests[i].value.id, 'at', env.now)



env.process(generate_products())
env.run()