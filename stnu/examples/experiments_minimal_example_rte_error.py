from copy import deepcopy
from typing import Union, Any

from rcpsp.rcpsp_max.process_file import parse_sch_file
from rcpsp.solvers.RCPSP_CP_benchmark import RCPSP_CP_Benchmark
from stnu.algorithms.call_java_cstnu_tool import run_dc_algorithm
from stnu.algorithms.rte_star import rte_star
from stnu.get_resource_chains_reservations_benchmark import get_resource_chains, add_resource_chains
from classes.stnu import STNU, SampleStrategy, Edge
from stnu.java_comparison.stnu_to_xml_function import stnu_to_xml
import time
import classes.general
from rcpsp.solvers.check_feasibility import check_feasibility_rcpsp_max
import numpy as np

logger = classes.general.get_logger(__name__)


def run_rte(stnu_location, output_location=None):

    if output_location is None:
        logger.info(f'Start DC checking algorithm from XML file {stnu_location}')
        # Run the DC algorithm using the Java CSTNU tool, the result is written to a xml file
        dc, output_location = run_dc_algorithm("stnu/java_comparison/xml_files", stnu_location)
        logger.info(f'dc is {dc} and output location {output_location}')

        if not dc:
            logger.info(f'the network is not DC')
            return False
    else:
        dc = True

    # Read ESTNU xml file into Python object that was the output from the previous step
    logger.info(f'Read ESTNU from output location {output_location}')
    estnu = STNU.from_graphml(output_location)

    if dc:
        np.random.seed(1)
        # Sample a realisation for the contingent weights
        sample = estnu.sample_contingent_weights(strategy=SampleStrategy.RANDOM_EXECUTION_STRATEGY)
        logger.info(f'Sample that will be given to RTE_star: {sample}')

        # Run RTE algorithm with alternative oracle and store makespan
        if sample_mode == "standard":
            rte_data = rte_star(estnu, oracle="standard")
        elif sample_mode == "sample":
            rte_data = rte_star(estnu, oracle="sample", sample=sample)
        if rte_data:
            logger.info(f'Final schedule is {rte_data.f}')
            logger.info(f'{estnu.translation_dict}')
        else:
            logger.info(f'For some reason the RTE star could not finish')
            return True

    else:
        print(f'The network is not dynamically controllable')
        return False

sample_mode = "sample"
rte_error = run_rte(stnu_location='example_rcpsp_max_stnu_python')

