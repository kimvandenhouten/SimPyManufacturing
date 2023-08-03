import copy
import random
import numpy as np
import time
import pandas as pd


def best_insert(x, item, count_eval, f_eval):
    print("Start best insert")
    best_insert_x = np.insert(x, 0, item)
    best_insert_fitness = f_eval(best_insert_x, count_eval)
    count_eval += 1
    for k in range(1, len(x) - 1):
        test_x = np.insert(x, k, item)
        test_fitness = f_eval(test_x, count_eval)
        count_eval += 1
        if test_fitness < best_insert_fitness:
            best_insert_fitness = test_fitness
            best_insert_x = test_x
    return best_insert_x, best_insert_fitness, count_eval


def IterativeImprovementInsertion(x, fitness_x, count_eval, f_eval, budget=1000):
    print("Start iterated improvement")
    n = len(x)
    improve = True
    stop_loop = False
    while improve:
        improve = False
        indices = [i for i in range(0, n-1)]
        np.random.shuffle(indices)
        print(indices)
        for i in indices:
            item = x[i]
            y = np.delete(x, i)
            best_insert_x = np.insert(y, 0, item)
            best_insert_fitness = f_eval(best_insert_x, count_eval)
            count_eval += 1
            for k in range(1, n-2):
                test_x = np.insert(y, k, item)
                test_fitness = f_eval(test_x, count_eval)
                count_eval += 1
                if test_fitness < best_insert_fitness:
                    best_insert_fitness = copy.copy(test_fitness)
                    best_insert_x = copy.copy(test_x)

                if count_eval >= budget:
                    stop_loop = True
                    break

            if best_insert_fitness < fitness_x:
                fitness_x = copy.copy(best_insert_fitness)
                x = copy.copy(best_insert_x)
                improve = True

            if stop_loop:
                break

    return x, fitness_x, count_eval


def iterated_greedy(n, f_eval, d=7, seed=1, time_limit=200, output_file="results_random_search.txt", printing=True,
                     write=True, stop_criterium="Time", budget=400, init=None):
    random.seed(seed)
    np.random.seed(seed)
    count_eval = 1
    sequences = []
    fitnesses = []
    best_sequences = []
    best_fitnesses = []
    runtime = []
    count_evaluations = []

    # Start algorithm
    if init is None:
        x = np.random.permutation(np.arange(n))
    else:
        x = copy.copy(init)
    fitness_x = f_eval(x, count_eval)
    count_eval += 1

    # Save results
    start = time.time()
    x_best = copy.copy(x)
    fitness_best = copy.copy(fitness_x)
    print(f'First sequence is {x} with fitness {fitness_x}')
    sequences.append(x)
    runtime.append(time.time() - start)
    fitnesses.append(fitness_x)
    best_sequences.append(x_best)
    best_fitnesses.append(fitness_best)
    count_evaluations.append(count_eval)
    stop = False

    # First iterative improvement
    x, fitness_x, count_eval = IterativeImprovementInsertion(x, fitness_x, count_eval, f_eval, budget=budget)

    # Save results
    if fitness_x < fitness_best:
        x_best = copy.copy(x)
        fitness_best = copy.copy(fitness_x)

    print(f'After first IterativeImprovement, sequence is {x} with fitness {fitness_x}')
    print("Best so far", x_best, fitness_best)

    sequences.append(list(x))
    runtime.append(time.time() - start)
    fitnesses.append(fitness_x)
    best_sequences.append(list(x_best))
    best_fitnesses.append(fitness_best)
    count_evaluations.append(count_eval)

    if stop_criterium == "Time":
        if time.time() - start >= time_limit:
            print(f"Stop because of time")
            stop = True
    elif count_eval > budget:
        print(f"Stop because of budget")
        stop = True

    while not stop:
        x_ = copy.copy(x)

        # destruction phase
        to_remove_idx = np.random.choice(range(0, n), d, replace=False)
        print(f'alternative to remove_idx {to_remove_idx}')
        to_remove_items = x_[to_remove_idx]
        x_ = np.delete(x_, to_remove_idx)

        # construction phase
        for j in range(0, d):
            item = to_remove_items[j]
            x_, fitness_x_, count_eval = best_insert(x_, item, count_eval, f_eval)
        print("After construction", x_, fitness_x_, len(x_))

        if stop_criterium == "Time":
            if time.time() - start >= time_limit:
                print("Stop because of time")
                stop = True
        elif count_eval > budget:
            print(f"Stop because of budget")
            stop = True

        if stop:
            if fitness_x_ < fitness_x:
                x = copy.copy(x_)
                fitness_x = copy.copy(fitness_x_)
                if fitness_x < fitness_best:
                    x_best = copy.copy(x)
                    fitness_best = copy.copy(fitness_x)

        else:
            x_, fitness_x_, count_eval = IterativeImprovementInsertion(x_, fitness_x_, count_eval, f_eval, budget=budget)
            if fitness_x_ < fitness_x:
                x = copy.copy(x_)
                fitness_x = copy.copy(fitness_x_)
                if fitness_x < fitness_best:
                    x_best = copy.copy(x)
                    fitness_best = copy.copy(fitness_x)

        sequences.append(list(x))
        runtime.append(time.time() - start)
        fitnesses.append(fitness_x)
        best_sequences.append(list(x_best))
        best_fitnesses.append(fitness_best)
        count_evaluations.append(count_eval)
        print("Best so far", x_best, fitness_best, count_eval)

        if stop_criterium == "Time":
            if time.time() - start >= time_limit:
                print(f"Stop because of time")
                stop = True
        elif count_eval > budget:
            print(f"Stop because of budget")
            stop = True

    if write:
        results = pd.DataFrame()
        results['Time'] = runtime
        results['Fitness'] = fitnesses
        results['Sequence'] = sequences
        results['Best_sequence'] = best_sequences
        results['Best_fitness'] = best_fitnesses
        results["Number of evaluations"] = count_evaluations
        print("Total number of fitness evaluations", count_eval)
        results.to_csv(output_file, header=True, index=False)

    return count_eval - 1, x_best