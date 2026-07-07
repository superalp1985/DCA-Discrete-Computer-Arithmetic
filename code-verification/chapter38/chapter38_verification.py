"""
Chapter 38: Discrete Spectral Theory - Verification Code

This module verifies the core concepts from DCA Chapter 38 on discrete spectral theory:
1. Graph Laplacian matrix
2. Spectral properties
3. Connected components and null space
4. Quadratic form x^T L x
5. Integer invariants
"""

import numpy as np
from typing import List, Tuple, Set, Dict, Optional
from dataclasses import dataclass
from collections import deque
import time


@dataclass
class Graph:
    """Finite graph with integer weights"""
    vertices: Set[int]
    edges: Set[Tuple[int, int]]
    weighted: bool = False
    weights: Dict[Tuple[int, int], int] = None

    def __post_init__(self):
        if self.weighted and self.weights is None:
            self.weights = {}

    def adjacency_matrix(self) -> List[List[int]]:
        """Return adjacency matrix"""
        n = len(self.vertices)
        vertex_list = sorted(self.vertices)
        vertex_index = {v: i for i, v in enumerate(vertex_list)}

        A = [[0] * n for _ in range(n)]
        for u, v in self.edges:
            i = vertex_index[u]
            j = vertex_index[v]
            w = self.weights.get((u, v), 1) if self.weighted else 1
            A[i][j] = w
            A[j][i] = w

        return A

    def degree_matrix(self) -> List[List[int]]:
        """Return degree matrix"""
        n = len(self.vertices)
        vertex_list = sorted(self.vertices)
        vertex_index = {v: i for i, v in enumerate(vertex_list)}

        # Compute degrees
        degrees = [0] * n
        for u, v in self.edges:
            i = vertex_index[u]
            j = vertex_index[v]
            w = self.weights.get((u, v), 1) if self.weighted else 1
            degrees[i] += w
            degrees[j] += w

        # Create diagonal matrix
        D = [[degrees[i] if i == j else 0 for j in range(n)] for i in range(n)]
        return D

    def laplacian_matrix(self) -> List[List[int]]:
        """Return graph Laplacian L = D - A"""
        D = np.array(self.degree_matrix())
        A = np.array(self.adjacency_matrix())
        L = D - A
        return L.tolist()

    def is_connected(self) -> bool:
        """Check if graph is connected using BFS"""
        if not self.vertices:
            return True

        start = next(iter(self.vertices))
        visited = set()
        queue = deque([start])

        while queue:
            v = queue.popleft()
            if v in visited:
                continue
            visited.add(v)

            for u in self.vertices:
                if (v, u) in self.edges or (u, v) in self.edges:
                    if u not in visited:
                        queue.append(u)

        return visited == self.vertices

    def connected_components(self) -> List[Set[int]]:
        """Return list of connected components"""
        if not self.vertices:
            return []

        components = []
        unvisited = set(self.vertices)

        while unvisited:
            start = next(iter(unvisited))
            component = set()
            queue = deque([start])

            while queue:
                v = queue.popleft()
                if v in component:
                    continue
                component.add(v)

                for u in self.vertices:
                    if (v, u) in self.edges or (u, v) in self.edges:
                        if u not in component:
                            queue.append(u)

            components.append(component)
            unvisited -= component

        return components

    def num_connected_components(self) -> int:
        """Return number of connected components"""
        return len(self.connected_components())


def verify_laplacian_definition():
    """
    Verify graph Laplacian definition: L = D - A
    """
    print("Testing Laplacian Definition...")

    # Simple triangle graph
    g = Graph({0, 1, 2}, {(0, 1), (1, 2), (0, 2)})

    A = g.adjacency_matrix()
    D = g.degree_matrix()
    L = g.laplacian_matrix()

    # Verify L = D - A
    for i in range(3):
        for j in range(3):
            assert L[i][j] == D[i][j] - A[i][j]

    # Expected L for triangle:
    # [[ 2, -1, -1],
    #  [-1,  2, -1],
    #  [-1, -1,  2]]
    expected = [[2, -1, -1], [-1, 2, -1], [-1, -1, 2]]
    assert L == expected

    print("  ✓ Laplacian definition verified")
    return True


def verify_quadratic_form():
    """
    Verify quadratic form identity: x^T L x = sum_{(u,v) in E} (x_u - x_v)^2
    """
    print("Testing Quadratic Form Identity...")

    # Path graph: 0 - 1 - 2
    g = Graph({0, 1, 2}, {(0, 1), (1, 2)})
    L = np.array(g.laplacian_matrix())

    # Test with different x vectors
    test_vectors = [
        [1, 2, 3],
        [0, 1, 0],
        [5, 5, 5],
        [1, 0, 1]
    ]

    for x in test_vectors:
        x_arr = np.array(x)

        # Compute x^T L x
        quadratic_form = x_arr @ L @ x_arr

        # Compute sum of (x_u - x_v)^2 over edges
        edge_sum = 0
        for u, v in g.edges:
            edge_sum += (x[u] - x[v]) ** 2

        assert abs(quadratic_form - edge_sum) < 1e-6, \
            f"Quadratic form mismatch: {quadratic_form} vs {edge_sum}"

    print("  ✓ Quadratic form identity verified")
    return True


