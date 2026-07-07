#!/usr/bin/env python3
"""
DCA Chapter 14: From Mathematical Definitions to ISA - Complete Verification Code
Author: Wang Bingqin
Date: 2026-07-06
"""

import random
import time
from typing import Dict, List, Tuple, Optional


class DCA_ISA:
    """
    Simplified DCA-ISA implementation
    Demonstrates mapping from mathematical definitions to instruction set
    """

    def __init__(self, w: int = 32, memory_size: int = 1024):
        """
        Initialize ISA state

        Args:
            w: Word length in bits
            memory_size: Size of memory array in words
        """
        self.w = w
        self.mask = (1 << w) - 1
        self.registers = [0] * 8  # 8 general-purpose registers
        self.memory = [0] * memory_size
        self.pc = 0  # Program counter
        self.flags = {'zero': False, 'carry': False, 'negative': False}

    def word_add(self, a: int, b: int) -> int:
        """ADD instruction: modular addition"""
        result = (a + b) & self.mask
        self._update_flags(result)
        return result

    def word_sub(self, a: int, b: int) -> int:
        """SUB instruction: subtraction via two's complement"""
        b_complement = (~b) & self.mask
        result = (a + b_complement + 1) & self.mask
        self._update_flags(result)
        return result

    def word_mul(self, a: int, b: int) -> int:
        """MUL instruction: shift-accumulate multiplication"""
        result = 0
        for i in range(self.w):
            if (b >> i) & 1:
                result = (result + (a << i)) & self.mask
        self._update_flags(result)
        return result

    def maj(self, a: int, b: int, c: int) -> int:
        """MAJ instruction: majority gate for full adder carry"""
        return (a & b) | (b & c) | (a & c)

    def popcnt(self, a: int) -> int:
        """POPCNT instruction: population count (Hamming weight)"""
        return bin(a & self.mask).count('1')

    def bitrev(self, a: int) -> int:
        """BITREV instruction: bit reversal for NTT"""
        result = 0
        for i in range(self.w):
            if (a >> i) & 1:
                result |= 1 << (self.w - 1 - i)
        return result & self.mask

    def min_op(self, a: int, b: int) -> int:
        """MIN instruction: minimum for optimization and ReLU"""
        return a if a < b else b

    def max_op(self, a: int, b: int) -> int:
        """MAX instruction: maximum for optimization and ReLU"""
        return a if a > b else b

    def load(self, addr: int) -> int:
        """LOAD instruction: load from memory"""
        return self.memory[addr & (len(self.memory) - 1)]

    def store(self, addr: int, value: int):
        """STORE instruction: store to memory"""
        self.memory[addr & (len(self.memory) - 1)] = value & self.mask

    def madd(self, accum: int, a: int, b: int) -> int:
        """MADD instruction: multiply-accumulate for matrix operations"""
        product = self.word_mul(a, b)
        return self.word_add(accum, product)

    def _update_flags(self, result: int):
        """Update condition flags based on result"""
        self.flags['zero'] = (result == 0)
        self.flags['negative'] = (result >> (self.w - 1)) & 1


