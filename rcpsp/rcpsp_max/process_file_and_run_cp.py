import pandas as pd
from rcpsp.rcpsp_max.process_file import parse_sch_file
from rcpsp.solvers.RCPSP_CP_benchmark import RCPSP_CP_Benchmark

data = []
for instance_id in range(1, 271):
    capacity, durations, needs, temporal_constraints = parse_sch_file(f'benchmark_rcpsp/rcpsp_max/j10/PSP{instance_id}.SCH')
    rcpsp_max = RCPSP_CP_Benchmark(capacity, durations, None, needs, temporal_constraints, "RCPSP_max")
    res, schedule = rcpsp_max.solve()
    if res:
        makespan = res.solution.objective_values[0]
        gap = res.solution.objective_gaps[0]
        print(f'Makespan is {makespan}, gap is {gap}')
        data.append({"instance": f'PSP{instance_id}',
                     "gap": gap,
                     "makespan": makespan,
                     "solve_status": "feasible"})
        data_df = pd.DataFrame(data)
        data_df.to_csv(f'benchmark_rcpsp/rcpsp_max/results_rcpsp_max.csv')
    else:
        print(f'The model has no solution')
        data.append({"instance": f'PSP{instance_id}',
                     "gap": "",
                     "makespan": "",
                     "solve_status": "infeasible"})
        data_df = pd.DataFrame(data)
        data_df.to_csv(f'benchmark_rcpsp/rcpsp_max/results_rcpsp_max.csv')

