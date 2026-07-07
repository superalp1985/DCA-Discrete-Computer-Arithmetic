#!/usr/bin/env python3
"""
DCA Chapter 9: Discrete Dynamical Systems and Integer AI Operations
Verification Code for Finite State Cycles and Integer Neural Networks
"""

import time
import unittest
from typing import Callable, Dict, List, Tuple, Optional
from collections import defaultdict
import math


# ============================================================================
# SECTION 1: Discrete Dynamical Systems - Finite State Cycles
# ============================================================================

class FiniteDynamicalSystem:
    """
    Implementation of finite discrete dynamical systems with cycle detection.

    Core formula: x_{t+1} = F(x_t)
    """

    def __init__(self, state_space_size: int):
        """
        Initialize a finite dynamical system.

        Args:
            state_space_size: Size of the finite state space S
        """
        self.state_space_size = state_space_size
        self.transition_count = 0

    def compute_orbit(self, F: Callable[[int], int], x0: int, limit: int = 10000) -> Optional[Tuple[int, int, List[int]]]:
        """
        Compute the orbit of a starting state and detect cycles.

        Args:
            F: Transition function F: S -> S
            x0: Initial state
            limit: Maximum number of steps before giving up

        Returns:
            Tuple of (cycle_start, cycle_length, orbit) or None if no cycle found within limit
        """
        seen: Dict[int, int] = {}
        x = x0
        orbit = [x]

        for t in range(limit):
            if x in seen:
                cycle_start = seen[x]
                cycle_length = t - seen[x]
                return cycle_start, cycle_length, orbit
            seen[x] = t
            x = F(x) % self.state_space_size
            orbit.append(x)
            self.transition_count += 1

        return None

    def verify_pigeonhole_principle(self, F: Callable[[int], int], x0: int) -> bool:
        """
        Verify pigeonhole principle: any orbit of length > |S| must repeat a state.

        Args:
            F: Transition function
            x0: Initial state

        Returns:
            True if principle holds (cycle found within |S|+1 steps)
        """
        seen = set()
        x = x0

        for t in range(self.state_space_size + 1):
            if x in seen:
                return t <= self.state_space_size
            seen.add(x)
            x = F(x) % self.state_space_size

        return False  # Should never reach here for valid systems

    def find_all_cycles(self, F: Callable[[int], int]) -> List[List[int]]:
        """
        Find all cycles in the dynamical system.

        Args:
            F: Transition function

        Returns:
            List of cycles (each cycle is a list of states)
        """
        visited = set()
        cycles = []

        for state in range(self.state_space_size):
            if state in visited:
                continue

            # Follow orbit from this state
            orbit = []
            current = state
            seen_in_orbit = {}

            for t in range(self.state_space_size * 2):
                if current in seen_in_orbit:
                    # Found cycle
                    cycle_start = seen_in_orbit[current]
                    cycle = orbit[cycle_start:]
                    if cycle and all(c not in sum([c for c in cycles], [])):
                        cycles.append(cycle)
                    break

                seen_in_orbit[current] = t
                orbit.append(current)
                current = F(current) % self.state_space_size

            visited.update(orbit)

        return cycles

    def compute_attractor_basin(self, F: Callable[[int], int], state: int) -> Dict[int, List[int]]:
        """
        Compute the basin of attraction for all cycles.

        Args:
            F: Transition function
            state: Representative state for each cycle

        Returns:
            Dictionary mapping cycle representatives to their basins
        """
        basins = defaultdict(list)
        cycles = self.find_all_cycles(F)

        # Map cycle states to representatives
        cycle_reps = {}
        for i, cycle in enumerate(cycles):
            rep = min(cycle)
            for s in cycle:
                cycle_reps[s] = rep

        # Compute basin for each initial state
        for init_state in range(self.state_space_size):
            orbit_info = self.compute_orbit(F, init_state)
            if orbit_info:
                cycle_start, _, orbit = orbit_info
                cycle_state = orbit[cycle_start]
                rep = cycle_reps.get(cycle_state, cycle_state)
                basins[rep].append(init_state)

        return dict(basins)


