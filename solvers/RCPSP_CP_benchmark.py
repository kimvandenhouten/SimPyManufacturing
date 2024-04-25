import pandas as pd
from docplex.cp.model import *


class RCPSP_CP_Benchmark:
    def __init__(self, capacity, durations, successors, needs, temporal_constraints=None, problem_type="RCPSP"):
        # convert to RCPSP instance
        self.capacity = capacity
        self.durations = durations
        self.needs = needs
        self.successors = successors
        self.temporal_constraints = temporal_constraints
        self.problem_type = problem_type

    def solve(self, durations=None, time_limit=None, write=False, output_file="results.csv"):

        # Set durations to self.durations if no input vector is given
        durations = self.durations if durations is None else durations
        demands = self.needs
        capacities = self.capacity
        nb_tasks = len(self.durations)
        nb_resources = len(capacities)

        # Create model
        mdl = CpoModel()

        # Create task interval variables
        tasks = [interval_var(name='T{}'.format(i + 1), size=durations[i]) for i in range(nb_tasks)]

        # Add precedence constraints
        if self.problem_type == "RCPSP":
            mdl.add(start_of(tasks[s]) >= end_of(tasks[t]) for t in range(nb_tasks) for s in self.successors[t])


        elif self.problem_type == "RCPSP_max":
            mdl.add(start_of(tasks[s]) + lag <= start_of(tasks[t]) for (s, lag, t) in self.temporal_constraints)

        else:
            raise ValueError(f"Problem type {self.problem_type} is not known ")

        # Constrain capacity of needs
        mdl.add(sum(pulse(tasks[t], demands[t][r]) for t in range(nb_tasks) if demands[t][r] > 0) <= capacities[r] for r in
                range(nb_resources))

        # Add objective value
        mdl.add(minimize(max(end_of(t) for t in tasks)))

        # Solve model
        print('Solving model...')
        res = mdl.solve(TimeLimit=time_limit, Workers=1, LogVerbosity="Quiet")

        data = []
        if res:
            for i in range(len(self.durations)):
                start = res.get_var_solution(tasks[i]).start
                end = res.get_var_solution(tasks[i]).end
                data.append({"task": i, "start": start, "end": end,})
            data_df = pd.DataFrame(data)
            if write:
                data_df.to_csv(output_file)
        else:
            print('WARNING: CP solver failed')
            data_df = None

        return res, data_df