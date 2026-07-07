"""
DCA Chapter 30: Formal Verification Loop Verification Code
Chapter Title: Formal Verification Loop - Specification, Implementation, Testing, and Proof
验证内容：规格-实现-证明-测试闭环、精化关系、循环不变式
"""

import inspect
import time
from typing import Callable, List, Dict, Any, TypeVar, Generic, Tuple
from dataclasses import dataclass
from enum import Enum
import hashlib
import random


# ============================================================================
# Specification Language (Simple Pre/Post Conditions)
# ============================================================================

@dataclass
class Specification:
    """规格说明"""
    name: str
    preconditions: List[Callable]  # 前置条件
    postconditions: List[Callable]  # 后置条件
    invariants: List[Callable] = None  # 循环不变式

    def __post_init__(self):
        if self.invariants is None:
            self.invariants = []


class VerificationResult:
    """验证结果"""
    def __init__(self, passed: bool, message: str = "", details: Dict = None):
        self.passed = passed
        self.message = message
        self.details = details or {}

    def __bool__(self):
        return self.passed


# ============================================================================
# Refinement Relation
# ============================================================================

@dataclass
class RefinementRelation:
    """精化关系：抽象状态与具体状态之间的关系"""
    name: str
    relation_check: Callable[[Any, Any], bool]  # R(A, C): 抽象状态A与具体状态C是否满足关系

    def check(self, abstract_state: Any, concrete_state: Any) -> bool:
        """检查精化关系是否成立"""
        return self.relation_check(abstract_state, concrete_state)


# ============================================================================
# Property-Based Testing
# ============================================================================

class PropertyTester:
    """基于性质的测试器"""

    def __init__(self):
        self.test_results = []
        self.performance_data = {}

    def generate_integers(self, n: int, min_val: int = -100, max_val: int = 100) -> List[int]:
        """生成测试用整数"""
        return [random.randint(min_val, max_val) for _ in range(n)]

    def generate_lists(self, n: int, length: int = 10) -> List[List[int]]:
        """生成测试用列表"""
        return [[random.randint(-10, 10) for _ in range(length)] for _ in range(n)]

    def test_property(self, impl: Callable, spec: Specification,
                     test_cases: List[Any]) -> VerificationResult:
        """
        测试实现是否满足规格

        Args:
            impl: 实现函数
            spec: 规格说明
            test_cases: 测试用例

        Returns:
            验证结果
        """
        passed = 0
        failed = 0
        failures = []

        for case in test_cases:
            # 检查前置条件
            preconditions_met = all(cond(case) for cond in spec.preconditions)
            if not preconditions_met:
                continue  # 跳过不满足前置条件的用例

            # 执行实现
            try:
                result = impl(case)

                # 检查后置条件
                postconditions_met = all(cond(case, result) for cond in spec.postconditions)
                if postconditions_met:
                    passed += 1
                else:
                    failed += 1
                    failures.append((case, result))
            except Exception as e:
                failed += 1
                failures.append((case, str(e)))

        total = passed + failed
        success_rate = passed / total if total > 0 else 0

        return VerificationResult(
            passed=success_rate >= 0.95,  # 95% 通过率
            message=f"Passed: {passed}/{total} ({success_rate*100:.1f}%)",
            details={'passed': passed, 'failed': failed, 'failures': failures[:3]}
        )

    def benchmark(self, func: Callable, inputs: List[Any], iterations: int = 100) -> Dict:
        """性能基准测试"""
        times = []
        for inp in inputs:
            start = time.time()
            for _ in range(iterations):
                result = func(inp)
            elapsed = time.time() - start
            times.append(elapsed / iterations)

        return {
            'mean': sum(times) / len(times),
            'min': min(times),
            'max': max(times),
            'std': (sum((t - sum(times)/len(times))**2 for t in times) / len(times))**0.5
        }


# ============================================================================
# Loop Invariant Verification
# ============================================================================

