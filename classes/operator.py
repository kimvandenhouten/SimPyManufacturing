import random
import numpy as np
import copy

from classes.classes import FailureCode, STN
from classes.classes import SimulatorLogger, Action, FailureCode


class OperatorSTN:
    # FIXME Can we make this operator send activity more efficient? How does it scale to larger problem instances

    def __init__(self, plan, stn, resource_use_cp, name="stn_operator", printing=True):
        self.current_time = 0
        self.name = name
        self.plan = plan
        self.printing = printing
        self.pushback = []
        self.stn = stn
        self.sent_activities = []
        self.calculating = False
        self.resource_use_cp = resource_use_cp
        self.resource_use_factory = []
        self.required_resources = {}

        for item in self.resource_use_cp:
            key = (item['product'], item['activity'])
            if key not in self.required_resources:
                self.required_resources[key] = []
            self.required_resources[key].append((item['resource_group'], item['id']))

    def send_next_activity(self, current_time):
        """
        Send new activities to factory
        """
        if self.calculating:
            send_activity = False
            activity_id, product_index = None, None
            delay = 0
        else:
            finish = False
            activities_that_can_start = []
            for index, (product_index, activity_id, event) in self.stn.translation_dict.items():
                if event == STN.EVENT_START:
                    es = -self.stn.shortest_distances[index][STN.ORIGIN_IDX]
                    if es == current_time:

                        if (product_index, activity_id) not in self.sent_activities:
                            activities_that_can_start.append((product_index, activity_id))

            if len(activities_that_can_start) == 0:
                delay = 1
                send_activity = False
                activity_id, product_index, required_resources = None, None, None

            else:
                if self.printing:
                    print(f'At time {current_time}: activities that can start {activities_that_can_start}')
                delay = 0
                send_activity = True
                (product_index, activity_id) = activities_that_can_start[0]
                self.sent_activities.append((product_index, activity_id))
                required_resources = self.required_resources[(product_index, activity_id)]

        return send_activity, delay, activity_id, product_index, finish, required_resources

    def set_start_time(self, activity_id, product_index, start_time, resources):
        node_idx = self.stn.translation_dict_reversed[(product_index, activity_id, STN.EVENT_START)]
        if self.printing:
            print(f"setting start time for prod {product_index} act {activity_id} with node index {node_idx}")
        for resource in resources:
            self.resource_use_factory.append({'product': product_index,
                                              'activity': activity_id,
                                              "resource_group": resource.resource_group,
                                              "id": resource.id})
        # Check whether this matches with the original CP resource assignment
            if {'product': product_index, 'activity': activity_id, "resource_group": resource.resource_group, "id": resource.id} not in self.resource_use_cp:
                print(f'Resource assignment does not match')
                # TODO: should we have a CP rescheduling here

        self.stn.add_tight_constraint(STN.ORIGIN_IDX, node_idx, start_time, propagate=True)

    def set_end_time(self, activity_id, product_index, end_time):
        node_idx = self.stn.translation_dict_reversed[(product_index, activity_id, STN.EVENT_FINISH)]
        if self.printing:
            print(f"setting end time for prod {product_index} act {activity_id} with node index {node_idx}")
        self.stn.add_tight_constraint(STN.ORIGIN_IDX, node_idx, end_time, propagate=True)

    def signal_failed_activity(self, product_index, activity_id, current_time, logger):
        """
        Process signal about a failed activity
        """
        max_lag_problem = False

        # TODO: can/should this be done with information from STN instead of operator/instance information?
        predecessors = self.plan.products[product_index].predecessors[activity_id]
        for pred_activity_id in predecessors:
            temp_rel = self.plan.products[product_index].temporal_relations[(pred_activity_id, activity_id)]
            start_pred_log = logger.fetch_latest_entry(product_index,
                                                       pred_activity_id, Action.START)
            if temp_rel.max_lag and current_time + 1 - start_pred_log.timestamp > temp_rel.max_lag:
                max_lag_problem = True

        if max_lag_problem:
            print(f'Operator Warning for product {product_index} activity {activity_id}: postponing with 1 time unit will not work')

            for activity in self.plan.products[product_index].activities:
                if (product_index, activity.id) not in self.sent_activities:
                    print(f'remove start and finish node and including edges from {(product_index, activity_id)}')
                    start_node = self.stn.translation_dict_reversed[(product_index, activity_id, self.stn.EVENT_START)]
                    end_node = self.stn.translation_dict_reversed[(product_index, activity_id, self.stn.EVENT_FINISH)]
                    self.stn.remove_node(start_node)
                    self.stn.remove_node(end_node)
            print(f'Recalculate floyd warshall')
            self.stn.floyd_warshall()

        else:
            # Update the STN by adding distance from origin to start of this activity
            node_from = self.stn.ORIGIN_IDX
            node_to = self.stn.translation_dict_reversed[
                (product_index, activity_id, self.stn.EVENT_START)]
            min_distance = current_time + 1
            self.stn.add_interval_constraint(node_from, node_to, min_distance, np.inf, propagate=True)
            self.sent_activities.remove((product_index, activity_id))
            self.calculating = False


