from rcpsp.rcpsp_max.process_file import parse_sch_file
from rcpsp.solvers.RCPSP_CP_benchmark import RCPSP_CP_Benchmark
import pandas as pd
from stnu.algorithms.call_java_cstnu_tool import run_dc_algorithm, run_rte_algorithm
from stnu.get_resource_chains_reservations_benchmark import get_resource_chains, add_resource_chains
from classes.stnu import STNU
from stnu.java_comparison.stnu_to_xml_function import stnu_to_xml
import time
import classes.general
logger = classes.general.get_logger(__name__)
from rcpsp.solvers.check_feasibility import check_feasibility_rcpsp_max
import numpy as np

data = []
results_location = "stnu/experiments/results/debugging_minimal_example.csv"
nr_samples = 1
instance_folder = "j10"


def run_minimal_example(stnu):

    stnu_to_xml(stnu, f"example_rigid_components", "stnu/java_comparison/xml_files")

    # Run the DC algorithm using the Java CSTNU tool, the result is written to a xml file
    start = time.time()
    dc, output_location = run_dc_algorithm("stnu/java_comparison/xml_files", f"example_rigid_components")
    logger.debug(f'dc is {dc} and output location {output_location}')
    time_dc_checking = time.time() - start  # track time of DC-checking step

    if not dc:
        logger.info(f'Network not DC')
        return False
    else:
        # Construct a row dict to append to the list of rows at the end of each iteration
        # Read ESTNU xml file into Python object that was the output from the previous step
        schedule = run_rte_algorithm(output_location)
        if schedule:
            makespan_rte_star = max(schedule.values())
            logger.info(f'Makespan is {makespan_rte_star}')
        return schedule


stnu = STNU(origin_horizon=False)
source = stnu.add_node('0_start')
s1 = stnu.add_node('1_start')
f1 = stnu.add_node('1_finish')

# Resource chains
#stnu.set_ordinary_edge(s3, f1, 0)

# Temporal constraints
stnu.set_ordinary_edge(s1, source, 0)
#stnu.set_ordinary_edge(f1, source, 0)
stnu.set_ordinary_edge(source, f1, 0)

# Contingent links
stnu.add_contingent_link(s1, f1, 2, 7)

schedule = run_minimal_example(stnu)