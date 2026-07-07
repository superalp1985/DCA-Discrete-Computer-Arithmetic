#!/usr/bin/env python3
"""
DCA Chapter 3: Discrete Analysis - Verification Code
Author: Wang Bingqin
Date: 2026-07-06

This module implements and verifies discrete calculus operations:
- Finite difference methods for derivatives
- Numerical integration methods
- Error analysis and convergence rates
- Taylor series approximations
"""

import math
import numpy as np
from typing import Callable, List, Tuple, Dict
from dataclasses import dataclass


@dataclass
class TestResult:
    """Stores test results for discrete analysis operations"""
    name: str
    passed: bool
    error: float
    expected_order: float
    actual_order: float
    details: Dict


class DiscreteDerivative:
    """
    Implements finite difference methods for computing discrete derivatives
    """

    @staticmethod
    def forward(f: Callable[[float], float], x: float, h: float) -> float:
        """Forward difference: f'(x) ≈ (f(x+h) - f(x)) / h"""
        return (f(x + h) - f(x)) / h

    @staticmethod
    def backward(f: Callable[[float], float], x: float, h: float) -> float:
        """Backward difference: f'(x) ≈ (f(x) - f(x-h)) / h"""
        return (f(x) - f(x - h)) / h

    @staticmethod
    def central(f: Callable[[float], float], x: float, h: float) -> float:
        """Central difference: f'(x) ≈ (f(x+h) - f(x-h)) / (2h)"""
        return (f(x + h) - f(x - h)) / (2 * h)

    @staticmethod
    def second_order_central(f: Callable[[float], float], x: float, h: float) -> float:
        """Second derivative using central difference: f''(x) ≈ (f(x+h) - 2f(x) + f(x-h)) / h²"""
        return (f(x + h) - 2 * f(x) + f(x - h)) / (h ** 2)

    @staticmethod
    def richardson_extrapolation(f: Callable[[float], float], x: float, h: float, p: int = 2) -> float:
        """
        Richardson extrapolation for higher accuracy
        Uses two approximations with step sizes h and h/2
        """
        d1 = DiscreteDerivative.central(f, x, h)
        d2 = DiscreteDerivative.central(f, x, h / 2)
        return d2 + (d2 - d1) / (2 ** p - 1)

    @staticmethod
    def error_analysis(f: Callable[[float], float],
                      f_prime: Callable[[float], float],
                      x: float,
                      h_values: List[float]) -> Dict[str, List[float]]:
        """
        Analyze error convergence for different finite difference methods
        """
        errors = {
            'forward': [],
            'backward': [],
            'central': [],
            'richardson': []
        }

        for h in h_values:
            errors['forward'].append(abs(DiscreteDerivative.forward(f, x, h) - f_prime(x)))
            errors['backward'].append(abs(DiscreteDerivative.backward(f, x, h) - f_prime(x)))
            errors['central'].append(abs(DiscreteDerivative.central(f, x, h) - f_prime(x)))
            errors['richardson'].append(abs(DiscreteDerivative.richardson_extrapolation(f, x, h) - f_prime(x)))

        return errors

    @staticmethod
    def convergence_order(errors: List[float], h_values: List[float]) -> float:
        """
        Estimate convergence order using two consecutive errors
        Returns p where error ~ O(h^p)
        """
        if len(errors) < 2:
            return 0.0

        # Use ratio of errors for smallest h values
        h_ratio = h_values[-2] / h_values[-1]
        error_ratio = errors[-2] / errors[-1]

        return math.log(error_ratio) / math.log(h_ratio)


