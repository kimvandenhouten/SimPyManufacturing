from stnu.java_comparison.stnu_to_xml_function import stnu_to_xml
from classes.stnu import STNU
import classes.general
from stnu.dc_checking import convert_to_normal_form, determine_dc
logger = classes.general.get_logger()
from stnu.rte_star import RTEdata, rte_generate_decision, hxe_update

# Example Hunsberger slide 118 (controllable)
name = "slide118"
stnu = STNU()
stnu.add_node('A')
stnu.add_node('B')
stnu.add_node('C')
stnu.set_ordinary_edge('B', 'C', 5)
stnu.add_contingent_link('A', 'C', 2, 9)
dc, estnu = determine_dc(stnu, dispatchability=True)

# TODO
rte_data = RTEdata.from_estnu(estnu)
logger.debug(f'enabled time points {rte_data.enabled_tp}')

t, V = rte_generate_decision(rte_data)
logger.debug(f'if we try to generate a first decision we get {t, V}')

rte_data = hxe_update(estnu, rte_data, t, V)

t, V = rte_generate_decision(rte_data)
logger.debug(f'if we try to generate a second decision we get {t, V}')

rte_data = hxe_update(estnu, rte_data, t, V)

t, V = rte_generate_decision(rte_data)
logger.debug(f'if we try to generate a third decision we get {t, V}')

rte_data = hxe_update(estnu, rte_data, t, V)
t, V = rte_generate_decision(rte_data)
logger.debug(f'if we try to generate a third decision we get {t, V}')