# ============================================================================
# SECTION 2: Integer AI Operations - Quantized Neural Networks
# ============================================================================

class QuantizationScheme:
    """
    Quantization scheme for neural networks.

    Core formula: q(x) = round(x/s) + z
    where s is scale and z is zero-point
    """

    def __init__(self, scale: float, zero_point: int, bits: int = 8):
        """
        Initialize quantization scheme.

        Args:
            scale: Quantization scale factor
            zero_point: Zero-point offset
            bits: Number of bits for quantized values
        """
        self.scale = scale
        self.zero_point = zero_point
        self.bits = bits
        self.qmin = -(2 ** (bits - 1))
        self.qmax = 2 ** (bits - 1) - 1

    def quantize(self, x: float) -> int:
        """
        Quantize a floating-point value.

        Args:
            x: Floating-point value

        Returns:
            Quantized integer value
        """
        q = int(round(x / self.scale) + self.zero_point)
        return max(self.qmin, min(self.qmax, q))

    def dequantize(self, q: int) -> float:
        """
        Dequantize an integer value.

        Args:
            q: Quantized integer value

        Returns:
            Approximate floating-point value
        """
        return (q - self.zero_point) * self.scale


class IntegerNeuralLayer:
    """
    Integer neural network layer with quantized operations.
    """

    def __init__(self, weights: List[List[int]], bias: List[int],
                 quant_scheme: QuantizationScheme):
        """
        Initialize an integer neural layer.

        Args:
            weights: Integer weight matrix
            bias: Integer bias vector
            quant_scheme: Quantization scheme
        """
        self.weights = weights
        self.bias = bias
        self.quant_scheme = quant_scheme

    def forward(self, x: List[int]) -> List[int]:
        """
        Forward pass with integer arithmetic.

        Args:
            x: Integer input vector

        Returns:
            Integer output vector
        """
        output = []
        for i in range(len(self.weights)):
            # Compute y = Wx + b using integer arithmetic
            y = self.bias[i]
            for j in range(len(x)):
                y += self.weights[i][j] * x[j]

            # Apply ReLU activation: max(0, y)
            y = max(0, y)

            # Quantize output
            q_output = self.quant_scheme.quantize(self.quant_scheme.dequantize(y))
            output.append(q_output)

        return output

    def verify_linear_property(self, x: List[int], c: int) -> bool:
        """
        Verify linearity property for quantized layer.

        Args:
            x: Input vector
            c: Scalar multiplier

        Returns:
            True if quantized operation respects linearity approximately
        """
        # Compute F(cx) vs c*F(x) (both quantized)
        cx = [c * xi for xi in x]
        fcx = self.forward(cx)
        fx = self.forward(x)
        cfx = [c * fxi for fxi in fx]

        # Check if results are within quantization error
        tolerance = self.quant_scheme.scale
        for i in range(len(fcx)):
            diff = abs(fcx[i] - cfx[i])
            if diff > tolerance * 10:  # Allow some quantization error
                return False
        return True


class IntegerNeuralNetwork:
    """
    Complete integer neural network with multiple layers.
    """

    def __init__(self, layers: List[IntegerNeuralLayer]):
        """
        Initialize integer neural network.

        Args:
            layers: List of network layers
        """
        self.layers = layers

    def forward(self, x: List[int]) -> List[int]:
        """
        Forward pass through all layers.

        Args:
            x: Integer input vector

        Returns:
            Integer output vector
        """
        current = x
        for layer in self.layers:
            current = layer.forward(current)
        return current

    def verify_network_consistency(self, test_inputs: List[List[int]]) -> bool:
        """
        Verify network consistency across multiple runs.

        Args:
            test_inputs: List of test input vectors

        Returns:
            True if network produces consistent outputs
        """
        for x in test_inputs:
            output1 = self.forward(x)
            output2 = self.forward(x)
            if output1 != output2:
                return False
        return True


# ============================================================================
# SECTION 3: Activation Functions and Operations
# ============================================================================

