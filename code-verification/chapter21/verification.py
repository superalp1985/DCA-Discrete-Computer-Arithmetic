"""
DCA Chapter 21: Discrete Metric Spaces - Verification Code
Testing Hamming distance, graph distances, and finite embeddings
"""

import time
import math
from typing import List, Tuple, Dict, Set, Callable
from collections import defaultdict
import heapq

# ============================================================================
# SECTION 1: Metric Space Axioms Verification
# ============================================================================

class MetricSpace:
    """Base class for discrete metric spaces"""
    def __init__(self, elements: List, distance_func: Callable):
        self.elements = elements
        self.distance_func = distance_func
        self.distance_cache = {}

    def distance(self, x, y) -> int:
        """Compute distance between two elements"""
        key = (x, y) if x <= y else (y, x)
        if key not in self.distance_cache:
            self.distance_cache[key] = self.distance_func(x, y)
        return self.distance_cache[key]

    def verify_non_negativity(self) -> Tuple[bool, str]:
        """Verify d(x,y) >= 0 for all x,y"""
        for x in self.elements:
            for y in self.elements:
                d = self.distance(x, y)
                if d < 0:
                    return False, f"Negative distance: d({x},{y}) = {d}"
        return True, "Non-negativity holds"

    def verify_identity(self) -> Tuple[bool, str]:
        """Verify d(x,y) = 0 iff x = y"""
        for x in self.elements:
            for y in self.elements:
                d = self.distance(x, y)
                if x == y and d != 0:
                    return False, f"Identity violation: d({x},{x}) = {d} != 0"
                if x != y and d == 0:
                    return False, f"Identity violation: d({x},{y}) = 0 but x != y"
        return True, "Identity of indiscernibles holds"

    def verify_symmetry(self) -> Tuple[bool, str]:
        """Verify d(x,y) = d(y,x) for all x,y"""
        for x in self.elements:
            for y in self.elements:
                d_xy = self.distance(x, y)
                d_yx = self.distance(y, x)
                if d_xy != d_yx:
                    return False, f"Symmetry violation: d({x},{y}) = {d_xy} != d({y},{x}) = {d_yx}"
        return True, "Symmetry holds"

    def verify_triangle_inequality(self) -> Tuple[bool, str]:
        """Verify d(x,z) <= d(x,y) + d(y,z) for all x,y,z"""
        violations = []
        for x in self.elements:
            for y in self.elements:
                for z in self.elements:
                    d_xz = self.distance(x, z)
                    d_xy = self.distance(x, y)
                    d_yz = self.distance(y, z)
                    if d_xz > d_xy + d_yz:
                        violations.append(f"d({x},{z}) = {d_xz} > d({x},{y}) + d({y},{z}) = {d_xy + d_yz}")
        if violations:
            return False, f"Triangle inequality violated with {len(violations)} cases"
        return True, "Triangle inequality holds"

    def verify_all_axioms(self) -> Dict[str, Tuple[bool, str]]:
        """Verify all metric space axioms"""
        return {
            "non_negativity": self.verify_non_negativity(),
            "identity": self.verify_identity(),
            "symmetry": self.verify_symmetry(),
            "triangle_inequality": self.verify_triangle_inequality()
        }

# ============================================================================
# SECTION 2: Hamming Distance Implementation
# ============================================================================

def hamming_distance(a: int, b: int, bit_width: int = 32) -> int:
    """Compute Hamming distance between two integers"""
    # XOR to find differing bits, then count set bits
    diff = a ^ b
    # Count bits in bit_width range
    mask = (1 << bit_width) - 1
    diff = diff & mask
    return bin(diff).count('1')

def hamming_distance_str(s1: str, s2: str) -> int:
    """Compute Hamming distance between two strings"""
    if len(s1) != len(s2):
        raise ValueError("Strings must be of equal length")
    return sum(c1 != c2 for c1, c2 in zip(s1, s2))

class HammingSpace(MetricSpace):
    """Hamming space for binary strings/numbers"""
    def __init__(self, elements: List[int], bit_width: int = 32):
        super().__init__(elements, lambda a, b: hamming_distance(a, b, bit_width))
        self.bit_width = bit_width

# ============================================================================
# SECTION 3: Graph Distance Implementation
# ============================================================================

