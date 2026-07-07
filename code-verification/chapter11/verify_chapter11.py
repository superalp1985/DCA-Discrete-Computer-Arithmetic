#!/usr/bin/env python3
"""
DCA Chapter 11: Discrete Differential Equations
Verification Code for Recurrence Systems and Finite Step Solvers
"""

import time
import unittest
from typing import List, Tuple, Callable, Dict, Optional
import math


# ============================================================================
# SECTION 1: Linear Recurrence Relations
# ============================================================================

class LinearRecurrence:
    """
    Implementation of linear recurrence relations.

    Core formula: x_{t+k} = a_{k-1}*x_{t+k-1} + ... + a_0*x_t + u_t
    """

    def __init__(self, coefficients: List[float]):
        """
        Initialize linear recurrence.

        Args:
            coefficients: List of coefficients [a_0, a_1, ..., a_{k-1}]
        """
        self.coefficients = coefficients
        self.order = len(coefficients)

    def compute(self, initial: List[float], steps: int,
                inputs: Optional[List[float]] = None) -> List[float]:
        """
        Compute recurrence sequence.

        Args:
            initial: Initial values [x_0, x_1, ..., x_{k-1}]
            steps: Number of additional steps to compute
            inputs: Optional external inputs [u_0, u_1, ...]

        Returns:
            Complete sequence including initial values
        """
        sequence = list(initial)
        k = self.order

        for t in range(steps):
            # Compute next term using recurrence formula
            next_val = sum(self.coefficients[i] * sequence[-k + i] for i in range(k))

            # Add external input if provided
            if inputs and t < len(inputs):
                next_val += inputs[t]

            sequence.append(next_val)

        return sequence

    def to_state_space(self) -> Tuple[List[List[float]], List[float]]:
        """
        Convert recurrence to state-space form: s_{t+1} = A*s_t + b*u_t

        For recurrence x_{t+k} = sum(a_i * x_{t+i}),
        state is s_t = [x_t, x_{t+1}, ..., x_{t+k-1}]

        Returns:
            Tuple of (A matrix, b vector)
        """
        k = self.order

        # Build companion matrix A
        A = [[0.0] * k for _ in range(k)]
        for i in range(k - 1):
            A[i + 1][i] = 1.0  # Shift rows
        for j in range(k):
            A[0][j] = self.coefficients[j]  # Recurrence coefficients

        # Build input vector b
        b = [0.0] * k
        b[0] = 1.0

        return A, b

    def solve_closed_form(self, initial: List[float], t: int) -> float:
        """
        Solve using closed-form formula for simple cases.

        Args:
            initial: Initial values
            t: Time step

        Returns:
            Value at time t
        """
        if t < len(initial):
            return initial[t]

        # For first-order: x_{t+1} = a*x_t
        if self.order == 1:
            a = self.coefficients[0]
            return initial[0] * (a ** t)

        # For second-order homogeneous with characteristic roots
        if self.order == 2:
            a, b = self.coefficients
            # Solve: r^2 - a*r - b = 0
            discriminant = a**2 + 4*b

            if discriminant >= 0:
                # Real roots
                r1 = (a + math.sqrt(discriminant)) / 2
                r2 = (a - math.sqrt(discriminant)) / 2

                # Solve for constants c1, c2 from initial conditions
                if abs(r1 - r2) > 1e-10:
                    c2 = (initial[1] - r1 * initial[0]) / (r2 - r1)
                    c1 = initial[0] - c2
                    return c1 * (r1 ** t) + c2 * (r2 ** t)
                else:
                    # Repeated root: (c1 + c2*t)*r^t
                    c1 = initial[0]
                    c2 = initial[1] / r1 - initial[0]
                    return (c1 + c2 * t) * (r1 ** t)
            else:
                # Complex roots - use numerical method
                sequence = self.compute(initial, t - len(initial) + 1)
                return sequence[-1]

        # For higher order, use numerical method
        sequence = self.compute(initial, t - len(initial) + 1)
        return sequence[-1]


# ============================================================================
# SECTION 2: State-Space Systems
# ============================================================================