def verify_laplacian_properties():
    """
    Verify basic Laplacian properties:
    1. Symmetric
    2. Row sums are zero
    3. Positive semidefinite
    """
    print("Testing Laplacian Properties...")

    g = Graph({0, 1, 2, 3}, {(0, 1), (1, 2), (2, 3), (3, 0)})
    L = np.array(g.laplacian_matrix())

    # 1. Symmetric
    n = len(L)
    for i in range(n):
        for j in range(n):
            assert L[i][j] == L[j][i], f"Non-symmetric at ({i},{j})"

    # 2. Row sums are zero
    for i in range(n):
        row_sum = sum(L[i, :])
        assert abs(row_sum) < 1e-6, f"Row {i} sum = {row_sum}, should be 0"

    # 3. Positive semidefinite (all eigenvalues >= 0)
    eigenvalues = np.linalg.eigvals(L)
    for eig in eigenvalues:
        assert abs(eig.imag) < 1e-6 or eig.imag >= 0  # Should be real
        assert eig.real >= -1e-6, f"Negative eigenvalue: {eig}"

    print("  ✓ Laplacian properties verified")
    return True


def verify_null_space_dimension():
    """
    Verify dimension of null space equals number of connected components
    """
    print("Testing Null Space Dimension...")

    # Connected graph (null space dimension = 1)
    g_connected = Graph({0, 1, 2}, {(0, 1), (1, 2)})
    L = np.array(g_connected.laplacian_matrix())

    # Compute null space dimension
    eigenvalues = np.linalg.eigvals(L)
    null_dim = sum(1 for eig in eigenvalues if abs(eig.real) < 1e-6)

    assert null_dim == 1, f"Expected null dim 1, got {null_dim}"
    assert g_connected.num_connected_components() == 1

    # Disconnected graph (null space dimension = number of components)
    g_disconnected = Graph({0, 1, 2, 3}, {(0, 1), (2, 3)})
    L = np.array(g_disconnected.laplacian_matrix())

    eigenvalues = np.linalg.eigvals(L)
    null_dim = sum(1 for eig in eigenvalues if abs(eig.real) < 1e-6)

    components = g_disconnected.num_connected_components()
    assert null_dim == components, f"Expected null dim {components}, got {null_dim}"

    print("  ✓ Null space dimension verified")
    return True


def verify_constant_vectors_in_null_space():
    """
    Verify constant vectors are in null space of connected component
    """
    print("Testing Constant Vectors in Null Space...")

    g = Graph({0, 1, 2}, {(0, 1), (1, 2)})
    L = np.array(g.laplacian_matrix())

    # Constant vector
    ones = np.array([1, 1, 1])

    # L * ones should be zero
    result = L @ ones
    assert np.allclose(result, 0), f"L*ones = {result}, should be zero"

    # Any constant vector
    c = 5
    constant_vec = np.array([c, c, c])
    result = L @ constant_vec
    assert np.allclose(result, 0), f"L*constant = {result}, should be zero"

    print("  ✓ Constant vectors in null space verified")
    return True


def verify_second_smallest_eigenvalue():
    """
    Verify algebraic connectivity (Fiedler value):
    Second smallest eigenvalue > 0 iff graph is connected
    """
    print("Testing Second Smallest Eigenvalue...")

    # Connected graph
    g_connected = Graph({0, 1, 2}, {(0, 1), (1, 2)})
    L = np.array(g_connected.laplacian_matrix())
    eigenvalues = sorted(np.linalg.eigvals(L).real)

    # Second eigenvalue should be > 0
    assert eigenvalues[1] > 1e-6, f"Fiedler value = {eigenvalues[1]}, should be > 0"

    # Disconnected graph
    g_disconnected = Graph({0, 1, 2, 3}, {(0, 1), (2, 3)})
    L = np.array(g_disconnected.laplacian_matrix())
    eigenvalues = sorted(np.linalg.eigvals(L).real)

    # Second eigenvalue should be 0
    assert abs(eigenvalues[1]) < 1e-6, f"Fiedler value = {eigenvalues[1]}, should be 0"

    print("  ✓ Second smallest eigenvalue verified")
    return True


def verify_cut_size():
    """
    Verify cut size computation
    """
    print("Testing Cut Size...")

    g = Graph({0, 1, 2, 3}, {(0, 1), (1, 2), (2, 3), (3, 0)})

    def cut_size(S: Set[int], graph: Graph) -> int:
        """Count edges crossing cut (S, V\\S)"""
        count = 0
        for u, v in graph.edges:
            if (u in S and v not in S) or (v in S and u not in S):
                count += 1
        return count

    # Cut {0, 1} from {2, 3}
    S = {0, 1}
    size = cut_size(S, g)
    assert size == 2  # Edges (1, 2) and (0, 3) cross

    print("  ✓ Cut size verified")
    return True


