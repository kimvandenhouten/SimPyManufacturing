from classes.stnu import STNU
import classes.general
from stnu.algorithms.dc_checking import determine_dc
logger = classes.general.get_logger()
from stnu.algorithms.rte_star import RTEdata, rte_generate_decision, hxe_update, hce_update


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

# TODO
rte_data = RTEdata.from_estnu(estnu)

# First decision
rte_decision = rte_generate_decision(rte_data)
if rte_decision.wait is False:
    t, V = rte_decision.t, rte_decision.x
    logger.debug(
        f'if we try to generate a first decision (t,V) we get {t, V} where V is node {estnu.translation_dict[V]}')
    rte_data = hxe_update(estnu, rte_data, t, V)
else:
    logger.debug(f'if we try to generate a first decision we get {rte_decision}')

# Second decision
rte_decision = rte_generate_decision(rte_data)
if rte_decision.wait is False:
    t, V = rte_decision.t, rte_decision.x
    logger.debug(
        f'if we try to generate a second decision (t,V) we get {t, V} where V is node {estnu.translation_dict[V]}')
    rte_data = hxe_update(estnu, rte_data, t, V)
else:
    logger.debug(f'if we try to generate a second decision we get {rte_decision}')


# Third decision
rte_decision = rte_generate_decision(rte_data)
if rte_decision.wait is False:
    t, V = rte_decision.t, rte_decision.x
    logger.debug(
        f'if we try to generate a third decision (t,V) we get {t, V} where V is node {estnu.translation_dict[V]}')
    rte_data = hxe_update(estnu, rte_data, t, V)
else:
    logger.debug(f'if we try to generate a third decision we get {rte_decision}')

if early_execution:
    # Here we simulate that at time rho, we execute contingent time point C
    rho = 3
    tau = [c]
    rte_data = hce_update(estnu, rte_data, rho, tau)

rte_decision = rte_generate_decision(rte_data)
if rte_decision.wait is False:
    t, V = rte_decision.t, rte_decision.x
    logger.debug(
        f'if we try to generate a fourth decision (t,V) we get {t, V} where V is node {estnu.translation_dict[V]}')
    rte_data = hxe_update(estnu, rte_data, t, V)
else:
    logger.debug(f'if we try to generate a fourth decision we get {rte_decision}')

