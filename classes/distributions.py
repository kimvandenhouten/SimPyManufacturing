import numpy as np


class Distribution:
    def __init__(self, default):
        self.type = "DEFAULT"
        self.default = default

    def sample(self) -> float:
        return self.default


class NormalDistribution(Distribution):
    def __init__(self, mean, variance):
        self.type = "NORMAL"
        self.mean = mean
        self.variance = variance

    def sample(self):
        return np.random.normal(self.mean, self.variance, 1)[0]


class PoissonDistribution(Distribution):
    def __init__(self, alpha):
        '''
        alpha: Expected number of events occurring in a fixed-time interval, must be >= 0.
        '''
        self.type = "POISSON"
        self.alpha = alpha

    def sample(self):
        return np.random.poisson(self.alpha, 1)[0]


class ExponentialDistribution(Distribution):
    def __init__(self, beta):
        '''
        beta: SCALE parameter which is the inverse of the rate parameter (lambda)
        '''
        self.type = "EXPONENTIAL"
        self.beta = beta

    def sample(self):
        return np.random.exponential(self.beta, 1)[0]


class LogNormalDistribution(Distribution):
    def __init__(self, mean, variance):
        self.type = "LOGNORMAL"
        self.mean = mean
        self.variance = variance

    def sample(self):
        return np.random.lognormal(self.mean, self.variance, 1000)[0]


def get_distribution(dist_type, arg_dict):
    if dist_type == "NORMAL":
        return NormalDistribution(**arg_dict)
    elif dist_type == "EXPONENTIAL":
        return ExponentialDistribution(**arg_dict)
    elif dist_type == "POISSON":
        return PoissonDistribution(**arg_dict)
    elif dist_type == "LOGNORMAL":
        return LogNormalDistribution(**arg_dict)
    raise TypeError("Illegal type for distribution: ", type)
