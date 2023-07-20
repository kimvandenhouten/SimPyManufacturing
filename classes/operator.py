import random
import numpy as np


class Operator:
    def __init__(self, plan, name="simple_operator"):
        self.current_time = 0
        self.name = name
        self.initial_plan = plan
        self.plan = plan
        self.printing = True

    def signal_failed_activity(self, product_ID, activity_ID, current_time):
        """
        Process signal about a failed activity
        """
        if self.printing:
            print(f'At time {current_time}: the operator receives the signal that PRODUCT {product_ID} ACTIVITY '
                  f'{activity_ID} got cancelled')

        # Remove activities from plan that are from the same product_ID as the cancelled activity
        for i, act in enumerate(self.plan.earliest_start):
            if self.printing:
                print(f'At time {current_time}: the current plan is {self.plan.earliest_start}')
                print(f'At time {current_time}: the repair policy removes all activities from product {product_ID} '
                      f'from the plan')
            if act['Product_ID'] == product_ID:
                del self.plan.earliest_start[i]

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
            activity_ID, product_ID, proc_time, needs = None, None, None, None

        else:
            # Obtain the start time of the next activity according to the plan
            earliest_start_times = []
            for i, dict in enumerate(self.plan.earliest_start):
                earliest_start_times.append(dict["Earliest_start"])
            earliest_start_times_argsort = np.argsort(earliest_start_times)

            # Compute the start time of the next activity
            i = earliest_start_times_argsort[0]
            earliest_start = self.plan.earliest_start[i]["Earliest_start"]

            # Check if this activity can start now
            if earliest_start == current_time:
                send_activity = True
                product_ID = self.plan.earliest_start[i]["Product_ID"]
                activity_ID = self.plan.earliest_start[i]["Activity_ID"]

                # Obtain information about resource needs and processing time
                needs = self.plan.PRODUCTS[product_ID].ACTIVITIES[activity_ID].NEEDS
                proc_time = self.plan.PRODUCTS[product_ID].ACTIVITIES[activity_ID].PROCESSING_TIME
                proc_time = random.randint(*proc_time)

                if self.printing:
                    print(f'At time {current_time}: the next event is PRODUCT {product_ID} ACTIVITY {activity_ID}'
                          f' and should start now')

                # Remove this activity from plan
                del self.plan.earliest_start[0]

                # Check if there are still activities that needs to be done
                if len(self.plan.earliest_start) == 0:
                    finish = True
                    delay = 0
                else:
                    finish = False
                    if earliest_start_times[1] == current_time:
                        delay = 0
                    else:
                        delay = 1
            else:
                send_activity = False
                delay = 1
                activity_ID, product_ID, proc_time, needs = None, None, None, None

        return send_activity, delay, activity_ID, product_ID, proc_time, needs, finish
