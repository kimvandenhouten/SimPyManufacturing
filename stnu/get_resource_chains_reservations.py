from classes.stn import STN
import numpy as np


def get_resource_chains(production_plan, earliest_start, complete=False):
    production_plan.set_earliest_start_times(earliest_start)

    # earliest_start is a list of dicts of this form:
    # {"task": i, "earliest_start": start, "start": start, "end": end,
    #             'product_index': self.product_index_translation[i],
    #             'activity_id': self.activity_id_translation[i],
    #             'product_id': self.product_id_translation[i]}

    activities = {}
    for p in production_plan.products:
        for a in p.activities:
            activities[(p.id, a.id)] = a

    reserved_until = {}
    for resource_index, resource_capacity in enumerate(production_plan.factory.capacity):
        reserved_until |= {resource_index: [0] * resource_capacity}

    resource_names = production_plan.factory.resource_names
    resource_use = {}

    resource_assignment = []
    for d in sorted(earliest_start, key=lambda d: d['start']):
        p = production_plan.products[d['product_index']]
        assert p.id == d['product_id']
        assert (p.id, d['activity_id']) in activities
        assert d['start'] == d['earliest_start']
        activity = activities[(p.id, d['activity_id'])]
        for resource_index, required in enumerate(activity.needs):
            resource_group = resource_names[resource_index]
            reservations = reserved_until[resource_index]
            assigned = []
            for idx in range(len(reservations)):
                if len(assigned) == required:
                    break
                if reservations[idx] <= d['start']:
                    reservations[idx] = d['end']
                    assigned.append({'product': d['product_index'],
                                     'activity': d['activity_id'],
                                     'resource_group': resource_group,
                                     'id': idx})
                    users = resource_use.setdefault((resource_group, idx), [])
                    users.append({'ProductIndex': d['product_index'], 'Activity': d['activity_id'], 'Start': d['start']})
            if len(assigned) < required:
                print(f'ERROR: only found {len(assigned)} of {required} resources (type {resource_index}) '
                      f'for activity {activity}')
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
                        resource_chains.append((predecessor["ProductIndex"], predecessor["Activity"],
                                                successor["ProductIndex"], successor["Activity"]))
    else:
        for resource_activities in resource_use.values():
            if len(resource_activities) > 1:  # Check if there are multiple activities assigned to the same resource
                # Sort by start time
                resource_activities = sorted(resource_activities, key=lambda x: x["Start"])

                # To do keep track of edges that should be added to STN
                for i in range(1, len(resource_activities)):
                    predecessor = resource_activities[i - 1]
                    successor = resource_activities[i]
                    resource_chains.append((predecessor["ProductIndex"], predecessor["Activity"],
                                            successor["ProductIndex"], successor["Activity"]))
    print(f'resource chains found')
    return resource_chains, resource_assignment


def add_resource_chains(stnu, resource_chains):
    for pred_p, pred_a, succ_p, succ_a in resource_chains:
        # the finish of the predecessor should precede the start of the successor
        pred_idx_finish = stnu.translation_dict_reversed[
            f"{pred_p}_{pred_a}_{STN.EVENT_FINISH}"]  # Get translation index from finish of predecessor
        suc_idx_start = stnu.translation_dict_reversed[
            f"{succ_p}_{succ_a}_{STN.EVENT_START}"]  # Get translation index from start of successor

        # add interval constraint between predecessor and successor
        stnu.set_ordinary_edge(suc_idx_start, pred_idx_finish, 0)

    return stnu
