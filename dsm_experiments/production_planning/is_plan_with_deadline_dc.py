import json
from factory_simulator.classes import ProductionPlan, Factory
from dsm_experiments.scheduling.check_feasibility import check_feasibility
from dsm_experiments.temporal_networks.stnu_factory import FACTORY_STNU, get_resource_chains, add_resource_chains

from temporal_networks.stnu import STNU
from temporal_networks.cstnu_tool.stnu_to_xml_function import stnu_to_xml
from temporal_networks.cstnu_tool.call_java_cstnu_tool import run_dc_algorithm
from temporal_networks.rte_star import rte_star

from rcpsp.solvers.RCPSP_CP import RCPSP_CP
import numpy as np
import pandas as pd

import general.logger
logger = general.logger.get_logger(__name__)


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
        stnu = FACTORY_STNU.from_production_plan(plan, max_time_lag=True, origin_horizon=True)
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
