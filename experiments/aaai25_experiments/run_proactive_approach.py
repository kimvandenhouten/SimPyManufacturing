from rcpsp.rcpsp_max.process_file import parse_sch_file
from rcpsp.solvers.RCPSP_CP_benchmark import RCPSP_CP_Benchmark
from rcpsp.solvers.check_feasibility import check_feasibility_rcpsp_max

import pandas as pd
import numpy as np
import time

import general.logger
logger = general.logger.get_logger(__name__)



# TODO: decouple the SAA approach and the evaluation approach?
def run_saa(rcpsp_max, nb_scenarios_saa, time_limit_saa):

    start_offline = time.time()
    logger.debug(f'Start solving SAA instance {rcpsp_max.instance_id} with {nb_scenarios_saa} scenarios')

    # TODO: implement the sampling strategy to sample scenarios
    train_durations_sample = rcpsp_max.sample_durations(nb_scenarios_saa)

    logger.debug(train_durations_sample)

    # TODO: solve the SAA approach
    res, start_times = rcpsp_max.solve_saa(train_durations_sample, time_limit_saa)
    finish_offline = time.time()
    time_offline = finish_offline - start_offline

    return res, start_times, time_offline


def evaluate_saa(rcpsp_max, res, start_times, time_offline, test_durations_sample, nb_scenarios_saa, time_limit_saa=60,
                 time_limit_pi=60):

    data = []

    if res:
        logger.debug(f'SAA found a solution, start times are {start_times}')

        # TODO: evaluate on test scenarios (simulation)


        feasibilities, objectives = [], []
        feasibilities_pi, objectives_pi = [], []
        rel_regrets = []

        for i, duration_sample in enumerate(test_durations_sample):
            start_online = time.time()
            finish_times = [start_times[i] + duration_sample[i] for i in range(len(duration_sample))]
            feasibility = check_feasibility_rcpsp_max(start_times, finish_times, duration_sample, rcpsp_max.capacity,
                                                      rcpsp_max.needs, rcpsp_max.temporal_constraints)
            feasibilities.append(feasibility)
            objective = max(finish_times) if feasibility else np.inf
            objectives.append(objective)

            finish_online = time.time()

            # Solve with perfect information
            res, schedule = rcpsp_max.solve(duration_sample, time_limit=time_limit_pi)

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
                logger.info(
                    f'Instance PSP{rcpsp_max.instance_id} with true durations {duration_sample} is FEASIBLE with makespan {objective}')
                rel_regret = 100 * (objective - objective_pi) / objective_pi

            if objective == np.inf:

                if objective_pi == np.inf:
                    rel_regret = 0
                    logger.info(
                        f'Instance PSP{rcpsp_max.instance_id} with true durations {duration_sample} is INFEASIBLE')
                else:
                    rel_regret = 100
                    logger.info(
                        f'Instance PSP{rcpsp_max.instance_id} with true durations {duration_sample} is INFEASIBLE under perfect information')

            rel_regrets.append(rel_regret)

            logger.debug(f'objective under perfect information is {objective_pi}, makespan obtained with proactive schedule is {objective}, '
                f'regret is {rel_regret}, and')


            # Store data
            data.append({
                "instance_folder": rcpsp_max.instance_folder,
                "instance_id": rcpsp_max.instance_id,
                "method": "proactive",
                "nr_samples": nb_scenarios_saa,
                "obj": objective,
                "obj_pi": objective_pi,
                "rel_regret": rel_regret,
                "time_limit_SAA": time_limit_saa,
                "feasibility": feasibility,
                "feasibility_pi": feasibility_pi,
                "real_durations": duration_sample,
                "start_times": start_times,
                "time_offline": time_offline,
                "time_online": finish_online - start_online
            })

    else:
        feasibilities, objectives = [], []
        feasibilities_pi, objectives_pi = [], []
        rel_regrets = []
        logger.debug(f'SAA  did not find a solution, start times are {start_times}')
        for i, duration_sample in enumerate(test_durations_sample):


            feasibilities.append(False)
            objectives.append(np.inf)
            logger.info(
                f'Instance PSP{rcpsp_max.instance_id} with true durations {duration_sample} is INFEASIBLE')
            # Solve with perfect information

            res, schedule = rcpsp_max.solve(duration_sample, time_limit=time_limit_pi)

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

            logger.debug(
                f'objective under perfect information is {objective_pi}, makespan obtained with proactive schedule is {np.inf}, '
                f'regret is {rel_regret}, and')

            # Store data
            data.append({
                "instance_folder": rcpsp_max.instance_folder,
                "instance_id": rcpsp_max.instance_id,
                "method": "proactive",
                "nr_samples": nb_scenarios_saa,
                "obj": np.inf,
                "obj_pi": objective_pi,
                "rel_regret": rel_regret,
                "time_limit_SAA": time_limit_saa,
                "time_limit_pi": time_limit_pi,
                "feasibility": False,
                "feasibility_pi": feasibility_pi,
                "real_durations": duration_sample,
                "start_times": start_times,
                "time_offline": time_offline,
                "time_online": 0

            })

        logger.debug(f'{sum(feasibilities)} feasible solutions found with SAA')
        logger.debug(f'while solving with perfect information resulted in {sum(feasibilities_pi)} feasible solutions '
              f'found with simulation')
        logger.debug(
            f'average objective while ignoring the infeasible ones is {np.mean([i for i in objectives if i < np.inf])}')
        logger.debug(f'average rel regret (%) is {np.mean(rel_regrets)}')

    return data