class GraphMetricSpace(MetricSpace):
    """Shortest path distance on a weighted graph"""
    def __init__(self, adjacency_list: Dict[int, Dict[int, int]], directed: bool = False):
        self.adjacency = adjacency_list
        self.directed = directed
        self.nodes = list(adjacency_list.keys())
        self.distances = self._compute_all_pairs_shortest_paths()
        super().__init__(self.nodes, lambda x, y: self.distances[x][y])

    def _compute_all_pairs_shortest_paths(self) -> Dict[int, Dict[int, int]]:
        """Compute all-pairs shortest paths using Dijkstra's algorithm"""
        distances = {u: {v: float('inf') for v in self.nodes} for u in self.nodes}
        for u in self.nodes:
            distances[u][u] = 0
            for v, w in self.adjacency.get(u, {}).items():
                distances[u][v] = min(distances[u][v], w)

        for u in self.nodes:
            visited = set()
            pq = [(0, u)]
            while pq:
                d_u_u, curr_u = heapq.heappop(pq)
                if curr_u in visited:
                    continue
                visited.add(curr_u)
                for neighbor, weight in self.adjacency.get(curr_u, {}).items():
                    if d_u_u + weight < distances[u][neighbor]:
                        distances[u][neighbor] = d_u_u + weight
                        heapq.heappush(pq, (distances[u][neighbor], neighbor))

        return distances

# ============================================================================
# SECTION 4: L1 Distance (Manhattan) on Integer Grid
# ============================================================================

class L1GridSpace(MetricSpace):
    """L1 distance (Manhattan) on integer grid"""
    def __init__(self, points: List[Tuple[int, int]]):
        super().__init__(points, lambda p, q: sum(abs(a - b) for a, b in zip(p, q)))

# ============================================================================
# SECTION 5: Isometric Embedding Verification
# ============================================================================

class IsometricEmbedding:
    """Verify isometric embeddings between metric spaces"""

    def __init__(self, source: MetricSpace, target: MetricSpace, embedding: Callable):
        self.source = source
        self.target = target
        self.embedding = embedding

    def verify_isometry(self, epsilon: int = 0) -> Tuple[bool, str]:
        """
        Verify if embedding is isometric
        d_source(x, y) = d_target(embedding(x), embedding(y))
        """
        violations = []
        max_error = 0

        for x in self.source.elements:
            for y in self.source.elements:
                d_src = self.source.distance(x, y)
                d_tgt = self.target.distance(self.embedding(x), self.embedding(y))
                error = abs(d_src - d_tgt)

                max_error = max(max_error, error)

                if error > epsilon:
                    violations.append(
                        f"Distance not preserved: d_src({x},{y}) = {d_src}, "
                        f"d_tgt = {d_tgt}, error = {error}"
                    )

        if violations:
            return False, f"Isometry violated with {len(violations)} cases, max error = {max_error}"
        return True, f"Isometry holds with max error = {max_error}"

# ============================================================================
# SECTION 6: Performance Benchmarking
# ============================================================================

class PerformanceBenchmarks:
    """Benchmark metric space operations"""

    @staticmethod
    def benchmark_hamming_distance(n_bits: int, n_operations: int = 1000000) -> Dict[str, float]:
        """Benchmark Hamming distance computation"""
        print(f"Benchmarking Hamming distance with {n_bits} bits, {n_operations} operations...")

        mask = (1 << n_bits) - 1
        import random

        start = time.time()
        for _ in range(n_operations):
            a = random.randint(0, mask)
            b = random.randint(0, mask)
            hamming_distance(a, b, n_bits)
        elapsed = time.time() - start

        return {
            "total_time": elapsed,
            "operations_per_second": n_operations / elapsed,
            "nanoseconds_per_operation": (elapsed / n_operations) * 1e9
        }

    @staticmethod
    def benchmark_metric_verification(elements: List[int], bit_width: int = 8) -> Dict[str, float]:
        """Benchmark metric space axioms verification"""
        space = HammingSpace(elements, bit_width)

        start = time.time()
        space.verify_all_axioms()
        elapsed = time.time() - start

        n = len(elements)
        n_pairs = n * n
        n_triples = n * n * n

        return {
            "total_time": elapsed,
            "verification_time_per_element_pair": elapsed / n_pairs if n_pairs > 0 else 0,
            "triangle_check_time_per_triple": elapsed / n_triples if n_triples > 0 else 0,
            "elements": n
        }

    @staticmethod
    def benchmark_graph_shortest_path(n_nodes: int, density: float = 0.3) -> Dict[str, float]:
        """Benchmark graph shortest path computation"""
        print(f"Benchmarking graph shortest path with {n_nodes} nodes, density {density}...")

        import random
        adjacency = {i: {} for i in range(n_nodes)}

        for i in range(n_nodes):
            for j in range(n_nodes):
                if i != j and random.random() < density:
                    weight = random.randint(1, 10)
                    adjacency[i][j] = weight
                    adjacency[j][i] = weight

        start = time.time()
        space = GraphMetricSpace(adjacency)
        elapsed = time.time() - start

        return {
            "total_time": elapsed,
            "time_per_node": elapsed / n_nodes,
            "nodes": n_nodes,
            "edges": sum(len(adj[i]) for adj in adjacency.values()) // 2
        }