class Operator:
    def __init__(self, plan, name="simple_operator", policy_type=1, printing=True):
        self.current_time = 0
        self.name = name
        self.initial_plan = plan
        self.plan = copy.deepcopy(plan)
        self.printing = printing
        self.pushback = []   # list of lists of activities to be pushed back
        self.policy_type = policy_type

    def pushback_product(self, product_index):
        pushback_product = []
        for act in self.plan.earliest_start:
            if act['product_index'] == product_index:
                self.plan.earliest_start.remove(act)
                pushback_product.append(act)
        self.pushback.append(pushback_product)

    def signal_failed_activity(self, product_index, activity_id, current_time, logger):
        """
        Process signal about a failed activity
        """
        failure_code = logger.failure_code
        if self.printing:
            print(f'At time {current_time}: Failure code received: {failure_code}')

        if self.printing:
            print(
                f'At time {current_time}: the operator receives the signal that product index {product_index} with id '
                f'{self.plan.products[product_index].id} ACTIVITY '
                f'{activity_id} got cancelled, so we apply policy {self.policy_type}')
            print(f'At time {current_time}: the current plan is {self.plan.earliest_start}')

        if self.policy_type == 1 or (self.policy_type == 2 and failure_code == FailureCode.MAX_LAG):
            # Remove activities from plan that are from the same product_id as the cancelled activity
            if self.printing:
                print(f'At time {current_time}: the repair policy removes all activities from product {product_index} '
                      f'from the plan')
            for i, act in enumerate(self.plan.earliest_start):
                if act['product_index'] == product_index:
                    del self.plan.earliest_start[i]

        elif (self.policy_type == 2 or self.policy_type == 3) and (
                failure_code != FailureCode.MAX_LAG):  # Postpone for all except for max time,
            self.plan.earliest_start.append(
                {'product_index': product_index, "activity_id": activity_id, "earliest_start": current_time + 1,
                 "product_id": self.plan.products[product_index].id})
        elif self.policy_type == 3 and failure_code == FailureCode.MAX_LAG:
            self.pushback_product(product_index)

        if self.printing:
            print(f'At time {current_time}: the updated plan is {self.plan.earliest_start}')

    def send_next_activity(self, current_time):
        """
        Send new activities to factory
        """
        finish = False

        # Check if there are still activities in the plan
        if len(self.plan.earliest_start) == 0:
            finish, send_activity = True, False
            delay = 0
            activity_id, product_index, proc_time, needs = None, None, None, None

        else:
            # Obtain the start time of the next activity according to the plan
            earliest_start_times = []
            for i, dict in enumerate(self.plan.earliest_start):
                earliest_start_times.append(dict["earliest_start"])
            earliest_start_times_argsort = np.argsort(earliest_start_times)
            earliest_start_times_argsort = self._temporal_sort(earliest_start_times_argsort)

            # Compute the start time of the next activity
            i = earliest_start_times_argsort[0]
            earliest_start = self.plan.earliest_start[i]["earliest_start"]

            # Check if this activity can start now
            if earliest_start == current_time:
                send_activity = True
                product_index = self.plan.earliest_start[i]["product_index"]
                activity_id = self.plan.earliest_start[i]["activity_id"]

                # Obtain information about resource needs and processing time
                needs = self.plan.products[product_index].activities[activity_id].needs
                proc_time = max(self.plan.products[product_index].activities[activity_id].processing_time[0], 1)

                if self.printing:
                    print(
                        f'At time {current_time}: the next event is product index {product_index} with id '
                        f'{self.plan.products[product_index].id} activity {activity_id}'
                        f' and should start now')

                # Remove this activity from plan
                del self.plan.earliest_start[i]

                if len(self.plan.earliest_start) == 0:
                    delay = 0
                else:
                    j = earliest_start_times_argsort[1]
                    if earliest_start_times[j] == current_time:
                        delay = 0
                    else:
                        delay = 1
            else:
                send_activity = False
                delay = 1
                activity_id, product_index, proc_time, needs = None, None, None, None

        return send_activity, delay, activity_id, product_index, proc_time, needs, finish

    def _temporal_sort(self, earliest_start_times_argsort):
        i = earliest_start_times_argsort[0]
        count = 1
        while len(earliest_start_times_argsort) > count and self.plan.earliest_start[i]["earliest_start"] == \
                self.plan.earliest_start[earliest_start_times_argsort[count]][
                    "earliest_start"]:
            j = earliest_start_times_argsort[count]
            if self._is_parallel_successor(i, j):
                earliest_start_times_argsort[1] = i
                earliest_start_times_argsort[0] = j
                break
            count += 1
        return earliest_start_times_argsort

    def _is_parallel_successor(self, i, j):
        is_parallel_successor = self.plan.earliest_start[i]['product_id'] == self.plan.earliest_start[j][
            'product_id']
        is_parallel_successor = is_parallel_successor and (self.plan.earliest_start[j]['activity_id'],
                                                           self.plan.earliest_start[i]['activity_id']) in \
                                self.plan.products[
                                    self.plan.earliest_start[i]['product_index']].temporal_relations.keys()
        is_parallel_successor = is_parallel_successor and \
                                self.plan.products[self.plan.earliest_start[i]['product_index']].temporal_relations[
                                    (self.plan.earliest_start[j]['activity_id'],
                                     self.plan.earliest_start[i]['activity_id'])].min_lag == 0
        return is_parallel_successor
