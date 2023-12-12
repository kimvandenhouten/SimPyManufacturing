import pandas as pd
from docplex.cp.model import *
import docplex.cp.solver as solver


class RCPSP_CP:
    def __init__(self, instance):
        # convert to RCPSP instance
        self.capacity = instance.factory.capacity
        self.durations = []
        self.deadlines = []
        self.resources = []
        self.successors = [[] for p in instance.products for a in p.activities]
        self.min_lag = {}
        self.max_lag = {}

        resource_translation = instance.factory.resource_names
        self.product_id_translation = []
        self.product_index_translation = []
        self.activity_id_translation = []

        self.incompatible_tasks = []

        activity_counter = 0
        product_counter = 0

        # loop over all products
        for p in instance.products:
            for (i, j) in p.temporal_relations:
                self.min_lag[(i + activity_counter, j + activity_counter)] = p.temporal_relations[(i, j)].min_lag
                self.max_lag[(i + activity_counter, j + activity_counter)] = p.temporal_relations[(i, j)].max_lag
                self.successors[i + activity_counter].append(j + activity_counter)

            nr_activities = len(p.activities)
            for act in range(0, nr_activities):
                self.product_index_translation.append(p.product_index)
                self.product_id_translation.append(p.id)
                self.activity_id_translation.append(act)

            for counter, a in enumerate(p.activities):
                if counter == nr_activities - 1:
                    self.deadlines.append(p.deadline)
                else:
                    self.deadlines.append(1000000000)

                self.durations.append(a.processing_time[0])
                self.resources.append(a.needs)

            activity_counter += nr_activities
            product_counter += 1

        self.translation_table = pd.DataFrame(
            {'product_id': self.product_id_translation,
             'activity_id': self.activity_id_translation,
             'product_index': self.product_index_translation
             })

        for constraint in instance.factory.compatibility_constraints:
            p1 = constraint[0]['product_id']
            a1 = constraint[0]['activity_id']
            p2 = constraint[1]['product_id']
            a2 = constraint[1]['activity_id']

            indices_1 = (self.translation_table[(self.translation_table['product_id'] == p1) & (
                        self.translation_table['activity_id'] == a1)].index.tolist())
            indices_2 = (self.translation_table[(self.translation_table['product_id'] == p2) & (
                        self.translation_table['activity_id'] == a2)].index.tolist())

            for a in indices_1:
                for b in indices_2:
                    self.incompatible_tasks.append((a, b))
        print(self.incompatible_tasks)

    def solve(self, time_limit=10, l1=0.5, l2=0.5, output_file="results.csv"):
        demands = self.resources
        capacities = self.capacity
        nb_tasks = len(self.durations)
        nb_resources = len(capacities)

        # Create model
        mdl = CpoModel()

        # Create task interval variables
        tasks = [interval_var(name='T{}'.format(i + 1), size=self.durations[i]) for i in range(nb_tasks)]

        # Add precedence constraints
        mdl.add(start_of(tasks[s]) >= start_of(tasks[t]) + self.min_lag[(t, s)] for t in range(nb_tasks) for s in self.successors[t])
        mdl.add(
            start_of(tasks[s]) <= start_of(tasks[t]) + self.max_lag[(t, s)] for t in range(nb_tasks) for s in self.successors[t] if
            self.max_lag[(t, s)] != None)

        # Add compatibility constraints
        mdl.add(no_overlap([tasks[i], tasks[j]]) for (i, j) in self.incompatible_tasks)

        # Constrain capacity of resources
        mdl.add(sum(pulse(tasks[t], demands[t][r]) for t in range(nb_tasks) if demands[t][r] > 0) <= capacities[r] for r in
                range(nb_resources))

        # Add objective value
        mdl.add(minimize(l1 * max(end_of(t) for t in tasks) + l2 * sum(
            max(end_of(tasks[t]) - self.deadlines[t], 0) for t in range(nb_tasks))))

        class intermediateSolverStatus(solver.cpo_callback.CpoCallback):
            def __init__(
                    self,
            ):
                self.anytimeData = {"anytime-solutions": [], "anytime-bounds": []}

            def invoke(self, solver, event, sres):
                # TO DO: Currently updates for all events, try to update only when new solution found
                if (sres.is_solution()):
                    self.anytimeData["anytime-solutions"].append(
                        (sres.get_solver_infos().get_solve_time(), sres.get_objective_value()))
                    self.anytimeData["anytime-bounds"].append(
                        (sres.get_solver_infos().get_solve_time(), sres.get_objective_bound()))

        # Create an instance of the callback
        callback = intermediateSolverStatus()

        # Add the callback to the model
        mdl.add_solver_callback(callback)

        # Solve model
        print('Solving model...')
        res = mdl.solve(TimeLimit=time_limit, Workers=1, )

        data = []
        if res:
            for i in range(len(self.durations)):
                start = res.get_var_solution(tasks[i]).start
                end = res.get_var_solution(tasks[i]).end
                data.append({"task": i, "earliest_start": start, "start": start, "end": end,
                             'product_index': self.product_index_translation[i],
                             'activity_id': self.activity_id_translation[i],
                             'product_id': self.product_id_translation[i]
                             })
            data_df = pd.DataFrame(data)
            data_df.to_csv(output_file)
        else:
            print('WARNING: CP solver failed')
            data_df = None

        return res, callback, data_df

    def reschedule(self, logger_info, time_limit=10, l1=0.5, l2=0.5, output_file="results.csv"):
        # FIXME: currently there is quite some overlap in solve and reschedule
        # TODO: adjust durations based on known activities (review)
        durations = copy.copy(self.durations)
        for index, row in logger_info.iterrows():
            product_index = row["ProductIndex"]
            activity_id = row["Activity"]
            true_duration = row["Finish"] - row["Start"]
            indices = (self.translation_table[(self.translation_table['product_index'] == product_index)
                                        & (self.translation_table['activity_id'] == activity_id)].index.tolist())
            index = indices[0]
            durations[index] = true_duration

        print(f'original deterministic durations {self.durations}')
        print(f'               updated durations {durations}')

        demands = self.resources
        capacities = self.capacity
        nb_tasks = len(self.durations)
        nb_resources = len(capacities)

        # Create model
        mdl = CpoModel()

        # Create task interval variables
        tasks = [interval_var(name='T{}'.format(i + 1), size=durations[i]) for i in range(nb_tasks)]

        # Add precedence constraints
        mdl.add(start_of(tasks[s]) >= start_of(tasks[t]) + self.min_lag[(t, s)] for t in range(nb_tasks) for s in self.successors[t])
        mdl.add(
            start_of(tasks[s]) <= start_of(tasks[t]) + self.max_lag[(t, s)] for t in range(nb_tasks) for s in self.successors[t] if
            self.max_lag[(t, s)] != None)

        # Add combatibility constraints
        mdl.add(no_overlap([tasks[i], tasks[j]]) for (i, j) in self.incompatible_tasks)

        # Constrain capacity of resources
        mdl.add(sum(pulse(tasks[t], demands[t][r]) for t in range(nb_tasks) if demands[t][r] > 0) <= capacities[r] for r in
                range(nb_resources))

        # Add objective value
        mdl.add(minimize(l1 * max(end_of(t) for t in tasks) + l2 * sum(
            max(end_of(tasks[t]) - self.deadlines[t], 0) for t in range(nb_tasks))))

        # TODO: add constraints on realized start times and end times (review)
        for index, row in logger_info.iterrows():
            product_index = row["ProductIndex"]
            activity_id = row["Activity"]
            indices = (self.translation_table[(self.translation_table['product_index'] == product_index)
                                        & (self.translation_table['activity_id'] == activity_id)].index.tolist())
            index = indices[0]

            # Updating the start is already sufficient since we updated the interval durations
            mdl.add(start_of(tasks[index]) == row["Start"]) # FIXME: currently the logging only contains finished activitities

        class intermediateSolverStatus(solver.cpo_callback.CpoCallback):
            def __init__(
                    self,
            ):
                self.anytimeData = {"anytime-solutions": [], "anytime-bounds": []}

            def invoke(self, solver, event, sres):
                # TO DO: Currently updates for all events, try to update only when new solution found
                if (sres.is_solution()):
                    self.anytimeData["anytime-solutions"].append(
                        (sres.get_solver_infos().get_solve_time(), sres.get_objective_value()))
                    self.anytimeData["anytime-bounds"].append(
                        (sres.get_solver_infos().get_solve_time(), sres.get_objective_bound()))

        # Create an instance of the callback
        callback = intermediateSolverStatus()

        # Add the callback to the model
        mdl.add_solver_callback(callback)

        # Solve model
        print('Solving model...')
        res = mdl.solve(TimeLimit=time_limit, Workers=1)

        data = []
        if res:
            for i in range(len(self.durations)):
                start = res.get_var_solution(tasks[i]).start
                end = res.get_var_solution(tasks[i]).end
                data.append({"task": i, "earliest_start": start, "start": start, "end": end,
                             'product_index': self.product_index_translation[i],
                             'activity_id': self.activity_id_translation[i],
                             'product_id': self.product_id_translation[i]
                             })
            data_df = pd.DataFrame(data)
            data_df.to_csv(output_file)

        return res, callback, data_df
