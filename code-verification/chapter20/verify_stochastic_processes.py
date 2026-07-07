"""
DCA Chapter 20: Discrete Stochastic Processes and Martingales - Verification Code
Testing finite time stochastic processes, filtrations, and martingale properties
"""

import time
from typing import List, Tuple, Dict, Callable, Optional, Any, Set
from dataclasses import dataclass, field
from enum import Enum
import random

# ============================================================================
# SECTION 1: Finite Probability Space
# ============================================================================

@dataclass
class Outcome:
    """An outcome in the probability space"""
    name: str
    probability: float

    def __post_init__(self):
        if not 0 <= self.probability <= 1:
            raise ValueError(f"Probability must be in [0,1], got {self.probability}")

@dataclass
class FiniteProbabilitySpace:
    """
    Finite probability space Omega = {omega_1, ..., omega_n}
    with probabilities P(omega_i) = p_i
    """
    outcomes: List[Outcome] = field(default_factory=list)

    def __post_init__(self):
        # Verify probabilities sum to 1
        total = sum(o.probability for o in self.outcomes)
        if abs(total - 1.0) > 1e-9:
            raise ValueError(f"Probabilities must sum to 1, got {total}")

    def probability(self, event: List[str]) -> float:
        """Compute probability of an event (subset of outcomes)"""
        return sum(o.probability for o in self.outcomes if o.name in event)

    def verify_total_probability(self) -> bool:
        """Verify total probability is 1"""
        return abs(sum(o.probability for o in self.outcomes) - 1.0) < 1e-9

# ============================================================================
# SECTION 2: Discrete Time Stochastic Process
# ============================================================================

@dataclass
class StochasticProcess:
    """
    Discrete time stochastic process X_0, X_1, ..., X_T
    Defined on finite probability space
    """
    name: str
    time_horizon: int
    values: Dict[str, List[float]]  # outcome -> [X_0, X_1, ..., X_T]
    probability_space: FiniteProbabilitySpace

    def __post_init__(self):
        # Verify each outcome has values for all time steps
        for outcome in self.probability_space.outcomes:
            if outcome.name not in self.values:
                raise ValueError(f"Missing values for outcome {outcome.name}")
            if len(self.values[outcome.name]) != self.time_horizon + 1:
                raise ValueError(f"Expected {self.time_horizon + 1} time steps")

    def value_at(self, t: int, outcome: str) -> float:
        """Get X_t for a specific outcome"""
        if t > self.time_horizon:
            raise ValueError(f"Time {t} exceeds horizon {self.time_horizon}")
        return self.values[outcome][t]

    def expected_value(self, t: int) -> float:
        """Compute E[X_t] = sum X_t(omega) * P(omega)"""
        return sum(
            self.value_at(t, o.name) * o.probability
            for o in self.probability_space.outcomes
        )

    def variance(self, t: int) -> float:
        """Compute Var(X_t) = E[X_t^2] - (E[X_t])^2"""
        e_x = self.expected_value(t)
        e_x2 = sum(
            (self.value_at(t, o.name) ** 2) * o.probability
            for o in self.probability_space.outcomes
        )
        return e_x2 - e_x ** 2

# ============================================================================
# SECTION 3: Filtrations
# ============================================================================

class Filtration:
    """
    Filtration F_0, F_1, ..., F_T representing information over time
    Each F_t is a sigma-algebra (partition of outcomes)
    """

    def __init__(self, partitions: List[List[Set[str]]]):
        """
        Args:
            partitions: List of partitions, one for each time step
                        Each partition is a list of disjoint sets covering all outcomes
        """
        self.partitions = partitions

    def information_set(self, t: int, outcome: str) -> Set[str]:
        """Get the information set containing outcome at time t"""
        for info_set in self.partitions[t]:
            if outcome in info_set:
                return info_set
        return {outcome}

    def is_measurable(self, t: int, random_variable: Dict[str, float]) -> bool:
        """
        Check if random variable is measurable w.r.t. F_t
        (i.e., constant on each information set)
        """
        for info_set in self.partitions[t]:
            values = [random_variable.get(o, 0) for o in info_set]
            if len(set(values)) > 1:
                return False  # Not constant on this information set
        return True

