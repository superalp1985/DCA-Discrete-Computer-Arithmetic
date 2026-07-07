#!/usr/bin/env python3
"""
DCA Chapter 7: Discrete Probability Theory - Complete Verification Code
Author: Wang Bingqin
Date: 2026-07-06

This module implements and verifies:
- Finite probability spaces with rational weights
- Probability distributions (Bernoulli, Binomial, Geometric, Poisson)
- Expected value and variance computation
- Conditional probability and Bayes' theorem
- Discrete Markov chains
- Random sampling and verification
"""

import random
import time
from fractions import Fraction
from typing import List, Tuple, Dict, Callable, Optional
from collections import Counter


class FiniteProbabilitySpace:
    """Finite probability space with rational weights"""

    def __init__(self, sample_space: List, probabilities: Optional[List[Fraction]] = None):
        """
        Initialize finite probability space

        Args:
            sample_space: List of possible outcomes
            probabilities: List of probabilities (as Fractions). If None, use uniform distribution
        """
        self.sample_space = sample_space

        if probabilities is None:
            # Uniform distribution
            self.probabilities = [Fraction(1, len(sample_space))] * len(sample_space)
        else:
            self.probabilities = probabilities

        # Validate probabilities sum to 1
        total = sum(self.probabilities, Fraction(0))
        if total != 1:
            raise ValueError(f"Probabilities must sum to 1, got {total}")

    def probability(self, event: Callable) -> Fraction:
        """
        Compute probability of an event

        Args:
            event: Predicate function that returns True for outcomes in the event

        Returns:
            Probability of the event
        """
        prob = Fraction(0)
        for outcome, p in zip(self.sample_space, self.probabilities):
            if event(outcome):
                prob += p
        return prob

    def conditional_probability(self, event_a: Callable, event_b: Callable) -> Fraction:
        """
        Compute P(A|B) = P(A∩B) / P(B)

        Args:
            event_a: Condition A predicate
            event_b: Condition B predicate

        Returns:
            Conditional probability P(A|B)
        """
        prob_b = self.probability(event_b)
        if prob_b == 0:
            raise ValueError("Cannot condition on event with probability 0")

        prob_ab = Fraction(0)
        for outcome, p in zip(self.sample_space, self.probabilities):
            if event_a(outcome) and event_b(outcome):
                prob_ab += p

        return prob_ab / prob_b

    def expected_value(self, random_variable: Callable) -> Fraction:
        """
        Compute E[X] = Σ X(ω) * P(ω)

        Args:
            random_variable: Function mapping outcomes to numeric values

        Returns:
            Expected value
        """
        expected = Fraction(0)
        for outcome, p in zip(self.sample_space, self.probabilities):
            expected += Fraction(random_variable(outcome)) * p
        return expected

    def variance(self, random_variable: Callable) -> Fraction:
        """
        Compute Var(X) = E[X²] - E[X]²

        Args:
            random_variable: Function mapping outcomes to numeric values

        Returns:
            Variance
        """
        e_x = self.expected_value(random_variable)
        e_x2 = self.expected_value(lambda o: random_variable(o) ** 2)
        return e_x2 - e_x * e_x

    def sample(self, n: int = 1) -> List:
        """
        Sample n outcomes from the probability space

        Args:
            n: Number of samples

        Returns:
            List of sampled outcomes
        """
        # Convert probabilities to cumulative distribution
        cum_prob = []
        total = Fraction(0)
        for p in self.probabilities:
            total += p
            cum_prob.append(total)

        samples = []
        for _ in range(n):
            r = random.random()
            # Find the outcome
            for i, cp in enumerate(cum_prob):
                if r < float(cp):
                    samples.append(self.sample_space[i])
                    break

        return samples


