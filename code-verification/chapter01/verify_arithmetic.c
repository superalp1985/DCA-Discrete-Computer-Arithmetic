/*
 * DCA Chapter 1: Arithmetic Foundations - C Verification Code
 * Author: Wang Bingqin
 * Date: 2026-07-06
 */

#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <time.h>
#include <assert.h>

/* ========== Utility Macros ========== */

#define MASK(w) (((1ULL << (w)) - 1ULL))

/* ========== Modular Addition ========== */

uint64_t word_add(uint64_t a, uint64_t b, int w) {
    uint64_t mask = MASK(w);
    return (a + b) & mask;
}

/* ========== Two's Complement Subtraction ========== */

uint64_t word_sub(uint64_t a, uint64_t b, int w) {
    uint64_t mask = MASK(w);
    uint64_t b_complement = (~b) & mask;
    return word_add(a, word_add(b_complement, 1, w), w);
}

/* ========== Shift-Accumulate Multiplication ========== */

uint64_t word_mul(uint64_t a, uint64_t b, int w) {
    uint64_t mask = MASK(w);
    uint64_t result = 0;

    for (int i = 0; i < w; i++) {
        if ((b >> i) & 1) {
            result = (result + (a << i)) & mask;
        }
    }

    return result;
}

/* ========== Division ========== */

typedef struct {
    uint64_t quotient;
    uint64_t remainder;
} DivResult;

DivResult word_div(uint64_t a, uint64_t b, int w) {
    uint64_t mask = MASK(w);
    uint64_t q = 0;
    uint64_t r = 0;

    for (int i = w - 1; i >= 0; i--) {
        r = (r << 1) | ((a >> i) & 1);
        if (r >= b) {
            r -= b;
            q |= (1ULL << i);
        }
    }

    DivResult result = {q, r};
    return result;
}

/* ========== Test Framework ========== */

typedef struct {
    int passed;
    int failed;
} TestResult;

TestResult test_word_add() {
    printf("Testing word_add...\n");

    TestResult result = {0, 0};
    TestResult random_result[4] = {{0, 0}, {0, 0}, {0, 0}, {0, 0}};
    int widths[] = {8, 16, 32, 64};

    /* Fixed test cases */
    struct {
        uint64_t a, b, expected;
        int w;
    } fixed_cases[] = {
        {0, 0, 0, 8},
        {255, 1, 0, 8},
        {250, 10, 4, 8},
        {65535, 1, 0, 16},
        {127, 1, 0, 7},
    };

    for (int i = 0; i < 5; i++) {
        uint64_t a = fixed_cases[i].a;
        uint64_t b = fixed_cases[i].b;
        uint64_t expected = fixed_cases[i].expected;
        int w = fixed_cases[i].w;

        uint64_t actual = word_add(a, b, w);
        if (actual == expected) {
            result.passed++;
        } else {
            result.failed++;
            printf("  FAILED: %llu + %llu (w=%d) = %llu, expected %llu\n",
                   (unsigned long long)a, (unsigned long long)b, w,
                   (unsigned long long)actual, (unsigned long long)expected);
        }
    }

    /* Random tests */
    srand(time(NULL));
    for (int wi = 0; wi < 4; wi++) {
        int w = widths[wi];
        uint64_t mask = MASK(w);

        for (int j = 0; j < 10000; j++) {
            uint64_t a = rand() & mask;
            uint64_t b = rand() & mask;
            uint64_t actual = word_add(a, b, w);
            uint64_t expected = (a + b) & mask;

            if (actual == expected) {
                random_result[wi].passed++;
            } else {
                random_result[wi].failed++;
            }
        }
    }

    printf("  Fixed tests: %d/%d\n", result.passed, result.passed + result.failed);
    for (int wi = 0; wi < 4; wi++) {
        int w = widths[wi];
        int total = random_result[wi].passed + random_result[wi].failed;
        printf("  %d-bit random: %d/%d\n", w, random_result[wi].passed, total);
    }

    return result;
}

