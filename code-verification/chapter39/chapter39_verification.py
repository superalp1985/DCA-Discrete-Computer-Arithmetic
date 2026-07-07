"""
Chapter 39: Discrete Neural Architecture Search - Verification Code

This module verifies the core concepts from DCA Chapter 39 on neural architecture search:
1. Finite architecture encoding
2. Search space definition
3. Resource constraints
4. Architecture evaluation
5. Discrete optimization
"""

import numpy as np
from typing import List, Tuple, Set, Dict, Optional, Callable
from dataclasses import dataclass
from enum import Enum
import random
import time


class OperationType(Enum):
    """Discrete operation types"""
    CONV3X3 = "conv3x3"
    CONV5X5 = "conv5x5"
    MAXPOOL = "maxpool"
    AVGPOOL = "avgpool"
    IDENTITY = "identity"
    SEPARABLE_CONV = "separable_conv"


@dataclass
class LayerSpec:
    """Layer specification"""
    op: OperationType
    channels: int
    skip: bool

    def encode(self) -> Tuple[int, int, int]:
        """Encode as finite tuple"""
        return (self.op.value, self.channels, int(self.skip))

    @classmethod
    def decode(cls, encoding: Tuple[int, int, int]) -> 'LayerSpec':
        """Decode from tuple"""
        op_code, channels, skip_flag = encoding
        # Map op code to OperationType
        ops = list(OperationType)
        op = ops[op_code % len(ops)]
        return cls(op, channels, bool(skip_flag))


@dataclass
class Architecture:
    """Neural network architecture encoding"""
    layers: List[LayerSpec]
    max_layers: int = 10

    def __post_init__(self):
        # Ensure finite length
        if len(self.layers) > self.max_layers:
            self.layers = self.layers[:self.max_layers]

    def encode(self) -> str:
        """Encode architecture as finite string"""
        parts = []
        for layer in self.layers:
            parts.append(f"{layer.op.value}:{layer.channels}:{int(layer.skip)}")
        return "|".join(parts)

    @classmethod
    def decode(cls, encoding: str) -> 'Architecture':
        """Decode from string"""
        if not encoding:
            return cls([])

        parts = encoding.split("|")
        layers = []
        for part in parts:
            if not part:
                continue
            op_str, ch_str, skip_str = part.split(":")
            layers.append(LayerSpec(
                OperationType(op_str),
                int(ch_str),
                bool(int(skip_str))
            ))
        return cls(layers)

    def size(self) -> int:
        """Return encoding size"""
        return len(self.encode())

    def num_parameters(self) -> int:
        """Estimate number of parameters"""
        total = 0
        for i, layer in enumerate(self.layers):
            if "conv" in layer.op.value:
                # Simple parameter count estimate
                in_ch = self.layers[i-1].channels if i > 0 else 3
                out_ch = layer.channels
                kernel_size = 3 if "3x3" in layer.op.value else 5
                if "separable" in layer.op.value:
                    total += in_ch * kernel_size * kernel_size + out_ch * in_ch
                else:
                    total += in_ch * out_ch * kernel_size * kernel_size
        return total

    def num_flops(self) -> int:
        """Estimate FLOPs"""
        total = 0
        for i, layer in enumerate(self.layers):
            if "conv" in layer.op.value:
                in_ch = self.layers[i-1].channels if i > 0 else 3
                out_ch = layer.channels
                kernel_size = 3 if "3x3" in layer.op.value else 5
                input_size = 32 // (2 ** i)  # Simple downsampling model
                total += in_ch * out_ch * kernel_size * kernel_size * input_size * input_size
        return total


