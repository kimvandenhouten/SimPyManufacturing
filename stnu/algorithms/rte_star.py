import classes.general
from classes.stnu import STNU, Edge
import numpy as np
import random
import typing

logger = classes.general.get_logger(level="INFO")


def intersect_intervals(a, b, c, d):
    x = max(a, c)
    y = min(b, d)

    if x > y:
        return False
    else:
        return x, y


class TimeWindow:
    def __init__(self, x: int, lb=0, ub=np.inf):
        self.x = x
        self.lb = lb
        self.ub = ub


class RTEdata:
    u_x: list[int]
    u_c: list[int]

    def __init__(self, u_x: list[int], u_c: list[int], enabled_x=None, now=0):
        self.u_x = u_x
        self.u_c = u_c
        if enabled_x is None:
            self.enabled_tp = []
        else:
            self.enabled_tp = enabled_x  # the enabled timepoints
        self.now = now  # the current time, initialized at 0
        self.f = {}  # variable assignments (schedule)
        self.time_windows = {}
        self.act_waits = {}
        self.sampled_weights = {}

    @classmethod
    def from_estnu(cls, estnu: STNU) -> 'RTEdata':
        # Obtain executable and contingent timepoints from the estnu
        u_x = estnu.get_executable_time_points()
        u_c = estnu.get_contingent_time_points()
        rte_data = RTEdata(u_x, u_c)

        # Initialize enabled timepoints
        for tp in u_x:
            enabled = True
            outgoing_edges = estnu.get_outgoing_edges(tp)
            for (weight, suc_node, edge_type, edge_label) in outgoing_edges:
                if weight < 0:
                    if suc_node not in rte_data.f:
                        # FIXME LP remove this "if"?
                        # FIXME It seems like it is always true: I don't see anything being added to rte_data.f
                        enabled = False
            if enabled:
                rte_data.enabled_tp.append(tp)

            # Initialize time windows
            rte_data.time_windows[tp] = TimeWindow(tp)

            # Initialize activated waits
            rte_data.act_waits[tp] = []

        return rte_data


class RTEdecision:
    def __init__(self, x=None, t=None, wait=False, fail=False):
        self.x = x  # the executable time point
        self.t = t  # the time point at which x will is determined to be executed
        self.wait = wait  # if wait is True the decision will be wait instead of (x,t)
        self.fail = fail


class Observation:
    def __init__(self, rho, tau):
        self.rho = rho
        self.tau = tau


def rte_star(estnu: STNU, oracle="standard", sample=None):
    """
    This procedure should run the RTE^* algorithm such as described in Hunsberger'2024 article "Foundations of
    Dispatchability for Simple Temporal Networks with Uncertainty"
    :param estnu: extended stnu
    :return: function (T_x union T_c -> R) which is the schedule, or False
    """
    # Line 1: First initialise the data structure with RTE_init(T_x, T_c)
    rte_data = RTEdata.from_estnu(estnu)

    # Line 2: While either U_x (unexecuted executable timepoints) or U_c (unexecuted contingent timepoints) are non-empty
    while len(rte_data.u_c) + len(rte_data.u_x) > 0:

        # Line 3: Generate exec. decision (use rte_generate_decision)
        rte_decision = rte_generate_decision(rte_data)

        # Line 4: If decision returns fail
        if rte_decision.fail:
            # Line 5: Return fail
            return False

        # Line 6: (rho, tau) = Observe contingent timepoints
        if oracle == "standard":
            observation = rte_oracle(estnu, rte_data, rte_decision)
        else:
            observation = rte_oracle_sample(estnu, rte_data, rte_decision, sample)

        # Line 7: Update RTE data structure
        rte_data = rte_update(estnu, rte_data, rte_decision, observation)

        # Line 8: If D=fail
        if rte_data is False:
            return False

    return rte_data


