import classes.general
from classes.stnu import STNU, Edge

logger = classes.general.get_logger()


class RTEdata:
    def __init__(self, u_x, u_c, enabled_x, now):
        self.u_x = u_x
        self.u_c = u_c
        self.enabled_x = enabled_x
        self.now = now
        # TODO: initialize time-windows for all u_x
        # TODO: initialize activated waits for all u_x


class RTEdecision:
    def __init__(self, x, t):
        self.x = x  # the executable time point
        self.t = t  # the time point at which x will is determined to be executed
        # TODO: implement wait decision


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
    # Line 1: First inialitize the data structure with RTE_init(T_x, T_c)
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
    # Line 1: If D.enabled_x is empty:
    # Line 2: return wait
    # Line 3: For each x \in D.enabled_x:
    # Line 4: Find maximum wait for X
    # Line 5: Find greatest lower bound for X
    # Line 6: Find earliest possible next execution: t_l
    # Line 7: Find latest possible next execution: t_u
    # Line 8: If the intersection from [t_l, t_u] and [now, inf] is empty
    # Line 9: Return fail
    # Line 10: Select any point V \in D.enabled_x for which the intersection is not empty
    # Line 11: Select any point t \in ...
    # Line 12: Return (t,V)


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
    # Line 2: Return fail
    # Line 3: If delta = wait, or delta = (t,V) and rho < t:
    # Line 4: D = HCE(S, D, rho, tau)
    # Line 5: Else
    # Line 6: D = HXE(S, D, t, V)
    # Line 7: If tau = empty set
    # Line 8: HCE(S, D, t, tau)
    # Line 9: Update D.now = rho
    # Line 10: Return D


def hce_update(S: STNU, D: RTEdata, rho, tau):
    """
    Handles contingent executions
    :param S: extended STNU
    :param D: RTE data structure
    :param rho: an execution time
    :param tau: contingent time-points to execute at rho
    :return: D: updated RTE data structure
    """
    # Line 1: for each C \in Tau do:
    # Line 2: Add (C, \rho) to D.f
    # Line 3: Remove C from D.U_c
    # Line 4: Update time-windows for neighbors of C
    # Line 5: Remove C-waits from all D.AcWts set
    # Line 6: Update D.Enabled_x due to incoming negative edges to C or any deleted C-waits


def hxe_update(S: STNU, D: RTEdata, rho, tau):
    """
    Handles non-contingent executions
    :param S: extended STNU
    :param D: RTE data structure
    :param rho: an execution time
    :param tau: contingent time-points to execute at rho
    :return: D: updated RTE data structure
    """
    # Line 1: Add (V, t) to D.f
    # Line 2: Add (C, rho) to D.f
    # Line 3: Update time windows for neighbors of V
    # Line 4: Update D.Enabled_x due to any negative incoming edges to V
    # Line 5: If V is activation_TP for some CTP C then
    # Line 6: Foreach (Y, C:-w, V) \in Edges_w (wait edges) do:
    # Line 7: Insert (t+w, C) into D.AcWts(Y)