class ActivationFunctions:
    """
    Discrete implementations of common activation functions.
    """

    @staticmethod
    def relu(x: int) -> int:
        """ReLU activation: max(0, x)"""
        return max(0, x)

    @staticmethod
    def leaky_relu(x: int, alpha: float = 0.01) -> int:
        """Leaky ReLU: max(alpha*x, x)"""
        return int(max(alpha * x, x))

    @staticmethod
    def sigmoid_approx(x: int, scale: float = 1.0) -> int:
        """
        Approximate sigmoid using piecewise linear function.

        Args:
            x: Input value
            scale: Scaling factor

        Returns:
            Approximate sigmoid value
        """
        # Simple linear approximation in range [-4, 4]
        clamped = max(-4, min(4, x / scale))
        if clamped < 0:
            return int(0.5 + 0.1 * clamped)
        else:
            return int(0.5 + 0.4 * clamped)

    @staticmethod
    def tanh_approx(x: int, scale: float = 1.0) -> int:
        """
        Approximate tanh using piecewise linear function.

        Args:
            x: Input value
            scale: Scaling factor

        Returns:
            Approximate tanh value
        """
        clamped = max(-4, min(4, x / scale))
        return int(clamped / 4)

    @staticmethod
    def softmax_approx(logits: List[int]) -> List[float]:
        """
        Approximate softmax using integer-friendly operations.

        Args:
            logits: Input logits

        Returns:
            Approximate softmax probabilities
        """
        # Find max for numerical stability
        max_logit = max(logits)

        # Compute exp(x - max) using simple approximation
        exps = []
        for logit in logits:
            diff = logit - max_logit
            # Simple exponential approximation
            if diff < -5:
                exp_val = 0.0
            elif diff < 0:
                exp_val = 1.0 / (1.0 - diff / 5.0)
            else:
                exp_val = 1.0 + diff / 5.0
            exps.append(exp_val)

        # Normalize
        total = sum(exps)
        if total == 0:
            return [1.0 / len(logits)] * len(logits)
        return [e / total for e in exps]


# ============================================================================
# SECTION 4: Integer Matrix Operations
# ============================================================================

class IntegerMatrixOps:
    """
    Integer matrix operations for neural network computations.
    """

    @staticmethod
    def matmul(A: List[List[int]], x: List[int]) -> List[int]:
        """
        Integer matrix-vector multiplication.

        Args:
            A: Matrix
            x: Vector

        Returns:
            Result vector y = Ax
        """
        return [sum(A[i][j] * x[j] for j in range(len(x))) for i in range(len(A))]

    @staticmethod
    def verify_matmul_property(A: List[List[int]], x: List[int],
                               B: List[List[int]], y: List[int]) -> bool:
        """
        Verify associativity property: A(Bx) = (AB)x

        Args:
            A: First matrix
            x: Input vector
            B: Second matrix
            y: Another input vector

        Returns:
            True if associativity holds (for small integer matrices)
        """
        # Compute A(Bx)
        Bx = IntegerMatrixOps.matmul(B, x)
        ABx = IntegerMatrixOps.matmul(A, Bx)

        # Compute (AB)x
        AB = [
            [sum(A[i][k] * B[k][j] for k in range(len(B))) for j in range(len(B[0]))]
            for i in range(len(A))
        ]
        ABy = IntegerMatrixOps.matmul(AB, x)

        return ABx == ABy

    @staticmethod
    def elementwise_multiply(a: List[int], b: List[int]) -> List[int]:
        """Element-wise multiplication of two vectors."""
        return [ai * bi for ai, bi in zip(a, b)]

    @staticmethod
    def verify_distributive_property(A: List[List[int]], x: List[int],
                                     y: List[int]) -> bool:
        """
        Verify distributive property: A(x+y) = Ax + Ay

        Args:
            A: Matrix
            x: First vector
            y: Second vector

        Returns:
            True if distributive property holds
        """
        xy_sum = [xi + yi for xi, yi in zip(x, y)]
        A_xy_sum = IntegerMatrixOps.matmul(A, xy_sum)

        Ax = IntegerMatrixOps.matmul(A, x)
        Ay = IntegerMatrixOps.matmul(A, y)
        Ax_plus_Ay = [axi + ayi for axi, ayi in zip(Ax, Ay)]

        return A_xy_sum == Ax_plus_Ay


