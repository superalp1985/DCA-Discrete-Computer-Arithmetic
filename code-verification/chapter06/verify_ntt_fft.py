#!/usr/bin/env python3
"""
DCA Chapter 6: NTT and FFT - Complete Verification Code
Author: Wang Bingqin
Date: 2026-07-06

This module implements and verifies:
- Cooley-Tukey FFT (floating point)
- Iterative NTT (Number Theoretic Transform)
- INTT (Inverse NTT)
- Convolution via NTT
- Convolution theorem verification
"""

import math
import cmath
import random
import time
from typing import List, Tuple


def is_power_of_two(n: int) -> bool:
    """Check if n is a power of two"""
    return n > 0 and (n & (n - 1)) == 0


def bit_reverse(n: int, bits: int) -> int:
    """
    Reverse the bits of n (for bit-reversal permutation)

    Args:
        n: Number to reverse
        bits: Number of bits to consider

    Returns:
        Bit-reversed value
    """
    result = 0
    for i in range(bits):
        result = (result << 1) | (n & 1)
        n >>= 1
    return result


def fft_cooley_tukey(a: List[complex], invert: bool = False) -> List[complex]:
    """
    Cooley-Tukey FFT algorithm (floating point version)

    Args:
        a: Input array (length must be power of 2)
        invert: If True, compute inverse FFT

    Returns:
        FFT (or IFFT) of input array
    """
    n = len(a)

    # Bit-reversal permutation
    j = 0
    for i in range(1, n):
        bit = n >> 1
        while j & bit:
            j ^= bit
            bit >>= 1
        j ^= bit

        if i < j:
            a[i], a[j] = a[j], a[i]

    # Cooley-Tukey FFT
    length = 2
    while length <= n:
        ang = 2 * math.pi / length * (-1 if invert else 1)
        wlen = complex(math.cos(ang), math.sin(ang))

        for i in range(0, n, length):
            w = 1 + 0j
            for j in range(i, i + length // 2):
                u = a[j]
                v = a[j + length // 2] * w
                a[j] = u + v
                a[j + length // 2] = u - v
                w *= wlen

        length <<= 1

    # Normalize for inverse FFT
    if invert:
        for i in range(n):
            a[i] /= n

    return a


def find_primitive_root(p: int, n: int) -> int:
    """
    Find primitive n-th root of unity in F_p

    Args:
        p: Prime modulus
        n: Required order (must divide p-1)

    Returns:
        Primitive n-th root of unity
    """
    # Common primitive roots for popular primes
    common_roots = {
        998244353: 3,  # 2^23 * 7 * 17 + 1
        1004535809: 3,  # 2^21 * 479 + 1
        469762049: 3,  # 2^26 * 7 + 1
        167772161: 3,  # 2^25 * 5 + 1
    }

    if p in common_roots and n <= (p - 1):
        g = common_roots[p]
        # Find the specific n-th root
        order = (p - 1) // n
        return pow(g, order, p)

    # General case: find primitive root and adjust
    # Find a generator of F_p*
    factors = {}
    temp = p - 1
    d = 2
    while d * d <= temp:
        while temp % d == 0:
            factors[d] = factors.get(d, 0) + 1
            temp //= d
        d += 1
    if temp > 1:
        factors[temp] = 1

    # Find generator
    g = 2
    while g < p:
        is_generator = True
        for q in factors.keys():
            if pow(g, (p - 1) // q, p) == 1:
                is_generator = False
                break
        if is_generator:
            break
        g += 1

    # Find n-th root
    root = pow(g, (p - 1) // n, p)
    return root


def modinv(a: int, p: int) -> int:
    """Compute modular inverse using Fermat's little theorem"""
    return pow(a, p - 2, p)


def ntt_iterative(a: List[int], p: int, invert: bool = False) -> List[int]:
    """
    Iterative Number Theoretic Transform

    Args:
        a: Input array (length must be power of 2)
        p: Prime modulus
        invert: If True, compute inverse NTT

    Returns:
        NTT (or INTT) of input array
    """
    n = len(a)

    # Find primitive root
    root = find_primitive_root(p, n)

    # Bit-reversal permutation
    j = 0
    for i in range(1, n):
        bit = n >> 1
        while j & bit:
            j ^= bit
            bit >>= 1
        j ^= bit

        if i < j:
            a[i], a[j] = a[j], a[i]

    # NTT butterfly operations
    length = 2
    while length <= n:
        wlen = pow(root, n // length, p)
        if invert:
            wlen = modinv(wlen, p)

        for i in range(0, n, length):
            w = 1
            for j in range(i, i + length // 2):
                u = a[j]
                v = (a[j + length // 2] * w) % p
                a[j] = (u + v) % p
                a[j + length // 2] = (u - v + p) % p
                w = (w * wlen) % p

        length <<= 1

    # Normalize for inverse NTT
    if invert:
        n_inv = modinv(n, p)
        for i in range(n):
            a[i] = (a[i] * n_inv) % p

    return a


def convolution_naive(a: List[int], b: List[int], p: int) -> List[int]:
    """
    Naive O(n*m) convolution

    Args:
        a: First array
        b: Second array
        p: Modulus

    Returns:
        Convolution result
    """
    result = [0] * (len(a) + len(b) - 1)
    for i, ai in enumerate(a):
        for j, bj in enumerate(b):
            result[i + j] = (result[i + j] + ai * bj) % p
    return result


def convolution_ntt(a: List[int], b: List[int], p: int) -> List[int]:
    """
    Convolution via NTT (O(n log n))

    Args:
        a: First array
        b: Second array
        p: Prime modulus

    Returns:
        Convolution result
    """
    # Find next power of two
    n = 1
    while n < len(a) + len(b) - 1:
        n <<= 1

    # Pad arrays
    a_pad = a + [0] * (n - len(a))
    b_pad = b + [0] * (n - len(b))

    # Compute NTT
    a_ntt = ntt_iterative(a_pad.copy(), p, False)
    b_ntt = ntt_iterative(b_pad.copy(), p, False)

    # Point-wise multiplication
    c_ntt = [(a_ntt[i] * b_ntt[i]) % p for i in range(n)]

    # Inverse NTT
    result = ntt_iterative(c_ntt, p, True)

    # Trim to correct length
    result_len = len(a) + len(b) - 1
    return result[:result_len]


def test_fft_correctness() -> dict:
    """Test FFT correctness with known transforms"""
    print("Testing FFT correctness...")

    results = {
        "impulse_response": {"passed": 0, "failed": 0},
        "sine_wave": {"passed": 0, "failed": 0},
        "dc_component": {"passed": 0, "failed": 0},
        "nyquist": {"passed": 0, "failed": 0},
    }

    # Test 1: Impulse response (FFT of delta is all ones)
    n = 8
    impulse = [0] * n
    impulse[0] = 1
    fft_result = fft_cooley_tukey(impulse.copy())
    expected = [1 + 0j] * n

    if all(abs(fft_result[i] - expected[i]) < 1e-10 for i in range(n)):
        results["impulse_response"]["passed"] += 1
    else:
        results["impulse_response"]["failed"] += 1
        print(f"  FAILED: Impulse response test")

    # Test 2: DC component (FFT of constant is delta)
    dc = [1 + 0j] * n
    fft_result = fft_cooley_tukey(dc.copy())

    if abs(fft_result[0] - n) < 1e-10 and all(abs(fft_result[i]) < 1e-10 for i in range(1, n)):
        results["dc_component"]["passed"] += 1
    else:
        results["dc_component"]["failed"] += 1
        print(f"  FAILED: DC component test")

    # Test 3: Nyquist frequency (alternating +1, -1)
    nyquist = [1 if i % 2 == 0 else -1 for i in range(n)]
    fft_result = fft_cooley_tukey(nyquist.copy())

    # Nyquist frequency should have energy at N/2
    nyquist_bin = n // 2
    if abs(fft_result[nyquist_bin]) > 0.1:
        results["nyquist"]["passed"] += 1
    else:
        results["nyquist"]["failed"] += 1
        print(f"  FAILED: Nyquist frequency test")

    # Test 4: Sine wave FFT
    freq = 2
    sine = [math.sin(2 * math.pi * freq * i / n) for i in range(n)]
    fft_result = fft_cooley_tukey(sine.copy())

    # Check that peak is at expected frequency
    max_magnitude = max(abs(x) for x in fft_result)
    max_idx = max(range(n), key=lambda i: abs(fft_result[i]))

    if max_idx == freq or max_idx == n - freq:
        results["sine_wave"]["passed"] += 1
    else:
        results["sine_wave"]["failed"] += 1
        print(f"  FAILED: Sine wave test")

    # Print summary
    for test_name, result in results.items():
        total = result["passed"] + result["failed"]
        print(f"  {test_name}: {result['passed']}/{total}")

    return results


def test_fft_round_trip() -> dict:
    """Test FFT round-trip (FFT -> IFFT -> original)"""
    print("Testing FFT round-trip...")

    results = {"passed": 0, "failed": 0}

    # Test various sizes
    for n in [2, 4, 8, 16, 32, 64, 128]:
        # Generate random signal
        signal = [random.random() * 10 - 5 for _ in range(n)]

        # FFT -> IFFT
        fft_result = fft_cooley_tukey(signal.copy())
        ifft_result = fft_cooley_tukey(fft_result.copy(), invert=True)

        # Check round-trip
        max_error = max(abs(signal[i] - ifft_result[i].real) for i in range(n))

        if max_error < 1e-9:
            results["passed"] += 1
        else:
            results["failed"] += 1
            print(f"  FAILED: Round-trip for n={n}, max_error={max_error}")

    total = results["passed"] + results["failed"]
    print(f"  Round-trip tests: {results['passed']}/{total}")

    return results


def test_ntt_correctness() -> dict:
    """Test NTT correctness with known transforms"""
    print("Testing NTT correctness...")

    # Use popular NTT-friendly prime
    p = 998244353

    results = {
        "impulse_response": {"passed": 0, "failed": 0},
        "dc_component": {"passed": 0, "failed": 0},
        "round_trip": {"passed": 0, "failed": 0},
    }

    # Test 1: Impulse response
    for n in [2, 4, 8, 16, 32, 64, 128]:
        impulse = [0] * n
        impulse[0] = 1

        ntt_result = ntt_iterative(impulse.copy(), p, False)
        expected = [1] * n

        if ntt_result == expected:
            results["impulse_response"]["passed"] += 1
        else:
            results["impulse_response"]["failed"] += 1
            print(f"  FAILED: Impulse response for n={n}")

    # Test 2: DC component
    for n in [2, 4, 8, 16]:
        dc = [1] * n
        ntt_result = ntt_iterative(dc.copy(), p, False)

        if ntt_result[0] == n and all(x == 0 for x in ntt_result[1:]):
            results["dc_component"]["passed"] += 1
        else:
            results["dc_component"]["failed"] += 1
            print(f"  FAILED: DC component for n={n}")

    # Test 3: Round-trip
    for n in [2, 4, 8, 16, 32, 64, 128]:
        signal = [random.randint(0, p - 1) for _ in range(n)]

        ntt_result = ntt_iterative(signal.copy(), p, False)
        intt_result = ntt_iterative(ntt_result.copy(), p, True)

        if intt_result == signal:
            results["round_trip"]["passed"] += 1
        else:
            results["round_trip"]["failed"] += 1
            print(f"  FAILED: Round-trip for n={n}")

    # Print summary
    for test_name, result in results.items():
        total = result["passed"] + result["failed"]
        print(f"  {test_name}: {result['passed']}/{total}")

    return results


def test_convolution_correctness() -> dict:
    """Test convolution via NTT matches naive convolution"""
    print("Testing convolution correctness...")

    p = 998244353

    results = {
        "small": {"passed": 0, "failed": 0},
        "medium": {"passed": 0, "failed": 0},
        "large": {"passed": 0, "failed": 0},
    }

    # Test various sizes
    test_sizes = [
        ("small", [(4, 5), (8, 7), (16, 15)]),
        ("medium", [(32, 31), (64, 63), (128, 127)]),
        ("large", [(256, 255), (512, 511), (1024, 1023)]),
    ]

    for size_name, size_list in test_sizes:
        for len_a, len_b in size_list:
            a = [random.randint(0, 100) for _ in range(len_a)]
            b = [random.randint(0, 100) for _ in range(len_b)]

            # Compute convolutions
            naive_result = convolution_naive(a, b, p)
            ntt_result = convolution_ntt(a, b, p)

            # Compare results
            if naive_result == ntt_result:
                results[size_name]["passed"] += 1
            else:
                results[size_name]["failed"] += 1
                print(f"  FAILED: Convolution for sizes ({len_a}, {len_b})")

    # Print summary
    for test_name, result in results.items():
        total = result["passed"] + result["failed"]
        print(f"  {test_name}: {result['passed']}/{total}")

    return results


def test_convolution_theorem() -> dict:
    """Test convolution theorem: FFT(a * b) = FFT(a) ⊙ FFT(b)"""
    print("Testing convolution theorem...")

    results = {"passed": 0, "failed": 0}

    # Test various sizes
    for n in [4, 8, 16, 32]:
        a = [random.random() * 10 - 5 for _ in range(n)]
        b = [random.random() * 10 - 5 for _ in range(n)]

        # Method 1: Convolution then FFT
        conv_result = [0] * (2 * n - 1)
        for i, ai in enumerate(a):
            for j, bj in enumerate(b):
                conv_result[i + j] += ai * bj

        # Pad to next power of two
        m = 1
        while m < len(conv_result):
            m <<= 1
        conv_padded = conv_result + [0] * (m - len(conv_result))
        fft_conv = fft_cooley_tukey(conv_padded)

        # Method 2: FFT then point-wise multiplication
        a_padded = a + [0] * (m - len(a))
        b_padded = b + [0] * (m - len(b))

        fft_a = fft_cooley_tukey(a_padded)
        fft_b = fft_cooley_tukey(b_padded)
        fft_product = [fft_a[i] * fft_b[i] for i in range(m)]

        # Compare FFTs
        max_error = max(abs(fft_conv[i] - fft_product[i]) for i in range(m))

        if max_error < 1e-6:
            results["passed"] += 1
        else:
            results["failed"] += 1
            print(f"  FAILED: Convolution theorem for n={n}, max_error={max_error}")

    total = results["passed"] + results["failed"]
    print(f"  Convolution theorem: {results['passed']}/{total}")

    return results


def test_primitive_root() -> dict:
    """Test primitive root computation"""
    print("Testing primitive root computation...")

    results = {"passed": 0, "failed": 0}

    # Test cases: (p, n, expected_order)
    test_cases = [
        (998244353, 8, 8),  # 998244353 = 2^23 * 7 * 17 + 1
        (998244353, 16, 16),
        (998244353, 32, 32),
        (998244353, 64, 64),
        (998244353, 128, 128),
    ]

    for p, n, expected_order in test_cases:
        root = find_primitive_root(p, n)

        # Check that root^n = 1 mod p
        if pow(root, n, p) != 1:
            results["failed"] += 1
            print(f"  FAILED: root^n != 1 for p={p}, n={n}")
            continue

        # Check that root has exact order n (no smaller power gives 1)
        has_correct_order = True
        for k in range(1, n):
            if n % k == 0:  # Only check divisors
                if pow(root, k, p) == 1:
                    has_correct_order = False
                    break

        if has_correct_order:
            results["passed"] += 1
        else:
            results["failed"] += 1
            print(f"  FAILED: Root has wrong order for p={p}, n={n}")

    total = results["passed"] + results["failed"]
    print(f"  Primitive root: {results['passed']}/{total}")

    return results


def benchmark_operations() -> dict:
    """Benchmark FFT and NTT operations"""
    print("\nBenchmarking operations...")

    results = {
        "fft": {},
        "ntt": {},
        "convolution_naive": {},
        "convolution_ntt": {},
    }

    # FFT benchmark
    for n in [64, 128, 256, 512, 1024]:
        signal = [random.random() * 10 - 5 for _ in range(n)]

        # Warmup
        for _ in range(10):
            fft_cooley_tukey(signal.copy())

        # Benchmark FFT
        iterations = 1000
        start = time.perf_counter_ns()
        for _ in range(iterations):
            fft_cooley_tukey(signal.copy())
        end = time.perf_counter_ns()

        ns_per_op = (end - start) / iterations
        results["fft"][n] = ns_per_op
        print(f"  FFT n={n}: {ns_per_op:.1f} ns/op")

    # NTT benchmark
    p = 998244353
    for n in [64, 128, 256, 512, 1024, 2048]:
        signal = [random.randint(0, p - 1) for _ in range(n)]

        # Warmup
        for _ in range(10):
            ntt_iterative(signal.copy(), p)

        # Benchmark NTT
        iterations = 1000
        start = time.perf_counter_ns()
        for _ in range(iterations):
            ntt_iterative(signal.copy(), p)
        end = time.perf_counter_ns()

        ns_per_op = (end - start) / iterations
        results["ntt"][n] = ns_per_op
        print(f"  NTT n={n}: {ns_per_op:.1f} ns/op")

    # Convolution benchmark
    for size in [64, 128, 256, 512]:
        a = [random.randint(0, 100) for _ in range(size)]
        b = [random.randint(0, 100) for _ in range(size)]

        # Warmup
        for _ in range(5):
            convolution_naive(a, b, p)
            convolution_ntt(a, b, p)

        # Benchmark naive convolution
        iterations = 100
        start = time.perf_counter_ns()
        for _ in range(iterations):
            convolution_naive(a, b, p)
        end = time.perf_counter_ns()

        ns_per_op = (end - start) / iterations
        results["convolution_naive"][size] = ns_per_op
        print(f"  Naive conv n={size}: {ns_per_op:.1f} ns/op")

        # Benchmark NTT convolution
        iterations = 100
        start = time.perf_counter_ns()
        for _ in range(iterations):
            convolution_ntt(a, b, p)
        end = time.perf_counter_ns()

        ns_per_op = (end - start) / iterations
        results["convolution_ntt"][size] = ns_per_op
        print(f"  NTT conv n={size}: {ns_per_op:.1f} ns/op")

    return results


def run_all_tests():
    """Run all verification tests"""
    print("=" * 60)
    print("DCA Chapter 6: NTT and FFT Verification")
    print("=" * 60)

    # Run correctness tests
    fft_correctness = test_fft_correctness()
    fft_round_trip = test_fft_round_trip()
    ntt_correctness = test_ntt_correctness()
    convolution_correctness = test_convolution_correctness()
    convolution_theorem = test_convolution_theorem()
    primitive_root = test_primitive_root()

    # Run benchmarks
    benchmark_results = benchmark_operations()

    # Summary
    print("\n" + "=" * 60)
    print("VERIFICATION SUMMARY")
    print("=" * 60)

    all_tests = [
        ("FFT Correctness", fft_correctness),
        ("FFT Round-trip", fft_round_trip),
        ("NTT Correctness", ntt_correctness),
        ("Convolution Correctness", convolution_correctness),
        ("Convolution Theorem", convolution_theorem),
        ("Primitive Root", primitive_root),
    ]

    all_passed = True
    total_passed = 0
    total_failed = 0

    for test_name, results in all_tests:
        passed = sum(v.get("passed", 0) for v in results.values() if isinstance(v, dict))
        failed = sum(v.get("failed", 0) for v in results.values() if isinstance(v, dict))

        if isinstance(results, dict) and "passed" in results:
            passed = results["passed"]
            failed = results["failed"]

        total_passed += passed
        total_failed += failed

        if failed > 0:
            all_passed = False

        print(f"{test_name}: {passed}/{passed + failed} tests passed")

    print(f"\nTotal: {total_passed}/{total_passed + total_failed} tests passed")

    if all_passed:
        print("\n✓ ALL TESTS PASSED!")
    else:
        print("\n✗ SOME TESTS FAILED!")

    return {
        "fft_correctness": fft_correctness,
        "fft_round_trip": fft_round_trip,
        "ntt_correctness": ntt_correctness,
        "convolution_correctness": convolution_correctness,
        "convolution_theorem": convolution_theorem,
        "primitive_root": primitive_root,
        "benchmark": benchmark_results,
        "all_passed": all_passed,
        "total_passed": total_passed,
        "total_failed": total_failed,
    }


if __name__ == "__main__":
    verification_results = run_all_tests()

    # Exit with appropriate code
    exit(0 if verification_results["all_passed"] else 1)