class DiscreteDistribution:
    """Base class for discrete probability distributions"""

    def pmf(self, x: int) -> Fraction:
        """Probability mass function"""
        raise NotImplementedError

    def cdf(self, x: int) -> Fraction:
        """Cumulative distribution function"""
        raise NotImplementedError

    def expected_value(self) -> Fraction:
        """Expected value"""
        raise NotImplementedError

    def variance(self) -> Fraction:
        """Variance"""
        raise NotImplementedError

    def sample(self, n: int = 1) -> List[int]:
        """Generate random samples"""
        raise NotImplementedError


class BernoulliDistribution(DiscreteDistribution):
    """Bernoulli distribution: P(X=1) = p, P(X=0) = 1-p"""

    def __init__(self, p: Fraction):
        if not (0 <= p <= 1):
            raise ValueError("Probability must be between 0 and 1")
        self.p = p

    def pmf(self, x: int) -> Fraction:
        if x == 1:
            return self.p
        elif x == 0:
            return 1 - self.p
        else:
            return Fraction(0)

    def cdf(self, x: int) -> Fraction:
        if x < 0:
            return Fraction(0)
        elif x < 1:
            return 1 - self.p
        else:
            return Fraction(1)

    def expected_value(self) -> Fraction:
        return self.p

    def variance(self) -> Fraction:
        return self.p * (1 - self.p)

    def sample(self, n: int = 1) -> List[int]:
        return [1 if random.random() < float(self.p) else 0 for _ in range(n)]


class BinomialDistribution(DiscreteDistribution):
    """Binomial distribution: number of successes in n trials"""

    def __init__(self, n: int, p: Fraction):
        if n < 0:
            raise ValueError("Number of trials must be non-negative")
        if not (0 <= p <= 1):
            raise ValueError("Probability must be between 0 and 1")
        self.n = n
        self.p = p
        self.q = 1 - p

    def pmf(self, k: int) -> Fraction:
        if not (0 <= k <= self.n):
            return Fraction(0)

        # C(n, k) * p^k * (1-p)^(n-k)
        from math import comb
        return Fraction(comb(self.n, k)) * (self.p ** k) * (self.q ** (self.n - k))

    def cdf(self, x: int) -> Fraction:
        if x < 0:
            return Fraction(0)
        if x >= self.n:
            return Fraction(1)

        total = Fraction(0)
        for k in range(x + 1):
            total += self.pmf(k)
        return total

    def expected_value(self) -> Fraction:
        return self.n * self.p

    def variance(self) -> Fraction:
        return self.n * self.p * self.q

    def sample(self, n_samples: int = 1) -> List[int]:
        # Use sum of Bernoulli samples
        samples = []
        for _ in range(n_samples):
            successes = 0
            for _ in range(self.n):
                if random.random() < float(self.p):
                    successes += 1
            samples.append(successes)
        return samples


class GeometricDistribution(DiscreteDistribution):
    """Geometric distribution: number of trials until first success"""

    def __init__(self, p: Fraction):
        if not (0 < p <= 1):
            raise ValueError("Probability must be between 0 and 1")
        self.p = p
        self.q = 1 - p

    def pmf(self, k: int) -> Fraction:
        if k < 1:
            return Fraction(0)
        return self.q ** (k - 1) * self.p

    def cdf(self, x: int) -> Fraction:
        if x < 1:
            return Fraction(0)
        # P(X ≤ x) = 1 - (1-p)^x
        return 1 - self.q ** x

    def expected_value(self) -> Fraction:
        return Fraction(1, self.p)

    def variance(self) -> Fraction:
        return self.q / (self.p ** 2)

    def sample(self, n: int = 1) -> List[int]:
        samples = []
        for _ in range(n):
            trials = 1
            while random.random() >= float(self.p):
                trials += 1
            samples.append(trials)
        return samples


