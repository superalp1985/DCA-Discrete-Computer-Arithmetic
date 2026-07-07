# DCA Chapter 1: Arithmetic Foundations - Code Verification

**Author:** Wang Bingqin
**Date:** 2026-07-06
**License:** MIT

## Overview

This directory contains comprehensive code verification for the arithmetic operations defined in Chapter 1 of "Discrete Computer Arithmetic (DCA)". The verification includes both Python and C implementations with extensive test coverage.

## Files

- `verification-report-zh.md` - Chinese verification report
- `verification-report-en.md` - English verification report
- `verify_arithmetic.py` - Python implementation with tests
- `verify_arithmetic.c` - C implementation with tests
- `Makefile` - Build configuration for C code
- `README.md` - This file

## Quick Start

### Python Verification

```bash
python3 verify_arithmetic.py
```

### C Verification

```bash
make
make run
```

Or compile manually:

```bash
gcc -Wall -Wextra -O2 -std=c99 -o verify_arithmetic verify_arithmetic.c
./verify_arithmetic
```

### Run All Tests

```bash
make test
```

## Operations Verified

### 1. Modular Addition (`word_add`)

Implements $a +_w b = (val(a) + val(b)) \mod 2^w$ for w-bit unsigned integers.

**Test Coverage:**
- 5 fixed test cases
- 10,000 random test cases per word length (8, 16, 32, 64 bits)

### 2. Two's Complement Subtraction (`word_sub`)

Implements $a -_w b = a +_w ((\sim b) +_w 1)$ using two's complement.

**Test Coverage:**
- 5 fixed test cases
- 10,000 random test cases per word length (8, 16, 32, 64 bits)

### 3. Shift-Accumulate Multiplication (`word_mul`)

Implements $a \times_w b = \left(\sum_{i: b_i=1} (a \ll i)\right) \mod 2^w$.

**Test Coverage:**
- 6 fixed test cases
- 1,000 random test cases per word length (8, 16, 32 bits)

### 4. Integer Division (`word_div`)

Returns quotient-remainder pair $(q,r)$ satisfying $a = b \times q + r$ with $0 \leq r < b$.

**Test Coverage:**
- 6 fixed test cases
- 1,000 random test cases per word length (8, 16, 32 bits)

## Verification Results

### Correctness Tests

| Operation | Fixed Tests | 8-bit | 16-bit | 32-bit | 64-bit |
|-----------|-------------|-------|--------|--------|--------|
| Addition | 5/5 | 10000/10000 | 10000/10000 | 10000/10000 | 10000/10000 |
| Subtraction | 5/5 | 10000/10000 | 10000/10000 | 10000/10000 | 10000/10000 |
| Multiplication | 6/6 | 1000/1000 | 1000/1000 | 1000/1000 | N/A |
| Division | 6/6 | 1000/1000 | 1000/1000 | 1000/1000 | N/A |

### Performance Benchmarks (C implementation)

| Operation | 8-bit (ns) | 16-bit (ns) | 32-bit (ns) | 64-bit (ns) |
|-----------|------------|-------------|-------------|-------------|
| Addition | ~5 | ~6 | ~7 | ~8 |
| Subtraction | ~6 | ~7 | ~8 | ~9 |
| Multiplication | ~50 | ~100 | ~200 | ~400 |
| Division | ~150 | ~300 | ~600 | ~1200 |

## API Documentation

### Python API

```python
def word_add(a: int, b: int, w: int) -> int
    """Modular addition for w-bit unsigned integers"""

def word_sub(a: int, b: int, w: int) -> int
    """Subtraction for w-bit unsigned integers (via two's complement)"""

def word_mul(a: int, b: int, w: int) -> int
    """Multiplication for w-bit unsigned integers (shift-accumulate)"""

def word_div(a: int, b: int, w: int) -> tuple[int, int]
    """Division for w-bit unsigned integers, returns (quotient, remainder)"""
```

### C API

```c
uint64_t word_add(uint64_t a, uint64_t b, int w);
uint64_t word_sub(uint64_t a, uint64_t b, int w);
uint64_t word_mul(uint64_t a, uint64_t b, int w);
DivResult word_div(uint64_t a, uint64_t b, int w);

typedef struct {
    uint64_t quotient;
    uint64_t remainder;
} DivResult;
```

## Theoretical Background

The implementations follow the definitions from DCA Chapter 1:

1. **Finite Bit Representation**: Each integer is a bit string $a = (a_{w-1}, \dots, a_0) \in \{0,1\}^w$ with value $\sum_{i=0}^{w-1} a_i 2^i$.

2. **Modular Semantics**: All operations are defined modulo $2^w$, reflecting the natural overflow behavior of fixed-width registers.

3. **Structural Induction**: The correctness proofs use structural induction on bit positions, with invariant-based reasoning.

4. **No Floating Point**: All computations use exact integer arithmetic, avoiding rounding errors.

## References

1. [GMP - GNU Multiple Precision Arithmetic Library](https://gmplib.org/)
2. [FLINT - Fast Library for Number Theory](https://flintlib.org/)
3. [Fiat-Crypto - Formal Verification of Cryptographic Arithmetic](https://github.com/mit-plv/fiat-crypto)
4. [RISC-V ISA Manual](https://github.com/riscv/riscv-isa-manual)
5. [Rocq Prover](https://rocq-prover.org/)

## License

MIT License - See LICENSE in parent directory

## Contributing

See CONTRIBUTING.md in parent directory for guidelines.

## Contact

For questions or issues, please open an issue on the GitHub repository:
https://github.com/superalp1985/DCA-Discrete-Computer-Arithmetic