def rte_generate_decision(D: RTEdata):
    """
    computes the next RTED for one iteration of the RTE* algorithm
    :param d: RTEdata structure
    :return: Eec decs: Wait or (t, V); or fail
    """
    # logger.debug(f'Enabled timepoints are: {D.enabled_tp}')
    # Line 1: If D.enabled_x is empty:
    if len(D.enabled_tp) == 0:
        # Line 2: return wait
        logger.debug('Generate decision returns wait')
        delta = RTEdecision(wait=True)
        return delta
    else:
        # Line 3: For each x \in D.enabled_x:
        glb = {}
        ub = {}
        for x in D.enabled_tp:
            act_waits = D.act_waits[x]
            # Line 4: Find maximum wait for X
            max_wait = max(act_waits) if len(act_waits) > 0 else 0
            if isinstance(max_wait, tuple):
                max_wait = max_wait[0]
            # Line 5: Find greatest lower bound for X
            glb[x] = max(max_wait, D.time_windows[x].lb)
            ub[x] = D.time_windows[x].ub

    # Line 6: Find earliest possible next execution: t_l
    t_l = min(glb.values())
    # Line 7: Find latest possible next execution: t_u
    t_u = min(ub.values())

    # Line 8: If the intersection from [t_l, t_u] and [now, inf] is empty
    if t_u < D.now or np.inf < t_l:
        # Line 9: Return fail
        logger.debug('Generate decision returns fail')
        delta = RTEdecision(fail=True)
        return delta

    # Line 10: Select any point V \in D.enabled_tp for which the intersection is not empty
    found_v = None  # This will store the item V that meets your criteria

    for V in D.enabled_tp:
        # Check if the intersection of [glb(V), ub(V)] and [D.now, t_u] is not empty
        if not (ub[V] < D.now or t_u < glb[V]):
            # If the condition does not hold, remember V and exit the loop
            found_v = V
            break

    if found_v is None:
        delta = RTEdecision(wait=True)
        return delta

    else:
        # Line 11: Select any point t in [glb(V), ub(V)] \intersection [D.now, t_u]
        t = max(glb[found_v], D.now)  # TODO: now I implemented just the LB

        # Line 12: Return (t,V)
        logger.debug(f'Generate decision returns (V,t) {(found_v, t)}')
        delta = RTEdecision(x=found_v, t=t)
        return delta


def rte_oracle(S: STNU, D: RTEdata, delta: RTEdecision):
    """
    This represents the real time feedback from the system
    :return: (t_c, t) where t_c is the contingent time-points, and t is the time
    """
    # Line 1: set f=D.f and now = D.now
    f = D.f
    now = D.now

    # Line 2: get currently active contingent links
    active_links = []
    for (A, C) in S.contingent_links:
        if A in f and C not in f:
            if f[A] <= now:
                active_links.append(
                    (A, C, S.contingent_links[(A, C)]['lc_value'], S.contingent_links[(A, C)]['uc_value']))
    logger.debug(f'Active links are {active_links}')

    # Line 3: check waiting forever
    if len(active_links) == 0 and delta.wait:
        # Line 4: return
        logger.debug(f'Oracle returns rho = inf and tau = []')
        observation = Observation(rho=np.inf, tau=[])
        return observation

    # Line 5: if no active links but there is a new scheduling decision
    if len(active_links) == 0 and not delta.wait and not delta.fail:
        # Line 6: return decision
        observation = Observation(rho=delta.t, tau=[])
        logger.debug(f'Oracle returns rho = {delta.t} and tau = []')
        return observation

    # Line 7 - 8: Compute bounds for possible contingent executions
    lb, ub, f_act_tp, real_weight_c = {}, {}, {}, {}
    for (A, C, x, y) in active_links:
        lb[C] = f[A] + x
        ub[C] = f[A] + y
        f_act_tp[C] = f[A]

    lb_c = min(lb.values())
    ub_c = min(ub.values())

    # Line 9: select any t_c in [lb_c, ub_c]
    t_c = random.randint(lb_c, ub_c)
    logger.debug(f'Randomly selected {t_c} as t_c')

    # Oracle decides not to execute any CTPs yet
    # Line 10: if delta = (t,V) and t_c > t
    if delta.wait is False and delta.fail is False:
        if t_c > delta.t:
            # Line 11: return
            logger.debug(f'Oracle returns rho = {delta.t} and tau = []')
            observation = Observation(rho=delta.t, tau=[])
            return observation

    # Oracle decides to execute one or more CTPs
    # Line 12: form tau_star
    tau_star = set()
    for (A, C, x, y) in active_links:
        if f[A] + x <= t_c <= f[A] + y:
            tau_star.add(C)

    # Line 13: select any non-empty subset of tau_star and return observation
    subset_size = random.randint(1, len(tau_star))
    tau = random.sample(tau_star, subset_size)
    for C in tau:
        D.sampled_weights[C] = t_c - f_act_tp[C]
        logger.debug(f'{S.translation_dict[C]}')

    observation = Observation(rho=t_c, tau=tau)
    logger.debug(f'Oracle returns rho = {t_c} and tau = {tau}')
    return observation


