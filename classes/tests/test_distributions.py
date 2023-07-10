import unittest

from classes.distributions import NormalDistribution, PoissonDistribution, ExponentialDistribution, Distribution


class TestDistribution(unittest.TestCase):
    def test_normal_distribution(self):
        mean = 5
        var = 0.1
        normal_distr = NormalDistribution(mean, var)
        sample = normal_distr.sample()
        self.assertNotEqual(sample, None)

    def test_poisson_distribution(self):
        alpha = 3
        pois_distr = PoissonDistribution(alpha)
        sample = pois_distr.sample()
        self.assertNotEqual(sample, None)  # add assertion here

    def test_exponential_distribution(self):
        alpha = 3
        exp_distr = ExponentialDistribution(alpha)
        sample = exp_distr.sample()
        self.assertNotEqual(sample, None)  # add assertion here

    def test_default_distribution(self):
        default_value = 3
        default_distr = Distribution(default_value)
        sample = default_distr.sample()
        self.assertNotEqual(sample, None)  # add assertion here
        self.assertEqual(sample, default_value)  # add assertion here



if __name__ == '__main__':
    unittest.main()
