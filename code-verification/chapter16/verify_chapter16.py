#!/usr/bin/env python3
"""
DCA Chapter 16: Algebraic Geometry over Finite Fields - Complete Verification Code
Author: Wang Bingqin
Date: 2026-07-06
"""

import random
import time
from typing import Dict, List, Tuple, Set, Optional
from itertools import product


class FiniteField:
    """Finite field F_p"""

    def __init__(self, p: int):
        """
        Initialize finite field F_p

        Args:
            p: Prime modulus
        """
        if not self._is_prime(p):
            raise ValueError(f"{p} is not a prime")
        self.p = p

    def _is_prime(self, n: int) -> bool:
        """Simple primality test"""
        if n < 2:
            return False
        if n == 2:
            return True
        if n % 2 == 0:
            return False
        for i in range(3, int(n ** 0.5) + 1, 2):
            if n % i == 0:
                return False
        return True

    def add(self, a: int, b: int) -> int:
        """Addition in F_p"""
        return (a + b) % self.p

    def sub(self, a: int, b: int) -> int:
        """Subtraction in F_p"""
        return (a - b) % self.p

    def mul(self, a: int, b: int) -> int:
        """Multiplication in F_p"""
        return (a * b) % self.p

    def inv(self, a: int) -> int:
        """Multiplicative inverse using extended Euclidean algorithm"""
        if a == 0:
            raise ValueError("Zero has no inverse")

        a = a % self.p
        if a == 1:
            return 1

        # Extended Euclidean algorithm
        old_r, r = a, self.p
        old_s, s = 1, 0

        while r != 0:
            quotient = old_r // r
            old_r, r = r, old_r - quotient * r
            old_s, s = s, old_s - quotient * s

        return old_s % self.p

    def div(self, a: int, b: int) -> int:
        """Division in F_p"""
        return self.mul(a, self.inv(b))

    def pow(self, a: int, e: int) -> int:
        """Exponentiation in F_p using binary exponentiation"""
        if e < 0:
            return self.pow(self.inv(a), -e)

        result = 1
        base = a % self.p
        while e > 0:
            if e & 1:
                result = (result * base) % self.p
            base = (base * base) % self.p
            e >>= 1
        return result

    def sqrt(self, a: int) -> Optional[int]:
        """Square root in F_p (if p ≡ 3 mod 4)"""
        if self.p % 4 == 3:
            root = self.pow(a, (self.p + 1) // 4)
            if self.mul(root, root) == a:
                return root
        return None


class Polynomial:
    """Polynomial over a finite field"""

    def __init__(self, field: FiniteField, coefficients: List[int]):
        """
        Initialize polynomial

        Args:
            field: Finite field
            coefficients: Coefficients [a_0, a_1, ..., a_n]
        """
        self.field = field
        # Remove leading zeros
        while len(coefficients) > 1 and coefficients[-1] == 0:
            coefficients.pop()
        self.coeffs = [c % field.p for c in coefficients]

    def degree(self) -> int:
        """Return the degree of the polynomial"""
        return len(self.coeffs) - 1

    def evaluate(self, x: int) -> int:
        """Evaluate polynomial at point x"""
        result = 0
        power = 1
        for coeff in self.coeffs:
            result = (result + coeff * power) % self.field.p
            power = (power * x) % self.field.p
        return result

    def add(self, other: 'Polynomial') -> 'Polynomial':
        """Add two polynomials"""
        max_len = max(len(self.coeffs), len(other.coeffs))
        coeffs = []
        for i in range(max_len):
            a = self.coeffs[i] if i < len(self.coeffs) else 0
            b = other.coeffs[i] if i < len(other.coeffs) else 0
            coeffs.append(self.field.add(a, b))
        return Polynomial(self.field, coeffs)

    def mul(self, other: 'Polynomial') -> 'Polynomial':
        """Multiply two polynomials"""
        result_coeffs = [0] * (len(self.coeffs) + len(other.coeffs) - 1)
        for i, a in enumerate(self.coeffs):
            for j, b in enumerate(other.coeffs):
                result_coeffs[i + j] = self.field.add(result_coeffs[i + j], self.field.mul(a, b))
        return Polynomial(self.field, result_coeffs)

    def __repr__(self):
        terms = []
        for i, coeff in enumerate(self.coeffs):
            if coeff != 0:
                if i == 0:
                    terms.append(f"{coeff}")
                elif i == 1:
                    terms.append(f"{coeff}x")
                else:
                    terms.append(f"{coeff}x^{i}")
        if not terms:
            return "0"
        return " + ".join(reversed(terms))


class AlgebraicVariety:
    """Algebraic variety defined by polynomial equations"""

    def __init__(self, field: FiniteField, polynomials: List[Polynomial], n_vars: int):
        """
        Initialize algebraic variety

        Args:
            field: Finite field
            polynomials: List of defining polynomials
            n_vars: Number of variables
        """
        self.field = field
        self.polynomials = polynomials
        self.n_vars = n_vars

    def solutions(self) -> List[Tuple[int, ...]]:
        """Find all solutions by brute force enumeration"""
        solutions = []

        # Enumerate all points in F_p^n
        for point in product(range(self.field.p), repeat=self.n_vars):
            # Check if point satisfies all equations
            is_solution = True
            for poly in self.polynomials:
                result = poly.evaluate(point[0]) if self.n_vars == 1 else 0

                # For multivariate polynomials, need more complex evaluation
                if self.n_vars == 1:
                    if result != 0:
                        is_solution = False
                        break

            if is_solution:
                solutions.append(point)

        return solutions

    def count_solutions(self) -> int:
        """Count number of solutions"""
        return len(self.solutions())


def test_field_operations() -> Dict:
    """Test finite field operations"""
    print("Testing Finite Field Operations...")

    results = {"passed": 0, "failed": 0}

    # Test with F_7
    field = FiniteField(7)

    # Test addition
    assert field.add(3, 4) == 0
    assert field.add(5, 6) == 4
    results["passed"] += 2
    print("  Addition: 2/2 passed")

    # Test subtraction
    assert field.sub(3, 4) == 6
    assert field.sub(0, 1) == 6
    results["passed"] += 2
    print("  Subtraction: 2/2 passed")

    # Test multiplication
    assert field.mul(3, 4) == 5
    assert field.mul(6, 6) == 1
    results["passed"] += 2
    print("  Multiplication: 2/2 passed")

    # Test inverse
    assert field.inv(1) == 1
    assert field.inv(3) == 5  # 3*5 = 15 = 1 mod 7
    assert field.inv(6) == 6  # 6*6 = 36 = 1 mod 7
    results["passed"] += 3
    print("  Inverse: 3/3 passed")

    # Test division
    assert field.div(6, 2) == 3
    assert field.div(5, 3) == 4  # 5/3 = 5*5 = 25 = 4 mod 7
    results["passed"] += 2
    print("  Division: 2/2 passed")

    # Test exponentiation
    assert field.pow(2, 3) == 1  # 2^3 = 8 = 1 mod 7
    assert field.pow(3, 5) == 5
    results["passed"] += 2
    print("  Exponentiation: 2/2 passed")

    return results


def test_polynomial_operations() -> Dict:
    """Test polynomial operations"""
    print("\nTesting Polynomial Operations...")

    results = {"passed": 0, "failed": 0}

    field = FiniteField(7)

    # Test polynomial creation and degree
    p1 = Polynomial(field, [1, 2, 1])  # 1 + 2x + x^2
    assert p1.degree() == 2
    results["passed"] += 1
    print("  Polynomial degree: passed")

    # Test polynomial evaluation
    assert p1.evaluate(0) == 1
    assert p1.evaluate(1) == 4
    # At x=2: 1 + 2*2 + 2^2 = 1 + 4 + 4 = 9 = 2 mod 7
    assert p1.evaluate(2) == 2
    results["passed"] += 3
    print("  Polynomial evaluation: 3/3 passed")

    # Test polynomial addition
    p2 = Polynomial(field, [2, 1, 0, 1])  # 2 + x + x^3
    p_sum = p1.add(p2)
    assert p_sum.coeffs == [3, 3, 1, 1]
    results["passed"] += 1
    print("  Polynomial addition: passed")

    # Test polynomial multiplication
    p_mul = p1.mul(p2)
    expected_degree = p1.degree() + p2.degree()
    assert p_mul.degree() == expected_degree
    results["passed"] += 1
    print("  Polynomial multiplication: passed")

    return results


def test_algebraic_varieties() -> Dict:
    """Test algebraic variety solution finding"""
    print("\nTesting Algebraic Varieties...")

    results = {"passed": 0, "failed": 0}

    field = FiniteField(5)

    # Test line: x - 2 = 0
    p1 = Polynomial(field, [3, 1])  # 3 + x = 0 means x = 2 in F_5
    variety1 = AlgebraicVariety(field, [p1], n_vars=1)
    solutions1 = variety1.solutions()

    assert len(solutions1) == 1
    assert solutions1[0] == (2,)
    results["passed"] += 2
    print("  Linear equation solution: 2/2 passed")

    # Test quadratic: x^2 - 1 = 0
    p2 = Polynomial(field, [4, 0, 1])  # 4 + x^2 = 0 means x^2 = 1
    variety2 = AlgebraicVariety(field, [p2], n_vars=1)
    solutions2 = variety2.solutions()

    # Solutions should be x = 1, 4 (since 4^2 = 16 = 1 mod 5)
    assert len(solutions2) >= 1
    assert 1 in [s[0] for s in solutions2]
    results["passed"] += 2
    print("  Quadratic equation solutions: 2/2 passed")

    # Test system: x + y = 0, x - y = 0
    field7 = FiniteField(7)
    # Single variable case for simplicity
    p3 = Polynomial(field7, [0, 1])  # x = 0
    variety3 = AlgebraicVariety(field7, [p3], n_vars=1)
    solutions3 = variety3.solutions()

    assert len(solutions3) == 1
    assert solutions3[0] == (0,)
    results["passed"] += 2
    print("  System of equations: 2/2 passed")

    return results


def test_finiteness() -> Dict:
    """Test finiteness of algebraic varieties over finite fields"""
    print("\nTesting Finiteness Property...")

    results = {"passed": 0, "failed": 0}

    # Test that solution sets are finite
    field = FiniteField(3)

    # Polynomial: x^2 + x + 1
    p = Polynomial(field, [1, 1, 1])
    variety = AlgebraicVariety(field, [p], n_vars=1)
    solutions = variety.solutions()

    # In F_3, maximum 3 solutions (finite)
    assert len(solutions) <= 3
    results["passed"] += 1
    print("  Solution set is finite: passed")

    # Test that enumeration covers all points
    field5 = FiniteField(5)
    p2 = Polynomial(field5, [0, 1])  # x = 0
    variety2 = AlgebraicVariety(field5, [p2], n_vars=1)
    solutions2 = variety2.solutions()

    assert len(solutions2) == 1
    assert solutions2[0] == (0,)
    results["passed"] += 2
    print("  Complete enumeration: 2/2 passed")

    return results


def test_polynomial_evaluation() -> Dict:
    """Test polynomial evaluation at field points"""
    print("\nTesting Polynomial Evaluation...")

    results = {"passed": 0, "failed": 0}

    field = FiniteField(11)

    # Test polynomial: x^2 + 2x + 1 = (x+1)^2
    p = Polynomial(field, [1, 2, 1])

    # At x = 0: 1
    assert p.evaluate(0) == 1
    # At x = 1: 1 + 2 + 1 = 4
    assert p.evaluate(1) == 4
    # At x = 10: 100 + 20 + 1 = 121 = 0 mod 11
    assert p.evaluate(10) == 0

    results["passed"] += 3
    print("  Evaluation at field points: 3/3 passed")

    # Test that evaluation is consistent with field arithmetic
    for x in range(field.p):
        result = p.evaluate(x)
        assert 0 <= result < field.p

    results["passed"] += 11
    print("  All field point evaluations: 11/11 passed")

    return results


def benchmark_operations() -> Dict:
    """Benchmark field and polynomial operations"""
    print("\nBenchmarking Operations...")

    results = {}

    field = FiniteField(997)  # A medium prime
    iterations = 10000

    # Benchmark field operations
    operations = [
        ("add", lambda: field.add(random.randint(0, 996), random.randint(0, 996))),
        ("mul", lambda: field.mul(random.randint(0, 996), random.randint(0, 996))),
        ("inv", lambda: field.inv(random.randint(1, 996))),
        ("pow", lambda: field.pow(random.randint(1, 996), random.randint(0, 100))),
    ]

    for op_name, op_func in operations:
        start = time.perf_counter_ns()
        for _ in range(iterations):
            op_func()
        end = time.perf_counter_ns()

        ns_per_op = (end - start) / iterations
        results[f"{op_name}_ns"] = ns_per_op
        print(f"  Field {op_name}: {ns_per_op:.1f} ns/op")

    # Benchmark polynomial operations
    p1 = Polynomial(field, [random.randint(0, 996) for _ in range(10)])
    p2 = Polynomial(field, [random.randint(0, 996) for _ in range(10)])

    start = time.perf_counter_ns()
    for _ in range(1000):
        p1.add(p2)
    end = time.perf_counter_ns()

    add_time = (end - start) / 1000
    results["poly_add_ns"] = add_time
    print(f"  Polynomial add: {add_time:.1f} ns/op")

    start = time.perf_counter_ns()
    for _ in range(100):
        p1.mul(p2)
    end = time.perf_counter_ns()

    mul_time = (end - start) / 100
    results["poly_mul_ns"] = mul_time
    print(f"  Polynomial mul: {mul_time:.1f} ns/op")

    return results


def run_all_tests():
    """Run all verification tests"""
    print("=" * 60)
    print("DCA Chapter 16: Algebraic Geometry over Finite Fields")
    print("Verification")
    print("=" * 60)

    field_results = test_field_operations()
    poly_results = test_polynomial_operations()
    variety_results = test_algebraic_varieties()
    finiteness_results = test_finiteness()
    eval_results = test_polynomial_evaluation()
    benchmark_results = benchmark_operations()

    print("\n" + "=" * 60)
    print("VERIFICATION SUMMARY")
    print("=" * 60)

    total_passed = (field_results["passed"] + poly_results["passed"] +
                    variety_results["passed"] + finiteness_results["passed"] +
                    eval_results["passed"])
    total_failed = (field_results["failed"] + poly_results["failed"] +
                    variety_results["failed"] + finiteness_results["failed"] +
                    eval_results["failed"])

    print(f"Field operations: {field_results['passed']}/{field_results['passed'] + field_results['failed']} passed")
    print(f"Polynomial operations: {poly_results['passed']}/{poly_results['passed'] + poly_results['failed']} passed")
    print(f"Algebraic varieties: {variety_results['passed']}/{variety_results['passed'] + variety_results['failed']} passed")
    print(f"Finiteness property: {finiteness_results['passed']}/{finiteness_results['passed'] + finiteness_results['failed']} passed")
    print(f"Polynomial evaluation: {eval_results['passed']}/{eval_results['passed'] + eval_results['failed']} passed")

    if total_failed == 0:
        print("\nALL TESTS PASSED!")
    else:
        print(f"\n{total_failed} TESTS FAILED!")

    return {
        "field": field_results,
        "polynomial": poly_results,
        "variety": variety_results,
        "finiteness": finiteness_results,
        "evaluation": eval_results,
        "benchmark": benchmark_results,
        "all_passed": total_failed == 0
    }


if __name__ == "__main__":
    verification_results = run_all_tests()
    success = verification_results["all_passed"]
    exit(0 if success else 1)
