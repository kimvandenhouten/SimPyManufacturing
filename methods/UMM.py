from imp import reload
import numpy as np
import methods.mallows_kendall as mk
from scipy.spatial import distance
import pandas as pd
import time


def binary_search_rho(w, ratio_samples_learn, weight_mass_learn,
                      # 0 <= w_i <= 1, w is sorted increasingly,
                      rho_ini=1, rho_end=0, tol=0.001):
    w = np.asarray(w)
    assert np.all(w >= 0.0)
    assert np.all(w <= 1.0)

    # If pos is None we take the largest 4th.
    # Find the rho s.t. the largest 25%(ratio_samples) of the weights  (rho**ws) take the 0.9(weight_mass) of the total ws.  rho^w[:pos] = 0.9*rho^w
    # codes as a recursive binary search in (0,1)
    pos = int(len(w) * ratio_samples_learn)
    rho_med = (rho_ini + rho_end) / 2
    # If the interval is very narrow, just return the value.
    if abs(rho_ini - rho_end) < 1E-20:
        return rho_med

    try:
        acum = np.cumsum(rho_med ** w)
        a = acum[pos]
        b = acum[-1]
        # If b is very small, all values are equal, the value of rho does not matter. Let's return 1.0
        if b < tol:
            return 1.0
        # If the differenc eot the target weight_mass is very small, just return.
        if abs(a / b - weight_mass_learn) < tol:
            return rho_med

        if a / b > weight_mass_learn:
            mid, last = rho_ini, rho_med
        else:
            mid, last = rho_med, rho_end
        return binary_search_rho(w, ratio_samples_learn, weight_mass_learn, mid, last)
    except:  # MANUEL: How can the above fail?
        print(w)
        pos = int(len(w) * ratio_samples_learn)
        print(pos, len(w), ratio_samples_learn)
        rho_med = rho_ini + (rho_end - rho_ini) / 2
        acum = np.cumsum(rho_med ** w)
        a = acum[pos]
        b = acum[-1]
        print(
            f"binary_search_rho: a={a} b={b} a/b={a / b} wml={weight_mass_learn} rho_med={rho_med} rho_ini={rho_ini} rho_end={rho_end} w={w}")
        raise


def get_expected_distance(iterat, n, budget):
    N = (n - 1) * n / 2
    f_ini, f_end = N / 4, 1
    iter_decrease = budget - 10
    jump = (f_ini - f_end) / iter_decrease
    a = f_ini - jump * iterat
    d_min = max(a, f_end)
    d_max = d_min + 1
    return d_min


def UMM(n, f_eval, seed=1, stop_criterium="Budget", time_limit=30, budget=400,
        m_ini=10, budgetMM=10,
        ratio_samples_learn=0.1,
        weight_mass_learn=0.9, writing=True, output_file="results/UMM_results.csv"):
    np.random.seed(seed)

    it = 1
    sample = [np.random.permutation(np.arange(n)) for _ in range(m_ini)]

    fitnesses = []
    best_fitnesses = []
    best_solutions = []
    for perm in sample:
        fitnesses.append(f_eval(np.argsort(perm), it))
        it += 1
    start = time.time()
    print(fitnesses)
    best_index = fitnesses.index(min(fitnesses))
    best_sol = sample[best_index]
    best_fitness = fitnesses[best_index]
    for perm in sample:
        best_fitnesses.append(best_fitness)
        best_solutions.append(best_sol)

    # ['rho','phi_estim','phi_sample','Distance']
    res = [[np.nan, np.nan, np.nan,
            mk.kendallTau(perm, best_sol) / (n * (n - 1) * 0.5)] for perm in sample]
    m= 0
    stop=False
    while not stop:
        ws = np.asarray(fitnesses).copy()
        # FIXME: For maximization, this need to be changed.
        ws = ws - ws.min()
        # FIXME: Handle if ws.max() == 0.
        ws = ws / ws.max()
        co = ws.copy()
        co.sort()

        rho = binary_search_rho(co, ratio_samples_learn, weight_mass_learn)
        # print(fitnesses)
        # print(ws)
        ws = rho ** ws  # MINIMIZE
        # print(ws)
        # ws = rho ** (1-ws) #MAXIMIZE
        # print(ws,co[:int(len(co)/4)].sum(),co.sum())

        borda = mk.uborda(np.array(sample), ws)
        phi_estim = mk.u_phi(sample, borda, ws)
        expected_dist = get_expected_distance(m, n, budget)
        phi_sample = mk.find_phi(n, expected_dist, expected_dist + 1)
        perms = mk.samplingMM(budgetMM, n, phi=phi_sample, k=None)
        # perm = perm[borda]
        # Transforms from sampling space to Borda space.
        perms = [perm[borda] for perm in perms]
        dists = distance.cdist(perms, sample, metric=mk.kendallTau)
        # MANUEL: We probably do not need to sort, just find the min per axis=1.
        dists = np.sort(dists, axis=1)
        indi = np.argmax(dists[:,
                         0])  # index of the perm with the farthest closest permutation. Maximizes the min dist to the sample
        perm = perms[indi]

        # FIXME: This should already be an array of int type.
        perm = np.asarray(perm, dtype='int')
        sample.append(perm)
        fitnesses.append(f_eval(np.argsort(perm), it))
        it += 1
        best_index = fitnesses.index(min(fitnesses))
        best_sol = sample[best_index]
        best_fitness = fitnesses[best_index]
        best_fitnesses.append(best_fitness)
        best_solutions.append(best_sol)
        # print(f'New fitness is {f_eval(perm)} in iteration {m}')
        print(f"UMM: eval={m}\tF={fitnesses[-1]}\tbest_known={best_fitness}")
        # print(fitnesses,ws)

        # This is only used for reporting stats.
        res.append([rho, phi_estim, phi_sample, mk.kendallTau(borda, best_sol) / (n * (n - 1) * 0.5)])

        m+=1
        if stop_criterium == "Time":
            if time.time() - start >= time_limit:
                print("Stop because of time")
                print(f"Final best sequence so far is {best_sol}, with fitness {best_fitness}")
                stop = True
        else:
            if it > budget:
                print("Stop because of budget")
                print(f"Final best sequence so far is {best_sol}, with fitness {best_fitness}")
                stop = True
    df = pd.DataFrame(res, columns=['rho', 'phi_estim', 'phi_sample', 'Distance'])

    df['Sequence'] = sample
    df['Fitness'] = fitnesses
    df['Best_sequence'] = best_solutions
    df['Best_fitness'] = best_fitnesses
    df['m_ini'] = m_ini
    df['seed'] = seed
    df['budget'] = budget
    df['budgetMM'] = budgetMM
    df['ratio_samples_learn'] = ratio_samples_learn
    df['weight_mass_learn'] = weight_mass_learn
    if writing:
        df.to_csv(output_file)
    return it - 1, best_sol
