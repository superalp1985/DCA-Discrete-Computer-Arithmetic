#!/usr/bin/env python3
"""
DCA Chapter 1: Arithmetic Foundations - Complete Verification Code
Author: Wang Bingqin
Date: 2026-07-06
"""

import random
import time
from typing import Tuple


def word_add(a: int, b: int, w: int) -> int:
    """
    Modular addition for w-bit unsigned integers

    Args:
        a: First operand
        b: Second operand
        w: Word length in bits

    Returns:
        (a + b) mod 2^w
    """
    mask = (1 << w) - 1
    return (a + b) & mask


def word_sub(a: int, b: int, w: int) -> int:
    """
    Subtraction for w-bit unsigned integers (via two's complement)

    Args:
        a: Minuend
        b: Subtrahend
        w: Word length in bits

    Returns:
        (a - b) mod 2^w
    """
    mask = (1 << w) - 1
    b_complement = (~b) & mask
    return word_add(a, word_add(b_complement, 1, w), w)


def word_mul(a: int, b: int, w: int) -> int:
    """
    Multiplication for w-bit unsigned integers (shift-accumulate)

    Args:
        a: First operand
        b: Second operand
        w: Word length in bits

    Returns:
        (a * b) mod 2^w
    """
    mask = (1 << w) - 1
    result = 0
    for i in range(w):
        if (b >> i) & 1:
            result = (result + (a << i)) & mask
    return result


def word_div(a: int, b: int, w: int) -> Tuple[int, int]:
    """
    Division for w-bit unsigned integers, returns quotient and remainder

    Args:
        a: Dividend
        b: Divisor (b > 0)
        w: Word length in bits

    Returns:
        Tuple of (quotient, remainder)
    """
    if b == 0:
        raise ValueError("Division by zero")

    mask = (1 << w) - 1
    q = 0
    r = 0

    for i in range(w - 1, -1, -1):
        r = (r << 1) | ((a >> i) & 1)
        if r >= b:
            r -= b
            q |= (1 << i)

    return q, r


def test_word_add() -> dict:
    """Test correctness of modular addition"""
    print("Testing word_add...")
    results = {
        "fixed": {"passed": 0, "failed": 0},
        "random": {w: {"passed": 0, "failed": 0} for w in [8, 16, 32, 64]}
    }

    # Fixed test cases
    test_cases = [
        (0, 0, 8, 0),
        (255, 1, 8, 0),
        (250, 10, 8, 4),
        (65535, 1, 16, 0),
        (127, 1, 7, 0),
    ]

    for a, b, w, expected in test_cases:
        result = word_add(a, b, w)
        if result == expected:
            results["fixed"]["passed"] += 1
        else:
            results["fixed"]["failed"] += 1
            print(f"  FAILED: {a} + {b} (w={w}) = {result}, expected {expected}")

    # Random tests
    for w in [8, 16, 32, 64]:
        mask = (1 << w) - 1
        for _ in range(10000):
            a = random.randint(0, mask)
            b = random.randint(0, mask)
            result = word_add(a, b, w)
            expected = (a + b) & mask
            if result == expected:
                results["random"][w]["passed"] += 1
            else:
                results["random"][w]["failed"] += 1

    print(f"  Fixed tests: {results['fixed']['passed']}/{results['fixed']['passed'] + results['fixed']['failed']}")
    for w in [8, 16, 32, 64]:
        total = results["random"][w]["passed"] + results["random"][w]["failed"]
        print(f"  {w}-bit random: {results['random'][w]['passed']}/{total}")

    return results


def test_word_sub() -> dict:
    """Test correctness of two's complement subtraction"""
    print("Testing word_sub...")
    results = {
        "fixed": {"passed": 0, "failed": 0},
        "random": {w: {"passed": 0, "failed": 0} for w in [8, 16, 32, 64]}
    }

    # Fixed test cases
    test_cases = [
        (10, 3, 8, 7),
        (0, 1, 8, 255),
        (5, 10, 8, 251),
        (100, 100, 8, 0),
        (255, 255, 8, 0),
    ]

    for a, b, w, expected in test_cases:
        result = word_sub(a, b, w)
        if result == expected:
            results["fixed"]["passed"] += 1
        else:
            results["fixed"]["failed"] += 1
            print(f"  FAILED: {a} - {b} (w={w}) = {result}, expected {expected}")

    # Random tests
    for w in [8, 16, 32, 64]:
        mask = (1 << w) - 1
        for _ in range(10000):
            a = random.randint(0, mask)
            b = random.randint(0, mask)
            result = word_sub(a, b, w)
            expected = (a - b) & mask
            if result == expected:
                results["random"][w]["passed"] += 1
            else:
                results["random"][w]["failed"] += 1

    print(f"  Fixed tests: {results['fixed']['passed']}/{results['fixed']['passed'] + results['fixed']['failed']}")
    for w in [8, 16, 32, 64]:
        total = results["random"][w]["passed"] + results["random"][w]["failed"]
        print(f"  {w}-bit random: {results['random'][w]['passed']}/{total}")

    return results