# ============================================================================
# SECTION 4: Conditional Expectation
# ============================================================================

class ConditionalExpectation:
    """Conditional expectation E[X | F_t]"""

    @staticmethod
    def compute(
        process: StochasticProcess,
        filtration: Filtration,
        t: int
    ) -> Dict[str, float]:
        """
        Compute E[X_T | F_t] for each information set at time t
        """
        result = {}

        for info_set in filtration.partitions[t]:
            # Compute conditional expectation on this information set
            # E[X_T | info_set] = sum_{omega in info_set} X_T(omega) * P(omega | info_set)

            # Probability of information set
            p_info_set = sum(
                o.probability
                for o in process.probability_space.outcomes
                if o.name in info_set
            )

            if p_info_set == 0:
                continue

            # Conditional expectation
            cond_exp = sum(
                process.value_at(process.time_horizon, o.name) * o.probability / p_info_set
                for o in process.probability_space.outcomes
                if o.name in info_set
            )

            # Same value for all outcomes in information set
            for outcome in info_set:
                result[outcome] = cond_exp

        return result

# ============================================================================
# SECTION 5: Martingales
# ============================================================================

class Martingale:
    """Martingale verification and properties"""

    @staticmethod
    def is_martingale(
        process: StochasticProcess,
        filtration: Filtration
    ) -> Tuple[bool, str]:
        """
        Check if process is a martingale: E[X_{t+1} | F_t] = X_t for all t
        """
        for t in range(process.time_horizon):
            # For each information set at time t
            for info_set in filtration.partitions[t]:
                # Compute probability of information set
                p_info_set = sum(
                    o.probability
                    for o in process.probability_space.outcomes
                    if o.name in info_set
                )

                if p_info_set == 0:
                    continue

                # Compute E[X_{t+1} | F_t] on this information set
                cond_exp = sum(
                    process.value_at(t + 1, o.name) * o.probability / p_info_set
                    for o in process.probability_space.outcomes
                    if o.name in info_set
                )

                # Check if equals X_t for all outcomes in info set
                for outcome in info_set:
                    x_t = process.value_at(t, outcome)
                    if abs(cond_exp - x_t) > 1e-6:
                        return False, f"Martingale property violated at t={t}, outcome={outcome}: E[X_{t+1}|F_t]={cond_exp} != X_t={x_t}"

        return True, "Process is a martingale"

    @staticmethod
    def is_submartingale(
        process: StochasticProcess,
        filtration: Filtration
    ) -> Tuple[bool, str]:
        """
        Check if process is a submartingale: E[X_{t+1} | F_t] >= X_t
        """
        for t in range(process.time_horizon):
            for info_set in filtration.partitions[t]:
                p_info_set = sum(
                    o.probability
                    for o in process.probability_space.outcomes
                    if o.name in info_set
                )

                if p_info_set == 0:
                    continue

                cond_exp = sum(
                    process.value_at(t + 1, o.name) * o.probability / p_info_set
                    for o in process.probability_space.outcomes
                    if o.name in info_set
                )

                for outcome in info_set:
                    x_t = process.value_at(t, outcome)
                    if cond_exp < x_t - 1e-6:
                        return False, f"Submartingale property violated at t={t}"

        return True, "Process is a submartingale"

    @staticmethod
    def is_supermartingale(
        process: StochasticProcess,
        filtration: Filtration
    ) -> Tuple[bool, str]:
        """
        Check if process is a supermartingale: E[X_{t+1} | F_t] <= X_t
        """
        for t in range(process.time_horizon):
            for info_set in filtration.partitions[t]:
                p_info_set = sum(
                    o.probability
                    for o in process.probability_space.outcomes
                    if o.name in info_set
                )

                if p_info_set == 0:
                    continue

                cond_exp = sum(
                    process.value_at(t + 1, o.name) * o.probability / p_info_set
                    for o in process.probability_space.outcomes
                    if o.name in info_set
                )

                for outcome in info_set:
                    x_t = process.value_at(t, outcome)
                    if cond_exp > x_t + 1e-6:
                        return False, f"Supermartingale property violated at t={t}"

        return True, "Process is a supermartingale"