TestResult test_word_sub() {
    printf("Testing word_sub...\n");

    TestResult result = {0, 0};
    TestResult random_result[4] = {{0, 0}, {0, 0}, {0, 0}, {0, 0}};
    int widths[] = {8, 16, 32, 64};

    /* Fixed test cases */
    struct {
        uint64_t a, b, expected;
        int w;
    } fixed_cases[] = {
        {10, 3, 7, 8},
        {0, 1, 255, 8},
        {5, 10, 251, 8},
        {100, 100, 0, 8},
        {255, 255, 0, 8},
    };

    for (int i = 0; i < 5; i++) {
        uint64_t a = fixed_cases[i].a;
        uint64_t b = fixed_cases[i].b;
        uint64_t expected = fixed_cases[i].expected;
        int w = fixed_cases[i].w;

        uint64_t actual = word_sub(a, b, w);
        if (actual == expected) {
            result.passed++;
        } else {
            result.failed++;
            printf("  FAILED: %llu - %llu (w=%d) = %llu, expected %llu\n",
                   (unsigned long long)a, (unsigned long long)b, w,
                   (unsigned long long)actual, (unsigned long long)expected);
        }
    }

    /* Random tests */
    for (int wi = 0; wi < 4; wi++) {
        int w = widths[wi];
        uint64_t mask = MASK(w);

        for (int j = 0; j < 10000; j++) {
            uint64_t a = rand() & mask;
            uint64_t b = rand() & mask;
            uint64_t actual = word_sub(a, b, w);
            uint64_t expected = (a - b) & mask;

            if (actual == expected) {
                random_result[wi].passed++;
            } else {
                random_result[wi].failed++;
            }
        }
    }

    printf("  Fixed tests: %d/%d\n", result.passed, result.passed + result.failed);
    for (int wi = 0; wi < 4; wi++) {
        int w = widths[wi];
        int total = random_result[wi].passed + random_result[wi].failed;
        printf("  %d-bit random: %d/%d\n", w, random_result[wi].passed, total);
    }

    return result;
}

TestResult test_word_mul() {
    printf("Testing word_mul...\n");

    TestResult result = {0, 0};
    TestResult random_result[3] = {{0, 0}, {0, 0}, {0, 0}};
    int widths[] = {8, 16, 32};

    /* Fixed test cases */
    struct {
        uint64_t a, b, expected;
        int w;
    } fixed_cases[] = {
        {0, 0, 0, 8},
        {1, 1, 1, 8},
        {10, 5, 50, 8},
        {255, 255, 1, 8},
        {256, 2, 512, 16},
        {1000, 1000, 16960, 16},
    };

    for (int i = 0; i < 6; i++) {
        uint64_t a = fixed_cases[i].a;
        uint64_t b = fixed_cases[i].b;
        uint64_t expected = fixed_cases[i].expected;
        int w = fixed_cases[i].w;

        uint64_t actual = word_mul(a, b, w);
        if (actual == expected) {
            result.passed++;
        } else {
            result.failed++;
            printf("  FAILED: %llu * %llu (w=%d) = %llu, expected %llu\n",
                   (unsigned long long)a, (unsigned long long)b, w,
                   (unsigned long long)actual, (unsigned long long)expected);
        }
    }

    /* Random tests */
    for (int wi = 0; wi < 3; wi++) {
        int w = widths[wi];
        uint64_t mask = MASK(w);

        for (int j = 0; j < 1000; j++) {
            uint64_t a = rand() & mask;
            uint64_t b = rand() & mask;
            uint64_t actual = word_mul(a, b, w);
            uint64_t expected = (a * b) & mask;

            if (actual == expected) {
                random_result[wi].passed++;
            } else {
                random_result[wi].failed++;
            }
        }
    }

    printf("  Fixed tests: %d/%d\n", result.passed, result.passed + result.failed);
    for (int wi = 0; wi < 3; wi++) {
        int w = widths[wi];
        int total = random_result[wi].passed + random_result[wi].failed;
        printf("  %d-bit random: %d/%d\n", w, random_result[wi].passed, total);
    }

    return result;
}