class NumericalIntegration:
    """
    Implements numerical integration methods
    """

    @staticmethod
    def left_rectangle(f: Callable[[float], float], a: float, b: float, n: int) -> float:
        """Left Riemann sum"""
        h = (b - a) / n
        return sum(f(a + i * h) for i in range(n)) * h

    @staticmethod
    def right_rectangle(f: Callable[[float], float], a: float, b: float, n: int) -> float:
        """Right Riemann sum"""
        h = (b - a) / n
        return sum(f(a + (i + 1) * h) for i in range(n)) * h

    @staticmethod
    def midpoint(f: Callable[[float], float], a: float, b: float, n: int) -> float:
        """Midpoint rule"""
        h = (b - a) / n
        return sum(f(a + (i + 0.5) * h) for i in range(n)) * h

    @staticmethod
    def trapezoidal(f: Callable[[float], float], a: float, b: float, n: int) -> float:
        """Trapezoidal rule"""
        h = (b - a) / n
        x = [a + i * h for i in range(n + 1)]
        y = [f(xi) for xi in x]
        return h * (0.5 * y[0] + sum(y[1:-1]) + 0.5 * y[-1])

    @staticmethod
    def simpson(f: Callable[[float], float], a: float, b: float, n: int) -> float:
        """Simpson's rule (requires n to be even)"""
        if n % 2 != 0:
            n += 1  # Make n even

        h = (b - a) / n
        x = [a + i * h for i in range(n + 1)]
        y = [f(xi) for xi in x]

        # Simpson's rule: (h/3) * [y0 + 4(y1 + y3 + ...) + 2(y2 + y4 + ...) + yn]
        sum_odd = sum(y[i] for i in range(1, n, 2))
        sum_even = sum(y[i] for i in range(2, n - 1, 2))

        return (h / 3) * (y[0] + 4 * sum_odd + 2 * sum_even + y[-1])

    @staticmethod
    def romberg(f: Callable[[float], float], a: float, b: float, levels: int = 6) -> float:
        """
        Romberg integration - recursive Richardson extrapolation
        Returns the most accurate estimate
        """
        R = np.zeros((levels, levels))

        # First column: trapezoidal rule with different numbers of intervals
        for k in range(levels):
            n = 2 ** k
            R[k, 0] = NumericalIntegration.trapezoidal(f, a, b, n)

        # Fill the table using Richardson extrapolation
        for j in range(1, levels):
            for k in range(j, levels):
                R[k, j] = R[k, j - 1] + (R[k, j - 1] - R[k - 1, j - 1]) / (4 ** j - 1)

        return R[levels - 1, levels - 1]

    @staticmethod
    def adaptive_simpson(f: Callable[[float], float],
                        a: float, b: float,
                        tol: float = 1e-10,
                        max_depth: int = 20) -> Tuple[float, int]:
        """
        Adaptive Simpson's rule - recursively subdivides until tolerance met
        Returns (integral, number of function evaluations)
        """
        count = [0]  # Use list to make it mutable in nested function

        def helper(a, b, whole, fa, fb, fc, depth):
            """Recursive helper function"""
            count[0] += 1
            if depth >= max_depth:
                return whole

            h = (b - a) / 2
            d = a + h / 2
            e = b - h / 2
            fd = f(d)
            fe = f(e)

            # Simpson's rule on left and right halves
            left = (h / 6) * (fa + 4 * fd + fc)
            right = (h / 6) * (fc + 4 * fe + fb)

            if abs(left + right - whole) < 15 * tol:
                return left + right

            # Recursively refine
            return helper(a, c, left, fa, fc, fd, depth + 1) + \
                   helper(c, b, right, fc, fb, fe, depth + 1)

        # Initial Simpson approximation
        c = (a + b) / 2
        fa = f(a)
        fb = f(b)
        fc = f(c)
        whole = (b - a) / 6 * (fa + 4 * fc + fb)

        result = helper(a, b, whole, fa, fb, fc, 0)
        return result, count[0]


