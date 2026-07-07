#!/usr/bin/env python3
"""
DCA Chapter 2: Algebraic Structures - Verification Code
Author: Wang Bingqin
Date: 2026-07-06
"""

import random
import math
from typing import List, Tuple, Dict, Optional


class FiniteSet:
    """Represents a finite set with elements"""

    def __init__(self, elements: List):
        self.elements = list(dict.fromkeys(elements))  # Remove duplicates
        self._index_map = {elem: i for i, elem in enumerate(self.elements)}

    def __len__(self):
        return len(self.elements)

    def __contains__(self, item):
        return item in self._index_map

    def __iter__(self):
        return iter(self.elements)

    def __repr__(self):
        return f"FiniteSet({self.elements})"

    def index(self, item):
        return self._index_map.get(item, -1)

    def sample(self):
        return random.choice(self.elements)


class Group:
    """
    Represents a finite group with a binary operation
    """

    def __init__(self, elements: List, operation, identity, inverse_func):
        """
        Args:
            elements: List of group elements
            operation: Binary operation function (a, b) -> result
            identity: Identity element
            inverse_func: Function returning inverse of an element
        """
        self.set = FiniteSet(elements)
        self.operation = operation
        self.identity = identity
        self.inverse_func = inverse_func

    def __len__(self):
        return len(self.set)

    def multiply(self, a, b):
        """Apply the group operation"""
        return self.operation(a, b)

    def inverse(self, a):
        """Get the inverse of element a"""
        return self.inverse_func(a)

    def verify_closure(self) -> bool:
        """Verify closure property: operation maps G×G to G"""
        for a in self.set:
            for b in self.set:
                result = self.multiply(a, b)
                if result not in self.set:
                    return False, (a, b, result)
        return True, None

    def verify_associativity(self) -> bool:
        """Verify associativity: (a*b)*c = a*(b*c) for all a,b,c"""
        for a in self.set:
            for b in self.set:
                for c in self.set:
                    left = self.multiply(self.multiply(a, b), c)
                    right = self.multiply(a, self.multiply(b, c))
                    if left != right:
                        return False, (a, b, c, left, right)
        return True, None

    def verify_identity(self) -> bool:
        """Verify identity: e*a = a*e = a for all a"""
        for a in self.set:
            if self.multiply(self.identity, a) != a:
                return False, ('left', self.identity, a)
            if self.multiply(a, self.identity) != a:
                return False, ('right', a, self.identity)
        return True, None

    def verify_inverse(self) -> bool:
        """Verify inverse: a*a^{-1} = a^{-1}*a = e for all a"""
        for a in self.set:
            inv_a = self.inverse(a)
            if self.multiply(a, inv_a) != self.identity:
                return False, ('left', a, inv_a)
            if self.multiply(inv_a, a) != self.identity:
                return False, ('right', inv_a, a)
        return True, None

    def is_commutative(self) -> bool:
        """Check if the group is commutative (Abelian)"""
        for a in self.set:
            for b in self.set:
                if self.multiply(a, b) != self.multiply(b, a):
                    return False
        return True

    def verify_group(self) -> Dict[str, bool]:
        """Verify all group properties"""
        results = {}
        results['closure'], _ = self.verify_closure()
        results['associativity'], _ = self.verify_associativity()
        results['identity'], _ = self.verify_identity()
        results['inverse'], _ = self.verify_inverse()
        results['is_group'] = all(results.values())
        results['is_abelian'] = self.is_commutative() if results['is_group'] else False
        return results