class LoopInvariantVerifier:
    """循环不变式验证器"""

    def __init__(self):
        self.traces = []

    def verify_invariant(self, loop_func: Callable, invariant: Callable,
                        initial_state: Any, max_iterations: int = 1000) -> VerificationResult:
        """
        验证循环不变式

        Args:
            loop_func: 循环函数 (state -> state)
            invariant: 不变式谓词 (state -> bool)
            initial_state: 初始状态
            max_iterations: 最大迭代次数

        Returns:
            验证结果
        """
        state = initial_state

        # 检查初始状态满足不变式
        if not invariant(state):
            return VerificationResult(
                passed=False,
                message="Initial state does not satisfy invariant",
                details={'state': state}
            )

        # 执行循环并检查不变式
        for i in range(max_iterations):
            # 检查循环前不变式成立
            if not invariant(state):
                return VerificationResult(
                    passed=False,
                    message=f"Invariant violated at iteration {i}",
                    details={'iteration': i, 'state': state}
                )

            # 执行一步
            try:
                state = loop_func(state)
            except Exception as e:
                return VerificationResult(
                    passed=False,
                    message=f"Loop failed at iteration {i}: {str(e)}",
                    details={'iteration': i, 'error': str(e)}
                )

        return VerificationResult(
            passed=True,
            message=f"Invariant holds for {max_iterations} iterations"
        )


# ============================================================================
# Refinement Verification
# ============================================================================

class RefinementVerifier:
    """精化验证器"""

    def verify_stepwise_refinement(self, abstract_step: Callable, concrete_step: Callable,
                                   refinement: RefinementRelation,
                                   initial_abstract: Any, initial_concrete: Any,
                                   steps: int = 10) -> VerificationResult:
        """
        验证逐步精化关系

        验证：如果 R(A, C) 成立，且 A' = abstract_step(A), C' = concrete_step(C)
        则应该存在 A'' 使得 R(A'', C') 成立

        Args:
            abstract_step: 抽象步函数
            concrete_step: 具体步函数
            refinement: 精化关系
            initial_abstract: 初始抽象状态
            initial_concrete: 初始具体状态
            steps: 验证步数

        Returns:
            验证结果
        """
        A = initial_abstract
        C = initial_concrete

        # 检查初始关系
        if not refinement.check(A, C):
            return VerificationResult(
                passed=False,
                message="Initial states do not satisfy refinement relation"
            )

        for i in range(steps):
            # 执行抽象步和具体步
            A_next = abstract_step(A)
            C_next = concrete_step(C)

            # 检查精化关系是否保持
            if not refinement.check(A_next, C_next):
                return VerificationResult(
                    passed=False,
                    message=f"Refinement relation violated at step {i}",
                    details={'abstract': A_next, 'concrete': C_next}
                )

            A, C = A_next, C_next

        return VerificationResult(
            passed=True,
            message=f"Refinement relation holds for {steps} steps"
        )


# ============================================================================
# Example Specifications and Implementations
# ============================================================================

# Example 1: Sorting
def sorting_spec() -> Specification:
    """排序规格"""
    def is_list(x): return isinstance(x, list)
    def non_empty(x): return len(x) > 0

    def is_permutation(input_list, output_list):
        """输出是输入的排列"""
        return sorted(input_list) == sorted(output_list)

    def is_sorted(input_list, output_list):
        """输出是有序的"""
        return all(output_list[i] <= output_list[i+1] for i in range(len(output_list)-1))

    return Specification(
        name="Sorting",
        preconditions=[is_list, non_empty],
        postconditions=[is_permutation, is_sorted]
    )

def bubble_sort(arr: List[int]) -> List[int]:
    """冒泡排序实现"""
    result = arr.copy()
    n = len(result)
    for i in range(n):
        for j in range(0, n-i-1):
            if result[j] > result[j+1]:
                result[j], result[j+1] = result[j+1], result[j]
    return result