# ============================================================================
# SECTION 6: Stopping Times
# ============================================================================

class StoppingTime:
    """Stopping time verification"""

    @staticmethod
    def is_stopping_time(
        tau: Dict[str, int],  # outcome -> stopping time
        filtration: Filtration,
        max_time: int
    ) -> Tuple[bool, str]:
        """
        Check if tau is a stopping time: {tau <= t} in F_t for all t
        """
        for t in range(max_time + 1):
            # Event {tau <= t}
            event_outcomes = [
                o.name for o in filtration.partitions[0][0]  # All outcomes
                if tau.get(o.name, max_time + 1) <= t
            ]

            # Check if event is measurable w.r.t. F_t
            # (i.e., can be expressed as union of information sets)
            info_sets_at_t = filtration.partitions[t]

            # Check if event can be formed by union of information sets
            measurable = True
            for outcome in event_outcomes:
                # Find information set containing this outcome
                found = False
                for info_set in info_sets_at_t:
                    if outcome in info_set:
                        # Check if all outcomes in info set are in event
                        if all(o in event_outcomes for o in info_set):
                            found = True
                            break
                        else:
                            # Information set not fully contained in event
                            measurable = False
                            break
                if not measurable:
                    break

            if not measurable:
                return False, f"Event {{tau <= {t}}} not measurable w.r.t. F_{t}"

        return True, "tau is a valid stopping time"

# ============================================================================
# SECTION 7: Optional Stopping Theorem
# ============================================================================

class OptionalStoppingTheorem:
    """Optional stopping theorem verification"""

    @staticmethod
    def verify_bounded_stopping(
        process: StochasticProcess,
        filtration: Filtration,
        tau: Dict[str, int]
    ) -> Tuple[bool, str]:
        """
        Verify optional stopping theorem for bounded stopping time:
        If X_t is martingale and tau is bounded stopping time, then
        E[X_tau] = E[X_0]
        """
        # First verify martingale property
        is_mg, msg = Martingale.is_martingale(process, filtration)
        if not is_mg:
            return False, f"Process is not a martingale: {msg}"

        # Verify stopping time
        max_time = process.time_horizon
        is_st, msg = StoppingTime.is_stopping_time(tau, filtration, max_time)
        if not is_st:
            return False, f"tau is not a stopping time: {msg}"

        # Compute E[X_tau]
        e_x_tau = sum(
            process.value_at(tau[o.name], o.name) * o.probability
            for o in process.probability_space.outcomes
        )

        # Compute E[X_0]
        e_x_0 = process.expected_value(0)

        if abs(e_x_tau - e_x_0) < 1e-6:
            return True, f"Optional stopping theorem holds: E[X_tau] = {e_x_tau} = E[X_0] = {e_x_0}"
        else:
            return False, f"Optional stopping theorem violated: E[X_tau] = {e_x_tau} != E[X_0] = {e_x_0}"

# ============================================================================
# SECTION 8: Random Walk
# ============================================================================