class Ring:
    """
    Represents a finite ring with addition and multiplication
    """

    def __init__(self, elements: List, add_op, mul_op,
                 add_identity, mul_identity, add_inverse_func):
        """
        Args:
            elements: List of ring elements
            add_op: Addition operation
            mul_op: Multiplication operation
            add_identity: Additive identity (0)
            mul_identity: Multiplicative identity (1), None if not a ring with 1
            add_inverse_func: Function returning additive inverse
        """
        self.set = FiniteSet(elements)
        self.add = add_op
        self.mul = mul_op
        self.add_zero = add_identity
        self.mul_one = mul_identity
        self.add_inverse = add_inverse_func

    def __len__(self):
        return len(self.set)

    def verify_additive_group(self) -> Dict[str, bool]:
        """Verify that the set with addition forms an abelian group"""
        results = {}

        # Closure under addition
        for a in self.set:
            for b in self.set:
                if self.add(a, b) not in self.set:
                    return {'is_additive_group': False}

        # Associativity
        for a in self.set:
            for b in self.set:
                for c in self.set:
                    if self.add(self.add(a, b), c) != self.add(a, self.add(b, c)):
                        return {'is_additive_group': False}

        # Identity
        for a in self.set:
            if self.add(self.add_zero, a) != a or self.add(a, self.add_zero) != a:
                return {'is_additive_group': False}

        # Inverses
        for a in self.set:
            inv_a = self.add_inverse(a)
            if self.add(a, inv_a) != self.add_zero or self.add(inv_a, a) != self.add_zero:
                return {'is_additive_group': False}

        # Commutativity (required for rings)
        for a in self.set:
            for b in self.set:
                if self.add(a, b) != self.add(b, a):
                    return {'is_additive_group': False}

        return {'is_additive_group': True}

    def verify_multiplicative_semi_group(self) -> Dict[str, bool]:
        """Verify closure and associativity of multiplication"""
        results = {}

        # Closure under multiplication
        for a in self.set:
            for b in self.set:
                if self.mul(a, b) not in self.set:
                    return {'is_multiplicative_closed': False}

        # Associativity
        for a in self.set:
            for b in self.set:
                for c in self.set:
                    if self.mul(self.mul(a, b), c) != self.mul(a, self.mul(b, c)):
                        return {'is_multiplicative_associative': False}

        return {'is_multiplicative_closed': True,
                'is_multiplicative_associative': True}

    def verify_distributivity(self) -> bool:
        """Verify distributive laws"""
        for a in self.set:
            for b in self.set:
                for c in self.set:
                    # Left distributive: a*(b+c) = a*b + a*c
                    left = self.mul(a, self.add(b, c))
                    right = self.add(self.mul(a, b), self.mul(a, c))
                    if left != right:
                        return False

                    # Right distributive: (a+b)*c = a*c + b*c
                    left = self.mul(self.add(a, b), c)
                    right = self.add(self.mul(a, c), self.mul(b, c))
                    if left != right:
                        return False
        return True

    def has_multiplicative_identity(self) -> bool:
        """Check if ring has multiplicative identity"""
        if self.mul_one is None:
            return False

        for a in self.set:
            if self.mul(self.mul_one, a) != a or self.mul(a, self.mul_one) != a:
                return False
        return True

    def verify_ring(self) -> Dict[str, bool]:
        """Verify all ring properties"""
        results = {}
        add_group = self.verify_additive_group()
        results.update(add_group)

        mul_semigroup = self.verify_multiplicative_semi_group()
        results.update(mul_semigroup)

        results['distributivity'] = self.verify_distributivity()
        results['has_mul_one'] = self.has_multiplicative_identity()

        if self.mul_one is not None:
            results['is_ring_with_one'] = (
                results['is_additive_group'] and
                results['is_multiplicative_closed'] and
                results['is_multiplicative_associative'] and
                results['distributivity'] and
                results['has_mul_one']
            )
        else:
            results['is_ring_with_one'] = False

        results['is_ring'] = (
            results['is_additive_group'] and
            results['is_multiplicative_closed'] and
            results['is_multiplicative_associative'] and
            results['distributivity']
        )

        return results