def test_word_mul() -> dict:
    """Test correctness of shift-accumulate multiplication"""
    print("Testing word_mul...")
    results = {
        "fixed": {"passed": 0, "failed": 0},
        "random": {w: {"passed": 0, "failed": 0} for w in [8, 16, 32]}
    }

    # Fixed test cases
    test_cases = [
        (0, 0, 8, 0),
        (1, 1, 8, 1),
        (10, 5, 8, 50),
        (255, 255, 8, 1),
        (256, 2, 16, 512),
        (1000, 1000, 16, 1000000 & 0xFFFF),
    ]

    for a, b, w, expected in test_cases:
        result = word_mul(a, b, w)
        if result == expected:
            results["fixed"]["passed"] += 1
        else:
            results["fixed"]["failed"] += 1
            print(f"  FAILED: {a} * {b} (w={w}) = {result}, expected {expected}")

    # Random tests
    for w in [8, 16, 32]:
        mask = (1 << w) - 1
        for _ in range(1000):
            a = random.randint(0, mask)
            b = random.randint(0, mask)
            result = word_mul(a, b, w)
            expected = (a * b) & mask
            if result == expected:
                results["random"][w]["passed"] += 1
            else:
                results["random"][w]["failed"] += 1

    print(f"  Fixed tests: {results['fixed']['passed']}/{results['fixed']['passed'] + results['fixed']['failed']}")
    for w in [8, 16, 32]:
        total = results["random"][w]["passed"] + results["random"][w]["failed"]
        print(f"  {w}-bit random: {results['random'][w]['passed']}/{total}")

    return results


def test_word_div() -> dict:
    """Test correctness of division"""
    print("Testing word_div...")
    results = {
        "fixed": {"passed": 0, "failed": 0},
        "random": {w: {"passed": 0, "failed": 0} for w in [8, 16, 32]}
    }

    # Fixed test cases
    test_cases = [
        (100, 10, 8, 10, 0),
        (255, 17, 8, 15, 0),
        (154, 10, 8, 15, 4),
        (0, 1, 8, 0, 0),
        (65535, 255, 16, 257, 0),
        (100, 7, 8, 14, 2),
    ]

    for a, b, w, expected_q, expected_r in test_cases:
        q, r = word_div(a, b, w)
        if q == expected_q and r == expected_r:
            results["fixed"]["passed"] += 1
        else:
            results["fixed"]["failed"] += 1
            print(f"  FAILED: {a} / {b} (w={w}) = ({q}, {r}), expected ({expected_q}, {expected_r})")

    # Random tests
    for w in [8, 16, 32]:
        mask = (1 << w) - 1
        for _ in range(1000):
            a = random.randint(0, mask)
            b = random.randint(1, mask)
            q, r = word_div(a, b, w)
            # Verify invariant
            if a == b * q + r and 0 <= r < b:
                results["random"][w]["passed"] += 1
            else:
                results["random"][w]["failed"] += 1

    print(f"  Fixed tests: {results['fixed']['passed']}/{results['fixed']['passed'] + results['fixed']['failed']}")
    for w in [8, 16, 32]:
        total = results["random"][w]["passed"] + results["random"][w]["failed"]
        print(f"  {w}-bit random: {results['random'][w]['passed']}/{total}")

    return results


def benchmark_operations() -> dict:
    """Benchmark all operations for different word lengths"""
    print("\nBenchmarking operations...")

    results = {
        "add": {},
        "sub": {},
        "mul": {},
        "div": {}
    }

    operations = [
        ("add", lambda a, b, w: word_add(a, b, w), 100000),
        ("sub", lambda a, b, w: word_sub(a, b, w), 100000),
        ("mul", lambda a, b, w: word_mul(a, b, w), 10000),
        ("div", lambda a, b, w: word_div(a, b, w), 5000),
    ]

    for op_name, op_func, iterations in operations:
        for w in [8, 16, 32, 64]:
            mask = (1 << w) - 1

            # Warmup
            for _ in range(100):
                a = random.randint(0, mask)
                b = random.randint(1, mask) if op_name == "div" else random.randint(0, mask)
                op_func(a, b, w)

            # Benchmark
            start = time.perf_counter_ns()
            for _ in range(iterations):
                a = random.randint(0, mask)
                b = random.randint(1, mask) if op_name == "div" else random.randint(0, mask)
                op_func(a, b, w)
            end = time.perf_counter_ns()

            ns_per_op = (end - start) / iterations
            results[op_name][w] = ns_per_op
            print(f"  {op_name}_{w}: {ns_per_op:.1f} ns/op")

    return results


def run_all_tests():
    """Run all verification tests"""
    print("=" * 60)
    print("DCA Chapter 1: Arithmetic Foundations Verification")
    print("=" * 60)

    # Run correctness tests
    add_results = test_word_add()
    sub_results = test_word_sub()
    mul_results = test_word_mul()
    div_results = test_word_div()

    # Run benchmarks
    benchmark_results = benchmark_operations()

    # Summary
    print("\n" + "=" * 60)
    print("VERIFICATION SUMMARY")
    print("=" * 60)

    all_passed = True
    for name, results in [
        ("word_add", add_results),
        ("word_sub", sub_results),
        ("word_mul", mul_results),
        ("word_div", div_results)
    ]:
        fixed_passed = results["fixed"]["passed"]
        fixed_total = fixed_passed + results["fixed"]["failed"]
        print(f"{name}: {fixed_passed}/{fixed_total} fixed tests passed")

        for w in results["random"]:
            passed = results["random"][w]["passed"]
            total = passed + results["random"][w]["failed"]
            if results["random"][w]["failed"] > 0:
                all_passed = False
            print(f"  {w}-bit: {passed}/{total} random tests passed")

    if all_passed:
        print("\n✓ ALL TESTS PASSED!")
    else:
        print("\n✗ SOME TESTS FAILED!")

    return {
        "add": add_results,
        "sub": sub_results,
        "mul": mul_results,
        "div": div_results,
        "benchmark": benchmark_results,
        "all_passed": all_passed
    }


if __name__ == "__main__":
    verification_results = run_all_tests()

    # Exit with appropriate code
    exit(0 if verification_results["all_passed"] else 1)