class DiscreteAnalysisVerifier:
    """
    Verifier for discrete analysis operations
    """

    def __init__(self):
        self.test_functions = [
            ('exp', math.exp, math.exp),
            ('sin', math.sin, math.cos),
            ('cos', math.cos, lambda x: -math.sin(x)),
            ('x^3', lambda x: x ** 3, lambda x: 3 * x ** 2),
            ('x^4', lambda x: x ** 4, lambda x: 4 * x ** 3),
            ('sqrt', math.sqrt, lambda x: 0.5 / math.sqrt(x) if x > 0 else 0),
            ('ln', math.log, lambda x: 1 / x if x > 0 else 0),
        ]

        self.integration_functions = [
            ('exp', math.exp, lambda x: math.exp(x) - math.exp(0)),
            ('x^2', lambda x: x ** 2, lambda x: x ** 3 / 3),
            ('x^3', lambda x: x ** 3, lambda x: x ** 4 / 4),
            ('sin', math.sin, lambda x: -math.cos(x) + math.cos(0)),
            ('cos', math.cos, lambda x: math.sin(x) - math.sin(0)),
        ]

    def verify_finite_differences(self) -> List[TestResult]:
        """Verify finite difference methods"""
        results = []
        x = 1.0
        h_values = [0.1, 0.05, 0.025, 0.0125, 0.00625, 0.003125]

        for name, f, f_prime in self.test_functions:
            try:
                # Compute errors
                errors = DiscreteDerivative.error_analysis(f, f_prime, x, h_values)

                # Test convergence order
                expected_orders = {
                    'forward': 1.0,
                    'backward': 1.0,
                    'central': 2.0,
                    'richardson': 4.0
                }

                for method, expected_order in expected_orders.items():
                    actual_order = DiscreteDerivative.convergence_order(
                        errors[method], h_values
                    )

                    # Order should be close to expected
                    tol = 0.3  # Allow some deviation
                    passed = abs(actual_order - expected_order) < tol

                    results.append(TestResult(
                        name=f"{name}_{method}_derivative",
                        passed=passed,
                        error=errors[method][-1],
                        expected_order=expected_order,
                        actual_order=actual_order,
                        details={'h_values': h_values, 'errors': errors[method]}
                    ))

            except Exception as e:
                results.append(TestResult(
                    name=f"{name}_derivative",
                    passed=False,
                    error=float('inf'),
                    expected_order=0,
                    actual_order=0,
                    details={'error': str(e)}
                ))

        return results

    def verify_numerical_integration(self) -> List[TestResult]:
        """Verify numerical integration methods"""
        results = []
        a, b = 0.0, 2.0
        n_values = [10, 20, 40, 80, 160, 320]

        for name, f, F in self.integration_functions:
            true_value = F(b) - F(a)

            for n in n_values:
                try:
                    # Left rectangle (O(1/n) convergence)
                    left_result = NumericalIntegration.left_rectangle(f, a, b, n)
                    left_error = abs(left_result - true_value)

                    # Trapezoidal (O(1/n²) convergence)
                    trap_result = NumericalIntegration.trapezoidal(f, a, b, n)
                    trap_error = abs(trap_result - true_value)

                    # Simpson (O(1/n⁴) convergence)
                    simp_result = NumericalIntegration.simpson(f, a, b, n)
                    simp_error = abs(simp_result - true_value)

                    results.append(TestResult(
                        name=f"{name}_left_rectangle_n{n}",
                        passed=left_error < 0.1,
                        error=left_error,
                        expected_order=1.0,
                        actual_order=0,
                        details={'n': n, 'true': true_value, 'computed': left_result}
                    ))

                    results.append(TestResult(
                        name=f"{name}_trapezoidal_n{n}",
                        passed=trap_error < 0.01,
                        error=trap_error,
                        expected_order=2.0,
                        actual_order=0,
                        details={'n': n, 'true': true_value, 'computed': trap_result}
                    ))

                    results.append(TestResult(
                        name=f"{name}_simpson_n{n}",
                        passed=simp_error < 1e-6,
                        error=simp_error,
                        expected_order=4.0,
                        actual_order=0,
                        details={'n': n, 'true': true_value, 'computed': simp_result}
                    ))

                except Exception as e:
                    results.append(TestResult(
                        name=f"{name}_integration",
                        passed=False,
                        error=float('inf'),
                        expected_order=0,
                        actual_order=0,
                        details={'error': str(e)}
                    ))

        return results

    def verify_romberg_integration(self) -> List[TestResult]:
        """Verify Romberg integration"""
        results = []
        a, b = 0.0, math.pi

        for name, f, F in self.integration_functions:
            if name == 'x^2' or name == 'x^3':
                # Skip polynomial tests for this one
                continue

            try:
                true_value = F(b) - F(a)

                # Test different levels
                for levels in [3, 4, 5, 6]:
                    romberg_result = NumericalIntegration.romberg(f, a, b, levels)
                    error = abs(romberg_result - true_value)

                    results.append(TestResult(
                        name=f"{name}_romberg_levels{levels}",
                        passed=error < 1e-10,
                        error=error,
                        expected_order=float('inf'),  # Exponential convergence
                        actual_order=0,
                        details={'levels': levels, 'true': true_value, 'computed': romberg_result}
                    ))

            except Exception as e:
                results.append(TestResult(
                    name=f"{name}_romberg",
                    passed=False,
                    error=float('inf'),
                    expected_order=0,
                    actual_order=0,
                    details={'error': str(e)}
                ))

        return results

    def verify_taylor_series(self) -> List[TestResult]:
        """Verify Taylor series approximations"""
        results = []

        # Taylor expansion of e^x at x=0: e^x = 1 + x + x²/2! + x³/3! + ...
        def taylor_exp(x, n_terms):
            return sum(x ** k / math.factorial(k) for k in range(n_terms))

        # Test points
        test_points = [0.1, 0.5, 1.0]

        for x in test_points:
            true_value = math.exp(x)

            for n_terms in [2, 3, 5, 10]:
                try:
                    approx = taylor_exp(x, n_terms)
                    error = abs(approx - true_value)

                    # Error should decrease with more terms (for |x| < R of convergence)
                    passed = (n_terms == 2) or (error < abs(taylor_exp(x, n_terms - 1) - true_value))

                    results.append(TestResult(
                        name=f"exp_taylor_x{x}_terms{n_terms}",
                        passed=passed,
                        error=error,
                        expected_order=0,
                        actual_order=0,
                        details={'x': x, 'n_terms': n_terms, 'true': true_value, 'approx': approx}
                    ))

                except Exception as e:
                    results.append(TestResult(
                        name=f"exp_taylor_x{x}_terms{n_terms}",
                        passed=False,
                        error=float('inf'),
                        expected_order=0,
                        actual_order=0,
                        details={'error': str(e)}
                    ))

        return results