class StateSpaceSystem:
    """
    Discrete state-space system implementation.

    Core formula: s_{t+1} = A*s_t + b*u_t
    """

    def __init__(self, A: List[List[float]], b: List[float]):
        """
        Initialize state-space system.

        Args:
            A: State transition matrix
            b: Input vector
        """
        self.A = A
        self.b = b
        self.n = len(A)

    def step(self, state: List[float], input_val: float = 0.0) -> List[float]:
        """
        Perform one time step.

        Args:
            state: Current state vector
            input_val: External input value

        Returns:
            Next state
        """
        next_state = []
        for i in range(self.n):
            val = sum(self.A[i][j] * state[j] for j in range(self.n))
            val += self.b[i] * input_val
            next_state.append(val)
        return next_state

    def simulate(self, initial_state: List[float],
                 inputs: List[float]) -> List[List[float]]:
        """
        Simulate system over time.

        Args:
            initial_state: Initial state vector
            inputs: Input sequence

        Returns:
            List of states over time
        """
        states = [initial_state]
        current_state = initial_state

        for u in inputs:
            current_state = self.step(current_state, u)
            states.append(current_state)

        return states

    def verify_consistency(self, recurrence: LinearRecurrence,
                          initial: List[float], steps: int) -> bool:
        """
        Verify that state-space form matches original recurrence.

        Args:
            recurrence: Original recurrence relation
            initial: Initial values
            steps: Number of steps to verify

        Returns:
            True if forms match
        """
        # Compute using recurrence
        seq_rec = recurrence.compute(initial, steps)

        # Compute using state-space
        states = self.simulate(initial[:self.n], [0.0] * steps)
        seq_ss = [state[0] for state in states]

        # Compare sequences (use minimum length)
        min_len = min(len(seq_rec), len(seq_ss))
        for i in range(min_len):
            if abs(seq_rec[i] - seq_ss[i]) > 1e-6:
                return False

        return True

    def compute_observability(self, C: List[List[float]]) -> List[List[float]]:
        """
        Compute observability matrix.

        Args:
            C: Output matrix

        Returns:
            Observability matrix
        """
        n = self.n
        m = len(C)
        O = []

        for i in range(n):
            if i == 0:
                O.extend(C)
            else:
                # C * A^i
                CA = self._matrix_multiply(C, self._matrix_power(self.A, i))
                O.extend(CA)

        return O

    def _matrix_multiply(self, A: List[List[float]],
                        B: List[List[float]]) -> List[List[float]]:
        """Multiply two matrices."""
        n = len(A)
        m = len(B[0])
        p = len(B)

        result = [[0.0] * m for _ in range(n)]
        for i in range(n):
            for j in range(m):
                result[i][j] = sum(A[i][k] * B[k][j] for k in range(p))
        return result

    def _matrix_power(self, A: List[List[float]], n: int) -> List[List[float]]:
        """Compute matrix power using binary exponentiation."""
        size = len(A)

        # Identity matrix
        result = [[1.0 if i == j else 0.0 for j in range(size)] for i in range(size)]
        base = [row[:] for row in A]

        while n > 0:
            if n % 2 == 1:
                result = self._matrix_multiply(result, base)
            base = self._matrix_multiply(base, base)
            n //= 2

        return result


# ============================================================================
# SECTION 3: Finite Field Recurrence
# ============================================================================

