import numpy as np
import copy
import pandas as pd
import time


def random_search(n, f_eval, time_limit=200, stop_criterium="Time", budget=400,
                  printing=True, write=True, output_file="results_random_search.txt"):
    # Set-up algorithm parameters

    iteration = 1
    sequences = []
    fitnesses = []
    best_sequences = []
    best_fitnesses = []
    runtime = []

    # Start algorithm
    sequence = np.random.permutation(np.arange(n))

    # write first sequence to output file
    fitness = f_eval(sequence, iteration)
    start = time.time()
    print(f'Initial sequence is {sequence + 1} with fitness {fitness}')

    # best sequence
    best_sequence = copy.copy(sequence)
    best_fitness = fitness

    # Store data
    best_sequences.append(list(best_sequence.copy()))
    best_fitnesses.append(best_fitness)
    sequences.append(list(sequence.copy()))
    fitnesses.append(fitness)
    runtime.append(time.time() - start)
    print(f"best fitness is {best_fitness}")
    stop = False
    it = 1
    while stop == False:
        it += 1

        # Mutation: swap two items in permutation
        sequence = np.random.permutation(np.arange(n))

        # write new sequence to output file
        fitness = f_eval(sequence, it)

        if printing:
            print(f"New sequence is {sequence} with fitness {fitness}")

        # Store data
        best_sequences.append(list(best_sequence.copy()))
        best_fitnesses.append(best_fitness)
        sequences.append(list(sequence.copy()))
        fitnesses.append(fitness)
        runtime.append(time.time() - start)

        if fitness < best_fitness:
            best_sequence = copy.copy(sequence)
            best_fitness = fitness

        if printing:
            print(f'At end of iteration {it}, current sequence is {sequence}')
            print(f"Best fitness so far is {best_fitness} from sequence {best_sequence}")

        if stop_criterium == "Time":
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