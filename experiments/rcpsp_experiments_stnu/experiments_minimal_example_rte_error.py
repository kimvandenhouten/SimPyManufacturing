import numpy as np

import general.logger
from temporal_networks.cstnu_tool.call_java_cstnu_tool import run_dc_algorithm
from temporal_networks.rte_star import rte_star
from temporal_networks.stnu import STNU, SampleStrategy

logger = general.logger.get_logger(__name__)


def run_rte(stnu_location, output_location=None):

    if output_location is None:
        logger.info(f'Start DC checking algorithm from XML file {stnu_location}')
        # Run the DC algorithm using the Java CSTNU tool, the result is written to a xml file
        dc, output_location = run_dc_algorithm("temporal_networks/cstnu_tool/xml_files", stnu_location)
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
rte_error = run_rte(stnu_location='rte_error_example')