# ============================================================================
# SECTION 7: Comprehensive Test Suite
# ============================================================================

class TestSuite:
    """Comprehensive test suite for discrete metric spaces"""

    def __init__(self):
        self.results = []
        self.benchmarks = []

    def test_hamming_distance_properties(self) -> bool:
        """Test Hamming distance properties"""
        print("Testing Hamming distance properties...")

        # Test small bit space exhaustively
        bit_width = 4
        elements = list(range(2**bit_width))
        space = HammingSpace(elements, bit_width)
        results = space.verify_all_axioms()

        self.results.append({
            "test": "Hamming Distance Axioms",
            "passed": all(r[0] for r in results.values()),
            "details": results
        })

        passed = self.results[-1]["passed"]
        print(f"  Result: {'PASS' if passed else 'FAIL'}")
        for axiom, (success, msg) in results.items():
            print(f"    {axiom}: {msg}")

        return passed

    def test_l1_distance_properties(self) -> bool:
        """Test L1 distance properties on integer grid"""
        print("Testing L1 distance properties...")

        # Test small grid
        points = [(x, y) for x in range(3) for y in range(3)]
        space = L1GridSpace(points)
        results = space.verify_all_axioms()

        self.results.append({
            "test": "L1 Distance Axioms",
            "passed": all(r[0] for r in results.values()),
            "details": results
        })

        passed = self.results[-1]["passed"]
        print(f"  Result: {'PASS' if passed else 'FAIL'}")
        for axiom, (success, msg) in results.items():
            print(f"    {axiom}: {msg}")

        return passed

    def test_graph_distance_properties(self) -> bool:
        """Test graph shortest path distance properties"""
        print("Testing graph distance properties...")

        # Create a simple test graph
        adjacency = {
            0: {1: 1, 2: 4},
            1: {0: 1, 2: 2, 3: 5},
            2: {0: 4, 1: 2, 3: 1},
            3: {1: 5, 2: 1}
        }

        space = GraphMetricSpace(adjacency)
        results = space.verify_all_axioms()

        self.results.append({
            "test": "Graph Distance Axioms",
            "passed": all(r[0] for r in results.values()),
            "details": results
        })

        passed = self.results[-1]["passed"]
        print(f"  Result: {'PASS' if passed else 'FAIL'}")
        for axiom, (success, msg) in results.items():
            print(f"    {axiom}: {msg}")

        return passed

    def test_string_hamming_distance(self) -> bool:
        """Test Hamming distance on strings"""
        print("Testing string Hamming distance...")

        # Test known cases
        assert hamming_distance_str("1010", "1100") == 2
        assert hamming_distance_str("hello", "hallo") == 1
        assert hamming_distance_str("kitten", "sitting") == 3  # After equal length check

        # Verify metric properties on binary strings of length 4
        strings = [''.join(bits) for bits in zip(*[iter('0')*8 + '1'*8]*4)]
        strings = [format(i, '04b') for i in range(16)]

        passed = True
        for s1 in strings:
            for s2 in strings:
                d1 = hamming_distance_str(s1, s2)
                d2 = hamming_distance(int(s1, 2), int(s2, 2), 4)
                if d1 != d2:
                    passed = False
                    print(f"  Mismatch: {s1}, {s2}: str={d1}, int={d2}")

        self.results.append({
            "test": "String Hamming Distance",
            "passed": passed,
            "details": "String and integer implementations match"
        })

        print(f"  Result: {'PASS' if passed else 'FAIL'}")
        return passed

    def test_isometric_embeddings(self) -> bool:
        """Test isometric embedding verification"""
        print("Testing isometric embeddings...")

        # Create source space (small Hamming space)
        source_elements = [0, 1, 2, 3, 4]
        source = HammingSpace(source_elements, bit_width=3)

        # Create target space (L1 grid)
        target_points = [(0, 0), (1, 0), (0, 1), (1, 1), (2, 0)]
        target = L1GridSpace(target_points)

        # Embedding: map number to binary tuple
        def embedding(x):
            bits = format(x, '03b')
            return (int(bits[0]), int(bits[1]))

        iso = IsometricEmbedding(source, target, embedding)
        result, msg = iso.verify_isometry()

        self.results.append({
            "test": "Isometric Embedding",
            "passed": result,
            "details": msg
        })

        print(f"  Result: {'PASS' if result else 'FAIL'}")
        print(f"  {msg}")

        return result

    def test_triangle_inequality_bitwise(self) -> bool:
        """Verify triangle inequality at bit level for Hamming distance"""
        print("Testing triangle inequality at bit level...")

        # For Hamming distance, triangle inequality holds because
        # each bit where x != z must be counted in either (x != y) or (y != z)
        passed = True

        for a in range(8):
            for b in range(8):
                for c in range(8):
                    d_ac = hamming_distance(a, c, 3)
                    d_ab = hamming_distance(a, b, 3)
                    d_bc = hamming_distance(b, c, 3)

                    if d_ac > d_ab + d_bc:
                        passed = False
                        print(f"  Violation: {a}, {b}, {c}: d({a},{c})={d_ac} > d({a},{b})+d({b},{c})={d_ab+d_bc}")

        self.results.append({
            "test": "Bitwise Triangle Inequality",
            "passed": passed,
            "details": "Verified all 512 triples"
        })

        print(f"  Result: {'PASS' if passed else 'FAIL'}")
        return passed

    def run_all_tests(self) -> Dict[str, any]:
        """Run all tests and return summary"""
        print("=" * 60)
        print("DCA Chapter 21: Discrete Metric Spaces - Test Suite")
        print("=" * 60)

        tests = [
            ("Hamming Distance Properties", self.test_hamming_distance_properties),
            ("L1 Distance Properties", self.test_l1_distance_properties),
            ("Graph Distance Properties", self.test_graph_distance_properties),
            ("String Hamming Distance", self.test_string_hamming_distance),
            ("Isometric Embeddings", self.test_isometric_embeddings),
            ("Bitwise Triangle Inequality", self.test_triangle_inequality_bitwise),
        ]

        for name, test_func in tests:
            print(f"\nRunning: {name}")
            print("-" * 40)
            try:
                test_func()
            except Exception as e:
                print(f"  ERROR: {e}")
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

    def run_benchmarks(self) -> Dict[str, any]:
        """Run performance benchmarks"""
        print("\n" + "=" * 60)
        print("PERFORMANCE BENCHMARKS")
        print("=" * 60)

        self.benchmarks = []

        # Benchmark 1: Hamming distance
        print("\nBenchmark 1: Hamming Distance")
        print("-" * 40)
        for n_bits in [8, 16, 32, 64]:
            result = PerformanceBenchmarks.benchmark_hamming_distance(n_bits)
            self.benchmarks.append({
                "name": f"Hamming Distance ({n_bits} bits)",
                "result": result
            })
            print(f"  {n_bits} bits: {result['operations_per_second']:.0f} ops/sec")

        # Benchmark 2: Metric verification
        print("\nBenchmark 2: Metric Space Verification")
        print("-" * 40)
        for n_elements in [16, 32, 64, 128]:
            elements = list(range(n_elements))
            result = PerformanceBenchmarks.benchmark_metric_verification(elements)
            self.benchmarks.append({
                "name": f"Verification ({n_elements} elements)",
                "result": result
            })
            print(f"  {n_elements} elements: {result['total_time']:.4f}s")

        # Benchmark 3: Graph shortest paths
        print("\nBenchmark 3: Graph Shortest Paths")
        print("-" * 40)
        for n_nodes in [10, 20, 50]:
            result = PerformanceBenchmarks.benchmark_graph_shortest_path(n_nodes)
            self.benchmarks.append({
                "name": f"Graph Shortest Path ({n_nodes} nodes)",
                "result": result
            })
            print(f"  {n_nodes} nodes: {result['total_time']:.4f}s ({result['edges']} edges)")

        return {
            "benchmarks": self.benchmarks
        }

# ============================================================================
# SECTION 8: Main Execution
# ============================================================================

def main():
    """Main execution function"""
    suite = TestSuite()

    # Run tests
    test_results = suite.run_all_tests()

    # Run benchmarks
    benchmark_results = suite.run_benchmarks()

    # Print final summary
    print("\n" + "=" * 60)
    print("FINAL SUMMARY")
    print("=" * 60)
    print(f"Tests Passed: {test_results['passed_tests']}/{test_results['total_tests']}")
    print(f"Success Rate: {test_results['passed_tests']/test_results['total_tests']*100:.1f}%")

    return {
        "test_results": test_results,
        "benchmark_results": benchmark_results
    }

if __name__ == "__main__":
    results = main()