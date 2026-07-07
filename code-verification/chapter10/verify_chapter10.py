#!/usr/bin/env python3
"""
DCA Chapter 10: Discrete Complex Analysis and Dual Numbers
Verification Code for Finite Field Extensions and Automatic Differentiation
"""

import time
import unittest
from typing import Tuple, List, Callable, Optional, Dict
import math


# ============================================================================
# SECTION 1: Finite Field Extensions - Discrete Complex Numbers
# ============================================================================

class FiniteFieldComplex:
    """
    Implementation of complex numbers over finite fields.

    Core formula: F_p[i] = F_p[x]/(x^2 + 1)
    Elements are written as a + bi where i^2 = -1
    """

    def __init__(self, p: int):
        """
        Initialize finite field with complex extension.

        Args:
            p: Prime modulus for the base field
        """
        self.p = p
        self.has_i = self._check_has_i()

    def _check_has_i(self) -> bool:
        """
        Check if sqrt(-1) exists in F_p (i.e., if p ≡ 1 mod 4).

        Returns:
            True if sqrt(-1) exists in base field
        """
        # Using Euler's criterion: (-1)^((p-1)/2) = 1 iff p ≡ 1 mod 4
        return pow(-1, (self.p - 1) // 2, self.p) == 1

    def add(self, z1: Tuple[int, int], z2: Tuple[int, int]) -> Tuple[int, int]:
        """
        Add two complex numbers modulo p.

        Args:
            z1: First complex number (a, b) representing a + bi
            z2: Second complex number (c, d) representing c + di

        Returns:
            Sum (a+c, b+d) mod p
        """
        a, b = z1
        c, d = z2
        return ((a + c) % self.p, (b + d) % self.p)

    def sub(self, z1: Tuple[int, int], z2: Tuple[int, int]) -> Tuple[int, int]:
        """
        Subtract two complex numbers modulo p.

        Args:
            z1: First complex number
            z2: Second complex number

        Returns:
            Difference (a-c, b-d) mod p
        """
        a, b = z1
        c, d = z2
        return ((a - c) % self.p, (b - d) % self.p)

    def mul(self, z1: Tuple[int, int], z2: Tuple[int, int]) -> Tuple[int, int]:
        """
        Multiply two complex numbers modulo p.

        Uses formula: (a+bi)(c+di) = (ac-bd) + (ad+bc)i
        Since i^2 = -1, we have -bd*i^2 = -bd*(-1) = bd

        Args:
            z1: First complex number
            z2: Second complex number

        Returns:
            Product (ac-bd, ad+bc) mod p
        """
        a, b = z1
        c, d = z2
        real = (a * c - b * d) % self.p
        imag = (a * d + b * c) % self.p
        return (real, imag)

    def conj(self, z: Tuple[int, int]) -> Tuple[int, int]:
        """
        Compute complex conjugate.

        Args:
            z: Complex number (a, b)

        Returns:
            Conjugate (a, -b) mod p
        """
        a, b = z
        return (a, (-b) % self.p)

    def norm(self, z: Tuple[int, int]) -> int:
        """
        Compute squared norm: |z|^2 = z * conj(z) = a^2 + b^2

        Args:
            z: Complex number

        Returns:
            Norm modulo p
        """
        a, b = z
        return (a * a + b * b) % self.p

    def pow(self, z: Tuple[int, int], n: int) -> Tuple[int, int]:
        """
        Compute complex exponentiation using binary exponentiation.

        Args:
            z: Base complex number
            n: Exponent (non-negative integer)

        Returns:
            z^n mod p
        """
        if n == 0:
            return (1, 0)  # 1 + 0i
        if n == 1:
            return z

        result = (1, 0)
        base = z
        exp = n

        while exp > 0:
            if exp % 2 == 1:
                result = self.mul(result, base)
            base = self.mul(base, base)
            exp //= 2

        return result

    def inv(self, z: Tuple[int, int]) -> Optional[Tuple[int, int]]:
        """
        Compute multiplicative inverse: z^(-1) = conj(z) / |z|^2

        Args:
            z: Complex number

        Returns:
            Inverse if it exists, None otherwise
        """
        n = self.norm(z)
        if n == 0:
            return None  # Zero has no inverse

        # Compute modular inverse of norm
        try:
            n_inv = pow(n, -1, self.p)
        except ValueError:
            return None  # Inverse doesn't exist

        # Multiply conjugate by n^(-1)
        a, b = self.conj(z)
        return ((a * n_inv) % self.p, (b * n_inv) % self.p)

    def div(self, z1: Tuple[int, int], z2: Tuple[int, int]) -> Optional[Tuple[int, int]]:
        """
        Divide two complex numbers: z1 / z2 = z1 * z2^(-1)

        Args:
            z1: Numerator
            z2: Denominator

        Returns:
            Quotient if denominator is invertible, None otherwise
        """
        z2_inv = self.inv(z2)
        if z2_inv is None:
            return None
        return self.mul(z1, z2_inv)

    def verify_field_axioms(self) -> bool:
        """
        Verify field axioms for the complex extension.

        Returns:
            True if all axioms hold
        """
        # Test a few representative elements
        test_elements = [(1, 2), (3, 4), (5, 6), (0, 1), (1, 0)]

        for a in test_elements:
            for b in test_elements:
                for c in test_elements:
                    # Associativity of addition
                    if self.add(self.add(a, b), c) != self.add(a, self.add(b, c)):
                        return False

                    # Associativity of multiplication
                    if self.mul(self.mul(a, b), c) != self.mul(a, self.mul(b, c)):
                        return False

                    # Distributivity
                    left = self.mul(a, self.add(b, c))
                    right = self.add(self.mul(a, b), self.mul(a, c))
                    if left != right:
                        return False

        return True


# ============================================================================
# SECTION 2: Dual Numbers - Automatic Differentiation
# ============================================================================

class DualNumber:
    """
    Implementation of dual numbers for automatic differentiation.

    Core formula: (a + bε)(c + dε) = ac + (ad + bc)ε, where ε^2 = 0
    This corresponds to forward-mode automatic differentiation.
    """

    def __init__(self, real: float, dual: float = 0.0):
        """
        Initialize a dual number.

        Args:
            real: Real part (value)
            dual: Dual part (derivative)
        """
        self.real = real
        self.dual = dual

    def __add__(self, other: 'DualNumber') -> 'DualNumber':
        """Addition: (a + bε) + (c + dε) = (a+c) + (b+d)ε"""
        if isinstance(other, DualNumber):
            return DualNumber(self.real + other.real, self.dual + other.dual)
        return DualNumber(self.real + other, self.dual)

    def __radd__(self, other: float) -> 'DualNumber':
        """Right addition for scalar + dual"""
        return DualNumber(other + self.real, self.dual)

    def __sub__(self, other: 'DualNumber') -> 'DualNumber':
        """Subtraction: (a + bε) - (c + dε) = (a-c) + (b-d)ε"""
        if isinstance(other, DualNumber):
            return DualNumber(self.real - other.real, self.dual - other.dual)
        return DualNumber(self.real - other, self.dual)

    def __rsub__(self, other: float) -> 'DualNumber':
        """Right subtraction for scalar - dual"""
        return DualNumber(other - self.real, -self.dual)

    def __mul__(self, other: 'DualNumber') -> 'DualNumber':
        """
        Multiplication: (a + bε)(c + dε) = ac + (ad + bc)ε
        Since ε^2 = 0, the bdε^2 term vanishes
        """
        if isinstance(other, DualNumber):
            real = self.real * other.real
            dual = self.real * other.dual + self.dual * other.real
            return DualNumber(real, dual)
        return DualNumber(self.real * other, self.dual * other)

    def __rmul__(self, other: float) -> 'DualNumber':
        """Right multiplication for scalar * dual"""
        return DualNumber(other * self.real, other * self.dual)

    def __truediv__(self, other: 'DualNumber') -> 'DualNumber':
        """
        Division: (a + bε) / (c + dε)
        Using quotient rule: (a/c) + (b*c - a*d)/c^2 * ε
        """
        if isinstance(other, DualNumber):
            c = other.real
            d = other.dual
            real = self.real / c
            dual = (self.dual * c - self.real * d) / (c * c)
            return DualNumber(real, dual)
        return DualNumber(self.real / other, self.dual / other)

    def __pow__(self, n: int) -> 'DualNumber':
        """Integer exponentiation using binary exponentiation"""
        if n == 0:
            return DualNumber(1.0, 0.0)
        if n == 1:
            return DualNumber(self.real, self.dual)

        result = DualNumber(1.0, 0.0)
        base = DualNumber(self.real, self.dual)
        exp = n

        while exp > 0:
            if exp % 2 == 1:
                result = result * base
            base = base * base
            exp //= 2

        return result

    def __neg__(self) -> 'DualNumber':
        """Negation: -(a + bε) = -a - bε"""
        return DualNumber(-self.real, -self.dual)

    def __eq__(self, other: 'DualNumber') -> bool:
        """Equality comparison"""
        if isinstance(other, DualNumber):
            return abs(self.real - other.real) < 1e-10 and abs(self.dual - other.dual) < 1e-10
        return abs(self.real - other) < 1e-10 and self.dual == 0

    def __repr__(self) -> str:
        """String representation"""
        return f"DualNumber({self.real:.4f}, {self.dual:.4f})"

    def value(self) -> float:
        """Get the real part (function value)"""
        return self.real

    def derivative(self) -> float:
        """Get the dual part (derivative)"""
        return self.dual

    @staticmethod
    def exp(x: 'DualNumber') -> 'DualNumber':
        """
        Exponential function: exp(a + bε) = exp(a) + b*exp(a)*ε

        This follows from the chain rule: d/dx exp(x) = exp(x)
        """
        exp_a = math.exp(x.real)
        return DualNumber(exp_a, x.dual * exp_a)

    @staticmethod
    def log(x: 'DualNumber') -> 'DualNumber':
        """
        Natural logarithm: log(a + bε) = log(a) + b/a*ε

        This follows from: d/dx log(x) = 1/x
        """
        log_a = math.log(x.real)
        return DualNumber(log_a, x.dual / x.real)

    @staticmethod
    def sin(x: 'DualNumber') -> 'DualNumber':
        """
        Sine function: sin(a + bε) = sin(a) + b*cos(a)*ε

        This follows from: d/dx sin(x) = cos(x)
        """
        sin_a = math.sin(x.real)
        cos_a = math.cos(x.real)
        return DualNumber(sin_a, x.dual * cos_a)

    @staticmethod
    def cos(x: 'DualNumber') -> 'DualNumber':
        """
        Cosine function: cos(a + bε) = cos(a) - b*sin(a)*ε

        This follows from: d/dx cos(x) = -sin(x)
        """
        cos_a = math.cos(x.real)
        sin_a = math.sin(x.real)
        return DualNumber(cos_a, -x.dual * sin_a)

    @staticmethod
    def sqrt(x: 'DualNumber') -> 'DualNumber':
        """
        Square root: sqrt(a + bε) = sqrt(a) + b/(2*sqrt(a))*ε

        This follows from: d/dx sqrt(x) = 1/(2*sqrt(x))
        """
        sqrt_a = math.sqrt(x.real)
        return DualNumber(sqrt_a, x.dual / (2 * sqrt_a))

    @staticmethod
    def abs(x: 'DualNumber') -> 'DualNumber':
        """
        Absolute value (non-differentiable at 0)
        """
        if x.real >= 0:
            return DualNumber(abs(x.real), x.dual)
        else:
            return DualNumber(abs(x.real), -x.dual)

    @staticmethod
    def max(x: 'DualNumber', y: 'DualNumber') -> 'DualNumber':
        """
        Maximum function (non-differentiable at equality)
        """
        if x.real > y.real:
            return x
        elif y.real > x.real:
            return y
        else:
            # At equality, derivative is ambiguous - use average
            return DualNumber(x.real, (x.dual + y.dual) / 2)

    @staticmethod
    def min(x: 'DualNumber', y: 'DualNumber') -> 'DualNumber':
        """
        Minimum function (non-differentiable at equality)
        """
        if x.real < y.real:
            return x
        elif y.real < x.real:
            return y
        else:
            # At equality, derivative is ambiguous - use average
            return DualNumber(x.real, (x.dual + y.dual) / 2)

    @staticmethod
    def relu(x: 'DualNumber') -> 'DualNumber':
        """
        ReLU activation function
        """
        return DualNumber.max(x, DualNumber(0.0, 0.0))


# ============================================================================
# SECTION 3: Automatic Differentiation Engine
# ============================================================================

class AutoDiffEngine:
    """
    Forward-mode automatic differentiation using dual numbers.
    """

    @staticmethod
    def derivative(f: Callable[[DualNumber], DualNumber], x: float) -> float:
        """
        Compute derivative of function f at point x.

        Args:
            f: Function to differentiate
            x: Point at which to compute derivative

        Returns:
            Derivative f'(x)
        """
        # Create dual number with value x and derivative 1
        dual_x = DualNumber(x, 1.0)
        result = f(dual_x)
        return result.derivative()

    @staticmethod
    def gradient(f: Callable[[List[DualNumber]], DualNumber],
                 x: List[float]) -> List[float]:
        """
        Compute gradient of multivariate function.

        Args:
            f: Function taking list of dual numbers
            x: Point at which to compute gradient

        Returns:
            Gradient vector
        """
        grad = []
        for i in range(len(x)):
            # Create dual inputs where only xi has derivative 1
            dual_inputs = [DualNumber(val, 1.0 if j == i else 0.0)
                          for j, val in enumerate(x)]
            result = f(dual_inputs)
            grad.append(result.derivative())
        return grad

    @staticmethod
    def verify_derivative(f: Callable[[DualNumber], DualNumber],
                         f_prime_numeric: Callable[[float], float],
                         x: float, tol: float = 1e-6) -> bool:
        """
        Verify automatic derivative against numeric derivative.

        Args:
            f: Function using dual numbers
            f_prime_numeric: Numeric derivative function
            x: Test point
            tol: Tolerance for comparison

        Returns:
            True if derivatives match within tolerance
        """
        auto_diff = AutoDiffEngine.derivative(f, x)
        numeric = f_prime_numeric(x)
        return abs(auto_diff - numeric) < tol


# ============================================================================
# SECTION 4: Integer Dual Numbers
# ============================================================================

class IntegerDual:
    """
    Integer version of dual numbers for exact computation.
    """

    def __init__(self, real: int, dual: int = 0):
        """
        Initialize integer dual number.

        Args:
            real: Real part
            dual: Dual part
        """
        self.real = real
        self.dual = dual

    def __add__(self, other: 'IntegerDual') -> 'IntegerDual':
        """Integer addition"""
        if isinstance(other, IntegerDual):
            return IntegerDual(self.real + other.real, self.dual + other.dual)
        return IntegerDual(self.real + other, self.dual)

    def __mul__(self, other: 'IntegerDual') -> 'IntegerDual':
        """
        Integer multiplication: (a + bε)(c + dε) = ac + (ad + bc)ε
        """
        if isinstance(other, IntegerDual):
            real = self.real * other.real
            dual = self.real * other.dual + self.dual * other.real
            return IntegerDual(real, dual)
        return IntegerDual(self.real * other, self.dual * other)

    def __pow__(self, n: int) -> 'IntegerDual':
        """Integer exponentiation"""
        if n == 0:
            return IntegerDual(1, 0)
        if n == 1:
            return IntegerDual(self.real, self.dual)

        result = IntegerDual(1, 0)
        base = IntegerDual(self.real, self.dual)
        exp = n

        while exp > 0:
            if exp % 2 == 1:
                result = result * base
            base = base * base
            exp //= 2

        return result

    def __repr__(self) -> str:
        """String representation"""
        return f"IntegerDual({self.real}, {self.dual})"

    def verify_binomial_theorem(self, n: int) -> bool:
        """
        Verify binomial theorem: (a + b)^n = sum(C(n,k) * a^(n-k) * b^k)

        For dual numbers with ε^2 = 0, this simplifies.

        Args:
            n: Exponent

        Returns:
            True if theorem holds
        """
        # Test with simple values
        a = IntegerDual(2, 3)
        direct = a ** n

        # For dual numbers, (a + bε)^n = a^n + n*a^(n-1)*b*ε
        # because higher powers of ε vanish
        expected_real = self.real ** n
        expected_dual = n * (self.real ** (n - 1)) * self.dual

        return direct.real == expected_real and direct.dual == expected_dual


# ============================================================================
# SECTION 5: Verification Tests
# ============================================================================

class TestFiniteFieldComplex(unittest.TestCase):
    """Tests for finite field complex numbers."""

    def setUp(self):
        self.fp7 = FiniteFieldComplex(7)
        self.fp13 = FiniteFieldComplex(13)

    def test_addition(self):
        """Test complex addition."""
        z1 = (1, 2)
        z2 = (3, 4)
        result = self.fp7.add(z1, z2)
        self.assertEqual(result, (4, 6))

    def test_multiplication(self):
        """Test complex multiplication."""
        z1 = (1, 2)
        z2 = (3, 4)
        result = self.fp7.mul(z1, z2)
        # (1+2i)(3+4i) = 3 + 4i + 6i + 8i^2 = 3 + 10i + 8(-1) = -5 + 10i
        # Mod 7: -5 ≡ 2, 10 ≡ 3
        self.assertEqual(result, (2, 3))

    def test_conjugation(self):
        """Test complex conjugation."""
        z = (3, 4)
        conj = self.fp7.conj(z)
        self.assertEqual(conj, (3, 3))  # -4 mod 7 = 3

    def test_norm(self):
        """Test norm computation."""
        z = (3, 4)
        norm = self.fp7.norm(z)
        self.assertEqual(norm, (3*3 + 4*4) % 7)  # 25 mod 7 = 4

    def test_field_axioms(self):
        """Test field axioms."""
        holds = self.fp13.verify_field_axioms()
        self.assertTrue(holds)

    def test_pow(self):
        """Test complex exponentiation."""
        z = (1, 1)
        result = self.fp7.pow(z, 2)
        expected = self.fp7.mul(z, z)
        self.assertEqual(result, expected)

    def test_inverse(self):
        """Test multiplicative inverse."""
        z = (1, 1)
        inv = self.fp7.inv(z)
        if inv is not None:
            # z * z^(-1) should equal 1
            product = self.fp7.mul(z, inv)
            self.assertEqual(product, (1, 0))


class TestDualNumbers(unittest.TestCase):
    """Tests for dual numbers."""

    def test_addition(self):
        """Test dual number addition."""
        x = DualNumber(3.0, 4.0)
        y = DualNumber(5.0, 6.0)
        result = x + y
        self.assertAlmostEqual(result.real, 8.0)
        self.assertAlmostEqual(result.dual, 10.0)

    def test_multiplication(self):
        """Test dual number multiplication."""
        x = DualNumber(2.0, 3.0)
        y = DualNumber(4.0, 5.0)
        result = x * y
        # (2 + 3ε)(4 + 5ε) = 8 + (10 + 12)ε = 8 + 22ε
        self.assertAlmostEqual(result.real, 8.0)
        self.assertAlmostEqual(result.dual, 22.0)

    def test_epsilon_squared_zero(self):
        """Test that ε^2 = 0."""
        epsilon = DualNumber(0.0, 1.0)
        result = epsilon * epsilon
        self.assertAlmostEqual(result.real, 0.0)
        self.assertAlmostEqual(result.dual, 0.0)

    def test_division(self):
        """Test dual number division."""
        x = DualNumber(6.0, 4.0)
        y = DualNumber(2.0, 1.0)
        result = x / y
        self.assertAlmostEqual(result.real, 3.0, places=5)
        self.assertAlmostEqual(result.dual, 0.5, places=5)

    def test_exponential(self):
        """Test exponential function."""
        x = DualNumber(1.0, 1.0)
        result = DualNumber.exp(x)
        # exp(1 + ε) = exp(1) + exp(1)*ε
        expected = math.exp(1.0)
        self.assertAlmostEqual(result.real, expected)
        self.assertAlmostEqual(result.dual, expected)

    def test_sine(self):
        """Test sine function."""
        x = DualNumber(math.pi / 2, 1.0)
        result = DualNumber.sin(x)
        # sin(π/2 + ε) = sin(π/2) + cos(π/2)*ε = 1 + 0*ε
        self.assertAlmostEqual(result.real, 1.0, places=5)
        self.assertAlmostEqual(result.dual, 0.0, places=5)

    def test_cosine(self):
        """Test cosine function."""
        x = DualNumber(0.0, 1.0)
        result = DualNumber.cos(x)
        # cos(0 + ε) = cos(0) - sin(0)*ε = 1 + 0*ε
        self.assertAlmostEqual(result.real, 1.0, places=5)
        self.assertAlmostEqual(result.dual, 0.0, places=5)

    def test_sqrt(self):
        """Test square root function."""
        x = DualNumber(4.0, 2.0)
        result = DualNumber.sqrt(x)
        # sqrt(4 + 2ε) = 2 + (2/(2*2))*ε = 2 + 0.5*ε
        self.assertAlmostEqual(result.real, 2.0, places=5)
        self.assertAlmostEqual(result.dual, 0.5, places=5)

    def test_relu(self):
        """Test ReLU activation."""
        x1 = DualNumber(-2.0, 1.0)
        result1 = DualNumber.relu(x1)
        self.assertAlmostEqual(result1.real, 0.0)
        self.assertAlmostEqual(result1.dual, 0.0)

        x2 = DualNumber(2.0, 1.0)
        result2 = DualNumber.relu(x2)
        self.assertAlmostEqual(result2.real, 2.0)
        self.assertAlmostEqual(result2.dual, 1.0)


class TestAutoDiffEngine(unittest.TestCase):
    """Tests for automatic differentiation engine."""

    def test_polynomial_derivative(self):
        """Test derivative of polynomial."""
        # f(x) = x^2 + 3x + 1, f'(x) = 2x + 3
        def f(x):
            return x**2 + 3*x + 1

        def f_prime_numeric(x):
            return 2*x + 3

        # Wrap for dual numbers
        def f_dual(x):
            return x**2 + 3*x + 1

        for x_val in [0.0, 1.0, 2.0, 5.0]:
            auto_diff = AutoDiffEngine.derivative(lambda d: f_dual(d), x_val)
            numeric = f_prime_numeric(x_val)
            self.assertAlmostEqual(auto_diff, numeric, places=5)

    def test_composite_function(self):
        """Test derivative of composite function."""
        # f(x) = sin(x^2), f'(x) = 2x*cos(x^2)
        def f(x):
            return DualNumber.sin(x**2)

        for x_val in [0.0, 0.5, 1.0]:
            auto_diff = AutoDiffEngine.derivative(f, x_val)
            numeric = 2 * x_val * math.cos(x_val**2)
            self.assertAlmostEqual(auto_diff, numeric, places=5)

    def test_gradient(self):
        """Test gradient computation."""
        # f(x, y) = x^2 + y^2
        def f(inputs):
            return inputs[0]**2 + inputs[1]**2

        grad = AutoDiffEngine.gradient(f, [3.0, 4.0])
        self.assertAlmostEqual(grad[0], 6.0)  # df/dx = 2x = 6
        self.assertAlmostEqual(grad[1], 8.0)  # df/dy = 2y = 8


class TestIntegerDual(unittest.TestCase):
    """Tests for integer dual numbers."""

    def test_addition(self):
        """Test integer dual addition."""
        x = IntegerDual(3, 4)
        y = IntegerDual(5, 6)
        result = x + y
        self.assertEqual(result.real, 8)
        self.assertEqual(result.dual, 10)

    def test_multiplication(self):
        """Test integer dual multiplication."""
        x = IntegerDual(2, 3)
        y = IntegerDual(4, 5)
        result = x * y
        self.assertEqual(result.real, 8)
        self.assertEqual(result.dual, 22)

    def test_epsilon_squared_zero(self):
        """Test that ε^2 = 0 for integers."""
        epsilon = IntegerDual(0, 1)
        result = epsilon * epsilon
        self.assertEqual(result.real, 0)
        self.assertEqual(result.dual, 0)

    def test_power(self):
        """Test integer dual exponentiation."""
        x = IntegerDual(2, 1)
        result = x ** 3
        # (2 + ε)^3 = 8 + 3*4*ε = 8 + 12ε
        self.assertEqual(result.real, 8)
        self.assertEqual(result.dual, 12)


# ============================================================================
# SECTION 6: Performance Benchmarks
# ============================================================================

class PerformanceBenchmarks:
    """Performance benchmarks for DCA Chapter 10 operations."""

    @staticmethod
    def benchmark_complex_operations(p: int, iterations: int = 1000) -> Dict[str, float]:
        """
        Benchmark finite field complex operations.

        Args:
            p: Field modulus
            iterations: Number of iterations

        Returns:
            Dictionary of timing results
        """
        field = FiniteFieldComplex(p)
        z1 = (3, 4)
        z2 = (5, 6)

        times = []
        for _ in range(iterations):
            start = time.time()
            field.mul(z1, z2)
            end = time.time()
            times.append(end - start)

        return {
            'mean': sum(times) / len(times),
            'min': min(times),
            'max': max(times)
        }

    @staticmethod
    def benchmark_dual_operations(iterations: int = 10000) -> Dict[str, float]:
        """
        Benchmark dual number operations.

        Args:
            iterations: Number of iterations

        Returns:
            Dictionary of timing results
        """
        x = DualNumber(2.0, 3.0)
        y = DualNumber(4.0, 5.0)

        times = []
        for _ in range(iterations):
            start = time.time()
            _ = x * y + DualNumber.sin(x)
            end = time.time()
            times.append(end - start)

        return {
            'mean': sum(times) / len(times),
            'min': min(times),
            'max': max(times)
        }

    @staticmethod
    def benchmark_autodiff(iterations: int = 1000) -> Dict[str, float]:
        """
        Benchmark automatic differentiation.

        Args:
            iterations: Number of iterations

        Returns:
            Dictionary of timing results
        """
        def f(x):
            return DualNumber.sin(x**2) + DualNumber.exp(x)

        times = []
        for _ in range(iterations):
            start = time.time()
            AutoDiffEngine.derivative(f, 1.5)
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

        # Complex operations benchmarks
        for p in [7, 13, 97]:
            results[f'complex_p_{p}'] = PerformanceBenchmarks.benchmark_complex_operations(p)

        # Dual number benchmarks
        results['dual_ops'] = PerformanceBenchmarks.benchmark_dual_operations()

        # AutoDiff benchmarks
        results['autodiff'] = PerformanceBenchmarks.benchmark_autodiff()

        return results


# ============================================================================
# SECTION 7: Main Execution
# ============================================================================

def main():
    """Main execution function for verification."""
    print("=" * 80)
    print("DCA Chapter 10: Discrete Complex Analysis and Dual Numbers")
    print("Verification Suite")
    print("=" * 80)
    print()

    # Run unit tests
    print("Running unit tests...")
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    suite.addTests(loader.loadTestsFromTestCase(TestFiniteFieldComplex))
    suite.addTests(loader.loadTestsFromTestCase(TestDualNumbers))
    suite.addTests(loader.loadTestsFromTestCase(TestAutoDiffEngine))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegerDual))

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