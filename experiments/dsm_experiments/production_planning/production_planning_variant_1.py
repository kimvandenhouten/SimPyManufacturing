import json
from factory_simulator.classes import ProductionPlan, Factory
import enum
import json
from factory_simulator.classes import ProductionPlan, Factory
from dsm_experiments.production_planning.is_plan_with_deadline_dc import is_plan_with_deadline_dc
import random
import copy

import general.logger
logger = general.logger.get_logger(__name__)


import general.logger
logger = general.logger.get_logger(__name__)


class InitHeuristic(enum.Enum):
    EARLIEST_DEADLINE_FIRST = enum.auto()
    RANDOM = enum.auto()


def production_planning_variant_1(factory: Factory, work_inventory_product_ids: list[int], deadlines: list[int],
                                  makespan_deadline: int, size_init: int, heuristic_init: InitHeuristic = InitHeuristic.RANDOM,
                                  iterations: int = 30) -> (list[int], float):

    # Initialize solution subset
    if heuristic_init == InitHeuristic.RANDOM:
        current_solution_indices = random.sample(range(len(work_inventory_product_ids)), size_init)
    elif heuristic_init == InitHeuristic.EARLIEST_DEADLINE_FIRST:
        # Create a list of tuples (index, deadline) from the deadlines list
        indexed_deadlines = list(enumerate(deadlines))

        # Sort the indexed list by deadlines (second element of each tuple)
        indexed_deadlines.sort(key=lambda x: x[1])

        # Check if k is within the range of the list
        if size_init <= len(deadlines):
            # Extract the first k indices from the sorted list
            current_solution_indices = [index for index, deadline in indexed_deadlines[:size_init]]
            logger.debug(f"{size_init} indices with the lowest deadlines: {current_solution_indices}")
        else:
            raise Exception("Requested more indices than there are available in the list.")

    elite_solutions = []
    for it in range(iterations):
        # Set-up the plan
        plan = ProductionPlan(id=1, size=len(work_inventory_product_ids), name="ProductionPlan",
                              factory=factory, product_ids=[work_inventory_product_ids[i] for i in current_solution_indices],
                              deadlines=[deadlines[i] for i in current_solution_indices])

        # Set deadline and check dc
        dc = is_plan_with_deadline_dc(plan, deadline=makespan_deadline)

        if dc:
            elite_solutions.append(current_solution_indices)

        # Mutation of the current solution
        if dc:
            missing_indices = [index for index in range(0, len(work_inventory_product_ids)) if index not in current_solution_indices]
            new_index = random.choice(missing_indices)
            current_solution_indices = copy.copy(current_solution_indices)
            current_solution_indices.append(new_index)
            logger.info(f'New solution is {current_solution_indices}')
        else:
            index_to_remove = random.randint(0, len(current_solution_indices) - 1)
            current_solution_indices = copy.copy(current_solution_indices)
            current_solution_indices.pop(index_to_remove)
            logger.info(f'New solution is {current_solution_indices}')

    logger.info(f'Final elite solutions {elite_solutions}')

    ranking = []
    if len(elite_solutions) > 0:
        for solution in elite_solutions:
            not_scheduled = [index for index in range(0, len(work_inventory_product_ids)) if index not in solution]
            total_penalty = sum([makespan_deadline/deadlines[i] for i in not_scheduled])
            logger.info(f'total penalty for solution {solution} is total_penalty {total_penalty}')

            ranking.append({"solution": solution,
                            "total_penalty": total_penalty})

        best_sol_dict = min(ranking, key=lambda x: x["total_penalty"])
        best_sol = best_sol_dict["solution"]
        best_penalty = best_sol_dict["total_penalty"]

        logger.info(f"Best solution: {best_sol}, with total penalty {best_penalty}")

        return best_sol, best_penalty

    else:
        logger.info(f'No solution found within the computation budget that has the DC property')
        return None, None


# Read factory information
factory = Factory(**json.load(open(f'../factory_data/factory/factory_1.json')))

# Set-up synthetic work inventory (30 products with deadlines varying between 0 and 720*3)
work_inventory_product_ids = random.choices(range(0, len(factory.products)), k=30)
deadlines = random.choices(range(1, 720*3), k=30)
logger.info(f'The work inventory with deadlines is {zip(work_inventory_product_ids, deadlines)}')

for init_heuristic in [InitHeuristic.RANDOM, InitHeuristic.EARLIEST_DEADLINE_FIRST]:
    logger.info(f'Start production planning with {init_heuristic}')
    best_sol, best_pen = production_planning_variant_1(factory, work_inventory_product_ids, deadlines,
                                                       720, 15, init_heuristic, 30)

