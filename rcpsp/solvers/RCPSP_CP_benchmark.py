import numpy as np
import pandas as pd
from docplex.cp.model import *

import general.logger

logger = general.logger.get_logger(__name__)


class RCPSP_CP_Benchmark:
    def __init__(self, capacity, durations, successors, needs, temporal_constraints=None, problem_type="RCPSP",
                 instance_folder="", instance_id=""):
        # convert to RCPSP instance
        self.capacity = capacity
        self.durations = durations
        self.needs = needs
        self.successors = successors
        self.temporal_constraints = temporal_constraints
        self.problem_type = problem_type
        self.instance_folder = instance_folder
        self.instance_id = instance_id
        self.num_tasks = len(self.durations)

    @classmethod
    def parsche_file(cls, directory, instance_folder, instance_id):

        if instance_folder[0] == "j":
            filename = f'{directory}/{instance_folder}/PSP{instance_id}.SCH'
        elif instance_folder[0:3] == "ubo":
            filename = f'{directory}/{instance_folder}/psp{instance_id}.sch'
        else:
            raise ValueError(f"instance folder is not recognized ({instance_folder})")

        with open(filename, 'r') as file:
            lines = file.readlines()

        # Extract the header information
        header = lines[0].strip().split()
        n_tasks = int(header[0])
        n_res = int(header[1])

        # Initialize structures
        durations = [0] * (n_tasks + 2)  # Assuming tasks are numbered from 0 to n_tasks + 1
        needs = []
        temporal_relations = []

        # Parse each task line
        for line in lines[1:n_tasks + 2]:
            parts = line.strip().split()
            task_id = int(parts[0])
            num_successors = int(parts[2])
            successors = parts[3: 3 + num_successors]
            lags = parts[3 + num_successors:]
            for i, suc in enumerate(successors):
                eval_lags = lags[i]
                eval_lags = eval_lags.strip('[]').split(',')
                eval_lags = [int(i) for i in eval_lags]
                for lag in eval_lags:
                    temporal_relations.append((task_id, int(lag), int(suc)))

        for line in lines[n_tasks + 3:-1]:
            parts = line.strip().split()
            task_id = int(parts[0])
            duration = int(parts[2])
            durations[task_id] = duration
            resource_needs = parts[3:]
            resource_needs = [int(i) for i in resource_needs]
            needs.append(resource_needs)

        # Resource capacities and the last resource line
        capacity = list(map(int, lines[-1].strip().split()))

        rcpsp_max = cls(capacity, durations, None, needs, temporal_relations, "RCPSP_max",
                        instance_folder, instance_id)

        return rcpsp_max

    def solve(self, durations=None, time_limit=None, write=False, output_file="results.csv", mode="Quiet"):

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
        logger.info('Solving model...')

        if mode == "Quiet":
            res = mdl.solve(TimeLimit=time_limit, Workers=1, LogVerbosity="Quiet")
        else:
            res = mdl.solve(TimeLimit=time_limit, Workers=1)

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
            logger.info('WARNING: CP solver failed')
            data_df = None

        return res, data_df

    def solve_reactive(self, durations, scheduled_start_times, current_time, time_limit=None):

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

        # Constraint to enforce already scheduled start times (rescheduling approach)
        for t in range(nb_tasks):
            if scheduled_start_times[t] >= 0:
                mdl.add(start_of(tasks[t]) == scheduled_start_times[t])
            else:
                mdl.add(start_of(tasks[t]) >= current_time)

        # Constrain capacity of needs
        mdl.add(sum(pulse(tasks[t], demands[t][r]) for t in range(nb_tasks) if demands[t][r] > 0) <=
                capacities[r] for r in range(nb_resources))

        # Add objective value
        mdl.add(minimize(max(end_of(t) for t in tasks)))

        # Solve model
        logger.info('Solving model...')
        res = mdl.solve(TimeLimit=time_limit, Workers=1, LogVerbosity="Quiet")

        start_times = []
        if res:
            for i in range(len(self.durations)):
                start = res.get_var_solution(tasks[i]).start
                start_times.append(start)
            makespan = res.solution.get_objective_value()
            logger.info(f'Makespan is {makespan}')
            return start_times, makespan
        else:
            logger.info('WARNING: CP solver failed')
            return None, np.inf

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
            logger.warning('WARNING: CP solver failed')
            start_times = None

        return res, start_times

    def get_bound(self, mode="upper_bound", noise_factor=1):
        scenario = []
        for duration in self.durations:
            if duration == 0:
                scenario.append(0)
            else:
                if mode == "lower_bound":
                    bound = int(max(1, duration - noise_factor * np.sqrt(duration)))
                else:
                    bound = int(duration + noise_factor * np.sqrt(duration))
                scenario.append(bound)
        return scenario

    def sample_durations(self, nb_scenarios=1, noise_factor=1):
        scenarios = []
        for _ in range(nb_scenarios):
            scenario = []
            for duration in self.durations:
                if duration == 0:
                    scenario.append(0)
                else:
                    lower_bound = int(max(1, duration - noise_factor * np.sqrt(duration)))
                    upper_bound = int(duration + noise_factor * np.sqrt(duration))
                    duration_sample = np.random.randint(lower_bound, upper_bound)
                    scenario.append(duration_sample)
            scenarios.append(scenario)

        return scenarios



