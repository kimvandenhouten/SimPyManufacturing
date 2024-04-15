import classes.general
from classes.stnu import STNU, Edge
import numpy as np
import random
import typing
logger = classes.general.get_logger()


def intersect_intervals(a, b, c, d):
    x = max(a, c)
    y = min(b, d)

    if x > y:
        return False
    else:
        return x, y

class TimeWindow:
    def __init__(self, x, lb=0, ub=np.inf):
        self.x = x
        self.lb = lb
        self.ub = ub

class RTEdata:
    def __init__(self, u_x=[], u_c=[], enabled_x=[], now=0):
        self.u_x = u_x
        self.u_c = u_c
        self.enabled_tp = enabled_x  # the enabled timepoints
        self.now = now  # the current time, initialized at 0
        self.f = {}  # variable assignments (schedule)
        self.time_windows = {}
        self.act_waits = {}
        # TODO: initialize time-windows for all u_x
        # TODO: initialize activated waits for all u_x

    @classmethod
    def from_estnu(cls, estnu: STNU) -> 'RTEdata':
        # Obtain executable and contingent timepoints from the estnu
        u_x = estnu.get_executable_time_points()
        u_c = estnu.get_contingent_time_points()
        rte_data = RTEdata(u_x=u_x, u_c=u_c)

        # Initialize enable timepoints
        for tp in u_x:
            enabled = True
            outgoing_edges = estnu.get_outgoing_edges(tp)
            for (weight, suc_node, edge_type, edge_label) in outgoing_edges:
                if weight < 0:
                    if suc_node not in rte_data.f:
                        enabled = False
            if enabled:
                rte_data.enabled_tp.append(tp)

            # Initialize time windows
            rte_data.time_windows[tp] = TimeWindow(x=tp)

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


def rte_stnu(estnu: STNU):
    """
    This procedure should run the RTE^* algorithm such as described in Hunsberger'2024 article "Foundations of
    Dispatchability for Simple Temporal Networks with Uncertainty"
    :param estnu: extended stnu
    :return: function (T_x union T_c -> R) which is the schedule, or False
    """
    # Line 1: First initialise the data structure with RTE_init(T_x, T_c)
    # Line 2: While both U_x (unexecuted executable timepoints) and U_c (unexecuted contingent timepoints) are non-empty
    # Line 3: Generate exec. decision (use rte_generate_decision)
    # Line 4: If decision returns fail
    # Line 5: Return fail
    # Line 6: (rho, tau) = Observe contingent timepoints
    # Line 7: Update RTE data structure
    # Line 8: If D=fail
    # Line 8: return fail
    return True


def rte_generate_decision(D: RTEdata):
    """
    computes the next RTED for one iteration of the RTE* algorithm
    :param d: RTEdata structure
    :return: Eec decs: Wait or (t, V); or fail
    """
    #logger.debug(f'Enabled timepoints are: {D.enabled_tp}')
    # Line 1: If D.enabled_x is empty:
    if len(D.enabled_tp) == 0:
        # Line 2: return wait
        logger.debug('Decision is wait')
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
    t_l = glb[min(glb)]
    # Line 7: Find latest possible next execution: t_u
    t_u = ub[max(ub)]

    # Line 8: If the intersection from [t_l, t_u] and [now, inf] is empty
    if t_u < D.now or np.inf < t_l:
        # Line 9: Return fail
        logger.debug('Decision is fail')
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
        logger.debug(f'Decision is (V,t) {(found_v,t)}')
        delta = RTEdecision(x=found_v, t=t)
        return delta


def rte_oracle():
    """
    This represents the real time feedback from the system
    :return: (t_c, t) where t_c is the contingent time-points, and t is the time
    """
    # Option 1:
    # return (t_c, t) where t_c is the time of observation, and t is the non-empty set of timepoints
    # return (t, empty set) where t is the time, and the empty set is returned
    # return (inf, empty set) where we wait forever but there are no possible contingent executions


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
        return "Fail"

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
            #logger.debug(f'Update time window of {W} to [{new_lb}, {new_ub}]')

    # for incoming edges (U, gamma, V)
    incoming_edges = S.get_incoming_edges(node_to=V, ordinary=True, uc=False, lc=False)
    for (gamma, U, _, _) in incoming_edges:
        # TW(U) = intersection of TW(U) and [t-gamma, np.inf)
        if U in D.time_windows:
            new_lb, new_ub = intersect_intervals(D.time_windows[U].lb, D.time_windows[U].ub, t - gamma, np.inf)
            D.time_windows[U].lb = new_lb
            D.time_windows[U].ub = new_ub
            #logger.debug(f'Update time window of {U} to [{new_lb}, {new_ub}]')

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
                #logger.debug(f'Activated wait for {X} with {(t-weight, label)}')
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
        #logger.debug(f'At time {rho} we will execute contingent time point {C} which is {S.translation_dict[C]}')

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
                #logger.debug(f'Update time window of {W} to [{new_lb}, {new_ub}]')

        # Line 5: Remove C-waits from all D.AcWts set
        #logger.debug(f'We should remove the C-Waits from {D.act_waits}')
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



