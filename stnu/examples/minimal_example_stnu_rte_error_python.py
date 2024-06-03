from rcpsp.rcpsp_max.process_file import parse_sch_file
from rcpsp.solvers.RCPSP_CP_benchmark import RCPSP_CP_Benchmark
import pandas as pd
from stnu.algorithms.call_java_cstnu_tool import run_dc_algorithm
from stnu.algorithms.rte_star import rte_star
from stnu.get_resource_chains_reservations_benchmark import get_resource_chains, add_resource_chains
from classes.stnu import STNU, SampleStrategy
from stnu.java_comparison.stnu_to_xml_function import stnu_to_xml
import time
import classes.general
logger = classes.general.get_logger(__name__)
from rcpsp.solvers.check_feasibility import check_feasibility_rcpsp_max
import numpy as np
sample_mode = "sample"
data = []
results_location = "stnu/experiments/results/debugging_minimal_example_rte_error.csv"
file_name_stnu = "minimal_example_stnu_rte_error_python"

stnu = STNU(origin_horizon=False)
s3 = stnu.add_node('3_start')
f3 = stnu.add_node('3_finish')
s6 = stnu.add_node('6_start')
f6 = stnu.add_node('6_finish')

# Resource chains
stnu.set_ordinary_edge(s6, f3, 0)

# Temporal constraints
stnu.set_ordinary_edge(s6, s3, 3)

# Contingent links
stnu.add_contingent_link(s3, f3, 3, 8)
stnu.add_contingent_link(s6, f6, 6, 12)

stnu_to_xml(stnu, f"example_rcpsp_max_stnu_python", "stnu/java_comparison/xml_files")

# Run the DC algorithm using the Java CSTNU tool, the result is written to a xml file
start = time.time()
dc, output_location = run_dc_algorithm("stnu/java_comparison/xml_files", f"example_rcpsp_max_stnu_python")
logger.info(f'dc is {dc} and output location {output_location}')
time_dc_checking = time.time() - start  # track time of DC-checking step

# Read ESTNU xml file into Python object that was the output from the previous step
# FIXME: Can we avoid this intermediate writing and reading step?
estnu = STNU.from_graphml(output_location)
if dc:
    # Sample a realisation for the contingent weights
    sample = estnu.sample_contingent_weights(strategy=SampleStrategy.LATE_EXECUTION_STRATEGY)
    logger.info(f'Sample that will be given to RTE_star: {sample}')

    # Run RTE algorithm with alternative oracle and store makespan
    start = time.time()
    if sample_mode == "standard":
        rte_data = rte_star(estnu, oracle="standard")
    else:
        rte_data = rte_star(estnu, oracle="sample", sample=sample)