class PoissonDistribution(DiscreteDistribution):
    """Poisson distribution: P(X=k) = λ^k * e^(-λ) / k!"""

    def __init__(self, lambda_param: Fraction):
        if lambda_param <= 0:
            raise ValueError("Lambda must be positive")
        self.lam = lambda_param

    def pmf(self, k: int) -> Fraction:
        if k < 0:
            return Fraction(0)

        # λ^k / k! * e^(-λ)
        from math import factorial, exp
        return Fraction(self.lam ** k) / Fraction(factorial(k)) * Fraction(exp(-float(self.lam)))

    def cdf(self, x: int) -> Fraction:
        if x < 0:
            return Fraction(0)

        total = Fraction(0)
        for k in range(x + 1):
            total += self.pmf(k)
        return total

    def expected_value(self) -> Fraction:
        return self.lam

    def variance(self) -> Fraction:
        return self.lam

    def sample(self, n: int = 1) -> List[int]:
        # Knuth's algorithm
        samples = []
        for _ in range(n):
            k = 0
            p = 1
            L = float(self.lam)
            while True:
                k += 1
                p *= random.random()
                if p < math.exp(-L):
                    break
            samples.append(k - 1)
        return samples


import math


class DiscreteMarkovChain:
    """Discrete-time Markov chain with finite state space"""

    def __init__(self, transition_matrix: List[List[Fraction]], states: Optional[List] = None):
        """
        Initialize Markov chain

        Args:
            transition_matrix: Square matrix where P[i][j] = P(X_{t+1}=j | X_t=i)
            states: Optional list of state labels
        """
        self.n_states = len(transition_matrix)

        # Validate transition matrix
        for row in transition_matrix:
            if len(row) != self.n_states:
                raise ValueError("Transition matrix must be square")
            if sum(row, Fraction(0)) != 1:
                raise ValueError("Each row must sum to 1")

        self.transition_matrix = transition_matrix
        self.states = states if states else list(range(self.n_states))

    def transition_probability(self, i: int, j: int, steps: int = 1) -> Fraction:
        """
        Compute P(X_{t+steps}=j | X_t=i)

        Args:
            i: Starting state
            j: Ending state
            steps: Number of steps

        Returns:
            Transition probability
        """
        if steps == 1:
            return self.transition_matrix[i][j]

        # Compute P^steps
        result = self._matrix_power(self.transition_matrix, steps)
        return result[i][j]

    def _matrix_power(self, matrix: List[List[Fraction]], power: int) -> List[List[Fraction]]:
        """Compute matrix power using binary exponentiation"""
        if power == 0:
            # Return identity matrix
            return [[Fraction(int(i == j)) for j in range(self.n_states)]
                    for i in range(self.n_states)]

        if power == 1:
            return matrix

        if power % 2 == 0:
            half = self._matrix_power(matrix, power // 2)
            return self._matrix_multiply(half, half)
        else:
            return self._matrix_multiply(matrix, self._matrix_power(matrix, power - 1))

    def _matrix_multiply(self, A: List[List[Fraction]], B: List[List[Fraction]]) -> List[List[Fraction]]:
        """Multiply two matrices"""
        n = len(A)
        result = [[Fraction(0) for _ in range(n)] for _ in range(n)]

        for i in range(n):
            for j in range(n):
                for k in range(n):
                    result[i][j] += A[i][k] * B[k][j]

        return result

    def stationary_distribution(self, max_iter: int = 1000, tol: Fraction = Fraction(1, 1000000)) -> Optional[List[Fraction]]:
        """
        Compute stationary distribution using power iteration

        Returns:
            Stationary distribution π where πP = π
        """
        # Start with uniform distribution
        pi = [Fraction(1, self.n_states) for _ in range(self.n_states)]

        for _ in range(max_iter):
            pi_new = [Fraction(0) for _ in range(self.n_states)]

            # π_new[j] = Σ_i π[i] * P[i][j]
            for j in range(self.n_states):
                for i in range(self.n_states):
                    pi_new[j] += pi[i] * self.transition_matrix[i][j]

            # Check convergence
            max_diff = max(abs(pi_new[j] - pi[j]) for j in range(self.n_states))
            if max_diff < tol:
                return pi_new

            pi = pi_new

        return None  # Did not converge

    def sample_path(self, initial_state: int, length: int) -> List[int]:
        """
        Sample a path of given length starting from initial_state

        Args:
            initial_state: Starting state
            length: Length of the path

        Returns:
            List of states
        """
        path = [initial_state]
        current = initial_state

        for _ in range(length - 1):
            # Sample next state based on transition probabilities
            r = random.random()
            cum_prob = 0.0

            for next_state in range(self.n_states):
                cum_prob += float(self.transition_matrix[current][next_state])
                if r < cum_prob:
                    current = next_state
                    break

            path.append(current)

        return path


def test_finite_probability_space() -> Dict:
    """Test finite probability space operations"""
    print("Testing finite probability space...")

    results = {
        "probability_axioms": {"passed": 0, "failed": 0},
        "conditional_probability": {"passed": 0, "failed": 0},
        "expected_value": {"passed": 0, "failed": 0},
        "variance": {"passed": 0, "failed": 0},
    }

    # Test 1: Probability axioms
    # Create a simple die roll
    die = FiniteProbabilitySpace(list(range(1, 7)))

    # P(any outcome) should sum to 1
    total_prob = sum(die.probability(lambda x: x == i) for i in range(1, 7))
    if total_prob == 1:
        results["probability_axioms"]["passed"] += 1
    else:
        results["probability_axioms"]["failed"] += 1
        print(f"  FAILED: Probability axiom - total prob = {total_prob}")

    # Test 2: Conditional probability (Bayes' theorem)
    # P(even | > 3) should equal P(> 3 | even) * P(even) / P(> 3)
    p_even = die.probability(lambda x: x % 2 == 0)
    p_gt3 = die.probability(lambda x: x > 3)
    p_even_and_gt3 = die.probability(lambda x: x % 2 == 0 and x > 3)

    p_even_given_gt3 = die.conditional_probability(lambda x: x % 2 == 0, lambda x: x > 3)
    p_gt3_given_even = die.conditional_probability(lambda x: x > 3, lambda x: x % 2 == 0)

    # Bayes' theorem: P(A|B) = P(B|A) * P(A) / P(B)
    bayes_rhs = p_gt3_given_even * p_even / p_gt3

    if p_even_given_gt3 == bayes_rhs:
        results["conditional_probability"]["passed"] += 1
    else:
        results["conditional_probability"]["failed"] += 1
        print(f"  FAILED: Bayes' theorem - {p_even_given_gt3} != {bayes_rhs}")

    # Test 3: Expected value
    # For fair die, E[X] = 3.5
    e_x = die.expected_value(lambda x: x)
    if e_x == Fraction(7, 2):
        results["expected_value"]["passed"] += 1
    else:
        results["expected_value"]["failed"] += 1
        print(f"  FAILED: Expected value - got {e_x}, expected 7/2")

    # Test 4: Variance
    # For fair die, Var(X) = E[X²] - E[X]² = 91/6 - 49/4 = 35/12
    var_x = die.variance(lambda x: x)
    expected_var = Fraction(35, 12)
    if var_x == expected_var:
        results["variance"]["passed"] += 1
    else:
        results["variance"]["failed"] += 1
        print(f"  FAILED: Variance - got {var_x}, expected {expected_var}")

    # Print summary
    for test_name, result in results.items():
        total = result["passed"] + result["failed"]
        print(f"  {test_name}: {result['passed']}/{total}")

    return results


def test_distributions() -> Dict:
    """Test various probability distributions"""
    print("Testing probability distributions...")

    results = {
        "bernoulli": {"passed": 0, "failed": 0},
        "binomial": {"passed": 0, "failed": 0},
        "geometric": {"passed": 0, "failed": 0},
        "poisson": {"passed": 0, "failed": 0},
    }

    # Test Bernoulli
    p = Fraction(3, 7)
    bernoulli = BernoulliDistribution(p)

    # Check PMF sums to 1
    if bernoulli.pmf(0) + bernoulli.pmf(1) == 1:
        results["bernoulli"]["passed"] += 1
    else:
        results["bernoulli"]["failed"] += 1
        print(f"  FAILED: Bernoulli PMF doesn't sum to 1")

    # Check expected value
    if bernoulli.expected_value() == p:
        results["bernoulli"]["passed"] += 1
    else:
        results["bernoulli"]["failed"] += 1
        print(f"  FAILED: Bernoulli expected value")

    # Check variance
    if bernoulli.variance() == p * (1 - p):
        results["bernoulli"]["passed"] += 1
    else:
        results["bernoulli"]["failed"] += 1
        print(f"  FAILED: Bernoulli variance")

    # Test Binomial
    n, p = 10, Fraction(1, 2)
    binomial = BinomialDistribution(n, p)

    # Check PMF sums to 1
    pmf_sum = sum(binomial.pmf(k) for k in range(n + 1))
    if abs(float(pmf_sum) - 1.0) < 1e-10:
        results["binomial"]["passed"] += 1
    else:
        results["binomial"]["failed"] += 1
        print(f"  FAILED: Binomial PMF doesn't sum to 1")

    # Check expected value (should be n*p)
    if binomial.expected_value() == n * p:
        results["binomial"]["passed"] += 1
    else:
        results["binomial"]["failed"] += 1
        print(f"  FAILED: Binomial expected value")

    # Check variance (should be n*p*(1-p))
    if binomial.variance() == n * p * (1 - p):
        results["binomial"]["passed"] += 1
    else:
        results["binomial"]["failed"] += 1
        print(f"  FAILED: Binomial variance")

    # Test Geometric
    p = Fraction(1, 3)
    geometric = GeometricDistribution(p)

    # Check expected value (should be 1/p)
    if geometric.expected_value() == Fraction(1, p):
        results["geometric"]["passed"] += 1
    else:
        results["geometric"]["failed"] += 1
        print(f"  FAILED: Geometric expected value")

    # Check variance formula
    if geometric.variance() == (1 - p) / (p ** 2):
        results["geometric"]["passed"] += 1
    else:
        results["geometric"]["failed"] += 1
        print(f"  FAILED: Geometric variance")

    # Test Poisson
    lam = Fraction(5, 1)
    poisson = PoissonDistribution(lam)

    # Check expected value equals variance
    if abs(float(poisson.expected_value() - poisson.variance())) < 0.01:
        results["poisson"]["passed"] += 1
    else:
        results["poisson"]["failed"] += 1
        print(f"  FAILED: Poisson E[X] != Var(X)")

    # Check PMF sums approximately to 1
    pmf_sum = sum(poisson.pmf(k) for k in range(0, 50))
    if abs(float(pmf_sum) - 1.0) < 0.01:
        results["poisson"]["passed"] += 1
    else:
        results["poisson"]["failed"] += 1
        print(f"  FAILED: Poisson PMF doesn't sum to 1")

    # Print summary
    for test_name, result in results.items():
        total = result["passed"] + result["failed"]
        print(f"  {test_name}: {result['passed']}/{total}")

    return results


def test_markov_chain() -> Dict:
    """Test discrete Markov chain operations"""
    print("Testing Markov chains...")

    results = {
        "transition_matrix": {"passed": 0, "failed": 0},
        "matrix_power": {"passed": 0, "failed": 0},
        "stationary_distribution": {"passed": 0, "failed": 0},
    }

    # Create a simple two-state Markov chain
    # State 0 -> State 0 with prob 0.7, State 1 with prob 0.3
    # State 1 -> State 0 with prob 0.4, State 1 with prob 0.6
    P = [
        [Fraction(7, 10), Fraction(3, 10)],
        [Fraction(4, 10), Fraction(6, 10)],
    ]

    mc = DiscreteMarkovChain(P)

    # Test 1: Validate transition matrix
    row_sums_valid = all(sum(row, Fraction(0)) == 1 for row in P)
    if row_sums_valid:
        results["transition_matrix"]["passed"] += 1
    else:
        results["transition_matrix"]["failed"] += 1
        print(f"  FAILED: Transition matrix validation")

    # Test 2: Matrix power correctness
    # P^2 should equal P * P
    P_squared = mc._matrix_power(P, 2)
    P_squared_direct = mc._matrix_multiply(P, P)

    if P_squared == P_squared_direct:
        results["matrix_power"]["passed"] += 1
    else:
        results["matrix_power"]["failed"] += 1
        print(f"  FAILED: Matrix power computation")

    # Test 3: Stationary distribution
    # For this chain, stationary distribution is approximately [0.571, 0.429]
    stationary = mc.stationary_distribution()

    if stationary is not None:
        # Verify πP = π
        pi_P = [sum(stationary[i] * P[i][j] for i in range(2)) for j in range(2)]

        max_diff = max(abs(stationary[j] - pi_P[j]) for j in range(2))
        if max_diff < Fraction(1, 10000):
            results["stationary_distribution"]["passed"] += 1
        else:
            results["stationary_distribution"]["failed"] += 1
            print(f"  FAILED: Stationary distribution - πP != π")
    else:
        results["stationary_distribution"]["failed"] += 1
        print(f"  FAILED: Stationary distribution did not converge")

    # Print summary
    for test_name, result in results.items():
        total = result["passed"] + result["failed"]
        print(f"  {test_name}: {result['passed']}/{total}")

    return results


def test_sampling_consistency() -> Dict:
    """Test that sampling is consistent with theoretical probabilities"""
    print("Testing sampling consistency...")

    results = {
        "bernoulli_sampling": {"passed": 0, "failed": 0},
        "binomial_sampling": {"passed": 0, "failed": 0},
        "uniform_sampling": {"passed": 0, "failed": 0},
    }

    # Test Bernoulli sampling
    p = Fraction(3, 10)
    dist = BernoulliDistribution(p)
    samples = dist.sample(10000)

    # Check that sample mean is close to p
    sample_mean = Fraction(sum(samples), len(samples))
    if abs(float(sample_mean - p)) < 0.02:  # Allow 2% tolerance
        results["bernoulli_sampling"]["passed"] += 1
    else:
        results["bernoulli_sampling"]["failed"] += 1
        print(f"  FAILED: Bernoulli sampling - mean {sample_mean} far from {p}")

    # Test Binomial sampling
    n, p = 20, Fraction(1, 2)
    dist = BinomialDistribution(n, p)
    samples = dist.sample(1000)

    sample_mean = Fraction(sum(samples), len(samples))
    expected_mean = n * p

    if abs(float(sample_mean - expected_mean)) < 0.5:  # Allow 0.5 tolerance
        results["binomial_sampling"]["passed"] += 1
    else:
        results["binomial_sampling"]["failed"] += 1
        print(f"  FAILED: Binomial sampling - mean {sample_mean} far from {expected_mean}")

    # Test uniform sampling from finite probability space
    die = FiniteProbabilitySpace(list(range(1, 7)))
    samples = die.sample(60000)

    # Check that each outcome appears approximately 1/6 of the time
    counts = Counter(samples)
    for i in range(1, 7):
        expected_ratio = Fraction(1, 6)
        actual_ratio = Fraction(counts[i], len(samples))

        if abs(float(actual_ratio - expected_ratio)) < 0.01:  # 1% tolerance
            pass  # Good
        else:
            results["uniform_sampling"]["failed"] += 1
            print(f"  FAILED: Uniform sampling for {i}")
            break
    else:
        results["uniform_sampling"]["passed"] += 1

    # Print summary
    for test_name, result in results.items():
        total = result["passed"] + result["failed"]
        print(f"  {test_name}: {result['passed']}/{total}")

    return results


def benchmark_operations() -> Dict:
    """Benchmark probability operations"""
    print("\nBenchmarking operations...")

    results = {
        "expected_value": {},
        "variance": {},
        "sampling": {},
        "markov_power": {},
    }

    # Benchmark expected value computation
    for n in [10, 100, 1000]:
        space = FiniteProbabilitySpace(list(range(n)))
        iterations = 1000

        start = time.perf_counter_ns()
        for _ in range(iterations):
            space.expected_value(lambda x: x)
        end = time.perf_counter_ns()

        ns_per_op = (end - start) / iterations
        results["expected_value"][n] = ns_per_op
        print(f"  Expected value (n={n}): {ns_per_op:.1f} ns/op")

    # Benchmark variance computation
    for n in [10, 100, 1000]:
        space = FiniteProbabilitySpace(list(range(n)))
        iterations = 1000

        start = time.perf_counter_ns()
        for _ in range(iterations):
            space.variance(lambda x: x)
        end = time.perf_counter_ns()

        ns_per_op = (end - start) / iterations
        results["variance"][n] = ns_per_op
        print(f"  Variance (n={n}): {ns_per_op:.1f} ns/op")

    # Benchmark sampling
    for n_samples in [100, 1000, 10000]:
        space = FiniteProbabilitySpace(list(range(6)))
        iterations = 10

        start = time.perf_counter_ns()
        for _ in range(iterations):
            space.sample(n_samples)
        end = time.perf_counter_ns()

        ns_per_sample = (end - start) / (iterations * n_samples)
        results["sampling"][n_samples] = ns_per_sample
        print(f"  Sampling (n={n_samples}): {ns_per_sample:.1f} ns/sample")

    # Benchmark Markov chain matrix power
    for power in [10, 50, 100]:
        P = [
            [Fraction(7, 10), Fraction(3, 10)],
            [Fraction(4, 10), Fraction(6, 10)],
        ]
        mc = DiscreteMarkovChain(P)
        iterations = 10

        start = time.perf_counter_ns()
        for _ in range(iterations):
            mc._matrix_power(P, power)
        end = time.perf_counter_ns()

        ns_per_op = (end - start) / iterations
        results["markov_power"][power] = ns_per_op
        print(f"  Markov power (power={power}): {ns_per_op:.1f} ns/op")

    return results


def run_all_tests():
    """Run all verification tests"""
    print("=" * 60)
    print("DCA Chapter 7: Discrete Probability Theory Verification")
    print("=" * 60)

    # Run correctness tests
    prob_space_results = test_finite_probability_space()
    distributions_results = test_distributions()
    markov_results = test_markov_chain()
    sampling_results = test_sampling_consistency()

    # Run benchmarks
    benchmark_results = benchmark_operations()

    # Summary
    print("\n" + "=" * 60)
    print("VERIFICATION SUMMARY")
    print("=" * 60)

    all_tests = [
        ("Finite Probability Space", prob_space_results),
        ("Distributions", distributions_results),
        ("Markov Chains", markov_results),
        ("Sampling Consistency", sampling_results),
    ]

    all_passed = True
    total_passed = 0
    total_failed = 0

    for test_name, results in all_tests:
        passed = sum(v.get("passed", 0) for v in results.values() if isinstance(v, dict))
        failed = sum(v.get("failed", 0) for v in results.values() if isinstance(v, dict))

        total_passed += passed
        total_failed += failed

        if failed > 0:
            all_passed = False

        print(f"{test_name}: {passed}/{passed + failed} tests passed")

    print(f"\nTotal: {total_passed}/{total_passed + total_failed} tests passed")

    if all_passed:
        print("\n✓ ALL TESTS PASSED!")
    else:
        print("\n✗ SOME TESTS FAILED!")

    return {
        "prob_space": prob_space_results,
        "distributions": distributions_results,
        "markov": markov_results,
        "sampling": sampling_results,
        "benchmark": benchmark_results,
        "all_passed": all_passed,
        "total_passed": total_passed,
        "total_failed": total_failed,
    }


if __name__ == "__main__":
    verification_results = run_all_tests()

    # Exit with appropriate code
    exit(0 if verification_results["all_passed"] else 1)