class FiniteFieldRecurrence:
    """
    Recurrence relations over finite fields.

    Core formula: x_{t+k} = sum(a_i * x_{t+i}) mod p
    """

    def __init__(self, coefficients: List[int], modulus: int):
        """
        Initialize finite field recurrence.

        Args:
            coefficients: Coefficients [a_0, ..., a_{k-1}]
            modulus: Field modulus p
        """
        self.coefficients = [c % modulus for c in coefficients]
        self.modulus = modulus
        self.order = len(coefficients)

    def compute(self, initial: List[int], steps: int) -> List[int]:
        """
        Compute sequence over finite field.

        Args:
            initial: Initial values [x_0, ..., x_{k-1}]
            steps: Number of steps

        Returns:
            Sequence modulo p
        """
        sequence = [x % self.modulus for x in initial]
        k = self.order

        for t in range(steps):
            next_val = sum(self.coefficients[i] * sequence[-k + i]
                          for i in range(k)) % self.modulus
            sequence.append(next_val)

        return sequence

    def find_period(self, initial: List[int], max_steps: int = 10000) -> Tuple[int, int]:
        """
        Find period of sequence (pigeonhole principle).

        Args:
            initial: Initial values
            max_steps: Maximum steps to search

        Returns:
            Tuple of (preperiod, period)
        """
        seen = {}
        k = self.order
        state = tuple(x % self.modulus for x in initial[:k])

        for t in range(max_steps):
            if state in seen:
                preperiod = seen[state]
                period = t - seen[state]
                return preperiod, period

            seen[state] = t

            # Compute next state
            next_val = sum(self.coefficients[i] * state[i]
                          for i in range(k)) % self.modulus
            state = tuple(list(state[1:]) + [next_val])

        return -1, -1  # Period not found

    def verify_linear_recurrence_modular(self, sequence: List[int]) -> bool:
        """
        Verify that sequence satisfies the recurrence.

        Args:
            sequence: Sequence to verify

        Returns:
            True if sequence satisfies recurrence
        """
        k = self.order
        if len(sequence) < k:
            return False

        for t in range(k, len(sequence)):
            expected = sum(self.coefficients[i] * sequence[t - k + i]
                         for i in range(k)) % self.modulus
            if sequence[t] % self.modulus != expected:
                return False

        return True


# ============================================================================
# SECTION 4: Difference Equation Solvers
# ============================================================================

class DifferenceSolver:
    """
    Solver for difference equations.
    """

    @staticmethod
    def solve_first_order(a: float, b: float, x0: float,
                         inputs: List[float]) -> List[float]:
        """
        Solve first-order difference equation: x_{t+1} = a*x_t + b*u_t

        Args:
            a: Coefficient
            b: Input coefficient
            x0: Initial value
            inputs: Input sequence

        Returns:
            Solution sequence
        """
        solution = [x0]
        x = x0

        for u in inputs:
            x = a * x + b * u
            solution.append(x)

        return solution

    @staticmethod
    def solve_homogeneous(coefficients: List[float],
                         initial: List[float],
                         steps: int) -> List[float]:
        """
        Solve homogeneous linear recurrence.

        Args:
            coefficients: Recurrence coefficients
            initial: Initial values
            steps: Number of steps

        Returns:
            Solution sequence
        """
        recurrence = LinearRecurrence(coefficients)
        return recurrence.compute(initial, steps)

    @staticmethod
    def solve_particular(coefficients: List[float],
                        input_func: Callable[[int], float],
                        initial: List[float],
                        steps: int) -> List[float]:
        """
        Solve non-homogeneous recurrence with particular solution.

        Args:
            coefficients: Recurrence coefficients
            input_func: Input function u(t)
            initial: Initial values
            steps: Number of steps

        Returns:
            Solution sequence
        """
        k = len(coefficients)
        sequence = list(initial)

        for t in range(steps):
            u_t = input_func(t)
            next_val = sum(coefficients[i] * sequence[-k + i]
                         for i in range(k)) + u_t
            sequence.append(next_val)

        return sequence


# ============================================================================
# SECTION 5: Stability Analysis
# ============================================================================