# ============================================================================
# SECTION 5: Verification Tests
# ============================================================================

class TestDiscreteDynamicalSystems(unittest.TestCase):
    """Tests for discrete dynamical systems."""

    def setUp(self):
        self.system = FiniteDynamicalSystem(state_space_size=10)

    def test_orbit_detection(self):
        """Test basic orbit and cycle detection."""
        # Simple function: x -> (x + 3) mod 10
        F = lambda x: (x + 3) % 10
        result = self.system.compute_orbit(F, 0)

        self.assertIsNotNone(result)
        cycle_start, cycle_length, orbit = result
        self.assertEqual(cycle_length, 10)  # Full cycle
        self.assertEqual(len(set(orbit)), 10)  # All states visited

    def test_pigeonhole_principle(self):
        """Test pigeonhole principle verification."""
        F = lambda x: (x * 2 + 1) % 7
        holds = self.system.verify_pigeonhole_principle(F, 1)
        self.assertTrue(holds)

    def test_cycle_finding(self):
        """Test finding all cycles in a system."""
        # Identity function: each state is its own cycle
        F = lambda x: x
        cycles = self.system.find_all_cycles(F)
        self.assertEqual(len(cycles), 10)  # 10 cycles of length 1

    def test_constant_function(self):
        """Test system with constant function."""
        F = lambda x: 5
        result = self.system.compute_orbit(F, 0)
        self.assertIsNotNone(result)
        cycle_start, cycle_length, orbit = result
        self.assertEqual(cycle_length, 1)  # Fixed point
        self.assertEqual(orbit[cycle_start], 5)

    def test_attractor_basins(self):
        """Test attractor basin computation."""
        # Function: x -> (x // 2)
        F = lambda x: x // 2
        basins = self.system.compute_attractor_basin(F, 0)
        self.assertIn(0, basins)  # 0 is always an attractor


class TestIntegerNeuralNetworks(unittest.TestCase):
    """Tests for integer neural network operations."""

    def setUp(self):
        self.quant_scheme = QuantizationScheme(scale=0.1, zero_point=128, bits=8)

    def test_quantization(self):
        """Test quantization and dequantization."""
        x = 1.5
        q = self.quant_scheme.quantize(x)
        dq = self.quant_scheme.dequantize(q)
        self.assertAlmostEqual(dq, x, delta=0.1)

    def test_integer_layer_forward(self):
        """Test integer layer forward pass."""
        weights = [[1, 2], [3, 4]]
        bias = [5, 6]
        layer = IntegerNeuralLayer(weights, bias, self.quant_scheme)

        x = [1, 2]
        output = layer.forward(x)

        self.assertEqual(len(output), 2)
        self.assertTrue(all(isinstance(o, int) for o in output))

    def test_linear_property(self):
        """Test linearity property verification."""
        weights = [[1, 0], [0, 1]]
        bias = [0, 0]
        layer = IntegerNeuralLayer(weights, bias, self.quant_scheme)

        x = [2, 3]
        c = 5
        holds = layer.verify_linear_property(x, c)
        # Should approximately hold for identity layer
        self.assertTrue(holds)

    def test_network_consistency(self):
        """Test network consistency."""
        layer1 = IntegerNeuralLayer([[1, 0], [0, 1]], [0, 0], self.quant_scheme)
        layer2 = IntegerNeuralLayer([[1, 1], [1, 1]], [0, 0], self.quant_scheme)
        network = IntegerNeuralNetwork([layer1, layer2])

        test_inputs = [[1, 2], [3, 4], [5, 6]]
        consistent = network.verify_network_consistency(test_inputs)
        self.assertTrue(consistent)


