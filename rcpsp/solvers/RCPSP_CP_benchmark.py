from typing import List, Any

import pandas as pd
from docplex.cp.model import *
import numpy as np
from numpy import ndarray, dtype, signedinteger, long, bool_, int8, short, intc, unsignedinteger, uint8, ushort, uintc, \
    uintp
from numpy._typing import _8Bit, _16Bit, _32Bit, _64Bit


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
            raise NotImplementedError(f"Problem type has not been recognized {self.problem_type}")

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

    def solve_saa(self, durations: list[list[int]], time_limit=None,  write=False, output_file="results.csv"):
        # Create model
        mdl = CpoModel()
        demands = self.needs
        capacities = self.capacity
        nb_tasks = len(self.durations)
        nb_resources = len(capacities)

        nb_scenarios = len(durations)
        scenarios = range(nb_scenarios)

        # Create task interval variables
        all_tasks = []
        first_stage = [mdl.integer_var(name=f'start_times_{i}') for i in range(nb_tasks)]
        makespans = [mdl.integer_var(name=f'makespan_scenarios{omega}') for omega in scenarios]

        mdl.add(first_stage[t] >= 0 for t in range(nb_tasks))
        # Make scenario intervals
        for omega in range(nb_scenarios):
            tasks = [mdl.interval_var(name=f'T{i}_{omega}', size=durations[omega][i]) for i in range(nb_tasks)]
            all_tasks.append(tasks)

        # Add constraints
        for omega in scenarios:
            tasks = all_tasks[omega]

            # Add relation between scenario start times and first stage decision
            mdl.add(start_of(tasks[t]) == first_stage[t] for t in range(nb_tasks))

            # Precedence relations
            if self.problem_type == "RCPSP":
                mdl.add(start_of(tasks[s]) >= end_of(tasks[t]) for t in range(nb_tasks) for s in self.successors[t])

            elif self.problem_type == "RCPSP_max":
                mdl.add(start_of(tasks[s]) + lag <= start_of(tasks[t]) for (s, lag, t) in self.temporal_constraints)

            else:
                raise NotImplementedError(f"Problem type has not been recognized {self.problem_type}")

            # Constrain capacity of resources
            mdl.add(
                sum(pulse(tasks[t], demands[t][r]) for t in range(nb_tasks) if demands[t][r] > 0) <= capacities[r] for r
                in
                range(nb_resources))

            # Makespan constraint for this scenario
            mdl.add(makespans[omega] >= max(end_of(t) for t in tasks))

        # Solve model, objective is Sample Average Approximation of the makespan
        mdl.add(minimize(sum([makespans[omega] for omega in scenarios])))

        res = mdl.solve(TimeLimit=time_limit, Workers=1, LogVerbosity="Quiet")

        if res:
            start_times = [res.get_var_solution(first_stage[i]).value for i in range(nb_tasks)]
        else:
            print('WARNING: CP solver failed')
            start_times = None

        return res, start_times

    def sample_durations(self, nb_scenarios=1):
        scenarios = []
        for _ in range(nb_scenarios):
            scenario = []
            for duration in self.durations:
                if duration == 0:
                    scenario.append(0)
                else:
                    lower_bound = int(max(1, duration - np.sqrt(duration)))
                    upper_bound = int(duration + np.sqrt(duration))
                    duration_sample = np.random.randint(lower_bound, upper_bound)
                    scenario.append(duration_sample)
            scenarios.append(scenario)

        return scenarios