class StabilityAnalysis:
    """
    Stability analysis for discrete systems.
    """

    @staticmethod
    def compute_eigenvalues(A: List[List[float]]) -> List[complex]:
        """
        Compute eigenvalues of matrix (for 2x2 case).

        Args:
            A: Square matrix

        Returns:
            List of eigenvalues
        """
        if len(A) != 2 or len(A[0]) != 2:
            raise NotImplementedError("Only 2x2 matrices supported")

        a, b = A[0]
        c, d = A[1]

        # Characteristic polynomial: λ^2 - (a+d)λ + (ad-bc) = 0
        trace = a + d
        det = a * d - b * c

        discriminant = trace**2 - 4*det
        sqrt_disc = complex(discriminant)**0.5

        lambda1 = (trace + sqrt_disc) / 2
        lambda2 = (trace - sqrt_disc) / 2

        return [lambda1, lambda2]

    @staticmethod
    def is_stable(eigenvalues: List[complex]) -> bool:
        """
        Check if system is stable (all |λ| < 1).

        Args:
            eigenvalues: List of eigenvalues

        Returns:
            True if system is stable
        """
        return all(abs(lam) < 1 for lam in eigenvalues)

    @staticmethod
    def analyze_recurrence_stability(coefficients: List[float]) -> bool:
        """
        Analyze stability of recurrence relation.

        Args:
            coefficients: Recurrence coefficients

        Returns:
            True if recurrence is stable
        """
        recurrence = LinearRecurrence(coefficients)
        A, _ = recurrence.to_state_space()

        try:
            eigenvalues = StabilityAnalysis.compute_eigenvalues(A)
            return StabilityAnalysis.is_stable(eigenvalues)
        except NotImplementedError:
            # For higher order, use numerical check
            sequence = recurrence.compute([1.0] * len(coefficients), 100)
            return max(abs(x) for x in sequence[-10:]) < 1.0


# ============================================================================
# SECTION 6: Verification Tests
# ============================================================================

class TestLinearRecurrence(unittest.TestCase):
    """Tests for linear recurrence relations."""

    def test_fibonacci(self):
        """Test Fibonacci sequence."""
        # x_{t+2} = x_{t+1} + x_t
        recurrence = LinearRecurrence([1, 1])
        sequence = recurrence.compute([0, 1], 10)
        # Expected: 0, 1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89
        expected = [0, 1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89]
        self.assertEqual(len(sequence), 12)
        for i, val in enumerate(expected):
            self.assertAlmostEqual(sequence[i], val)

    def test_arithmetic_progression(self):
        """Test arithmetic progression."""
        # x_{t+1} = x_t + 1
        recurrence = LinearRecurrence([1])
        sequence = recurrence.compute([0], 10)
        # sequence = [0, 1, 2, ..., 10] (11 elements)
        # The first 10 elements after initial should match 0..10
        for i in range(min(len(sequence), 11)):
            self.assertAlmostEqual(sequence[i], i)

    def test_geometric_progression(self):
        """Test geometric progression."""
        # x_{t+1} = 2*x_t
        recurrence = LinearRecurrence([2])
        sequence = recurrence.compute([1], 5)
        for i in range(len(sequence)):
            self.assertAlmostEqual(sequence[i], 2**i)

    def test_state_space_conversion(self):
        """Test conversion to state-space form."""
        recurrence = LinearRecurrence([1, 1])  # Fibonacci
        A, b = recurrence.to_state_space()

        # Check companion matrix structure
        self.assertEqual(A[0][0], 1)
        self.assertEqual(A[0][1], 1)
        self.assertEqual(A[1][0], 1)
        self.assertEqual(A[1][1], 0)

    def test_with_inputs(self):
        """Test recurrence with external inputs."""
        # x_{t+1} = x_t + u_t
        recurrence = LinearRecurrence([1])
        inputs = [1, 2, 3, 4, 5]
        sequence = recurrence.compute([0], 5, inputs)
        expected = [0, 1, 3, 6, 10, 15]  # Cumulative sum
        for i, val in enumerate(expected):
            self.assertAlmostEqual(sequence[i], val)


class TestStateSpaceSystem(unittest.TestCase):
    """Tests for state-space systems."""

    def test_step(self):
        """Test single time step."""
        # System: x_{t+1} = 0.8*x_t + 0.2*u_t
        A = [[0.8]]
        b = [0.2]
        system = StateSpaceSystem(A, b)

        next_state = system.step([10.0], 5.0)
        self.assertAlmostEqual(next_state[0], 0.8*10.0 + 0.2*5.0)

    def test_simulate(self):
        """Test simulation over time."""
        A = [[0.5]]
        b = [1.0]
        system = StateSpaceSystem(A, b)

        states = system.simulate([0.0], [1.0, 1.0, 1.0])
        self.assertEqual(len(states), 4)
        self.assertAlmostEqual(states[0][0], 0.0)
        self.assertAlmostEqual(states[1][0], 1.0)
        self.assertAlmostEqual(states[2][0], 1.5)
        self.assertAlmostEqual(states[3][0], 1.75)

    def test_consistency_with_recurrence(self):
        """Test consistency between state-space and recurrence."""
        recurrence = LinearRecurrence([1, 1])  # Fibonacci
        A, b = recurrence.to_state_space()
        system = StateSpaceSystem(A, b)

        consistent = system.verify_consistency(recurrence, [0, 1], 10)
        self.assertTrue(consistent)


