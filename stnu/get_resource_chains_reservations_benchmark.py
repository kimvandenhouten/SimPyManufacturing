from classes.stn import STN
import numpy as np
import classes.general
logger = classes.general.get_logger()


def get_resource_chains(schedule, capacity, resources, complete=False):
    # schedule is a list of dicts of this form:
    # {"task": i, " "start": start, "end": end}
    reserved_until = {}
    for resource_index, resource_capacity in enumerate(capacity):
        reserved_until |= {resource_index: [0] * resource_capacity}

    resource_use = {}

    resource_assignment = []
    for d in sorted(schedule, key=lambda d: d['start']):
        for resource_index, required in enumerate(resources[d['task']]):
            reservations = reserved_until[resource_index]
            assigned = []
            for idx in range(len(reservations)):
                if len(assigned) == required:
                    break
                if reservations[idx] <= d['start']:
                    reservations[idx] = d['end']
                    assigned.append({'task': d['task'],
                                     'resource_group': resource_index,
                                     'id': idx})
                    users = resource_use.setdefault((resource_index, idx), [])
                    users.append(
                        {'Task': d['task'], 'Start': d['start']})

            if len(assigned) < required:
                ValueError(f'ERROR: only found {len(assigned)} of {required} resources (type {resource_index}) '
                      f'for task {d["task"]}')
            else:
                assert len(assigned) == required
                resource_assignment += assigned

    resource_chains = []
    if complete:
        for resource_activities in resource_use.values():
            if len(resource_activities) > 1:  # Check if there are multiple activities assigned to the same resource
                # Sort by start time
                resource_activities = sorted(resource_activities, key=lambda x: x["Start"])
                # To do keep track of edges that should be added to STN
                for i in range(1, len(resource_activities)):
                    for j in range(0, i):
                        predecessor = resource_activities[j]
                        successor = resource_activities[i]
                        resource_chains.append((predecessor["Task"],
                                                successor["Task"]))
    else:
        for resource_activities in resource_use.values():
            if len(resource_activities) > 1:  # Check if there are multiple activities assigned to the same resource
                # Sort by start time
                resource_activities = sorted(resource_activities, key=lambda x: x["Start"])

                # To do keep track of edges that should be added to STN
                for i in range(1, len(resource_activities)):
                    predecessor = resource_activities[i - 1]
                    successor = resource_activities[i]
                    resource_chains.append((predecessor["Task"],
                                            successor["Task"]))
    return resource_chains, resource_assignment


def add_resource_chains(stnu, resource_chains):
    for pred_task, succ_task in resource_chains:
        # the finish of the predecessor should precede the start of the successor
        pred_idx_finish = stnu.translation_dict_reversed[
            f"{pred_task}_{STN.EVENT_FINISH}"]  # Get translation index from finish of predecessor
        suc_idx_start = stnu.translation_dict_reversed[
            f"{succ_task}_{STN.EVENT_START}"]  # Get translation index from start of successor

        # add interval constraint between predecessor and successor
        stnu.set_ordinary_edge(suc_idx_start, pred_idx_finish, 0)

    return stnu