def rte_oracle_sample(S: STNU, D: RTEdata, delta: RTEdecision, sample: dict):
    """
    This represents the real time feedback from the system
    :return: (t_c, t) where t_c is the contingent time-points, and t is the time
    """
    # Line 1: set f=D.f and now = D.now
    f = D.f
    now = D.now

    # Line 2: get currently active contingent links
    active_links = []
    for (A, C) in S.contingent_links:
        if A in f and C not in f:
            if f[A] <= now:
                active_links.append((A, C, S.contingent_links[(A, C)]['lc_value'], S.contingent_links[(A, C)]['uc_value']))
    logger.debug(f'Active links are {active_links}')

    # Line 3: check waiting forever
    if len(active_links) == 0 and delta.wait:
        # Line 4: return
        logger.debug(f'Oracle returns rho = inf and tau = []')
        observation = Observation(rho=np.inf, tau=[])
        return observation

    # Line 5: if no active links but there is a new scheduling decision
    if len(active_links) == 0 and not delta.wait and not delta.fail:
        # Line 6: return decision
        observation = Observation(rho=delta.t, tau=[])
        logger.debug(f'Oracle returns rho = {delta.t} and tau = []')
        return observation

    # Line 7 - 8: Compute bounds for possible contingent executions
    lb, ub, f_act_tp, real_weight_c = {}, {}, {}, {}
    finish = {}
    t_c = np.inf  # Keep track of the earliest finishing contingent TP
    for (A, C, x, y) in active_links:
        finish[C] = f[A] + sample[C]
        f_act_tp[C] = f[A]
        # Keep track of the earliest finishing contingent TP
        if finish[C] < t_c:
            t_c = finish[C]

    # Oracle decides not to execute any CTPs yet
    # Line 10: if delta = (t,V) and t_c > t
    if delta.wait is False and delta.fail is False:
        if t_c > delta.t:
            # Line 11: return
            logger.debug(f'Oracle returns rho = {delta.t} and tau = []')
            observation = Observation(rho=delta.t, tau=[])
            return observation

    # Define contingent timepoints that will be executed now based on sample
    tau = []
    for (A, C, x, y) in active_links:
        if finish[C] == t_c:
            tau.append(C)

    # Line 13: select any non-empty subset of tau_star and return observation
    for C in tau:
        D.sampled_weights[C] = t_c - f_act_tp[C]
        logger.debug(f'{S.translation_dict[C]}')

    observation = Observation(rho=t_c, tau=tau)
    logger.debug(f'Oracle returns rho = {t_c} and tau = {tau}')
    return observation

def rte_update(S: STNU, D: RTEdata, delta: RTEdecision, observation: Observation):
    """
    :param estnu:
    :param D:
    :param delta:
    :param observation: (rho, tau)
    :return: update D (RTEdata), or FAIL
    """
    # Line 1: If rho = inf
    if observation.rho == np.inf:
        # Line 2: Return fail
        return False

    # Line 3: If delta = wait, or delta = (t,V) and rho < t:
    if delta.wait or (delta.wait is False and observation.rho < delta.t):
        # Line 4: D = HCE(S, D, rho, tau)
        D = hce_update(S, D, observation.rho, observation.tau)
    # Line 5: Else
    else:
        # Line 6: D = HXE(S, D, t, V)
        D = hxe_update(S, D, delta.t, delta.x)
        # Line 7: If tau is not empty set, also execute contingent timepoints
        if len(observation.tau) > 0:
            # Line 8: HCE(S, D, t, tau)
            D = hce_update(S, D, delta.t, observation.tau)

    # Line 9: Update D.now = rho
    D.now = observation.rho

    # Line 10: Return D
    return D