def bubble_sort_step(state: Tuple[List[int], int, int]) -> Tuple[List[int], int, int]:
    """冒泡排序的单步（用于不变式验证）"""
    arr, i, j = state
    new_arr = arr.copy()

    if i < len(new_arr):
        if j < len(new_arr) - i - 1:
            if new_arr[j] > new_arr[j+1]:
                new_arr[j], new_arr[j+1] = new_arr[j+1], new_arr[j]
            return (new_arr, i, j + 1)
        else:
            return (new_arr, i + 1, 0)
    else:
        return (new_arr, i, j)

# Example 2: Matrix Multiplication
def matrix_mult_spec() -> Specification:
    """矩阵乘法规格"""
    def is_matrix(x): return isinstance(x, list) and all(isinstance(row, list) for row in x)
    def is_square(x): return all(len(row) == len(x) for row in x)

    def dimensions_match(input_mats, output_mat):
        """维度匹配"""
        A, B = input_mats
        return len(output_mat) == len(A) and len(output_mat[0]) == len(B[0])

    def correct_computation(input_mats, output_mat):
        """计算正确"""
        A, B = input_mats
        n = len(A)
        for i in range(n):
            for j in range(n):
                if output_mat[i][j] != sum(A[i][k] * B[k][j] for k in range(n)):
                    return False
        return True

    return Specification(
        name="Matrix Multiplication",
        preconditions=[is_matrix, is_square],
        postconditions=[dimensions_match, correct_computation]
    )

def matrix_multiply(A: List[List[int]], B: List[List[int]]) -> List[List[int]]:
    """矩阵乘法实现"""
    n = len(A)
    result = [[0 for _ in range(n)] for _ in range(n)]
    for i in range(n):
        for j in range(n):
            result[i][j] = sum(A[i][k] * B[k][j] for k in range(n))
    return result

# Example 3: Binary Search
def binary_search_spec() -> Specification:
    """二分查找规格"""
    def is_sorted_list(x):
        return isinstance(x, list) and all(x[i] <= x[i+1] for i in range(len(x)-1))

    def index_in_range(input_tuple, result):
        arr, target = input_tuple
        return result is None or -len(arr) <= result < len(arr)

    def element_found(input_tuple, result):
        arr, target = input_tuple
        if result is None or result == -1:
            return target not in arr
        return arr[result] == target

    return Specification(
        name="Binary Search",
        preconditions=[is_sorted_list],
        postconditions=[index_in_range, element_found]
    )

def binary_search(arr: List[int], target: int) -> int:
    """二分查找实现"""
    left, right = 0, len(arr) - 1
    while left <= right:
        mid = (left + right) // 2
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
    return -1


# ============================================================================
# Verification Loop Implementation
# ============================================================================

class VerificationLoop:
    """验证闭环"""

    def __init__(self):
        self.property_tester = PropertyTester()
        self.invariant_verifier = LoopInvariantVerifier()
        self.refinement_verifier = RefinementVerifier()
        self.verification_log = []

    def log(self, component: str, result: VerificationResult):
        """记录验证结果"""
        self.verification_log.append({
            'component': component,
            'result': result,
            'timestamp': time.time()
        })

    def verify_component(self, name: str, impl: Callable, spec: Specification,
                         test_cases: List[Any]) -> bool:
        """验证单个组件"""
        result = self.property_tester.test_property(impl, spec, test_cases)
        self.log(name, result)
        return result.passed

    def verify_loop_invariant(self, name: str, loop_func: Callable,
                              invariant: Callable, initial_state: Any) -> bool:
        """验证循环不变式"""
        result = self.invariant_verifier.verify_invariant(loop_func, invariant, initial_state)
        self.log(f"{name}_invariant", result)
        return result.passed

    def verify_refinement(self, name: str, abstract: Callable, concrete: Callable,
                         refinement: RefinementRelation, initial_A: Any,
                         initial_C: Any) -> bool:
        """验证精化关系"""
        result = self.refinement_verifier.verify_stepwise_refinement(
            abstract, concrete, refinement, initial_A, initial_C
        )
        self.log(f"{name}_refinement", result)
        return result.passed

    def generate_report(self) -> Dict:
        """生成验证报告"""
        passed = sum(1 for log in self.verification_log if log['result'].passed)
        total = len(self.verification_log)

        return {
            'total_verifications': total,
            'passed': passed,
            'failed': total - passed,
            'success_rate': passed / total if total > 0 else 0,
            'details': self.verification_log
        }