TestResult test_word_div() {
    printf("Testing word_div...\n");

    TestResult result = {0, 0};
    TestResult random_result[3] = {{0, 0}, {0, 0}, {0, 0}};
    int widths[] = {8, 16, 32};

    /* Fixed test cases */
    struct {
        uint64_t a, b, expected_q, expected_r;
        int w;
    } fixed_cases[] = {
        {100, 10, 10, 0, 8},
        {255, 17, 15, 0, 8},
        {154, 10, 15, 4, 8},
        {0, 1, 0, 0, 8},
        {65535, 255, 257, 0, 16},
        {100, 7, 14, 2, 8},
    };

    for (int i = 0; i < 6; i++) {
        uint64_t a = fixed_cases[i].a;
        uint64_t b = fixed_cases[i].b;
        uint64_t expected_q = fixed_cases[i].expected_q;
        uint64_t expected_r = fixed_cases[i].expected_r;
        int w = fixed_cases[i].w;

        DivResult dr = word_div(a, b, w);
        if (dr.quotient == expected_q && dr.remainder == expected_r) {
            result.passed++;
        } else {
            result.failed++;
            printf("  FAILED: %llu / %llu (w=%d) = (%llu, %llu), expected (%llu, %llu)\n",
                   (unsigned long long)a, (unsigned long long)b, w,
                   (unsigned long long)dr.quotient, (unsigned long long)dr.remainder,
                   (unsigned long long)expected_q, (unsigned long long)expected_r);
        }
    }

    /* Random tests - verify invariant a = b*q + r and 0 <= r < b */
    for (int wi = 0; wi < 3; wi++) {
        int w = widths[wi];
        uint64_t mask = MASK(w);

        for (int j = 0; j < 1000; j++) {
            uint64_t a = rand() & mask;
            uint64_t b = (rand() & mask) | 1;  /* Ensure b > 0 */
            DivResult dr = word_div(a, b, w);

            /* Verify invariant a = b*q + r */
            uint64_t reconstructed = b * dr.quotient + dr.remainder;
            int invariant_ok = (reconstructed == a);
            int bound_ok = (dr.remainder < b);

            if (invariant_ok && bound_ok) {
                random_result[wi].passed++;
            } else {
                random_result[wi].failed++;
            }
        }
    }

    printf("  Fixed tests: %d/%d\n", result.passed, result.passed + result.failed);
    for (int wi = 0; wi < 3; wi++) {
        int w = widths[wi];
        int total = random_result[wi].passed + random_result[wi].failed;
        printf("  %d-bit random: %d/%d\n", w, random_result[wi].passed, total);
    }

    return result;
}

/* ========== Main ========== */

int main() {
    printf("============================================================\n");
    printf("DCA Chapter 1: Arithmetic Foundations Verification\n");
    printf("============================================================\n\n");

    TestResult add_result = test_word_add();
    TestResult sub_result = test_word_sub();
    TestResult mul_result = test_word_mul();
    TestResult div_result = test_word_div();

    printf("\n============================================================\n");
    printf("VERIFICATION SUMMARY\n");
    printf("============================================================\n");

    int total_passed = 0;
    int total_failed = 0;

    struct {
        char *name;
        TestResult result;
    } results[] = {
        {"word_add", add_result},
        {"word_sub", sub_result},
        {"word_mul", mul_result},
        {"word_div", div_result}
    };

    for (int i = 0; i < 4; i++) {
        total_passed += results[i].result.passed;
        total_failed += results[i].result.failed;
        printf("%s: %d/%d fixed tests passed\n",
               results[i].name,
               results[i].result.passed,
               results[i].result.passed + results[i].result.failed);
    }

    if (total_failed == 0) {
        printf("\nALL TESTS PASSED!\n");
        return 0;
    } else {
        printf("\nSOME TESTS FAILED!\n");
        return 1;
    }
}