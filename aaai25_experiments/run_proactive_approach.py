from rcpsp.rcpsp_max.process_file import parse_sch_file
from rcpsp.solvers.RCPSP_CP_benchmark import RCPSP_CP_Benchmark
import time
import classes.general
logger = classes.general.get_logger(__name__)
from rcpsp.solvers.check_feasibility import check_feasibility_rcpsp_max
import pandas as pd
import numpy as np

time_limit_saa = 120
data_agg = []
results_location = "aaai25_experiments/results/results_saa.csv"


def run_saa_experiment(instance_folder, instance_id, nb_scenarios_saa, time_limit_saa, nb_scenarios_test):
        data = []
        logger.info(f'Start instance {instance_id}')
        capacity, durations, needs, temporal_constraints = parse_sch_file(f'rcpsp/rcpsp_max/{instance_folder}/PSP{instance_id}.SCH')
        
        rcpsp_max = RCPSP_CP_Benchmark(capacity, durations, None, needs, temporal_constraints, "RCPSP_max")

        # TODO: implement the sampling strategy to sample scenarios
        train_durations_sample = rcpsp_max.sample_durations(nb_scenarios_saa)
        logger.debug(train_durations_sample)

        # TODO: solve the SAA approach
        res, start_times = rcpsp_max.solve_saa(train_durations_sample, time_limit_saa)

        if res:
            logger.debug(f'SAA found a solution, start times are {start_times}')

            # TODO: evaluate on test scenarios (simulation)
            test_durations_sample = rcpsp_max.sample_durations(nb_scenarios_test)

            feasibilities, objectives = [], []
            feasibilities_pi, objectives_pi = [], []
            rel_regrets = []

            for i, duration_sample in enumerate(test_durations_sample):
                finish_times = [start_times[i] + duration_sample[i] for i in range(len(duration_sample))]
                feasibility = check_feasibility_rcpsp_max(start_times, finish_times, duration_sample, capacity, needs,
                                            temporal_constraints)
                feasibilities.append(feasibility)
                objective = max(finish_times) if feasibility else np.inf
                objectives.append(objective)

                # Solve with perfect information
                rcpsp_max = RCPSP_CP_Benchmark(capacity, duration_sample, None, needs, temporal_constraints, "RCPSP_max")
                res, schedule = rcpsp_max.solve(time_limit=60)

                if res:
                    feasibility_pi = True
                    objective_pi = max(schedule["end"].tolist())
                    gap_pi = res.get_objective_gaps()[0]
                else:
                    feasibility_pi = False
                    objective_pi = np.inf

                feasibilities_pi.append(feasibility_pi)
                objectives_pi.append(objective_pi)

                if objective < np.inf:
                    rel_regret = 100 * (objective - objective_pi) / objective_pi

                if objective == np.inf:
                    if objective_pi == np.inf:
                        rel_regret = 0
                    else:
                        rel_regret = 100

                rel_regrets.append(rel_regret)

                logger.info(
                    f'objective under perfect information is {objective_pi}, makespan obtained with proactive schedule is {objective}, '
                    f'regret is {rel_regret}, and')

                # Store data
                data.append({
                    "instance_name": f'{instance_folder}_{instance_id}',
                    "method": "proactive",
                    "nr_samples": nb_scenarios_saa,
                    "test_sample_id": i,
                    "obj": objective,
                    "obj_pi": objective_pi,
                    "rel_regret": rel_regret})
            
        else:
            feasibilities, objectives = [], []
            feasibilities_pi, objectives_pi = [], []
            rel_regrets = []
            logger.debug(f'SAA  did not find a solution, start times are {start_times}')
            test_durations_sample = rcpsp_max.sample_durations(nb_scenarios_test)
            for i, duration_sample in enumerate(test_durations_sample):

                feasibilities.append(False)
                objectives.append(np.inf)

                # Solve with perfect information
                rcpsp_max = RCPSP_CP_Benchmark(capacity, duration_sample, None, needs, temporal_constraints,
                                               "RCPSP_max")
                res, schedule = rcpsp_max.solve(time_limit=60)

                if res:
                    feasibility_pi = True
                    objective_pi = max(schedule["end"].tolist())
                    gap_pi = res.get_objective_gaps()[0]
                else:
                    feasibility_pi = False
                    objective_pi = np.inf

                if objective_pi == np.inf:
                    rel_regret = 0
                else:
                    rel_regret = 100

                rel_regrets.append(rel_regret)

                logger.info(
                    f'objective under perfect information is {objective_pi}, makespan obtained with proactive schedule is {np.inf}, '
                    f'regret is {rel_regret}, and')

                # Store data
                data.append({
                    "instance_name": f'{instance_folder}_{instance_id}',
                    "method": "proactive",
                    "nr_samples": nb_scenarios_saa,
                    "test_sample_id": i,
                    "obj": np.inf,
                    "obj_pi": objective_pi,
                    "rel_regret": rel_regret})

            logger.debug(f'{sum(feasibilities)} feasible solutions found with SAA')
            logger.debug(f'while solving with perfect infromation resulted in {sum(feasibilities_pi)} feasible solutions '
                  f'found with simulation')
            logger.debug(
                f'average objective while ignoring the infeasible ones is {np.mean([i for i in objectives if i < np.inf])}')
            logger.debug(f'average rel regret (%) is {np.mean(rel_regrets)}')

        return data


nb_scenarios_test = 50
for nb_scenarios_saa in [10]:
    for instance_folder in ["j10"]:
        for instance_id in range(1, 271):

            data_agg += run_saa_experiment(instance_folder, instance_id, nb_scenarios_saa, time_limit_saa, nb_scenarios_test)
            df = pd.DataFrame(data_agg)
            df.to_csv(results_location, index=False)



