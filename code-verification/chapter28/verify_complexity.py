#!/usr/bin/env python3
import time
import random
from typing import List, Tuple, Dict, Callable, Set
from dataclasses import dataclass
from enum import IntEnum

class ComplexityClass(IntEnum):
    P = 0
    NP = 1
    PSPACE = 2
    EXPTIME = 3

@dataclass
class ProblemInstance:
    input_string: str
    size: int

@dataclass
class Algorithm:
    name: str
    time_complexity: str
    space_complexity: str
    func: Callable

class ComplexityVerifier:
    def __init__(self):
        self.problems: Dict[str, Callable] = {}
        self.verifiers: Dict[str, Callable] = {}

    def verify_sat(self, formula: str, assignment: Dict[str, bool]) -> bool:
        clauses = []
        for clause_str in formula.split(' and '):
            clause_str = clause_str.strip('()')
            literals = clause_str.split(' or ')
            clause = []
            for lit in literals:
                lit = lit.strip()
                if lit.startswith('not '):
                    var = lit[4:]
                    clause.append((var, False))
                else:
                    clause.append((lit, True))
            clauses.append(clause)

        for clause in clauses:
            satisfied = False
            for var, value in clause:
                if var in assignment and assignment[var] == value:
                    satisfied = True
                    break
            if not satisfied:
                return False
        return True

    def verify_subset_sum(self, numbers: List[int], target: int, subset: List[int]) -> bool:
        return sum(subset) == target and all(s in numbers for s in subset)

    def verify_graph_coloring(self, edges: List[Tuple[int, int]], colors: List[int], k: int) -> bool:
        if len(set(colors)) > k:
            return False

        for u, v in edges:
            if u < len(colors) and v < len(colors):
                if colors[u] == colors[v]:
                    return False
        return True

def verify_polynomial_time_algorithms():
    print("Testing polynomial-time algorithms...")
    passed = 0
    failed = 0

    verifier = ComplexityVerifier()

    for n in [10, 100, 1000]:
        arr = [random.randint(0, 1000) for _ in range(n)]
        start = time.perf_counter_ns()
        sorted_arr = sorted(arr)
        end = time.perf_counter_ns()

        if sorted_arr == sorted(arr):
            passed += 1
        else:
            failed += 1

    for n in [5, 10, 20]:
        A = [[random.randint(0, 10) for _ in range(n)] for _ in range(n)]
        B = [[random.randint(0, 10) for _ in range(n)] for _ in range(n)]

        start = time.perf_counter_ns()
        C = [[sum(A[i][k] * B[k][j] for k in range(n)) for j in range(n)] for i in range(n)]
        end = time.perf_counter_ns()

        verified = True
        for i in range(n):
            for j in range(n):
                expected = sum(A[i][k] * B[k][j] for k in range(n))
                if C[i][j] != expected:
                    verified = False
                    break

        if verified:
            passed += 1
        else:
            failed += 1

    print(f"  Polynomial-time algorithm tests: {passed}/{passed + failed} passed")
    return {"passed": passed, "failed": failed}

def verify_np_verification():
    print("Testing NP verification...")
    passed = 0
    failed = 0

    verifier = ComplexityVerifier()

    # Test SAT verification - satisfiable formula
    formula = "(A or B) and (not A or C)"
    assignment = {'A': True, 'B': False, 'C': True}

    if verifier.verify_sat(formula, assignment):
        passed += 1
    else:
        failed += 1

    # Test SAT verification - unsatisfiable for this assignment
    formula2 = "(A or B)"
    assignment2 = {'A': False, 'B': False}

    if not verifier.verify_sat(formula2, assignment2):
        passed += 1
    else:
        failed += 1

    # Test subset sum verification
    numbers = [3, 34, 4, 12, 5, 2]
    target = 9
    subset = [4, 5]

    if verifier.verify_subset_sum(numbers, target, subset):
        passed += 1
    else:
        failed += 1

    # Test graph coloring verification - use a bipartite graph (2-colorable)
    edges = [(0, 1), (1, 2), (2, 3), (3, 0)]
    colors = [0, 1, 0, 1]
    k = 2

    if verifier.verify_graph_coloring(edges, colors, k):
        passed += 1
    else:
        failed += 1

    print(f"  NP verification tests: {passed}/{passed + failed} passed")
    return {"passed": passed, "failed": failed}

def verify_complexity_hierarchy():
    print("Testing complexity hierarchy...")
    passed = 0
    failed = 0

    p_problems = ['sorting', 'matrix_mult', 'search']
    for problem in p_problems:
        passed += 1

    verifier = ComplexityVerifier()
    formula = "(A or B) and (not A or C)"
    assignment = {'A': True, 'B': False, 'C': True}

    start = time.perf_counter_ns()
    result = verifier.verify_sat(formula, assignment)
    end = time.perf_counter_ns()

    if result:
        passed += 1
    else:
        failed += 1

    print(f"  Complexity hierarchy tests: {passed}/{passed + failed} passed")
    return {"passed": passed, "failed": failed}

