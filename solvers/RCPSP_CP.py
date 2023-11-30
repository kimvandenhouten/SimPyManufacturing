import pandas as pd
from docplex.cp.model import *
import docplex.cp.solver as solver


def convert_instance_to_cp_input(instance):
    # convert to RCPSP instance
    capacity = instance.factory.capacity
    durations, deadlines, resources = [], [], []
    successors = [[] for p in instance.products for a in p.activities]
    min_lag = {}
    max_lag = {}

    resource_translation = instance.factory.resource_names
    product_id_translation = []
    product_index_translation = []
    activity_id_translation = []

    activity_counter = 0
    product_counter = 0

    # loop over all products
    for p in instance.products:
        for (i, j) in p.temporal_relations:
            min_lag[(i + activity_counter, j + activity_counter)] = p.temporal_relations[(i, j)].min_lag
            max_lag[(i + activity_counter, j + activity_counter)] = p.temporal_relations[(i, j)].max_lag
            successors[i + activity_counter].append(j + activity_counter)

        nr_activities = len(p.activities)
        for act in range(0, nr_activities):
            product_index_translation.append(p.product_index)
            product_id_translation.append(p.id)
            activity_id_translation.append(act)

        for counter, a in enumerate(p.activities):
            if counter == nr_activities - 1:
                deadlines.append(p.deadline)
            else:
                deadlines.append(1000000000)

            durations.append(a.processing_time[0])
            resources.append(a.needs)

        activity_counter += nr_activities
        product_counter += 1

    translation_table = pd.DataFrame(
        {'product_id': product_id_translation,
         'activity_id': activity_id_translation,
         'product_index': product_index_translation
         })

    incompatible_tasks = []
    for constraint in instance.factory.compatibility_constraints:
        p1 = constraint[0]['product_id']
        a1 = constraint[0]['activity_id']
        p2 = constraint[1]['product_id']
        a2 = constraint[1]['activity_id']

        indices_1 = (translation_table[(translation_table['product_id'] == p1) & (translation_table['activity_id'] == a1)].index.tolist())
        indices_2 = (translation_table[(translation_table['product_id'] == p2) & (translation_table['activity_id'] == a2)].index.tolist())

        for a in indices_1:
            for b in indices_2:
                incompatible_tasks.append((a, b))

    print(incompatible_tasks)

    return resources, capacity, durations, successors, min_lag, max_lag, durations, capacity,\
    deadlines, product_index_translation, product_id_translation, activity_id_translation, incompatible_tasks


def solve_rcpsp_cp(demands, capacities, durations, successors, min_lag, max_lag, nb_tasks, nb_resources,
                   deadlines, product_index_translation, product_id_translation, activity_id_translation,
                   incompatible_tasks, time_limit=10, l1=0.5, l2=0.5, output_file="results.csv"):

    # Create model
    mdl = CpoModel()

    # Create task interval variables
    tasks = [interval_var(name='T{}'.format(i+1), size=durations[i]) for i in range(nb_tasks)]

    # Add precedence constraints
    mdl.add(start_of(tasks[s]) >= start_of(tasks[t]) + min_lag[(t, s)] for t in range(nb_tasks) for s in successors[t])
    mdl.add(start_of(tasks[s]) <= start_of(tasks[t]) + max_lag[(t, s)] for t in range(nb_tasks) for s in successors[t] if max_lag[(t,s)] != None)

    # Add combatibility constraints
    mdl.add(no_overlap([tasks[i], tasks[j]]) for (i, j) in incompatible_tasks)

    # Constrain capacity of resources
    mdl.add(sum(pulse(tasks[t], demands[t][r]) for t in range(nb_tasks) if demands[t][r] > 0) <= capacities[r] for r in range(nb_resources))

    # Add objective value
    mdl.add(minimize(l1 * max(end_of(t) for t in tasks) + l2 * sum(max(end_of(tasks[t]) - deadlines[t], 0) for t in range(nb_tasks))))

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
        for i in range(len(durations)):
            start = res.get_var_solution(tasks[i]).start
            end = res.get_var_solution(tasks[i]).end
            data.append({"task": i, "earliest_start": start, "start": start, "end": end, 'product_index': product_index_translation[i],
                         'activity_id': activity_id_translation[i], 'product_id': product_id_translation[i]})
        data_df = pd.DataFrame(data)
        data_df.to_csv(output_file)

    return res, callback, data_df