class FiniteField:
    """
    Represents a finite field F_p where p is prime
    """

    def __init__(self, p: int):
        """
        Args:
            p: Prime number defining the field F_p
        """
        if not self._is_prime(p):
            raise ValueError(f"{p} is not prime")
        self.p = p
        self.elements = list(range(p))

    def _is_prime(self, n: int) -> bool:
        """Simple primality test for small numbers"""
        if n < 2:
            return False
        if n == 2:
            return True
        if n % 2 == 0:
            return False
        for i in range(3, int(math.sqrt(n)) + 1, 2):
            if n % i == 0:
                return False
        return True

    def add(self, a: int, b: int) -> int:
        """Addition in F_p: (a + b) mod p"""
        return (a + b) % self.p

    def sub(self, a: int, b: int) -> int:
        """Subtraction in F_p: (a - b) mod p"""
        return (a - b) % self.p

    def mul(self, a: int, b: int) -> int:
        """Multiplication in F_p: (a * b) mod p"""
        return (a * b) % self.p

    def inverse(self, a: int) -> int:
        """Multiplicative inverse in F_p: a^{-1} mod p"""
        if a == 0:
            raise ValueError("Zero has no multiplicative inverse")

        # Extended Euclidean algorithm
        def extended_gcd(a, b):
            if b == 0:
                return a, 1, 0
            gcd, x1, y1 = extended_gcd(b, a % b)
            x = y1
            y = x1 - (a // b) * y1
            return gcd, x, y

        _, inv, _ = extended_gcd(a, self.p)
        return inv % self.p

    def div(self, a: int, b: int) -> int:
        """Division in F_p: a / b = a * b^{-1} mod p"""
        return self.mul(a, self.inverse(b))

    def pow(self, a: int, n: int) -> int:
        """Exponentiation in F_p: a^n mod p"""
        if n < 0:
            a = self.inverse(a)
            n = -n
        result = 1
        base = a % self.p
        while n > 0:
            if n % 2 == 1:
                result = (result * base) % self.p
            base = (base * base) % self.p
            n //= 2
        return result

    def __len__(self):
        return self.p

    def verify_field(self) -> Dict[str, bool]:
        """Verify all field properties"""
        results = {}

        # Create Ring representation
        ring = Ring(
            elements=self.elements,
            add_op=self.add,
            mul_op=self.mul,
            add_identity=0,
            mul_identity=1,
            add_inverse_func=lambda x: self.sub(0, x)
        )
        ring_results = ring.verify_ring()
        results.update(ring_results)

        # Verify multiplicative inverses exist for all non-zero elements
        results['multiplicative_inverses'] = True
        for a in range(1, self.p):
            try:
                inv_a = self.inverse(a)
                if self.mul(a, inv_a) != 1:
                    results['multiplicative_inverses'] = False
                    break
            except Exception:
                results['multiplicative_inverses'] = False
                break

        results['is_field'] = (
            results['is_ring_with_one'] and
            results['multiplicative_inverses']
        )

        return results


class Matrix:
    """Matrix operations over a ring"""

    def __init__(self, data: List[List[int]], mod: Optional[int] = None):
        self.data = data
        self.rows = len(data)
        self.cols = len(data[0]) if data else 0
        self.mod = mod

    def __mul__(self, other):
        """Matrix multiplication"""
        if self.cols != other.rows:
            raise ValueError("Matrix dimensions don't match")

        result = [[0 for _ in range(other.cols)] for _ in range(self.rows)]
        for i in range(self.rows):
            for j in range(other.cols):
                for k in range(self.cols):
                    result[i][j] += self.data[i][k] * other.data[k][j]
                    if self.mod:
                        result[i][j] %= self.mod

        return Matrix(result, self.mod)

    def __add__(self, other):
        """Matrix addition"""
        if self.rows != other.rows or self.cols != other.cols:
            raise ValueError("Matrix dimensions don't match")

        result = [[0 for _ in range(self.cols)] for _ in range(self.rows)]
        for i in range(self.rows):
            for j in range(self.cols):
                result[i][j] = self.data[i][j] + other.data[i][j]
                if self.mod:
                    result[i][j] %= self.mod

        return Matrix(result, self.mod)

    def __repr__(self):
        return f"Matrix({self.data})"


def test_finite_field(p: int) -> Dict:
    """Test a finite field F_p"""
    print(f"\nTesting F_{p}...")

    field = FiniteField(p)
    results = field.verify_field()

    # Print results
    for prop, value in results.items():
        status = "✓" if value else "✗"
        print(f"  {status} {prop}: {value}")

    return results


def test_cyclic_group(n: int) -> Dict:
    """Test cyclic group Z_n under addition"""
    print(f"\nTesting Z_{n} (addition)...")

    elements = list(range(n))

    def operation(a, b):
        return (a + b) % n

    def inverse_func(a):
        return (-a) % n

    group = Group(elements, operation, 0, inverse_func)
    results = group.verify_group()

    for prop, value in results.items():
        status = "✓" if value else "✗"
        print(f"  {status} {prop}: {value}")

    return results


def test_multiplicative_group(p: int) -> Dict:
    """Test multiplicative group F_p*"""
    print(f"\nTesting F_{p}* (multiplication)...")

    elements = list(range(1, p))  # All non-zero elements

    def operation(a, b):
        return (a * b) % p

    def inverse_func(a):
        # Find multiplicative inverse
        for x in range(1, p):
            if (a * x) % p == 1:
                return x
        raise ValueError(f"No inverse found for {a}")

    group = Group(elements, operation, 1, inverse_func)
    results = group.verify_group()

    for prop, value in results.items():
        status = "✓" if value else "✗"
        print(f"  {status} {prop}: {value}")

    return results


def test_ring_mod(n: int) -> Dict:
    """Test ring Z/nZ"""
    print(f"\nTesting Z/{n}Z...")

    elements = list(range(n))

    def add_op(a, b):
        return (a + b) % n

    def mul_op(a, b):
        return (a * b) % n

    def add_inverse(a):
        return (-a) % n

    mul_one = 1 if math.gcd(n, 1) == 1 else None

    ring = Ring(elements, add_op, mul_op, 0, mul_one, add_inverse)
    results = ring.verify_ring()

    for prop, value in results.items():
        status = "✓" if value else "✗"
        print(f"  {status} {prop}: {value}")

    # Check if it's a field
    is_field = n > 1 and all(results.values()) and results.get('multiplicative_inverses', False)
    if is_field:
        print(f"  ✓ is_field: True (since {n} is prime)")
    else:
        print(f"  ✗ is_field: False")

    return results


def benchmark_operations(field: FiniteField, iterations: int = 100000) -> Dict:
    """Benchmark field operations"""
    import time

    print(f"\nBenchmarking F_{field.p} ({iterations} iterations)...")

    results = {}

    # Generate random operands
    a_vals = [random.randint(0, field.p - 1) for _ in range(iterations)]
    b_vals = [random.randint(0, field.p - 1) for _ in range(iterations)]

    # Addition
    start = time.perf_counter_ns()
    for a, b in zip(a_vals, b_vals):
        field.add(a, b)
    end = time.perf_counter_ns()
    results['add_ns'] = (end - start) / iterations

    # Multiplication
    start = time.perf_counter_ns()
    for a, b in zip(a_vals, b_vals):
        field.mul(a, b)
    end = time.perf_counter_ns()
    results['mul_ns'] = (end - start) / iterations

    # Inversion (non-zero only)
    a_vals_nz = [random.randint(1, field.p - 1) for _ in range(min(iterations // 10, 1000))]
    start = time.perf_counter_ns()
    for a in a_vals_nz:
        field.inverse(a)
    end = time.perf_counter_ns()
    results['inv_ns'] = (end - start) / len(a_vals_nz)

    # Exponentiation
    start = time.perf_counter_ns()
    for a in a_vals_nz:
        field.pow(a, random.randint(1, field.p - 2))
    end = time.perf_counter_ns()
    results['pow_ns'] = (end - start) / len(a_vals_nz)

    for op, ns in results.items():
        print(f"  {op}: {ns:.1f} ns/op")

    return results


def run_all_tests():
    """Run all verification tests"""
    print("=" * 60)
    print("DCA Chapter 2: Algebraic Structures Verification")
    print("=" * 60)

    all_results = {}

    # Test various finite fields
    primes = [2, 3, 5, 7, 11, 13, 17, 19]
    for p in primes:
        all_results[f'F{p}'] = test_finite_field(p)

    # Test cyclic groups
    for n in [2, 3, 4, 5, 6, 8, 10]:
        all_results[f'Z{n}'] = test_cyclic_group(n)

    # Test multiplicative groups
    for p in [3, 5, 7, 11]:
        all_results[f'F{p}*'] = test_multiplicative_group(p)

    # Test rings (both prime and composite moduli)
    for n in [2, 3, 4, 5, 6, 8, 9, 10]:
        all_results[f'Z{n}Z'] = test_ring_mod(n)

    # Benchmark
    print("\n" + "=" * 60)
    print("PERFORMANCE BENCHMARKS")
    print("=" * 60)
    field = FiniteField(9973)
    bench_results = benchmark_operations(field, 100000)
    all_results['benchmark'] = bench_results

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    field_tests = [r for name, r in all_results.items() if name.startswith('F') and not name.endswith('*')]
    all_fields_valid = all(r.get('is_field', False) for r in field_tests)

    print(f"Finite fields tested: {len(field_tests)}")
    print(f"All fields valid: {all_fields_valid}")

    group_tests = [r for name, r in all_results.items() if name.startswith('Z') or name.endswith('*')]
    all_groups_valid = all(r.get('is_group', False) for r in group_tests)

    print(f"Groups tested: {len(group_tests)}")
    print(f"All groups valid: {all_groups_valid}")

    if all_fields_valid and all_groups_valid:
        print("\n✓ ALL TESTS PASSED!")
    else:
        print("\n✗ SOME TESTS FAILED!")

    return all_results


if __name__ == "__main__":
    verification_results = run_all_tests()

    # Exit with appropriate code
    all_passed = all(
        r.get('is_field', True) if k.startswith('F') and not k.endswith('*') else
        r.get('is_group', True) if k.startswith('Z') or k.endswith('*') else
        True
        for k, r in verification_results.items()
        if k not in ['benchmark']
    )

    exit(0 if all_passed else 1)