def benchmark_discrete_operations():
    """Benchmark performance of discrete operations"""
    import time

    print("\n" + "=" * 60)
    print("PERFORMANCE BENCHMARKS")
    print("=" * 60)

    results = {}
    iterations = 100000

    # Benchmark finite difference
    f = math.exp
    x = 1.0
    h = 0.001

    start = time.perf_counter_ns()
    for _ in range(iterations):
        DiscreteDerivative.central(f, x, h)
    end = time.perf_counter_ns()
    results['central_difference_ns'] = (end - start) / iterations

    # Benchmark trapezoidal integration
    start = time.perf_counter_ns()
    for _ in range(1000):
        NumericalIntegration.trapezoidal(f, 0, 1, 1000)
    end = time.perf_counter_ns()
    results['trapezoidal_1000_intervals_ns'] = (end - start) / 1000

    # Benchmark Simpson integration
    start = time.perf_counter_ns()
    for _ in range(1000):
        NumericalIntegration.simpson(f, 0, 1, 100)
    end = time.perf_counter_ns()
    results['simpson_100_intervals_ns'] = (end - start) / 1000

    for op, ns in results.items():
        print(f"  {op}: {ns:.1f} ns/op")

    return results


def run_all_tests():
    """Run all verification tests"""
    print("=" * 60)
    print("DCA Chapter 3: Discrete Analysis Verification")
    print("=" * 60)

    verifier = DiscreteAnalysisVerifier()
    all_results = []

    print("\n" + "=" * 60)
    print("FINITE DIFFERENCE METHODS")
    print("=" * 60)

    fd_results = verifier.verify_finite_differences()
    all_results.extend(fd_results)

    # Print summary for finite differences
    fd_summary = {}
    for result in fd_results:
        method = result.name.split('_')[-1]
        if method not in fd_summary:
            fd_summary[method] = []
        fd_summary[method].append(result.passed)

    for method, passed_list in fd_summary.items():
        total = len(passed_list)
        passed = sum(passed_list)
        print(f"\n{method.capitalize()}: {passed}/{total} passed")

    print("\n" + "=" * 60)
    print("NUMERICAL INTEGRATION")
    print("=" * 60)

    int_results = verifier.verify_numerical_integration()
    all_results.extend(int_results)

    # Print summary for integration
    int_summary = {'left_rectangle': [], 'trapezoidal': [], 'simpson': []}
    for result in int_results:
        for method in int_summary:
            if method in result.name:
                int_summary[method].append(result.passed)
                break

    for method, passed_list in int_summary.items():
        total = len(passed_list)
        passed = sum(passed_list)
        print(f"\n{method.replace('_', ' ').title()}: {passed}/{total} passed")

    print("\n" + "=" * 60)
    print("ROMBERG INTEGRATION")
    print("=" * 60)

    romberg_results = verifier.verify_romberg_integration()
    all_results.extend(romberg_results)

    passed = sum(r.passed for r in romberg_results)
    total = len(romberg_results)
    print(f"\nRomberg: {passed}/{total} passed")

    print("\n" + "=" * 60)
    print("TAYLOR SERIES")
    print("=" * 60)

    taylor_results = verifier.verify_taylor_series()
    all_results.extend(taylor_results)

    passed = sum(r.passed for r in taylor_results)
    total = len(taylor_results)
    print(f"\nTaylor Series: {passed}/{total} passed")

    # Performance benchmarks
    bench_results = benchmark_discrete_operations()

    # Overall summary
    print("\n" + "=" * 60)
    print("OVERALL SUMMARY")
    print("=" * 60)

    total_tests = len(all_results)
    passed_tests = sum(r.passed for r in all_results)

    print(f"\nTotal tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {total_tests - passed_tests}")
    print(f"Success rate: {passed_tests / total_tests * 100:.1f}%")

    if passed_tests == total_tests:
        print("\n✓ ALL TESTS PASSED!")
    else:
        print(f"\n✗ {total_tests - passed_tests} TESTS FAILED!")
        print("\nFailed tests:")
        for result in all_results:
            if not result.passed:
                print(f"  - {result.name}: {result.details}")

    return {
        'verification': all_results,
        'benchmarks': bench_results
    }


if __name__ == "__main__":
    import sys

    # Check if numpy is available
    try:
        import numpy as np
        results = run_all_tests()
        sys.exit(0 if all(r.passed for r in results['verification']) else 1)
    except ImportError:
        print("Error: numpy is required for Romberg integration")
        print("Install with: pip install numpy")
        sys.exit(1)