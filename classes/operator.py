import random
import numpy as np
import copy

from classes.classes import FailureCode, STN


class OperatorSTN:
    def __init__(self, plan, stn, name="stn_operator", printing=True):
        self.current_time = 0
        self.name = name
        self.initial_plan = plan
        self.printing = printing
        self.pushback = []
        self.stn = stn
        self.sent_activities = set()

    def send_next_activity(self, current_time):
        """
        Send new activities to factory
        """
        finish = False

        activities_that_can_start = []

        for index, (product_index, activity_id, event) in self.stn.translation_dict.items():
            if event == STN.EVENT_START:
                es = -self.stn.shortest_distances[index][0]
                if es == current_time:
                    if (product_index, activity_id) not in self.sent_activities:
                        activities_that_can_start.append((product_index, activity_id))

        if len(activities_that_can_start) == 0:
            time_out = 1
            return [], time_out
        else:
            time_out = 0
            print(f'current time {current_time} {[activities_that_can_start[0]]}')
            self.sent_activities.add(activities_that_can_start[0])
            return [activities_that_can_start[0]], time_out

    def set_start_time(self, activity_id, product_index, start_time):
        print(f"setting start time for prod {product_index} act {activity_id}")
        node_idx = self.stn.translation_dict_reversed[(product_index, activity_id, STN.EVENT_START)]
        self.stn.set_edge(STN.ORIGIN_IDX, node_idx, start_time)
        self.stn.set_edge(node_idx, STN.ORIGIN_IDX, -start_time)
        self.stn.floyd_warshall()

    def set_end_time(self, activity_id, product_index, end_time):
        print(f"setting end time for prod {product_index} act {activity_id}")
        node_idx = self.stn.translation_dict_reversed[(product_index, activity_id, STN.EVENT_FINISH)]
        self.stn.set_edge(STN.ORIGIN_IDX, node_idx, end_time)
        self.stn.set_edge(node_idx, STN.ORIGIN_IDX, -end_time)
        self.stn.floyd_warshall()

    def signal_failed_activity(self, product_index, activity_id, current_time, failure_code):
        """
        Process signal about a failed activity
        """
        # TODO: implement failed activity
        if self.printing:
            print(f'At time {current_time}: Failure code received: {failure_code}')


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

    def signal_failed_activity(self, product_index, activity_id, current_time, failure_code):
        """
        Process signal about a failed activity
        """
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
        #if self.printing:
            #print(f'At time {current_time}: the operator is asked for the next decision')

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
                # proc_time = np.ceil(proc_time)

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