class RandomWalk:
    """Simple random walk process"""

    @staticmethod
    def create_binomial_walk(steps: int, up_prob: float = 0.5) -> StochasticProcess:
        """
        Create binomial random walk: X_0 = 0, X_{t+1} = X_t + 1 (prob p) or X_t - 1 (prob 1-p)
        """
        # Generate all possible paths
        outcomes = []
        paths = []
        probs = []

        # All 2^steps possible sequences
        for i in range(2 ** steps):
            path = [0]
            prob = 1.0

            for j in range(steps):
                step_up = (i >> j) & 1
                if step_up:
                    path.append(path[-1] + 1)
                    prob *= up_prob
                else:
                    path.append(path[-1] - 1)
                    prob *= (1 - up_prob)

            outcomes.append(f"path_{i}")
            paths.append(path)
            probs.append(prob)

        # Create probability space
        prob_space = FiniteProbabilitySpace([
            Outcome(name=outcomes[i], probability=probs[i])
            for i in range(len(outcomes))
        ])

        # Create process
        values = {outcomes[i]: paths[i] for i in range(len(outcomes))}
        process = StochasticProcess(
            name="BinomialWalk",
            time_horizon=steps,
            values=values,
            probability_space=prob_space
        )

        return process

    @staticmethod
    def verify_martingale_property(steps: int, up_prob: float = 0.5) -> bool:
        """Verify that symmetric random walk is a martingale"""
        walk = RandomWalk.create_binomial_walk(steps, up_prob)

        # Create natural filtration
        # At time t, information is the path up to time t
        partitions = []
        for t in range(steps + 1):
            # Group paths by first t steps
            groups = {}
            for outcome in walk.probability_space.outcomes:
                path_prefix = tuple(walk.values[outcome.name][:t+1])
                if path_prefix not in groups:
                    groups[path_prefix] = []
                groups[path_prefix].append(outcome.name)

            partitions.append([set(v) for v in groups.values()])

        filtration = Filtration(partitions)

        # Check martingale property
        is_mg, msg = Martingale.is_martingale(walk, filtration)

        # For symmetric walk (p=0.5), should be martingale
        expected_martingale = (up_prob == 0.5)

        return is_mg == expected_martingale

# ============================================================================
# SECTION 9: Markov Chains
# ============================================================================

@dataclass
class MarkovChain:
    """Finite state Markov chain"""
    states: List[str]
    transition_matrix: List[List[float]]  # P[i][j] = P(X_{t+1}=j | X_t=i)
    initial_distribution: List[float]

    def __post_init__(self):
        # Validate transition matrix
        n = len(self.states)
        for i in range(n):
            if abs(sum(self.transition_matrix[i]) - 1.0) > 1e-9:
                raise ValueError(f"Row {i} of transition matrix doesn't sum to 1")

        # Validate initial distribution
        if abs(sum(self.initial_distribution) - 1.0) > 1e-9:
            raise ValueError("Initial distribution doesn't sum to 1")

    def step_probability(self, from_state: str, to_state: str) -> float:
        """Get transition probability P(X_{t+1}=to_state | X_t=from_state)"""
        i = self.states.index(from_state)
        j = self.states.index(to_state)
        return self.transition_matrix[i][j]

    def n_step_probability(self, n: int, from_state: str, to_state: str) -> float:
        """Compute n-step transition probability"""
        # Compute P^n
        import numpy as np
        P = np.array(self.transition_matrix)
        P_n = np.linalg.matrix_power(P, n)

        i = self.states.index(from_state)
        j = self.states.index(to_state)
        return float(P_n[i, j])

# ============================================================================
# SECTION 10: Test Suite
# ============================================================================