class ISA_Verifier:
    """Verifier for ISA instruction correctness"""

    def __init__(self, isa: DCA_ISA):
        self.isa = isa
        self.results = {"passed": 0, "failed": 0}

    def verify_add(self) -> bool:
        """Verify ADD instruction specification"""
        print("Verifying ADD instruction...")

        # Fixed test cases
        test_cases = [
            (0, 0, 0),
            (1, 1, 2),
            ((1 << 31) - 1, 1, (1 << 31)),  # Near boundary
            (255, 1, 256),  # 8-bit-like overflow test
            ((1 << 32) - 1, 1, 0),  # Full overflow
        ]

        for a, b, expected in test_cases:
            result = self.isa.word_add(a, b)
            if result == (expected & self.isa.mask):
                self.results["passed"] += 1
            else:
                self.results["failed"] += 1
                print(f"  FAILED: {a} + {b} = {result}, expected {expected & self.isa.mask}")

        # Random tests
        for _ in range(1000):
            a = random.randint(0, self.isa.mask)
            b = random.randint(0, self.isa.mask)
            result = self.isa.word_add(a, b)
            expected = (a + b) & self.isa.mask
            if result == expected:
                self.results["passed"] += 1
            else:
                self.results["failed"] += 1

        print(f"  ADD: {self.results['passed'] - self.results['failed']} passed")
        return self.results["failed"] == 0

    def verify_sub(self) -> bool:
        """Verify SUB instruction specification"""
        print("\nVerifying SUB instruction...")

        test_cases = [
            (10, 3, 7),
            (0, 1, self.isa.mask),  # Underflow
            (100, 100, 0),
            (255, 10, 245),
        ]

        for a, b, expected in test_cases:
            result = self.isa.word_sub(a, b)
            if result == (expected & self.isa.mask):
                self.results["passed"] += 1
            else:
                self.results["failed"] += 1

        # Random tests
        for _ in range(1000):
            a = random.randint(0, self.isa.mask)
            b = random.randint(0, self.isa.mask)
            result = self.isa.word_sub(a, b)
            expected = (a - b) & self.isa.mask
            if result == expected:
                self.results["passed"] += 1
            else:
                self.results["failed"] += 1

        print(f"  SUB: {1005 - self.results['failed']} tests passed")
        return self.results["failed"] == 0

    def verify_mul(self) -> bool:
        """Verify MUL instruction specification"""
        print("\nVerifying MUL instruction...")

        test_cases = [
            (0, 0, 0),
            (1, 1, 1),
            (10, 5, 50),
            (100, 100, 10000),
            ((1 << 16) - 1, (1 << 16) - 1, ((1 << 16) - 1) ** 2),
        ]

        for a, b, expected in test_cases:
            result = self.isa.word_mul(a, b)
            if result == (expected & self.isa.mask):
                self.results["passed"] += 1
            else:
                self.results["failed"] += 1

        # Random tests (fewer for multiplication)
        for _ in range(500):
            a = random.randint(0, self.isa.mask)
            b = random.randint(0, self.isa.mask)
            result = self.isa.word_mul(a, b)
            expected = (a * b) & self.isa.mask
            if result == expected:
                self.results["passed"] += 1
            else:
                self.results["failed"] += 1

        print(f"  MUL: {505 - self.results['failed']} tests passed")
        return self.results["failed"] == 0

    def verify_maj(self) -> bool:
        """Verify MAJ instruction (majority gate)"""
        print("\nVerifying MAJ instruction...")

        # Test all combinations of 3 bits
        for a in [0, 1]:
            for b in [0, 1]:
                for c in [0, 1]:
                    result = self.isa.maj(a, b, c)
                    expected = 1 if (a + b + c) >= 2 else 0
                    if result == expected:
                        self.results["passed"] += 1
                    else:
                        self.results["failed"] += 1

        print(f"  MAJ: {8 - self.results['failed']} tests passed")
        return self.results["failed"] == 0

    def verify_popcnt(self) -> bool:
        """Verify POPCNT instruction"""
        print("\nVerifying POPCNT instruction...")

        test_values = [0, 1, 2, 3, 7, 15, 255, 1023, 0xFFFFFFFF]
        for val in test_values:
            result = self.isa.popcnt(val)
            expected = bin(val & self.isa.mask).count('1')
            if result == expected:
                self.results["passed"] += 1
            else:
                self.results["failed"] += 1

        # Random tests
        for _ in range(1000):
            val = random.randint(0, self.isa.mask)
            result = self.isa.popcnt(val)
            expected = bin(val & self.isa.mask).count('1')
            if result == expected:
                self.results["passed"] += 1
            else:
                self.results["failed"] += 1

        print(f"  POPCNT: {1009 - self.results['failed']} tests passed")
        return self.results["failed"] == 0

    def verify_bitrev(self) -> bool:
        """Verify BITREV instruction"""
        print("\nVerifying BITREV instruction...")

        # Test known patterns
        test_values = [0, 1, 0x80000000, 0xFFFFFFFF, 0xAAAAAAAA, 0x55555555]

        for val in test_values:
            result = self.isa.bitrev(val)
            # Verify double reversal returns original
            double_rev = self.isa.bitrev(result)
            if double_rev == val:
                self.results["passed"] += 1
            else:
                self.results["failed"] += 1

        # Random tests
        for _ in range(100):
            val = random.randint(0, self.isa.mask)
            result = self.isa.bitrev(val)
            double_rev = self.isa.bitrev(result)
            if double_rev == val:
                self.results["passed"] += 1
            else:
                self.results["failed"] += 1

        print(f"  BITREV: {106 - self.results['failed']} tests passed")
        return self.results["failed"] == 0

    def verify_min_max(self) -> bool:
        """Verify MIN and MAX instructions"""
        print("\nVerifying MIN/MAX instructions...")

        for _ in range(500):
            a = random.randint(0, self.isa.mask)
            b = random.randint(0, self.isa.mask)

            min_result = self.isa.min_op(a, b)
            max_result = self.isa.max_op(a, b)

            if min_result == min(a, b):
                self.results["passed"] += 1
            else:
                self.results["failed"] += 1

            if max_result == max(a, b):
                self.results["passed"] += 1
            else:
                self.results["failed"] += 1

        print(f"  MIN/MAX: {1000 - self.results['failed']} tests passed")
        return self.results["failed"] == 0

    def verify_madd(self) -> bool:
        """Verify MADD instruction"""
        print("\nVerifying MADD instruction...")

        for _ in range(500):
            accum = random.randint(0, self.isa.mask)
            a = random.randint(0, self.isa.mask)
            b = random.randint(0, self.isa.mask)

            result = self.isa.madd(accum, a, b)
            expected = (accum + (a * b)) & self.isa.mask

            if result == expected:
                self.results["passed"] += 1
            else:
                self.results["failed"] += 1

        print(f"  MADD: {500 - self.results['failed']} tests passed")
        return self.results["failed"] == 0

    def verify_semantic_preservation(self) -> bool:
        """Verify that composed operations preserve mathematical semantics"""
        print("\nVerifying semantic preservation...")

        # Test: (a + b) - b = a (mod 2^w)
        for _ in range(100):
            a = random.randint(0, self.isa.mask)
            b = random.randint(0, self.isa.mask)
            result = self.isa.word_sub(self.isa.word_add(a, b), b)
            if result == (a & self.isa.mask):
                self.results["passed"] += 1
            else:
                self.results["failed"] += 1

        print(f"  Semantic preservation: {100 - self.results['failed']} tests passed")
        return self.results["failed"] == 0


