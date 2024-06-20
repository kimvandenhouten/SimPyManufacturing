import numpy as np

import general.logger
from temporal_networks.cstnu_tool.call_java_cstnu_tool import run_dc_algorithm
from temporal_networks.rte_star import rte_star
from temporal_networks.stnu import STNU, SampleStrategy
from rcpsp.solvers.RCPSP_CP_benchmark import RCPSP_CP_Benchmark


logger = general.logger.get_logger(__name__)


def run_rte(stnu_location, sample_duration, output_location=None):

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
        # Sample a realisation for the contingent weights
        sample = {}
        for task, duration in enumerate(sample_duration):
            if 0 >= task or task >= len(sample_duration) - 1:  # skip the source and sink node
                continue
            if estnu.translation_dict_reversed.get(f'{task}_{STNU.EVENT_FINISH}', False):
                find_contingent_node = estnu.translation_dict_reversed[f'{task}_{STNU.EVENT_FINISH}']
                sample[find_contingent_node] = duration
        logger.info(f'Sample that will be given to RTE_star: {sample}')

        # Run RTE algorithm with alternative oracle and store makespan

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


DIRECTORY_INSTANCES = 'rcpsp/rcpsp_max'
instance_folder, instance_id = "j30", 35
np.random.seed(1)
rcpsp_max = RCPSP_CP_Benchmark.parsche_file(DIRECTORY_INSTANCES, instance_folder, instance_id)
test_durations_samples = rcpsp_max.sample_durations(10)
sample_duration = test_durations_samples[0]
for seed in range(1):
    logger.info(f'sample duration {sample_duration}')
    rte_error = run_rte(stnu_location=f"rte_error_kim_without_nodes", sample_duration=sample_duration)