class TestSuite:
    """Comprehensive test suite for stochastic processes"""

    def __init__(self):
        self.results = []

    def test_probability_space(self) -> bool:
        """Test finite probability space"""
        print("Testing finite probability space...")

        # Create simple probability space
        prob_space = FiniteProbabilitySpace([
            Outcome(name="H", probability=0.5),
            Outcome(name="T", probability=0.5)
        ])

        passed = prob_space.verify_total_probability()

        # Test event probability
        event_prob = prob_space.probability(["H"])
        passed = passed and abs(event_prob - 0.5) < 1e-9

        self.results.append({
            "test": "Probability Space",
            "passed": passed,
            "details": "Finite probability space verified"
        })

        print(f"  Result: {'PASS' if passed else 'FAIL'}")
        return passed

    def test_random_walk(self) -> bool:
        """Test random walk as martingale"""
        print("Testing random walk...")

        passed = True

        # Test symmetric walk is martingale
        for steps in [1, 2, 3, 5]:
            result = RandomWalk.verify_martingale_property(steps, up_prob=0.5)
            passed = passed and result

        # Test asymmetric walk is not martingale
        for steps in [1, 2, 3]:
            walk = RandomWalk.create_binomial_walk(steps, up_prob=0.7)
            # Create filtration
            partitions = []
            for t in range(steps + 1):
                groups = {}
                for outcome in walk.probability_space.outcomes:
                    path_prefix = tuple(walk.values[outcome.name][:t+1])
                    if path_prefix not in groups:
                        groups[path_prefix] = []
                    groups[path_prefix].append(outcome.name)
                partitions.append([set(v) for v in groups.values()])

            filtration = Filtration(partitions)
            is_mg, _ = Martingale.is_martingale(walk, filtration)
            passed = passed and not is_mg  # Should NOT be martingale for p != 0.5

        self.results.append({
            "test": "Random Walk",
            "passed": passed,
            "details": "Random walk martingale property verified"
        })

        print(f"  Result: {'PASS' if passed else 'FAIL'}")
        return passed

    def test_conditional_expectation(self) -> bool:
        """Test conditional expectation"""
        print("Testing conditional expectation...")

        # Create simple process
        prob_space = FiniteProbabilitySpace([
            Outcome(name="HH", probability=0.25),
            Outcome(name="HT", probability=0.25),
            Outcome(name="TH", probability=0.25),
            Outcome(name="TT", probability=0.25)
        ])

        values = {
            "HH": [0, 1, 2],  # Two heads
            "HT": [0, 1, 1],
            "TH": [0, 0, 1],
            "TT": [0, 0, 0],  # Zero heads
        }

        process = StochasticProcess(
            name="CoinFlipCount",
            time_horizon=2,
            values=values,
            probability_space=prob_space
        )

        # Create filtration (natural filtration)
        partitions = [
            [{ "HH", "HT", "TH", "TT" }],  # F_0: no information
            [{ "HH", "HT" }, { "TH", "TT" }],  # F_1: first flip
            [{ "HH" }, { "HT" }, { "TH" }, { "TT" }],  # F_2: both flips
        ]

        filtration = Filtration(partitions)

        # Compute E[X_2 | F_1]
        cond_exp = ConditionalExpectation.compute(process, filtration, t=1)

        # Verify: on {HH, HT} (first flip H), E[X_2 | F_1] should be 1.5
        passed = abs(cond_exp["HH"] - 1.5) < 1e-6
        passed = passed and abs(cond_exp["HT"] - 1.5) < 1e-6

        # On {TH, TT} (first flip T), E[X_2 | F_1] should be 0.5
        passed = passed and abs(cond_exp["TH"] - 0.5) < 1e-6
        passed = passed and abs(cond_exp["TT"] - 0.5) < 1e-6

        self.results.append({
            "test": "Conditional Expectation",
            "passed": passed,
            "details": "Conditional expectation computation verified"
        })

        print(f"  Result: {'PASS' if passed else 'FAIL'}")
        return passed

    def test_stopping_time(self) -> bool:
        """Test stopping time verification"""
        print("Testing stopping time...")

        # Create simple process
        prob_space = FiniteProbabilitySpace([
            Outcome(name="path1", probability=0.5),
            Outcome(name="path2", probability=0.5)
        ])

        values = {
            "path1": [0, 1, 2],
            "path2": [0, -1, 0],
        }

        process = StochasticProcess(
            name="TestProcess",
            time_horizon=2,
            values=values,
            probability_space=prob_space
        )

        # Natural filtration
        partitions = [
            [{ "path1", "path2" }],
            [{ "path1" }, { "path2" }],
            [{ "path1" }, { "path2" }],
        ]

        filtration = Filtration(partitions)

        # Define stopping time: tau = 1 if X_1 = 1, else tau = 2
        tau = {
            "path1": 1,  # X_1 = 1
            "path2": 2,  # X_1 = -1
        }

        is_st, _ = StoppingTime.is_stopping_time(tau, filtration, max_time=2)

        # Test non-stopping time: tau = 1 if X_2 = 2 (depends on future)
        tau_not = {
            "path1": 2,  # X_2 = 2
            "path2": 2,
        }

        is_not_st, _ = StoppingTime.is_stopping_time(tau_not, filtration, max_time=2)

        passed = is_st and not is_not_st

        self.results.append({
            "test": "Stopping Time",
            "passed": passed,
            "details": "Stopping time verification works"
        })

        print(f"  Result: {'PASS' if passed else 'FAIL'}")
        return passed

    def test_optional_stopping(self) -> bool:
        """Test optional stopping theorem"""
        print("Testing optional stopping theorem...")

        # Create symmetric random walk
        walk = RandomWalk.create_binomial_walk(3, up_prob=0.5)

        # Create natural filtration
        partitions = []
        for t in range(4):
            groups = {}
            for outcome in walk.probability_space.outcomes:
                path_prefix = tuple(walk.values[outcome.name][:t+1])
                if path_prefix not in groups:
                    groups[path_prefix] = []
                groups[path_prefix].append(outcome.name)
            partitions.append([set(v) for v in groups.values()])

        filtration = Filtration(partitions)

        # Define bounded stopping time: tau = min{t: |X_t| = 1 or t = 3}
        tau = {}
        for outcome in walk.probability_space.outcomes:
            path = walk.values[outcome.name]
            for t, val in enumerate(path):
                if abs(val) >= 1:
                    tau[outcome.name] = t
                    break
            else:
                tau[outcome.name] = 3

        # Verify optional stopping theorem
        is_ost, msg = OptionalStoppingTheorem.verify_bounded_stopping(walk, filtration, tau)

        passed = is_ost

        self.results.append({
            "test": "Optional Stopping Theorem",
            "passed": passed,
            "details": msg
        })

        print(f"  Result: {'PASS' if passed else 'FAIL'}")
        return passed

    def test_markov_chain(self) -> bool:
        """Test Markov chain"""
        print("Testing Markov chain...")

        # Create simple 2-state Markov chain
        mc = MarkovChain(
            states=["A", "B"],
            transition_matrix=[
                [0.7, 0.3],  # From A
                [0.4, 0.6],  # From B
            ],
            initial_distribution=[0.5, 0.5]
        )

        # Test 1-step transition
        p = mc.step_probability("A", "B")
        passed = abs(p - 0.3) < 1e-9

        # Test n-step transition (P^2)
        p2 = mc.n_step_probability(2, "A", "B")
        # P^2[0][1] = P[0][0]*P[0][1] + P[0][1]*P[1][1]
        #           = 0.7*0.3 + 0.3*0.6 = 0.21 + 0.18 = 0.39
        expected = 0.39
        passed = passed and abs(p2 - expected) < 1e-9

        self.results.append({
            "test": "Markov Chain",
            "passed": passed,
            "details": "Markov chain transition probabilities verified"
        })

        print(f"  Result: {'PASS' if passed else 'FAIL'}")
        return passed

    def run_all_tests(self) -> Dict[str, any]:
        """Run all tests"""
        print("=" * 60)
        print("DCA Chapter 20: Stochastic Processes - Test Suite")
        print("=" * 60)

        tests = [
            ("Probability Space", self.test_probability_space),
            ("Random Walk", self.test_random_walk),
            ("Conditional Expectation", self.test_conditional_expectation),
            ("Stopping Time", self.test_stopping_time),
            ("Optional Stopping Theorem", self.test_optional_stopping),
            ("Markov Chain", self.test_markov_chain),
        ]

        for name, test_func in tests:
            print(f"\nRunning: {name}")
            print("-" * 40)
            try:
                test_func()
            except Exception as e:
                print(f"  ERROR: {e}")
                import traceback
                traceback.print_exc()
                self.results.append({
                    "test": name,
                    "passed": False,
                    "details": f"Exception: {str(e)}"
                })

        passed_count = sum(1 for r in self.results if r["passed"])
        total_count = len(self.results)

        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        print(f"Passed: {passed_count}/{total_count}")
        print(f"Failed: {total_count - passed_count}/{total_count}")

        return {
            "total_tests": total_count,
            "passed_tests": passed_count,
            "failed_tests": total_count - passed_count,
            "results": self.results
        }

# ============================================================================
# SECTION 11: Main Execution
# ============================================================================

def main():
    """Main execution function"""
    suite = TestSuite()
    test_results = suite.run_all_tests()

    print("\n" + "=" * 60)
    print("FINAL SUMMARY")
    print("=" * 60)
    print(f"Tests Passed: {test_results['passed_tests']}/{test_results['total_tests']}")
    print(f"Success Rate: {test_results['passed_tests']/test_results['total_tests']*100:.1f}%")

    return test_results

if __name__ == "__main__":
    results = main()