def benchmark_instructions(isa: DCA_ISA) -> Dict:
    """Benchmark instruction performance"""
    print("\nBenchmarking Instructions...")

    results = {}
    iterations = 10000

    operations = [
        ("ADD", lambda: isa.word_add(random.randint(0, isa.mask), random.randint(0, isa.mask))),
        ("SUB", lambda: isa.word_sub(random.randint(0, isa.mask), random.randint(0, isa.mask))),
        ("MUL", lambda: isa.word_mul(random.randint(0, isa.mask), random.randint(0, isa.mask))),
        ("MAJ", lambda: isa.maj(random.randint(0, 1), random.randint(0, 1), random.randint(0, 1))),
        ("POPCNT", lambda: isa.popcnt(random.randint(0, isa.mask))),
        ("BITREV", lambda: isa.bitrev(random.randint(0, isa.mask))),
        ("MIN", lambda: isa.min_op(random.randint(0, isa.mask), random.randint(0, isa.mask))),
        ("MAX", lambda: isa.max_op(random.randint(0, isa.mask), random.randint(0, isa.mask))),
        ("MADD", lambda: isa.madd(random.randint(0, isa.mask), random.randint(0, isa.mask), random.randint(0, isa.mask))),
    ]

    for op_name, op_func in operations:
        # Warmup
        for _ in range(100):
            op_func()

        # Benchmark
        start = time.perf_counter_ns()
        for _ in range(iterations):
            op_func()
        end = time.perf_counter_ns()

        ns_per_op = (end - start) / iterations
        results[op_name] = ns_per_op
        print(f"  {op_name}: {ns_per_op:.1f} ns/op")

    return results


def run_all_tests():
    """Run all verification tests"""
    print("=" * 60)
    print("DCA Chapter 14: From Mathematical Definitions to ISA")
    print("Verification")
    print("=" * 60)

    isa = DCA_ISA(w=32)
    verifier = ISA_Verifier(isa)

    # Run instruction verification
    verifier.verify_add()
    verifier.verify_sub()
    verifier.verify_mul()
    verifier.verify_maj()
    verifier.verify_popcnt()
    verifier.verify_bitrev()
    verifier.verify_min_max()
    verifier.verify_madd()
    verifier.verify_semantic_preservation()

    # Run benchmarks
    benchmark_results = benchmark_instructions(isa)

    # Summary
    print("\n" + "=" * 60)
    print("VERIFICATION SUMMARY")
    print("=" * 60)

    total_passed = verifier.results["passed"]
    total_failed = verifier.results["failed"]
    total_tests = total_passed + total_failed

    print(f"Total tests: {total_tests}")
    print(f"Passed: {total_passed}")
    print(f"Failed: {total_failed}")

    if total_failed == 0:
        print("\nALL TESTS PASSED!")
    else:
        print(f"\n{total_failed} TESTS FAILED!")

    return {
        "results": verifier.results,
        "benchmark": benchmark_results,
        "all_passed": total_failed == 0
    }


if __name__ == "__main__":
    verification_results = run_all_tests()
    success = verification_results["all_passed"]
    exit(0 if success else 1)