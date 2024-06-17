import general.logger
from temporal_networks.stnu import STNU

logger = general.logger.get_logger(__name__)


class RCPSP_STNU(STNU):
    def __init__(self, origin_horizon=True):

        super().__init__(origin_horizon)
    def from_rcpsp_instance(cls, durations, needs, capacity, successors):
    # TODO: can we extract this from the STNU class?
        stnu = cls(origin_horizon=False)
        for task, duration in enumerate(durations):
            task_start = stnu.add_node(f'{task}_{STNU.EVENT_START}')
            task_finish = stnu.add_node(f'{task}_{STNU.EVENT_FINISH}')
            if duration == 0:
                stnu.add_tight_constraint(task_start, task_finish, 0)
            else:
                lower_bound = int(max(1, duration - np.sqrt(duration)))
                upper_bound = int(duration + np.sqrt(duration))
                stnu.add_contingent_link(task_start, task_finish, lower_bound, upper_bound)

        for (task, task_successors) in enumerate(successors):
            for suc in task_successors:
                i_idx = stnu.translation_dict_reversed[f'{task}_{STNU.EVENT_FINISH}']
                j_idx = stnu.translation_dict_reversed[f'{suc}_{STNU.EVENT_START}']
                stnu.set_ordinary_edge(j_idx, i_idx, 0)

        return stnu

    @classmethod
    def from_rcpsp_max_instance(cls, durations, temporal_constraints, sink_source=1):
        # TODO: can we extract this from the STNU class?
        stnu = cls(origin_horizon=False)
        for task, duration in enumerate(durations):
            task_start = stnu.add_node(f'{task}_{STNU.EVENT_START}')

            if duration == 0 and sink_source == 1:
                logger.debug(f'This is a sink/source node from RCPSP/max, we add only a start event')
                # stnu.add_tight_constraint(task_start, task_finish, 0)
                # stnu.set_ordinary_edge(task_finish, task_start, 0)
            elif duration == 0 and sink_source == 2:
                logger.debug(f'This is a sink/source node from RCPSP/max, we add both a start event and a finish event')
                task_finish = stnu.add_node(f'{task}_{STNU.EVENT_FINISH}')
                stnu.add_tight_constraint(task_start, task_finish, 0)
            else:
                task_finish = stnu.add_node(f'{task}_{STNU.EVENT_FINISH}')
                lower_bound = int(max(1, duration - np.sqrt(duration)))
                upper_bound = int(duration + np.sqrt(duration))
                stnu.add_contingent_link(task_start, task_finish, lower_bound, upper_bound)

        for (pred, lag, suc) in temporal_constraints:
            i_idx = stnu.translation_dict_reversed[f'{pred}_{STNU.EVENT_START}']
            j_idx = stnu.translation_dict_reversed[f'{suc}_{STNU.EVENT_START}']
            # FIXME: check if this is correct
            stnu.set_ordinary_edge(j_idx, i_idx, -lag)

        return stnu

from temporal_networks.stnu import STNU
import numpy as np
import general.logger
logger = general.logger.get_logger(__name__)
def remove_all_duplicates(tuples_list):
    unique_tuples = []
    seen = set()

    for current_tuple in tuples_list:
        if current_tuple not in seen:
            unique_tuples.append(current_tuple)
            seen.add(current_tuple)

    return unique_tuples

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
    unique_tuples = remove_all_duplicates(resource_chains)
    return unique_tuples, resource_assignment


def add_resource_chains(stnu, resource_chains):
    for pred_task, succ_task in resource_chains:
        # the finish of the predecessor should precede the start of the successor
        pred_idx_finish = stnu.translation_dict_reversed[
            f"{pred_task}_{STNU.EVENT_FINISH}"]  # Get translation index from finish of predecessor
        suc_idx_start = stnu.translation_dict_reversed[
            f"{succ_task}_{STNU.EVENT_START}"]  # Get translation index from start of successor

        # add constraint between predecessor and successor
        stnu.set_ordinary_edge(suc_idx_start, pred_idx_finish, 0)

    return stnu