class SearchSpace:
    """
    Finite search space for NAS
    """

    def __init__(self,
                 operations: List[OperationType],
                 channel_options: List[int],
                 max_layers: int,
                 skip_allowed: bool = True):
        self.operations = operations
        self.channel_options = channel_options
        self.max_layers = max_layers
        self.skip_allowed = skip_allowed

    def size(self) -> int:
        """Compute total size of search space"""
        layer_options = len(self.operations) * len(self.channel_options)
        if self.skip_allowed:
            layer_options *= 2

        # Sum over all possible lengths
        total = 0
        for L in range(1, self.max_layers + 1):
            total += layer_options ** L

        return total

    def random_architecture(self) -> Architecture:
        """Generate random architecture"""
        num_layers = random.randint(1, self.max_layers)
        layers = []

        for _ in range(num_layers):
            op = random.choice(self.operations)
            channels = random.choice(self.channel_options)
            skip = self.skip_allowed and random.choice([True, False])
            layers.append(LayerSpec(op, channels, skip))

        return Architecture(layers)

    def enumerate_architectures(self, max_count: int = 1000) -> List[Architecture]:
        """Enumerate some architectures (limited)"""
        archs = []
        for _ in range(min(max_count, self.size())):
            archs.append(self.random_architecture())
        return archs


class ResourceConstraint:
    """
    Resource constraints for architecture
    """

    def __init__(self,
                 max_params: int,
                 max_flops: int,
                 max_memory: int):
        self.max_params = max_params
        self.max_flops = max_flops
        self.max_memory = max_memory

    def satisfies(self, arch: Architecture) -> bool:
        """Check if architecture satisfies constraints"""
        return (arch.num_parameters() <= self.max_params and
                arch.num_flops() <= self.max_flops)


class ArchitectureEvaluator:
    """
    Evaluate architecture performance
    """

    def __init__(self, constraint: ResourceConstraint):
        self.constraint = constraint

    def evaluate(self, arch: Architecture) -> Dict[str, float]:
        """
        Evaluate architecture with multiple metrics

        Returns dict with:
        - accuracy: estimated accuracy (0-1)
        - latency: estimated latency (ms)
        - params: parameter count
        - flops: FLOP count
        - memory: memory usage
        """
        # Simplified mock evaluation
        # In real NAS, would train and evaluate

        # Mock accuracy based on architecture
        base_acc = 0.7
        for layer in arch.layers:
            if layer.op == OperationType.CONV3X3:
                base_acc += 0.01
            elif layer.op == OperationType.CONV5X5:
                base_acc += 0.015
            elif layer.op == OperationType.SEPARABLE_CONV:
                base_acc += 0.012

        accuracy = min(0.95, base_acc)

        # Latency proportional to FLOPs
        latency = arch.num_flops() / 1e6  # ms

        return {
            'accuracy': accuracy,
            'latency': latency,
            'params': arch.num_parameters(),
            'flops': arch.num_flops(),
            'memory': arch.num_parameters() * 4  # bytes (float32)
        }


class NASSearcher:
    """
    Neural Architecture Search
    """

    def __init__(self,
                 search_space: SearchSpace,
                 evaluator: ArchitectureEvaluator,
                 budget: int = 100):
        self.search_space = search_space
        self.evaluator = evaluator
        self.budget = budget
        self.best_arch = None
        self.best_score = -1
        self.history = []

    def random_search(self) -> Architecture:
        """Random search for best architecture"""
        for _ in range(self.budget):
            arch = self.search_space.random_architecture()

            # Check constraints
            if not self.evaluator.constraint.satisfies(arch):
                continue

            # Evaluate
            metrics = self.evaluator.evaluate(arch)
            score = metrics['accuracy'] - 0.001 * metrics['latency']

            self.history.append((arch, metrics, score))

            if score > self.best_score:
                self.best_score = score
                self.best_arch = arch

        return self.best_arch

    def evaluate_population(self, population: List[Architecture]) -> List[Dict]:
        """Evaluate all architectures in population"""
        results = []
        for arch in population:
            if self.evaluator.constraint.satisfies(arch):
                metrics = self.evaluator.evaluate(arch)
                results.append(metrics)
        return results


def verify_finite_encoding():
    """
    Verify architecture has finite encoding
    """
    print("Testing Finite Encoding...")

    ops = [OperationType.CONV3X3, OperationType.MAXPOOL]
    layers = [LayerSpec(ops[0], 64, False), LayerSpec(ops[1], 64, True)]
    arch = Architecture(layers)

    # Encoding should be finite string
    encoding = arch.encode()
    assert isinstance(encoding, str)
    assert len(encoding) < float('inf')

    # Decoding should work
    decoded = Architecture.decode(encoding)
    assert len(decoded.layers) == len(arch.layers)

    print("  ✓ Finite encoding verified")
    return True