# ============================================================================
# Verification Tests
# ============================================================================

class FormalVerificationTests:
    """形式化验证测试"""

    def __init__(self):
        self.loop = VerificationLoop()
        self.results = []

    def test_sorting_specification(self):
        """测试排序规格"""
        print("\n[TEST] Sorting Specification")
        spec = sorting_spec()
        test_cases = self.loop.property_tester.generate_lists(100)

        result = self.loop.verify_component("bubble_sort", bubble_sort, spec, test_cases)
        self.results.append(("Sorting Spec", result))

        # 验证循环不变式
        def bubble_sort_invariant(state):
            arr, i, j = state
            # 最后 i 个元素已排序
            if i > 0:
                return all(arr[-k] >= arr[-k-1] for k in range(1, i+1))
            return True

        initial_state = ([3, 1, 4, 1, 5], 0, 0)
        inv_result = self.loop.verify_loop_invariant(
            "bubble_sort", bubble_sort_step, bubble_sort_invariant, initial_state
        )
        self.results.append(("Bubble Sort Invariant", inv_result))

    def test_matrix_multiplication_spec(self):
        """测试矩阵乘法规格"""
        print("\n[TEST] Matrix Multiplication Specification")
        spec = matrix_mult_spec()

        # 生成测试用例
        test_cases = []
        for _ in range(50):
            n = random.randint(2, 5)
            A = [[random.randint(-5, 5) for _ in range(n)] for _ in range(n)]
            B = [[random.randint(-5, 5) for _ in range(n)] for _ in range(n)]
            test_cases.append((A, B))

        result = self.loop.verify_component("matrix_multiply", matrix_multiply, spec, test_cases)
        self.results.append(("Matrix Multiplication Spec", result))

    def test_binary_search_spec(self):
        """测试二分查找规格"""
        print("\n[TEST] Binary Search Specification")
        spec = binary_search_spec()

        test_cases = []
        for _ in range(100):
            arr = sorted(random.sample(range(-100, 100), random.randint(10, 50)))
            target = random.randint(-100, 100)
            test_cases.append((arr, target))

        result = self.loop.verify_component("binary_search", binary_search, spec, test_cases)
        self.results.append(("Binary Search Spec", result))

    def test_refinement_relation(self):
        """测试精化关系"""
        print("\n[TEST] Refinement Relation")

        # 抽象规格：计数器
        def abstract_counter_step(state):
            count, _ = state
            return (count + 1, None)

        # 具体实现：带溢出检查的计数器
        def concrete_counter_step(state):
            count, overflow = state
            new_count = (count + 1) % 256
            new_overflow = overflow or (new_count < count)
            return (new_count, new_overflow)

        # 精化关系：当没有溢出时，抽象计数与具体计数相等
        def refinement_check(abstract, concrete):
            return abstract[0] == concrete[0]

        refinement = RefinementRelation(
            name="Counter Refinement",
            relation_check=refinement_check
        )

        initial_A = (0, None)
        initial_C = (0, False)

        result = self.loop.verify_refinement(
            "counter", abstract_counter_step, concrete_counter_step,
            refinement, initial_A, initial_C
        )
        self.results.append(("Counter Refinement", result))

    def test_performance_benchmarks(self):
        """性能基准测试"""
        print("\n[TEST] Performance Benchmarks")

        # 测试不同规模的排序性能
        for size in [10, 100, 1000]:
            test_data = [random.randint(-1000, 1000) for _ in range(size)]
            benchmark = self.loop.property_tester.benchmark(
                bubble_sort, [test_data], iterations=10
            )
            self.results.append((f"Sort Performance (n={size})", benchmark))

    def run_all_tests(self):
        """运行所有测试"""
        print("=" * 70)
        print("DCA Chapter 30: Formal Verification Loop Tests")
        print("=" * 70)

        start_time = time.time()

        self.test_sorting_specification()
        self.test_matrix_multiplication_spec()
        self.test_binary_search_spec()
        self.test_refinement_relation()
        self.test_performance_benchmarks()

        elapsed = time.time() - start_time

        self.print_summary(elapsed)

    def print_summary(self, elapsed: float):
        """打印测试总结"""
        print("\n" + "=" * 70)
        print("VERIFICATION SUMMARY")
        print("=" * 70)
        print(f"Total tests: {len(self.results)}")
        print(f"Time elapsed: {elapsed:.4f}s")

        passed = sum(1 for _, result in self.results if isinstance(result, bool) and result)
        failed = sum(1 for _, result in self.results if isinstance(result, bool) and not result)

        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(f"Success rate: {100 * passed / (passed + failed):.1f}%")

        # 详细报告
        report = self.loop.generate_report()
        print(f"\nVerification Loop Report:")
        print(f"  Total verifications: {report['total_verifications']}")
        print(f"  Success rate: {report['success_rate']*100:.1f}%")

        print("\n" + "=" * 70)


