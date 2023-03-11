import simpy
from collections import namedtuple
import pandas as pd
import copy
import random

Machine = namedtuple('Machine', 'id, size, duration')
m1 = Machine(1, 2, 2)  # Small and slow
m2 = Machine(2, 2, 2)  # Big and fast

env = simpy.Environment()
machine_shop = simpy.FilterStore(env, capacity=2)
machine_shop.items= [m1, m2]  # Pre-populate the machine shop


def user(name, env, ms, size):
    machine = yield ms.get(lambda machine: machine.size == size)
    print(name, 'got', machine, 'at', env.now)
    yield env.timeout(machine.duration)
    yield ms.put(machine)
    print(name, 'released', machine, 'at', env.now)


users = [env.process(user(i, env, machine_shop, 2))
         for i in range(5)]
env.run()

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


def user(name, env, factory, resource_group, duration):
    print(f'user started')
    print(resource_group)
    resource1 = yield factory.get(lambda resource: resource.resource_group == 'Harvesting tanks A')
    print(name, 'got', resource1.resource_group,' id ', resource1.id, 'at', env.now)
    yield env.timeout(duration)
    yield factory.put(resource1)
    print(name, 'released', resource1.resource_group, ' id ', resource1.id, 'at', env.now)


users = [env.process(user(name=i, env=env, factory=factory, resource_group=random.choice(resources), duration=random.randint(1, 10)))
         for i in range(10)]

env.run()