class TestFiniteFieldRecurrence(unittest.TestCase):
    """Tests for finite field recurrence."""

    def test_modulo_fibonacci(self):
        """Test Fibonacci modulo prime."""
        recurrence = FiniteFieldRecurrence([1, 1], 11)
        sequence = recurrence.compute([0, 1], 20)

        # Verify sequence satisfies recurrence
        valid = recurrence.verify_linear_recurrence_modular(sequence)
        self.assertTrue(valid)

    def test_period_detection(self):
        """Test period detection in finite field."""
        recurrence = FiniteFieldRecurrence([1, 1], 5)
        preperiod, period = recurrence.find_period([0, 1])

        self.assertGreater(period, 0)
        self.assertLessEqual(period, 5**2)  # Period bounded by p^k

    def test_modular_arithmetic(self):
        """Test modular arithmetic properties."""
        recurrence = FiniteFieldRecurrence([2, 3], 7)
        sequence = recurrence.compute([1, 2], 10)

        # All values should be in range [0, 6]
        for val in sequence:
            self.assertGreaterEqual(val, 0)
            self.assertLess(val, 7)


class TestDifferenceSolver(unittest.TestCase):
    """Tests for difference equation solvers."""

    def test_first_order_solver(self):
        """Test first-order difference equation solver."""
        # x_{t+1} = 0.5*x_t + 1
        solution = DifferenceSolver.solve_first_order(0.5, 1.0, 0.0, [1]*5)

        self.assertEqual(len(solution), 6)
        self.assertAlmostEqual(solution[0], 0.0)
        self.assertAlmostEqual(solution[1], 1.0)
        self.assertAlmostEqual(solution[2], 1.5)

    def test_homogeneous_solver(self):
        """Test homogeneous recurrence solver."""
        # x_{t+2} = x_{t+1} + x_t
        solution = DifferenceSolver.solve_homogeneous([1, 1], [0, 1], 10)

        # Should match Fibonacci
        self.assertEqual(solution[2], 1)
        self.assertEqual(solution[3], 2)
        self.assertEqual(solution[4], 3)
        self.assertEqual(solution[5], 5)

    def test_particular_solution(self):
        """Test non-homogeneous recurrence."""
        # x_{t+1} = x_t + t (with input u_t = t)
        input_func = lambda t: t
        solution = DifferenceSolver.solve_particular([1], input_func, [0], 10)

        # Should produce triangular numbers
        for i in range(len(solution)):
            expected = i * (i - 1) // 2
            self.assertAlmostEqual(solution[i], expected)


class TestStabilityAnalysis(unittest.TestCase):
    """Tests for stability analysis."""

    def test_eigenvalue_computation(self):
        """Test eigenvalue computation."""
        A = [[0.5, 0.3], [0.2, 0.6]]
        eigenvalues = StabilityAnalysis.compute_eigenvalues(A)

        self.assertEqual(len(eigenvalues), 2)
        # Eigenvalues should sum to trace (1.1)
        self.assertAlmostEqual(sum(eigenvalues).real, 1.1, places=5)

    def test_stability_check(self):
        """Test stability determination."""
        # Stable system
        eigenvalues_stable = [0.5, 0.3]
        self.assertTrue(StabilityAnalysis.is_stable(eigenvalues_stable))

        # Unstable system
        eigenvalues_unstable = [1.5, 0.3]
        self.assertFalse(StabilityAnalysis.is_stable(eigenvalues_unstable))

    def test_recurrence_stability(self):
        """Test recurrence stability analysis."""
        # Stable: x_{t+1} = 0.5*x_t
        stable = StabilityAnalysis.analyze_recurrence_stability([0.5])
        self.assertTrue(stable)

        # Unstable: x_{t+1} = 1.5*x_t
        unstable = StabilityAnalysis.analyze_recurrence_stability([1.5])
        self.assertFalse(unstable)


