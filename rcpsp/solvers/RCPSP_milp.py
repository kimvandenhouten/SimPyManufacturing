# This is a sample Python script.
import numpy as np
from pyomo.environ import *
import matplotlib.pyplot as plt
import pandas as pd
from IPython.display import display, HTML
import matplotlib.pyplot as plt
import gurobipy as gp
from gurobipy import GRB


class RCPSP:
    def __init__(self, capacity, durations, num_tasks, num_resources, resources, successors, temporal_relations=None):
        self.capacity = capacity
        self.durations = durations
        self.num_tasks = num_tasks
        self.num_resources = num_resources
        self.resources = resources
        self.successors = successors
        self.temporal_relations = temporal_relations

    def model(self, temp_relation="no_wait"):
        self.J = set([j for j in range(0, self.num_tasks)])
        self.R = set([r for r in range(0, self.num_resources)])
        self.p = {j: self.durations[j] for j in self.J}
        self.l = {(r, j): self.resources[j][r] for r in self.R for j in self.J}

        self.b = {r: self.capacity[r] for r in self.R}

        self.S = {j: set() for j in self.J}
        for (i, j) in self.successors:
            self.S[j].add(i)

        if temp_relation == "temporal" or temp_relation == "time_lag":
            self.d = {(i, j): self.temporal_relations[(i, j)].min_lag for (i, j) in self.successors}

        self.T = np.array(range(0, sum(self.durations)))

        # MODEL: create concrete model
        self.model = ConcreteModel()

        # MODEL: variables
        self.model.t = Var(self.J, domain=NonNegativeIntegers)  # finish time of j
        self.model.x = Var(self.J, self.T, domain=Boolean)  # j starts at time t
        self.model.u = Var(self.R, self.T, domain=Boolean)  # j starts at time t
        self.model.fM = Var(domain=NonNegativeIntegers)

        # MODEL: objective
        self.model.Obj = Objective(expr=self.model.fM, sense=minimize)

        self.model.cons = ConstraintList()

        for j in self.J:
            self.model.cons.add(self.model.t[j] <= self.model.fM)

        for j in self.J:
            self.model.cons.add(sum([self.model.x[j, t] * t for t in self.T]) + self.p[j] == self.model.t[j])

        if temp_relation == "no_wait":
            for j in self.J:
                for i in self.S[j]:
                    self.model.cons.add(self.model.t[j] - self.model.t[i] == self.p[j])

        elif temp_relation == "temporal":
            for j in self.J:
                for i in self.S[j]:
                    self.model.cons.add(self.model.t[j] - self.p[j] == self.model.t[i] - self.p[i] + self.d[i, j])

        elif temp_relation == "time_lag":
            for j in self.J:
                for i in self.S[j]:
                    self.model.cons.add(self.model.t[j] - self.p[j] >= self.model.t[i] - self.p[i] + self.d[i, j])

        else:
            for j in self.J:
                for i in self.S[j]:
                    self.model.cons.add(self.model.t[j] - self.model.t[i] >= self.p[j])

        for t in self.T:
            for r in self.R:
                lhs = 0
                if sum([self.l[r, j] for j in self.J]) > 0:
                    for j in self.J:
                        for tau in self.T[self.T <= t]:
                            if tau >= t - self.p[j] + 1:
                                lhs += self.l[r, j] * self.model.x[j, tau]
                    self.model.cons.add(lhs <= self.b[r])

        for j in self.J:
            self.model.cons.add(self.model.t[j] - self.p[j] >= 0)

        for j in self.J:
            self.model.cons.add(sum([self.model.x[j, t] for t in self.T]) == 1)

    def solve(self, time_limit=None):
        print("Makes solver")
        solver = 'gurobi'
        opt = SolverFactory(solver)
        if time_limit is not None:
            opt.options['Time_limit'] = time_limit
        print("Start solving")
        solution = opt.solve(self.model)

        self.terminal = solution.solver.termination_condition
        self.solver_time = round(solution.solver.time, 2)
        self.objective = round(self.model.fM(), 0)
        print(f'Terminal condition is {self.terminal}')
        print(f'Makespan value is {self.objective}')
        print(f'Solve time is {self.solver_time} seconds')


    def get_start_times(self):
        self.start_times = []
        self.finish_times = []
        for j in self.J:
            self.start_times.append(self.model.t[j]() - self.p[j])
            self.finish_times.append(self.model.t[j]())

    def make_resource_usage_table(self, resource_translation, task_translation):
        """
        :param num_tasks: number of tasks that are scheduled in MIP (integer)
        :param num_resources: number of resources that are modelled in MIP (integer)
        :param resources: the resource requirements per task, (list of lists)
        :param resource_translation: list that has the actual name of the resources (list of strings)
        :param batch_translation: list that keeps track of the batch to which the tasks belongs (list of integers)
        :return: datatable with resource usage
        """
        data_table = []
        for j in range(0, self.num_tasks):
            used_resources = self.resources[j]
            start = self.start_times[j]
            finish = self.finish_times[j]
            for r in range(0, self.num_resources):
                resource_requirement = used_resources[r]
                for i in range(0, resource_requirement):
                    data_table.append({"Task": j,
                                       "Task_translation": task_translation[j],
                                       "Start": start,
                                       "Finish": finish,
                                       "Resource": r,
                                       "Resource_translation": resource_translation[r]})

        data_table = pd.DataFrame(data_table)
        return data_table






