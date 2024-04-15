from stnu.java_comparison.stnu_to_xml_function import stnu_to_xml
from classes.stnu import STNU
import classes.general
from stnu.dc_checking import convert_to_normal_form, determine_dc
logger = classes.general.get_logger()
from stnu.rte_star import RTEdata, Observation, rte_generate_decision, rte_update


# Example Hunsberger slide 118 (controllable)
early_execution = True
name = "slide118"
stnu = STNU()
a = stnu.add_node('A')
b = stnu.add_node('B')
c = stnu.add_node('C')
stnu.set_ordinary_edge(b, c, 5)
stnu.add_contingent_link(a, c, 2, 9)
dc, estnu = determine_dc(stnu, dispatchability=True)

if early_execution:
    rte_data = RTEdata.from_estnu(estnu)

    # First decision
    rte_decision = rte_generate_decision(rte_data)
    if rte_decision.fail:
        logger.debug(f'Decision is fail')
    observation = Observation(rho=0, tau=[])
    rte_data = rte_update(estnu, rte_data, rte_decision, observation)

    # Second decision
    rte_decision = rte_generate_decision(rte_data)
    if rte_decision.fail:
        logger.debug(f'Decision is fail')
    observation = Observation(rho=0, tau=[])
    rte_data = rte_update(estnu, rte_data, rte_decision, observation)

    # Third decision
    rte_decision = rte_generate_decision(rte_data)
    if rte_decision.fail:
        logger.debug(f'Decision is fail')
    observation = Observation(rho=2, tau=[])
    rte_data = rte_update(estnu, rte_data, rte_decision, observation)

    # Fourth decision
    rte_decision = rte_generate_decision(rte_data)
    if rte_decision.fail:
        logger.debug(f'Decision is fail')
    observation = Observation(rho=3, tau=[c])
    rte_data = rte_update(estnu, rte_data, rte_decision, observation)

    # Fifth decision
    rte_decision = rte_generate_decision(rte_data)
    if rte_decision.fail:
        logger.debug(f'Decision is fail')
    observation = Observation(rho=3, tau=[])
    rte_data = rte_update(estnu, rte_data, rte_decision, observation)

else:
    rte_data = RTEdata.from_estnu(estnu)

    # First decision
    logger.debug(f'Iteration 1')
    rte_decision = rte_generate_decision(rte_data)
    if rte_decision.fail:
        logger.debug(f'Decision is fail')
    observation = Observation(rho=0, tau=[])
    rte_data = rte_update(estnu, rte_data, rte_decision, observation)

    # Second decision
    logger.debug(f'Iteration 2')
    rte_decision = rte_generate_decision(rte_data)
    if rte_decision.fail:
        logger.debug(f'Decision is fail')
    observation = Observation(rho=0, tau=[])
    rte_data = rte_update(estnu, rte_data, rte_decision, observation)

    # Third decision
    logger.debug(f'Iteration 3')
    rte_decision = rte_generate_decision(rte_data)
    if rte_decision.fail:
        logger.debug(f'Decision is fail')
    observation = Observation(rho=2, tau=[])
    rte_data = rte_update(estnu, rte_data, rte_decision, observation)

    # Fourth decision
    logger.debug(f'Iteration 4')
    rte_decision = rte_generate_decision(rte_data)
    if rte_decision.fail:
        logger.debug(f'Decision is fail')
    observation = Observation(rho=4, tau=[])
    rte_data = rte_update(estnu, rte_data, rte_decision, observation)

    # Fifth decision
    logger.debug(f'Iteration 5')
    rte_decision = rte_generate_decision(rte_data)
    if rte_decision.fail:
        logger.debug(f'Decision is fail')
    observation = Observation(rho=7, tau=[c])
    rte_data = rte_update(estnu, rte_data, rte_decision, observation)