def verify_search_space_finiteness():
    """
    Verify search space is finite
    """
    print("Testing Search Space Finiteness...")

    space = SearchSpace(
        operations=[OperationType.CONV3X3, OperationType.CONV5X5],
        channel_options=[32, 64],
        max_layers=3
    )

    # Size should be finite
    size = space.size()
    assert size < float('inf')

    # Compute expected size
    # Layer options: 2 ops * 2 channels = 4
    # Total: 4^1 + 4^2 + 4^3 = 4 + 16 + 64 = 84
    assert size == 84

    print("  ✓ Search space finiteness verified")
    return True


def verify_resource_constraints():
    """
    Verify resource constraints are enforced
    """
    print("Testing Resource Constraints...")

    constraint = ResourceConstraint(
        max_params=100000,
        max_flops=10000000,
        max_memory=400000
    )

    # Small architecture should satisfy
    arch_small = Architecture([
        LayerSpec(OperationType.CONV3X3, 16, False)
    ])
    assert constraint.satisfies(arch_small)

    # Large architecture should violate
    arch_large = Architecture([
        LayerSpec(OperationType.CONV3X3, 512, False),
        LayerSpec(OperationType.CONV3X3, 512, False),
        LayerSpec(OperationType.CONV3X3, 512, False)
    ])
    assert not constraint.satisfies(arch_large)

    print("  ✓ Resource constraints verified")
    return True


def verify_architecture_evaluation():
    """
    Verify architecture evaluation
    """
    print("Testing Architecture Evaluation...")

    constraint = ResourceConstraint(max_params=1000000, max_flops=1e9, max_memory=1e7)
    evaluator = ArchitectureEvaluator(constraint)

    arch = Architecture([
        LayerSpec(OperationType.CONV3X3, 32, False),
        LayerSpec(OperationType.MAXPOOL, 32, False),
        LayerSpec(OperationType.CONV3X3, 64, False)
    ])

    metrics = evaluator.evaluate(arch)

    # Metrics should be valid
    assert 0 <= metrics['accuracy'] <= 1
    assert metrics['latency'] >= 0
    assert metrics['params'] >= 0
    assert metrics['flops'] >= 0

    print("  ✓ Architecture evaluation verified")
    return True


def verify_random_search():
    """
    Verify random search finds valid architectures
    """
    print("Testing Random Search...")

    space = SearchSpace(
        operations=[OperationType.CONV3X3, OperationType.MAXPOOL],
        channel_options=[32, 64],
        max_layers=3
    )

    constraint = ResourceConstraint(max_params=100000, max_flops=1e7, max_memory=1e6)
    evaluator = ArchitectureEvaluator(constraint)

    searcher = NASSearcher(space, evaluator, budget=50)
    best = searcher.random_search()

    # Best architecture should exist
    assert best is not None
    assert len(best.layers) > 0

    # Should satisfy constraints
    assert constraint.satisfies(best)

    print("  ✓ Random search verified")
    return True


def verify_search_space_exhaustion():
    """
    Verify search space can be (theoretically) exhausted
    """
    print("Testing Search Space Exhaustion...")

    space = SearchSpace(
        operations=[OperationType.CONV3X3],
        channel_options=[32],
        max_layers=2
    )

    # Size should be small enough to enumerate
    size = space.size()
    assert size == 3  # 1-layer + 2-layer options

    # Enumerate
    archs = space.enumerate_archures(max_count=10)
    assert len(archs) > 0

    print("  ✓ Search space exhaustion verified")
    return True


def verify_layer_spec_encoding():
    """
    Verify layer specification encoding/decoding
    """
    print("Testing Layer Spec Encoding...")

    layer = LayerSpec(OperationType.CONV5X5, 128, True)

    # Encode
    encoding = layer.encode()
    assert isinstance(encoding, tuple)
    assert len(encoding) == 3

    # Decode
    decoded = LayerSpec.decode(encoding)
    assert decoded.op == layer.op
    assert decoded.channels == layer.channels
    assert decoded.skip == layer.skip

    print("  ✓ Layer spec encoding verified")
    return True