def verify_integer_invariants():
    """
    Verify integer invariants are preserved
    """
    print("Testing Integer Invariants...")

    g = Graph({0, 1, 2}, {(0, 1), (1, 2)})

    # Laplacian should have integer entries
    L = g.laplacian_matrix()
    for row in L:
        for entry in row:
            assert isinstance(entry, int) or entry.is_integer()

    # Trace of L should be integer (sum of degrees)
    trace = sum(L[i][i] for i in range(len(L)))
    assert isinstance(trace, int)

    print("  ✓ Integer invariants verified")
    return True


def verify_spectral_properties():
    """
    Verify spectral properties:
    - 0 is always an eigenvalue
    - Eigenvalues are non-negative
    """
    print("Testing Spectral Properties...")

    # Test on various graphs
    graphs = [
        Graph({0}, set()),  # Single vertex
        Graph({0, 1}, {(0, 1)}),  # Single edge
        Graph({0, 1, 2}, {(0, 1), (1, 2)}),  # Path
        Graph({0, 1, 2}, {(0, 1), (1, 2), (0, 2)}),  # Triangle
    ]

    for g in graphs:
        L = np.array(g.laplacian_matrix())
        eigenvalues = np.linalg.eigvals(L).real

        # 0 should be eigenvalue
        has_zero = any(abs(eig) < 1e-6 for eig in eigenvalues)
        assert has_zero, "0 should be eigenvalue"

        # All eigenvalues non-negative
        assert all(eig >= -1e-6 for eig in eigenvalues), "Eigenvalues should be non-negative"

    print("  ✓ Spectral properties verified")
    return True


def verify_laplacian_rank():
    """
    Verify rank of Laplacian = n - number_of_components
    """
    print("Testing Laplacian Rank...")

    # Connected graph
    g_connected = Graph({0, 1, 2}, {(0, 1), (1, 2)})
    L = np.array(g_connected.laplacian_matrix())
    rank = np.linalg.matrix_rank(L)
    n = len(g_connected.vertices)
    components = g_connected.num_connected_components()

    assert rank == n - components, f"Rank = {rank}, n - c = {n - components}"

    # Disconnected graph
    g_disconnected = Graph({0, 1, 2, 3}, {(0, 1), (2, 3)})
    L = np.array(g_disconnected.laplacian_matrix())
    rank = np.linalg.matrix_rank(L)
    n = len(g_disconnected.vertices)
    components = g_disconnected.num_connected_components()

    assert rank == n - components, f"Rank = {rank}, n - c = {n - components}"

    print("  ✓ Laplacian rank verified")
    return True


def benchmark_spectral_computation():
    """
    Benchmark spectral computation
    """
    print("Benchmarking Spectral Computation...")

    results = []

    for n in [10, 20, 50]:
        # Create random graph
        import random
        vertices = set(range(n))
        edges = set()
        for i in range(n):
            for j in range(i + 1, n):
                if random.random() < 0.3:  # 30% edge probability
                    edges.add((i, j))

        g = Graph(vertices, edges)

        # Benchmark Laplacian computation
        start = time.time()
        L = g.laplacian_matrix()
        laplacian_time = time.time() - start

        # Benchmark eigenvalue computation
        start = time.time()
        L_np = np.array(L)
        eigenvalues = np.linalg.eigvals(L_np).real
        eigen_time = time.time() - start

        results.append((n, laplacian_time, eigen_time))
        print(f"  n={n}: laplacian={laplacian_time:.4f}s, eigenvalues={eigen_time:.4f}s")

    return results


class TestSuite:
    """Comprehensive test suite for Chapter 38"""

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
    print("CHAPTER 38: DISCRETE SPECTRAL THEORY VERIFICATION")
    print("="*60)
    print()

    suite = TestSuite()

    # Core concept tests
    suite.run_test(verify_laplacian_definition, "Laplacian Definition")
    suite.run_test(verify_quadratic_form, "Quadratic Form Identity")
    suite.run_test(verify_laplacian_properties, "Laplacian Properties")
    suite.run_test(verify_null_space_dimension, "Null Space Dimension")
    suite.run_test(verify_constant_vectors_in_null_space, "Constant Vectors in Null Space")
    suite.run_test(verify_second_smallest_eigenvalue, "Second Smallest Eigenvalue")
    suite.run_test(verify_cut_size, "Cut Size")
    suite.run_test(verify_integer_invariants, "Integer Invariants")
    suite.run_test(verify_spectral_properties, "Spectral Properties")
    suite.run_test(verify_laplacian_rank, "Laplacian Rank")

    # Performance benchmarks
    print()
    print("Performance Benchmarks:")
    print("-" * 40)
    benchmark_results = benchmark_spectral_computation()

    # Summary
    print()
    suite.summary()

    return suite.results, benchmark_results


if __name__ == "__main__":
    main()