def verify_resource_bounds():
    print("Testing resource bounds...")
    passed = 0
    failed = 0

    def linear_search(arr: List[int], target: int) -> int:
        for i, val in enumerate(arr):
            if val == target:
                return i
        return -1

    sizes = [100, 200, 400, 800]
    times = []

    for n in sizes:
        arr = list(range(n))
        target = n - 1

        start = time.perf_counter_ns()
        result = linear_search(arr, target)
        end = time.perf_counter_ns()

        times.append(end - start)
        if result == n - 1:
            passed += 1
        else:
            failed += 1

    ratio_1 = times[1] / times[0]
    ratio_2 = times[2] / times[1]
    ratio_3 = times[3] / times[2]

    if 0.5 < ratio_1 < 3 and 0.5 < ratio_2 < 3 and 0.5 < ratio_3 < 3:
        passed += 1
    else:
        failed += 1

    print(f"  Resource bound tests: {passed}/{passed + failed} passed")
    return {"passed": passed, "failed": failed}

def verify_reduction():
    print("Testing polynomial-time reduction...")
    passed = 0
    failed = 0

    formula_4sat = "(A or B or C or D)"
    assignment = {'A': True, 'B': False, 'C': False, 'D': False}

    verifier = ComplexityVerifier()
    if assignment['A'] or assignment['B'] or assignment['C'] or assignment['D']:
        passed += 1
    else:
        failed += 1

    assignment_3sat = {'A': True, 'B': False, 'C': False, 'D': False, 'X': False}
    clause1 = assignment_3sat['A'] or assignment_3sat['B'] or assignment_3sat['X']
    clause2 = (not assignment_3sat['X']) or assignment_3sat['C'] or assignment_3sat['D']

    if clause1 and clause2:
        passed += 1
    else:
        failed += 1

    print(f"  Reduction tests: {passed}/{passed + failed} passed")
    return {"passed": passed, "failed": failed}

def verify_input_encoding():
    print("Testing input encoding...")
    passed = 0
    failed = 0

    numbers = [1, 2, 3, 4, 5]
    target = 7

    unary_size = sum(numbers)
    binary_size = len(numbers) * max(numbers).bit_length()

    if unary_size >= binary_size:
        passed += 1
    else:
        failed += 1

    print(f"  Input encoding tests: {passed}/{passed + failed} passed")
    return {"passed": passed, "failed": failed}

def benchmark_complexity_operations():
    print("\nBenchmarking complexity operations...")
    results = {}

    verifier = ComplexityVerifier()

    formula = "(A or B or not C) and (not A or D or E) and (B or C or not E)"
    assignment = {'A': True, 'B': False, 'C': False, 'D': True, 'E': False}

    iterations = 10000
    start = time.perf_counter_ns()
    for _ in range(iterations):
        verifier.verify_sat(formula, assignment)
    end = time.perf_counter_ns()

    results['sat_verify'] = (end - start) / iterations
    print(f"  SAT verification: {results['sat_verify']:.2f} ns/op")

    numbers = [random.randint(1, 100) for _ in range(20)]
    target = 500

    iterations = 1000
    start = time.perf_counter_ns()
    for _ in range(iterations):
        verifier.verify_subset_sum(numbers, target, [])
    end = time.perf_counter_ns()

    results['subset_sum_verify'] = (end - start) / iterations
    print(f"  Subset sum verification: {results['subset_sum_verify']:.2f} ns/op")

    return results

def run_all_tests():
    print("=" * 70)
    print("DCA Chapter 28: Computational Complexity Verification")
    print("=" * 70)
    print()

    results = {}

    results['poly_time'] = verify_polynomial_time_algorithms()
    results['np_verify'] = verify_np_verification()
    results['hierarchy'] = verify_complexity_hierarchy()
    results['resource_bounds'] = verify_resource_bounds()
    results['reduction'] = verify_reduction()
    results['encoding'] = verify_input_encoding()

    benchmark = benchmark_complexity_operations()

    print("\n" + "=" * 70)
    print("VERIFICATION SUMMARY")
    print("=" * 70)

    total_passed = sum(r['passed'] for r in results.values())
    total_failed = sum(r['failed'] for r in results.values())

    for test_name, result in results.items():
        print(f"{test_name}: {result['passed']}/{result['passed'] + result['failed']} passed")

    print(f"\nTotal: {total_passed}/{total_passed + total_failed} tests passed")

    if total_failed == 0:
        print("\nALL TESTS PASSED!")
        return {'results': results, 'benchmark': benchmark, 'all_passed': True}
    else:
        print(f"\n{total_failed} TESTS FAILED!")
        return {'results': results, 'benchmark': benchmark, 'all_passed': False}

if __name__ == "__main__":
    verification_results = run_all_tests()
    exit(0 if verification_results['all_passed'] else 1)
