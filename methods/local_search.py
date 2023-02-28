import numpy as np
import copy
import random
import pandas as pd
import time


def swap_random(sequence):
    seq = copy.copy(sequence)
    i1, i2 = np.random.randint(0, len(seq), 2)
    seq[i1], seq[i2] = seq[i2], seq[i1]
    return seq


def local_search(n, f_eval, time_limit=200, stop_criterium="Time", budget=400,
                 output_file="results_local_search.txt", printing=True, write=True, init=None):
    # Initialize
    iteration = 1
    sequences = []
    fitnesses = []
    best_sequences = []
    best_fitnesses = []
    runtime = []

    # Start algorithm
    if init is None:
        sequence = np.random.permutation(np.arange(n))
        print(sequence)
    else:
        sequence = copy.copy(init)
    # Write first sequence to output file
    fitness = f_eval(sequence, iteration)
    start = time.time()
    print(f'Initial fitness is {fitness}')
    print(f'Initial sequence is {sequence}')
    # best sequence
    best_sequence = copy.copy(sequence)
    best_fitness = copy.copy(fitness)
    print(f"best fitness is {best_fitness}")
    sequences.append(list(sequence.copy()))
    fitnesses.append(fitness)
    best_sequences.append(list(best_sequence.copy()))
    best_fitnesses.append(best_fitness)
    runtime.append(time.time() - start)

    stop = False

    it = 1
    while not stop:
        it += 1
        # Mutation: swap two items in permutation
        candidate_sequence = swap_random(sequence)

        # write new sequence to output file
        candidate_fitness = f_eval(candidate_sequence, it)
        if printing:
            print(f"Candidate fitness {candidate_fitness}")

        sequences.append(list(sequence.copy()))
        fitnesses.append(fitness)
        best_sequences.append(list(best_sequence.copy()))
        best_fitnesses.append(best_fitness)
        runtime.append(time.time() - start)

        # accept / reject
        if candidate_fitness < fitness:
            sequence = copy.copy(candidate_sequence)
            fitness = copy.copy(candidate_fitness)
            if printing:
                print("Solution is accepted")

            if fitness < best_fitness:
                best_sequence = copy.copy(sequence)
                best_fitness = candidate_fitness

        else:
            if printing:
                print("Solution is rejected")

        if printing:
            print(f"Best sequence so far has fitness {best_fitness}")

        if stop_criterium=="Time":
            if time.time() - start >= time_limit:
                print(f"Final best sequence so far is {best_sequence}, with fitness {best_fitness}")
                stop = True
        elif it > budget:
            print(f"Final best sequence so far is {best_sequence}, with fitness {best_fitness}")
            stop = True

    results = pd.DataFrame()
    results['Sequence'] = sequences
    results['Fitness'] = fitnesses
    results['Best_sequence'] = best_sequences
    results['Best_fitness'] = best_fitnesses
    results['Time'] = runtime
    if write:
        results.to_csv(output_file, header=True, index=False)

    return it, best_sequence