# ============================================================================
# SECTION 7: Performance Benchmarks
# ============================================================================

class PerformanceBenchmarks:
    """Performance benchmarks for DCA Chapter 11 operations."""

    @staticmethod
    def benchmark_recurrence(order: int, steps: int,
                            iterations: int = 1000) -> Dict[str, float]:
        """
        Benchmark recurrence computation.

        Args:
            order: Recurrence order
            steps: Number of steps
            iterations: Number of iterations

        Returns:
            Dictionary of timing results
        """
        coefficients = [1.0] * order
        initial = [1.0] * order
        recurrence = LinearRecurrence(coefficients)

        times = []
        for _ in range(iterations):
            start = time.time()
            recurrence.compute(initial, steps)
            end = time.time()
            times.append(end - start)

        return {
            'mean': sum(times) / len(times),
            'min': min(times),
            'max': max(times)
        }

    @staticmethod
    def benchmark_state_space(size: int, steps: int,
                            iterations: int = 1000) -> Dict[str, float]:
        """
        Benchmark state-space simulation.

        Args:
            size: State dimension
            steps: Number of steps
            iterations: Number of iterations

        Returns:
            Dictionary of timing results
        """
        A = [[0.5] * size for _ in range(size)]
        b = [1.0] * size
        system = StateSpaceSystem(A, b)
        initial = [0.0] * size
        inputs = [1.0] * steps

        times = []
        for _ in range(iterations):
            start = time.time()
            system.simulate(initial, inputs)
            end = time.time()
            times.append(end - start)

        return {
            'mean': sum(times) / len(times),
            'min': min(times),
            'max': max(times)
        }

    @staticmethod
    def run_all_benchmarks() -> Dict[str, Dict[str, float]]:
        """Run all performance benchmarks."""
        results = {}

        # Recurrence benchmarks
        for order in [2, 5, 10]:
            results[f'recurrence_order_{order}'] = PerformanceBenchmarks.benchmark_recurrence(
                order, steps=100)

        # State-space benchmarks
        for size in [2, 5, 10]:
            results[f'statespace_size_{size}'] = PerformanceBenchmarks.benchmark_state_space(
                size, steps=100)

        return results


# ============================================================================
# SECTION 8: Main Execution
# ============================================================================

def main():
    """Main execution function for verification."""
    print("=" * 80)
    print("DCA Chapter 11: Discrete Differential Equations")
    print("Verification Suite")
    print("=" * 80)
    print()

    # Run unit tests
    print("Running unit tests...")
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    suite.addTests(loader.loadTestsFromTestCase(TestLinearRecurrence))
    suite.addTests(loader.loadTestsFromTestCase(TestStateSpaceSystem))
    suite.addTests(loader.loadTestsFromTestCase(TestFiniteFieldRecurrence))
    suite.addTests(loader.loadTestsFromTestCase(TestDifferenceSolver))
    suite.addTests(loader.loadTestsFromTestCase(TestStabilityAnalysis))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print()
    print("=" * 80)
    print("Test Results Summary")
    print("=" * 80)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print()

    # Run performance benchmarks
    print("=" * 80)
    print("Performance Benchmarks")
    print("=" * 80)

    benchmarks = PerformanceBenchmarks.run_all_benchmarks()
    for name, timings in benchmarks.items():
        print(f"{name}:")
        print(f"  Mean: {timings['mean']*1000:.4f} ms")
        print(f"  Min: {timings['min']*1000:.4f} ms")
        print(f"  Max: {timings['max']*1000:.4f} ms")

    print()
    print("=" * 80)
    print("Verification Complete")
    print("=" * 80)

    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    exit(main())