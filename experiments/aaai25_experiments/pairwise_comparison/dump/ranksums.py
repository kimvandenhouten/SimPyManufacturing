import numpy as np
from scipy.stats import ranksums
rng = np.random.default_rng()
sample1 = rng.uniform(-1, 1, 200)
sample2 = rng.uniform(-0.5, 1.5, 300) # a shifted distribution

print(ranksums(sample1, sample2))

print(ranksums(sample1, sample2, alternative='less'))

print(ranksums(sample1, sample2, alternative='greater'))