def hxe_update(S: STNU, D: RTEdata, t: float, V: int):
    """
    Handles non-contingent executions
    :param S: extended STNU
    :param D: RTE data structure
    :param t: an execution time
    :param V: executable time-point to execute at rho
    :return: D: updated RTE data structure
    """
    # Line 1: Add (V, t) to D.f
    logger.debug(f'Update schedule node {V} that is {S.translation_dict[V]} scheduled at {t}')
    D.f[V] = t

    # Line 2: Remove (V, t) from D.u_x
    D.u_x.remove(V)

    # Line 3: Update time windows for neighbors of V
    # for outgoing edges (V, delta, W)
    outgoing_edges = S.get_outgoing_edges(node_from=V, ordinary=True, uc=False, lc=False)
    for (delta, W, _, _) in outgoing_edges:
        # TW(W) = intersection of TW(W) and (-np.inf, t + delta)
        if W in D.time_windows:  # skip contingent tps
            new_lb, new_ub = intersect_intervals(D.time_windows[W].lb, D.time_windows[W].ub, -np.inf, t + delta)
            D.time_windows[W].lb = new_lb
            D.time_windows[W].ub = new_ub
            # logger.debug(f'Update time window of {W} to [{new_lb}, {new_ub}]')

    # for incoming edges (U, gamma, V)
    incoming_edges = S.get_incoming_edges(node_to=V, ordinary=True, uc=False, lc=False)
    for (gamma, U, _, _) in incoming_edges:
        # TW(U) = intersection of TW(U) and [t-gamma, np.inf)
        if U in D.time_windows:
            new_lb, new_ub = intersect_intervals(D.time_windows[U].lb, D.time_windows[U].ub, t - gamma, np.inf)
            D.time_windows[U].lb = new_lb
            D.time_windows[U].ub = new_ub
            # logger.debug(f'Update time window of {U} to [{new_lb}, {new_ub}]')

    # Line 4: Update D.Enabled_x due to any negative incoming edges to V
    # FIXME: can we do this more efficient
    D.enabled_tp = []
    for tp in D.u_x:
        enabled = True
        outgoing_edges = S.get_outgoing_edges(tp)
        # FIXME: to discuss how edges with zero weight work in this algorithm (ordinary vs lowercase seems also important)
        for (weight, suc_node, edge_type, edge_label) in outgoing_edges:
            if weight < 0:
                if suc_node not in D.f:
                    enabled = False
            elif weight == 0 and edge_type == STNU.ORDINARY_LABEL:
                if suc_node not in D.f:
                    enabled = False
        if enabled:
            D.enabled_tp.append(tp)

    # Line 5: If V is activation_TP for some CTP C then
    if S.node_types[V] == STNU.ACTIVATION_TP:
        # Line 6: Foreach (Y, C:-w, V) \in Edges_w (wait edges) do:
        for (X, label, weight, Y) in S.get_wait_edges():
            if Y == V:
                D.act_waits[X].append((t - weight, label))
                # logger.debug(f'Activated wait for {X} with {(t-weight, label)}')
    return D


def hce_update(S: STNU, D: RTEdata, rho: float, tau: list):
    """
    Handles contingent executions
    :param S: extended STNU
    :param D: RTE data structure
    :param rho: an execution time
    :param tau: contingent time-points to execute at rho
    :return: D: updated RTE data structure
    """
    # Line 1: for each C \in Tau do:
    for C in tau:
        # logger.debug(f'At time {rho} we will execute contingent time point {C} which is {S.translation_dict[C]}')

        # Line 2: Add (C, \rho) to D.f
        D.f[C] = rho
        logger.debug(f'Update schedule node {C} that is {S.translation_dict[C]} scheduled at {rho}')

        # Line 3: Remove C from D.U_c
        D.u_c.remove(C)

        # Line 4: Update time-windows for neighbors of C
        # TODO: maybe we can make a function because these lines also occur in update_hxe
        outgoing_edges = S.get_outgoing_edges(node_from=C, ordinary=True, uc=False, lc=False)
        for (delta, W, _, _) in outgoing_edges:
            # TW(W) = intersection of TW(W) and (-np.inf, t + delta)
            if W in D.time_windows:  # skip contingent tps
                new_lb, new_ub = intersect_intervals(D.time_windows[W].lb, D.time_windows[W].ub, -np.inf, rho + delta)
                D.time_windows[W].lb = new_lb
                D.time_windows[W].ub = new_ub
                # logger.debug(f'Update time window of {W} to [{new_lb}, {new_ub}]')

        # Line 5: Remove C-waits from all D.AcWts set
        # logger.debug(f'We should remove the C-Waits from {D.act_waits}')
        for key, value_list in D.act_waits.items():
            # Filter tuples where the second element is not 'C'
            filtered_list = [tup for tup in value_list if tup[1] != S.translation_dict[C]]
            D.act_waits[key] = filtered_list

        # Line 6: Update D.Enabled_x due to incoming negative edges to C or any deleted C-waits
        # FIXME: can we do this more efficient
        # FIXME: should we implement something additional due to deleted C-waits? how can we test this
        D.enabled_tp = []
        for tp in D.u_x:
            enabled = True
            outgoing_edges = S.get_outgoing_edges(tp)
            # FIXME: to discuss how edges with zero weight work in this algorithm (ordinary vs lowercase seems also important)
            for (weight, suc_node, edge_type, edge_label) in outgoing_edges:
                if weight < 0:
                    if suc_node not in D.f:
                        enabled = False
                elif weight == 0 and edge_type == STNU.ORDINARY_LABEL:
                    if suc_node not in D.f:
                        enabled = False
            if enabled:
                D.enabled_tp.append(tp)

    return D
