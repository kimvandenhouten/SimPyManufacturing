import random
import numpy as np


class Operator:
    def __init__(self, plan, name="simple_operator"):
        self.current_time = 0
        self.name = name
        self.initial_plan = plan
        self.plan = plan

    def signal_failed_activity(self, product_ID, activity_ID, current_time):
        """
        Process signal about a failed activity
        """
        # Check if there was a clash for an activity
        print(f'\n')
        print(f'At time {current_time} the operators receives the signal that product {product_ID} activity {activity_ID} failed')
        # TODO remove all other activities from the schedule
        print(f'Now we should remove all remaining activities from product {product_ID} from the plan')
        print(f'STEP 1: Print the current plan {self.plan.earliest_start}')
        print(f'STEP 2: Now the operator should remove all future activities for this product from the list')
        print(f'\n')

    def send_next_activity(self, current_time):
        """
        Send new activities to factory
        """
        print(f'The operator is asked for the next decision at time {current_time}')
        # Obtain the start time of the next activity according to the plan
        # Return all information needed for the factory to start new activity
        # Sort activities by earliest start time
        earliest_start_times = []
        for i, dict in enumerate(self.plan.earliest_start):
            earliest_start_times.append(dict["Earliest_start"])
        earliest_start_times_argsort = np.argsort(earliest_start_times)

        # Iterate through the different activities
        i = earliest_start_times_argsort[0]
        product_ID = self.plan.earliest_start[i]["Product_ID"]
        activity_ID = self.plan.earliest_start[i]["Activity_ID"]

        # Obtain information about resource needs and processing time
        needs = self.plan.PRODUCTS[product_ID].ACTIVITIES[activity_ID].NEEDS
        proc_time = self.plan.PRODUCTS[product_ID].ACTIVITIES[activity_ID].PROCESSING_TIME
        proc_time = random.randint(*proc_time)

        # Compute delay
        delay = self.plan.earliest_start[i]["Earliest_start"] - current_time

        # Remove this activity from plan
        del self.plan.earliest_start[0]

        # Check if there are still activities that needs to be done
        if len(self.plan.earliest_start) == 0:
            finish = True
        else:
            finish = False
        return delay, activity_ID, product_ID, proc_time, needs, finish
