import numpy as np


class Distribution:
    def __init__(self, PROCESSING_TIME):
        self.DEFAULT = PROCESSING_TIME

    def sample(self) -> float:
        return self.DEFAULT


class NormalDistribution(Distribution):
    def __init__(self, MEAN, VARIANCE):
        self.MEAN = MEAN
        self.VARIANCE = VARIANCE

    def sample(self):
        return np.random.normal(self.MEAN, self.VARIANCE, 1)[0]


class PoissonDistribution(Distribution):
    def __init__(self, ALPHA):
        '''
        ALPHA: Expected number of events occurring in a fixed-time interval, must be >= 0.
        '''
        self.ALPHA = ALPHA

    def sample(self):
        return np.random.poisson(self.ALPHA, 1)[0]


class ExponentialDistribution(Distribution):
    def __init__(self, BETA):
        '''
        BETA: SCALE parameter which is the inverse of the rate parameter (lambda)
        '''
        self.BETA = BETA

    def sample(self):
        return np.random.exponential(self.BETA, 1)[0]


def get_distribution(dist_type, arg_dict):
    if dist_type == "NORMAL":
        return NormalDistribution(**arg_dict)
    elif dist_type == "EXPONENTIAL":
        return ExponentialDistribution(**arg_dict)
    elif dist_type == "POISSON":
        return PoissonDistribution(**arg_dict)
    raise TypeError("Illegal type for distribution: ", type)