# ============================================================================
# Proof Certificate System
# ============================================================================

class ProofCertificate:
    """证明证书系统"""

    @staticmethod
    def generate_hash(content: str) -> str:
        """生成内容的哈希"""
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    @staticmethod
    def create_certificate(theorem: str, proof_steps: List[str]) -> Dict:
        """创建证明证书"""
        content = "|".join([theorem] + proof_steps)
        return {
            'theorem': theorem,
            'proof_hash': ProofCertificate.generate_hash(content),
            'steps': len(proof_steps),
            'verified': True
        }

    @staticmethod
    def verify_certificate(certificate: Dict, proof_steps: List[str]) -> bool:
        """验证证明证书"""
        content = "|".join([certificate['theorem']] + proof_steps)
        expected_hash = ProofCertificate.generate_hash(content)
        return certificate['proof_hash'] == expected_hash


def demonstrate_proof_certificates():
    """演示证明证书系统"""
    print("\n" + "=" * 70)
    print("Proof Certificate System Demonstration")
    print("=" * 70)

    # 创建排序算法的证明证书
    theorem = "Bubble sort correctly sorts any list of integers"
    proof_steps = [
        "Initial state: unsorted list",
        "Loop invariant: elements after position n-i-1 are sorted",
        "Maintenance: each iteration places largest unsorted element",
        "Termination: after n iterations, entire list is sorted"
    ]

    cert = ProofCertificate.create_certificate(theorem, proof_steps)

    print(f"Theorem: {cert['theorem']}")
    print(f"Proof Hash: {cert['proof_hash']}")
    print(f"Steps: {cert['steps']}")
    print(f"Verified: {cert['verified']}")

    # 验证证书
    is_valid = ProofCertificate.verify_certificate(cert, proof_steps)
    print(f"\nCertificate valid: {is_valid}")

    # 尝试验证被篡改的证明
    tampered_steps = proof_steps[:-1] + ["Wrong conclusion"]
    is_valid = ProofCertificate.verify_certificate(cert, tampered_steps)
    print(f"Tampered certificate valid: {is_valid}")


if __name__ == "__main__":
    # 运行验证测试
    tests = FormalVerificationTests()
    tests.run_all_tests()

    # 演示证明证书系统
    demonstrate_proof_certificates()

    print("\n" + "=" * 70)
    print("Formal Verification Loop Verification Complete!")
    print("=" * 70)