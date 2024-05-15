import json
from classes.classes import ProductionPlan, Factory
import classes.general
from classes.stnu import STNU
from rcpsp.solvers.check_feasibility import check_feasibility
from stnu.java_comparison.stnu_to_xml_function import stnu_to_xml
from stnu.algorithms.call_java_cstnu_tool import run_dc_algorithm
from stnu.algorithms.rte_star import rte_star
from stnu.get_resource_chains_reservations import get_resource_chains, add_resource_chains
from rcpsp.solvers.RCPSP_CP import RCPSP_CP
import numpy as np
import pandas as pd

logger = classes.general.get_logger(__name__)


def is_plan_with_deadline_dc(plan: ProductionPlan, deadline: int):

    # Make STNU from production plan
    # Solve deterministic CP and data
    rcpsp = RCPSP_CP(plan)
    res, _, cp_output = rcpsp.solve(None, None, 1, 0)
    if res:
        makespan_cp_output = max(cp_output["end"].tolist())
        logger.info(f'makespan according to CP output is {makespan_cp_output}')
        earliest_start = cp_output.to_dict('records')
        resource_chains, resource_use = get_resource_chains(plan, earliest_start, True)

        # Set up STNU and write to xml
        stnu = STNU.from_production_plan(plan, max_time_lag=True, origin_horizon=True)
        stnu = add_resource_chains(stnu=stnu, resource_chains=resource_chains)

        # Set up deadline on the total makespan (so the horizon)
        stnu.set_ordinary_edge(STNU.ORIGIN_IDX, STNU.HORIZON_IDX, deadline)
        stnu_to_xml(stnu, f"input_deadlines", "stnu/java_comparison/xml_files")

        # Run DC-checking and store ESTNU in xml
        dc, output_location = run_dc_algorithm("stnu/java_comparison/xml_files", f"input_deadlines")
        logger.info(f'dc is {dc} when makespan deadline is {deadline} ')

        return dc

    else:
        logger.info(f'Deterministic CP model infeasible')
        return False