def verify_parameter_estimation():
    """
    Verify parameter count estimation
    """
    print("Testing Parameter Estimation...")

    # Single conv layer
    arch = Architecture([
        LayerSpec(OperationType.CONV3X3, 64, False)
    ])

    # 3 * 64 * 3 * 3 = 1728 parameters (assuming 3 input channels)
    params = arch.num_parameters()
    assert params > 0

    # More layers should have more parameters
    arch2 = Architecture([
        LayerSpec(OperationType.CONV3X3, 64, False),
        LayerSpec(OperationType.CONV3X3, 128, False)
    ])

    params2 = arch2.num_parameters()
    assert params2 > params

    print("  ✓ Parameter estimation verified")
    return True


def verify_flops_estimation():
    """
    Verify FLOP estimation
    """
    print("Testing FLOP Estimation...")

    arch = Architecture([
        LayerSpec(OperationType.CONV3X3, 64, False)
    ])

    flops = arch.num_flops()
    assert flops > 0

    # Larger input or more channels should increase FLOPs
    arch2 = Architecture([
        LayerSpec(OperationType.CONV3X3, 128, False)
    ])

    flops2 = arch2.num_flops()
    assert flops2 > flops

    print("  ✓ FLOP estimation verified")
    return True


def benchmark_nas_search():
    """
    Benchmark NAS search performance
    """
    print("Benchmarking NAS Search...")

    results = []

    for budget in [50, 100, 200]:
        space = SearchSpace(
            operations=list(OperationType)[:4],
            channel_options=[32, 64, 128],
            max_layers=5
        )

        constraint = ResourceConstraint(max_params=1e6, max_flops=1e8, max_memory=1e7)
        evaluator = ArchitectureEvaluator(constraint)

        searcher = NASSearcher(space, evaluator, budget=budget)

        start = time.time()
        best = searcher.random_search()
        elapsed = time.time() - start

        results.append((budget, elapsed, best.best_score if best else 0))
        print(f"  budget={budget}: time={elapsed:.4f}s, score={results[-1][2]:.4f}")

    return results


class TestSuite:
    """Comprehensive test suite for Chapter 39"""

    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.results = []

    def run_test(self, test_func, name: str):
        """Run a single test"""
        try:
            test_func()
            self.passed += 1
            self.results.append((name, "PASSED"))
            print(f"✓ {name} PASSED")
        except AssertionError as e:
            self.failed += 1
            self.results.append((name, f"FAILED: {e}"))
            print(f"✗ {name} FAILED: {e}")
        except Exception as e:
            self.failed += 1
            self.results.append((name, f"ERROR: {e}"))
            print(f"✗ {name} ERROR: {e}")

    def summary(self):
        """Print test summary"""
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)
        print(f"Passed: {self.passed}")
        print(f"Failed: {self.failed}")
        print(f"Total:  {self.passed + self.failed}")
        if self.failed == 0:
            print("✓ ALL TESTS PASSED")
        else:
            print("✗ SOME TESTS FAILED")
        print("="*60)


def main():
    """Run all verification tests"""
    print("="*60)
    print("CHAPTER 39: NEURAL ARCHITECTURE SEARCH VERIFICATION")
    print("="*60)
    print()

    suite = TestSuite()

    # Core concept tests
    suite.run_test(verify_finite_encoding, "Finite Encoding")
    suite.run_test(verify_search_space_finiteness, "Search Space Finiteness")
    suite.run_test(verify_resource_constraints, "Resource Constraints")
    suite.run_test(verify_architecture_evaluation, "Architecture Evaluation")
    suite.run_test(verify_random_search, "Random Search")
    suite.run_test(verify_search_space_exhaustion, "Search Space Exhaustion")
    suite.run_test(verify_layer_spec_encoding, "Layer Spec Encoding")
    suite.run_test(verify_parameter_estimation, "Parameter Estimation")
    suite.run_test(verify_flops_estimation, "FLOP Estimation")

    # Performance benchmarks
    print()
    print("Performance Benchmarks:")
    print("-" * 40)
    benchmark_results = benchmark_nas_search()

    # Summary
    print()
    suite.summary()

    return suite.results, benchmark_results


if __name__ == "__main__":
    main()