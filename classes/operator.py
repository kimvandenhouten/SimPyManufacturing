import random
import numpy as np
import copy


class Operator:
    def __init__(self, plan, name="simple_operator", policy_type=1, printing=True):
        self.current_time = 0
        self.name = name
        self.initial_plan = plan
        self.plan = copy.deepcopy(plan)
        self.printing = printing
        self.policy_type = policy_type

    def signal_failed_activity(self, product_id, activity_id, current_time):
        """
        Process signal about a failed activity
        """
        if self.printing:
            print(f'At time {current_time}: the operator receives the signal that product {product_id} ACTIVITY '
                  f'{activity_id} got cancelled, so we apply policy {self.policy_type}')
            print(f'At time {current_time}: the current plan is {self.plan.earliest_start}')

        if self.policy_type == 1:
            # Remove activities from plan that are from the same product_id as the cancelled activity
            if self.printing:
                print(f'At time {current_time}: the repair policy removes all activities from product {product_id} '
                      f'from the plan')
            for i, act in enumerate(self.plan.earliest_start):
                if act['product_id'] == product_id:
                    del self.plan.earliest_start[i]

        elif self.policy_type == 2:
            self.plan.earliest_start.append({'product_id': product_id, "activity_id": activity_id, "earliest_start": current_time + 1})

        if self.printing:
            print(f'At time {current_time}: the updated plan is {self.plan.earliest_start}')

    def send_next_activity(self, current_time):
        """
        Send new activities to factory
        """
        finish = False
        if self.printing:
            print(f'At time {current_time}: the operator is asked for the next decision')

        # Check if there are still activities in the plan
        if len(self.plan.earliest_start) == 0:
            finish, send_activity = True, False
            delay = 0
            activity_id, product_id, proc_time, needs = None, None, None, None

        else:
            # Obtain the start time of the next activity according to the plan
            earliest_start_times = []
            for i, dict in enumerate(self.plan.earliest_start):
                earliest_start_times.append(dict["earliest_start"])
            earliest_start_times_argsort = np.argsort(earliest_start_times)

            # Compute the start time of the next activity
            i = earliest_start_times_argsort[0]
            earliest_start = self.plan.earliest_start[i]["earliest_start"]

            # Check if this activity can start now
            if earliest_start == current_time:
                send_activity = True
                product_id = self.plan.earliest_start[i]["product_id"]
                activity_id = self.plan.earliest_start[i]["activity_id"]

                # Obtain information about resource needs and processing time
                needs = self.plan.products[product_ID].activities[activity_ID].NEEDS
                proc_time = max(self.plan.products[product_ID].activities[activity_ID].processing_time[0], 1)
                #proc_time = np.ceil(proc_time)

                if self.printing:
                    print(f'At time {current_time}: the next event is product {product_id} ACTIVITY {activity_id}'
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
                activity_id, product_id, proc_time, needs = None, None, None, None

        return send_activity, delay, activity_id, product_id, proc_time, needs, finish