class TestActivationFunctions(unittest.TestCase):
    """Tests for activation functions."""

    def test_relu(self):
        """Test ReLU activation."""
        self.assertEqual(ActivationFunctions.relu(-5), 0)
        self.assertEqual(ActivationFunctions.relu(0), 0)
        self.assertEqual(ActivationFunctions.relu(5), 5)

    def test_leaky_relu(self):
        """Test Leaky ReLU activation."""
        result_neg = ActivationFunctions.leaky_relu(-10)
        self.assertLess(result_neg, 0)
        result_pos = ActivationFunctions.leaky_relu(10)
        self.assertEqual(result_pos, 10)

    def test_softmax_approx(self):
        """Test approximate softmax."""
        logits = [1, 2, 3]
        probs = ActivationFunctions.softmax_approx(logits)

        self.assertEqual(len(probs), 3)
        self.assertAlmostEqual(sum(probs), 1.0, places=5)
        # Higher logit should get higher probability
        self.assertTrue(probs[2] > probs[1] > probs[0])


class TestIntegerMatrixOps(unittest.TestCase):
    """Tests for integer matrix operations."""

    def test_matmul(self):
        """Test matrix-vector multiplication."""
        A = [[1, 2], [3, 4]]
        x = [5, 6]
        result = IntegerMatrixOps.matmul(A, x)

        expected = [1*5 + 2*6, 3*5 + 4*6]
        self.assertEqual(result, expected)

    def test_distributive_property(self):
        """Test distributive property."""
        A = [[1, 2], [3, 4]]
        x = [1, 2]
        y = [3, 4]

        holds = IntegerMatrixOps.verify_distributive_property(A, x, y)
        self.assertTrue(holds)

    def test_elementwise_multiply(self):
        """Test element-wise multiplication."""
        a = [1, 2, 3]
        b = [4, 5, 6]
        result = IntegerMatrixOps.elementwise_multiply(a, b)

        expected = [4, 10, 18]
        self.assertEqual(result, expected)


# ============================================================================
# SECTION 6: Performance Benchmarks
# ============================================================================

class PerformanceBenchmarks:
    """Performance benchmarks for DCA Chapter 9 operations."""

    @staticmethod
    def benchmark_orbit_computation(state_space_size: int, iterations: int = 100) -> Dict[str, float]:
        """
        Benchmark orbit computation performance.

        Args:
            state_space_size: Size of state space
            iterations: Number of iterations

        Returns:
            Dictionary of timing results
        """
        system = FiniteDynamicalSystem(state_space_size)
        F = lambda x: (x * 7 + 3) % state_space_size

        times = []
        for _ in range(iterations):
            start = time.time()
            system.compute_orbit(F, 0)
            end = time.time()
            times.append(end - start)

        return {
            'mean': sum(times) / len(times),
            'min': min(times),
            'max': max(times)
        }

    @staticmethod
    def benchmark_integer_forward_pass(layer_size: int, iterations: int = 1000) -> Dict[str, float]:
        """
        Benchmark integer neural network forward pass.

        Args:
            layer_size: Size of the layer
            iterations: Number of iterations

        Returns:
            Dictionary of timing results
        """
        quant_scheme = QuantizationScheme(scale=0.1, zero_point=128, bits=8)
        weights = [[1 for _ in range(layer_size)] for _ in range(layer_size)]
        bias = [0 for _ in range(layer_size)]
        layer = IntegerNeuralLayer(weights, bias, quant_scheme)

        x = [1 for _ in range(layer_size)]

        times = []
        for _ in range(iterations):
            start = time.time()
            layer.forward(x)
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

        # Orbit computation benchmarks
        for size in [10, 100, 1000]:
            results[f'orbit_size_{size}'] = PerformanceBenchmarks.benchmark_orbit_computation(size)

        # Neural network benchmarks
        for size in [10, 50, 100]:
            results[f'nn_layer_size_{size}'] = PerformanceBenchmarks.benchmark_integer_forward_pass(size)

        return results


# ============================================================================
# SECTION 7: Main Execution
# ============================================================================

def main():
    """Main execution function for verification."""
    print("=" * 80)
    print("DCA Chapter 9: Discrete Dynamical Systems and Integer AI Operations")
    print("Verification Suite")
    print("=" * 80)
    print()

    # Run unit tests
    print("Running unit tests...")
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    suite.addTests(loader.loadTestsFromTestCase(TestDiscreteDynamicalSystems))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegerNeuralNetworks))
    suite.addTests(loader.loadTestsFromTestCase(TestActivationFunctions))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegerMatrixOps))

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