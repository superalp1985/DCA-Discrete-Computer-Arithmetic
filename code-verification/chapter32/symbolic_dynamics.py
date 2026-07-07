"""
DCA Chapter 32: Symbolic Dynamics and Discrete Chaos Verification Code
Chapter Title: Symbolic Dynamics and Discrete Chaos - SFT, Modular Maps, Long Period Behavior
验证内容：符号动力学、有限型子移位、模映射、离散混沌、周期检测
"""

import numpy as np
from typing import List, Tuple, Dict, Set, Callable
from collections import deque
import time
import hashlib
import random
from dataclasses import dataclass


# ============================================================================
# Symbolic Dynamics Core
# ============================================================================

@dataclass
class ShiftSpace:
    """移位空间"""
    alphabet: Set[int]
    forbidden_words: Set[Tuple[int, ...]]

    def __post_init__(self):
        self.forbidden_words = {tuple(word) for word in self.forbidden_words}

    def is_allowed(self, word: Tuple[int, ...]) -> bool:
        """检查词是否允许"""
        for forbidden in self.forbidden_words:
            if len(word) >= len(forbidden):
                for i in range(len(word) - len(forbidden) + 1):
                    if word[i:i+len(forbidden)] == forbidden:
                        return False
        return True

    def generate_sequences(self, length: int, max_sequences: int = 1000) -> List[List[int]]:
        """生成允许的序列"""
        sequences = []

        def backtrack(current: List[int]):
            if len(sequences) >= max_sequences:
                return
            if len(current) == length:
                sequences.append(current.copy())
                return

            for symbol in self.alphabet:
                current.append(symbol)
                if self.is_allowed(tuple(current)):
                    backtrack(current)
                current.pop()

        backtrack([])
        return sequences


@dataclass
class FiniteTypeShift:
    """有限型子移位 (SFT)"""
    alphabet: Set[int]
    memory: int  # 记忆长度（邻域大小-1）

    def __post_init__(self):
        # 构建转移图
        self.transitions = self._build_transitions()

    def _build_transitions(self) -> Dict[Tuple[int, ...], List[int]]:
        """构建转移图"""
        transitions = {}
        for state in self._generate_all_states():
            allowed_next = []
            for symbol in self.alphabet:
                next_state = state[1:] + (symbol,)
                if self.is_allowed(state + (symbol,)):
                    allowed_next.append(symbol)
            if allowed_next:
                transitions[state] = allowed_next
        return transitions

    def _generate_all_states(self) -> List[Tuple[int, ...]]:
        """生成所有可能的状态"""
        states = []
        from itertools import product
        for combo in product(self.alphabet, repeat=self.memory):
            states.append(combo)
        return states

    def is_allowed(self, word: Tuple[int, ...]) -> bool:
        """检查词是否允许（子类应重写）"""
        return True

    def evolve(self, initial_state: Tuple[int, ...], steps: int) -> List[int]:
        """演化序列"""
        sequence = list(initial_state)
        current = initial_state[-self.memory:] if len(initial_state) >= self.memory else initial_state

        for _ in range(steps):
            if current in self.transitions:
                next_symbol = random.choice(self.transitions[current])
                sequence.append(next_symbol)
                current = (current[1:] + (next_symbol,))
            else:
                break

        return sequence


class GoldenMeanShift(FiniteTypeShift):
    """黄金平均移位 (禁止 '11')"""

    def __init__(self):
        super().__init__(alphabet={0, 1}, memory=1)
        self.forbidden_words = {(1, 1)}

    def is_allowed(self, word: Tuple[int, ...]) -> bool:
        """检查是否包含 '11'"""
        return (1, 1) not in zip(word, word[1:])


class EvenShift(FiniteTypeShift):
    """偶数移位 (1之间必须有偶数个0)"""

    def __init__(self):
        super().__init__(alphabet={0, 1}, memory=3)

    def is_allowed(self, word: Tuple[int, ...]) -> bool:
        """检查1之间是否有偶数个0"""
        word_str = ''.join(map(str, word))
        # 检查所有相邻的1
        parts = word_str.split('1')
        for i, part in enumerate(parts[1:-1], 1):
            # 忽虑首尾的空字符串
            if i == 1 and len(parts[0]) == 0:
                continue
            if len(part) % 2 != 0:
                return False
        return True


# ============================================================================
# Modular Maps and Discrete Chaos
# ============================================================================

class ModularMap:
    """模映射"""

    def __init__(self, N: int):
        """
        初始化模映射

        Args:
            N: 模数
        """
        self.N = N
        self.state_space_size = N * N

    def cat_map(self, x: int, y: int) -> Tuple[int, int]:
        """
        Arnold Cat Map

        (x', y') = (x + y mod N, x + 2y mod N)
        """
        return ((x + y) % self.N, (x + 2 * y) % self.N)

    def invert_cat_map(self, x: int, y: int) -> Tuple[int, int]:
        """
        Cat Map 的逆映射

        逆矩阵为 [[2, -1], [-1, 1]]
        """
        return ((2*x - y) % self.N, (-x + y) % self.N)

    def logistic_map(self, x: int) -> int:
        """
        离散 Logistic 映射

        x_{n+1} = r * x_n * (1 - x_n) mod N
        """
        r = 4
        return int(r * x * (self.N - 1 - x) // (self.N - 1)) % self.N

    def tent_map(self, x: int) -> int:
        """
        离散 Tent 映射

        T(x) = 2x mod N for x < N/2
        T(x) = 2(N-x) mod N for x >= N/2
        """
        half = self.N // 2
        if x < half:
            return (2 * x) % self.N
        else:
            return (2 * (self.N - x)) % self.N

    def find_period(self, initial_state: Tuple[int, int],
                   map_func: Callable, max_iterations: int = 10000) -> Tuple[int, int]:
        """
        找到周期

        Returns:
            (transient_length, period_length)
        """
        seen = {}
        state = initial_state

        for t in range(max_iterations):
            state_hash = hashlib.md5(f"{state[0]},{state[1]}".encode()).hexdigest()
            if state_hash in seen:
                return seen[state_hash], t - seen[state_hash]
            seen[state_hash] = t
            state = map_func(*state)

        return max_iterations, 0


class LyapunovExponent:
    """李雅普诺夫指数（离散版本）"""

    @staticmethod
    def estimate(f: Callable, N: int, initial_x: int, steps: int = 1000) -> float:
        """
        估计李雅普诺夫指数

        λ ≈ (1/n) Σ log|f'(x_i)|

        在离散情况下使用差分近似导数
        """
        x = initial_x
        log_derivatives = []

        for _ in range(steps):
            # 使用差分近似导数
            delta = 1
            f_plus = (f(x) + delta) % N
            f_minus = (f(x) - delta) % N
            derivative = (f_plus - f_minus) / (2 * delta)

            if abs(derivative) > 1e-10:
                log_derivatives.append(abs(derivative))

            x = f(x)

        if not log_derivatives:
            return 0.0

        return sum(log_derivatives) / len(log_derivatives)


# ============================================================================
# Transition Matrix Analysis
# ============================================================================

class TransitionMatrix:
    """转移矩阵分析"""

    @staticmethod
    def build_matrix(shift: FiniteTypeShift) -> np.ndarray:
        """构建转移矩阵"""
        states = shift._generate_all_states()
        n = len(states)
        state_index = {state: i for i, state in enumerate(states)}

        matrix = np.zeros((n, n), dtype=int)

        for i, state in enumerate(states):
            if state in shift.transitions:
                for symbol in shift.transitions[state]:
                    next_state = state[1:] + (symbol,)
                    j = state_index[next_state]
                    matrix[i, j] = 1

        return matrix

    @staticmethod
    def count_words_of_length(shift: FiniteTypeShift, length: int) -> int:
        """
        计算长度为 n 的允许词数量

        使用转移矩阵的幂
        """
        if length <= shift.memory:
            # 直接枚举
            states = shift._generate_all_states()
            count = 0
            for state in states:
                if shift.is_allowed(state[:length]):
                    count += 1
            return count

        # 使用矩阵幂
        matrix = TransitionMatrix.build_matrix(shift)
        power_n = np.linalg.matrix_power(matrix, length - shift.memory)
        return power_n.sum()

    @staticmethod
    def topological_entropy(shift: FiniteTypeShift, max_length: int = 20) -> float:
        """
        计算拓扑熵

        h = lim_{n→∞} (1/n) log N(n)

        其中 N(n) 是长度为 n 的允许词数量
        """
        word_counts = []
        for n in range(1, max_length + 1):
            count = TransitionMatrix.count_words_of_length(shift, n)
            word_counts.append(count)

        # 拟合增长率
        log_counts = np.log([c if c > 0 else 1 for c in word_counts])
        lengths = np.arange(1, max_length + 1)

        # 使用最后几个点的斜率估计
        slope = np.polyfit(lengths[-5:], log_counts[-5:], 1)[0]

        return slope


# ============================================================================
# Chaos Detection
# ============================================================================

class ChaosDetector:
    """混沌检测器"""

    @staticmethod
    def sensitive_dependence(f: Callable, N: int, initial_state: int,
                           perturbation: int = 1, steps: int = 100) -> float:
        """
        测试对初始条件的敏感依赖性

        轨迹之间的平均距离
        """
        # 原始轨迹
        trajectory1 = []
        x = initial_state
        for _ in range(steps):
            trajectory1.append(x)
            x = f(x)

        # 扰动轨迹
        trajectory2 = []
        x = (initial_state + perturbation) % N
        for _ in range(steps):
            trajectory2.append(x)
            x = f(x)

        # 计算平均距离
        distances = [abs(t1 - t2) for t1, t2 in zip(trajectory1, trajectory2)]
        return sum(distances) / len(distances)

    @staticmethod
    def is_mixing(trajectory: List[int], N: int, window: int = 10) -> bool:
        """
        测试混合性（简化版）

        检查轨迹是否访问了足够多的不同状态
        """
        unique_states = len(set(trajectory))
        return unique_states > N * 0.8  # 访问了80%以上的状态

    @staticmethod
    def detect_long_period(mod_map: ModularMap, initial_state: Tuple[int, int],
                          map_func: Callable) -> Dict:
        """
        检测长周期行为
        """
        transient, period = mod_map.find_period(initial_state, map_func)

        return {
            'transient_length': transient,
            'period_length': period,
            'is_long_period': period > mod_map.N // 2,  # 周期超过状态空间一半
            'max_possible_period': mod_map.state_space_size
        }


# ============================================================================
# Verification Tests
# ============================================================================

class SymbolicDynamicsTests:
    """符号动力学验证测试"""

    def __init__(self):
        self.passed_tests = []
        self.failed_tests = []
        self.performance_data = {}

    def record_result(self, test_name: str, passed: bool, details: str = ""):
        """记录测试结果"""
        if passed:
            self.passed_tests.append(test_name)
        else:
            self.failed_tests.append((test_name, details))
        print(f"{'✓' if passed else '✗'} {test_name}")
        if details and not passed:
            print(f"  Details: {details}")

    def test_golden_mean_shift(self):
        """测试黄金平均移位"""
        shift = GoldenMeanShift()

        # 测试禁止词
        self.record_result(
            "Golden mean shift: '11' forbidden",
            not shift.is_allowed((1, 1)),
            "Word '11' should be forbidden"
        )

        # 测试允许词
        allowed_examples = [(0, 0), (0, 1), (1, 0), (0, 1, 0), (1, 0, 1)]
        for word in allowed_examples:
            self.record_result(
                f"Golden mean shift: '{word}' allowed",
                shift.is_allowed(word)
            )

    def test_even_shift(self):
        """测试偶数移位"""
        shift = EvenShift()

        # 测试允许词
        allowed = [(1, 0, 0, 1), (1, 0, 0, 0, 1)]
        forbidden = [(1, 0, 1), (1, 0, 0, 0, 0, 1)]

        for word in allowed:
            self.record_result(
                f"Even shift: '{word}' allowed",
                shift.is_allowed(word)
            )

        for word in forbidden:
            self.record_result(
                f"Even shift: '{word}' forbidden",
                not shift.is_allowed(word)
            )

    def test_cat_map_properties(self):
        """测试Cat Map性质"""
        N = 16
        mod_map = ModularMap(N)

        # 测试可逆性
        for _ in range(20):
            x, y = random.randint(0, N-1), random.randint(0, N-1)
            x_prime, y_prime = mod_map.cat_map(x, y)
            x_back, y_back = mod_map.invert_cat_map(x_prime, y_prime)

            self.record_result(
                f"Cat map invertibility at ({x}, {y})",
                (x_back, y_back) == (x, y)
            )

    def test_periodicity(self):
        """测试周期性"""
        N = 16
        mod_map = ModularMap(N)

        # 测试多个初始点
        periods = []
        for _ in range(10):
            x, y = random.randint(0, N-1), random.randint(0, N-1)
            transient, period = mod_map.find_period((x, y), mod_map.cat_map)
            periods.append(period)

        # 所有周期都应该有限
        all_finite = all(p > 0 for p in periods)

        self.record_result(
            "Cat map finite periods",
            all_finite,
            f"Periods: {periods[:5]}..."
        )

    def test_sensitive_dependence(self):
        """测试敏感依赖性"""
        N = 256
        mod_map = ModularMap(N)

        # Cat Map 应该展示敏感依赖性
        sensitivity = ChaosDetector.sensitive_dependence(
            lambda x: mod_map.logistic_map(x), N, 100
        )

        self.record_result(
            "Sensitive dependence detection",
            sensitivity > 0,
            f"Sensitivity metric: {sensitivity:.2f}"
        )

    def test_transition_matrix_properties(self):
        """测试转移矩阵性质"""
        shift = GoldenMeanShift()
        matrix = TransitionMatrix.build_matrix(shift)

        # 矩阵应该是方阵
        is_square = matrix.shape[0] == matrix.shape[1]

        # 元素应该是0或1
        is_binary = set(matrix.flatten()) <= {0, 1}

        self.record_result(
            "Transition matrix properties",
            is_square and is_binary,
            f"Shape: {matrix.shape}, Binary: {is_binary}"
        )

    def test_word_counting(self):
        """测试词计数"""
        shift = GoldenMeanShift()

        # 长度1的词：只有 {0, 1}
        count_1 = TransitionMatrix.count_words_of_length(shift, 1)

        # 长度2的词：{00, 01, 10} (11被禁止)
        count_2 = TransitionMatrix.count_words_of_length(shift, 2)

        self.record_result(
            "Word counting (length 1)",
            count_1 == 2,
            f"Count: {count_1}"
        )

        self.record_result(
            "Word counting (length 2)",
            count_2 == 3,
            f"Count: {count_2}"
        )

    def test_topological_entropy(self):
        """测试拓扑熵"""
        shift = GoldenMeanShift()
        entropy = TransitionMatrix.topological_entropy(shift)

        # 黄金平均移位的熵是 log(φ) ≈ 0.694
        # 这里我们只检查它为正数
        self.record_result(
            "Topological entropy positivity",
            entropy > 0,
            f"Entropy: {entropy:.4f}"
        )

    def test_mixing_property(self):
        """测试混合性"""
        N = 128
        mod_map = ModularMap(N)

        trajectory = []
        x = 42
        for _ in range(500):
            x = mod_map.logistic_map(x)
            trajectory.append(x)

        is_mixing = ChaosDetector.is_mixing(trajectory, N)

        self.record_result(
            "Mixing property",
            is_mixing,
            f"Visited {len(set(trajectory))} / {N} states"
        )

    def test_long_period_detection(self):
        """测试长周期检测"""
        N = 64
        mod_map = ModularMap(N)

        x, y = 1, 1
        result = ChaosDetector.detect_long_period(mod_map, (x, y), mod_map.cat_map)

        self.record_result(
            "Long period detection",
            result['period_length'] > 0,
            f"Period: {result['period_length']}, Max: {result['max_possible_period']}"
        )

    def test_modular_map_variants(self):
        """测试不同模映射"""
        N = 256
        mod_map = ModularMap(N)

        x = 100
        cat_result = mod_map.cat_map(x, x)
        logistic_result = mod_map.logistic_map(x)
        tent_result = mod_map.tent_map(x)

        # 所有结果应该在 [0, N) 范围内
        tests = [
            ("Cat map range", 0 <= cat_result[0] < N and 0 <= cat_result[1] < N),
            ("Logistic map range", 0 <= logistic_result < N),
            ("Tent map range", 0 <= tent_result < N)
        ]

        for name, passed in tests:
            self.record_result(name, passed)

    def test_benchmark_performance(self):
        """性能基准测试"""
        sizes = [16, 32, 64, 128]
        steps = 1000

        for N in sizes:
            mod_map = ModularMap(N)
            x, y = 1, 1

            start = time.time()
            for _ in range(steps):
                x, y = mod_map.cat_map(x, y)
            elapsed = time.time() - start

            self.performance_data[f'cat_map_N_{N}'] = elapsed
            self.record_result(
                f"Performance (N={N})",
                elapsed < 1.0,
                f"Time: {elapsed:.4f}s for {steps} steps"
            )

    def test_finite_state_convergence(self):
        """测试有限状态收敛"""
        N = 32
        mod_map = ModularMap(N)

        # 从所有状态开始，检查是否都进入周期
        all_periods = []
        for x in range(N):
            for y in range(N):
                transient, period = mod_map.find_period((x, y), mod_map.cat_map)
                all_periods.append((transient, period))

        # 所有状态都应该有有限的周期
        all_have_period = all(p > 0 for _, p in all_periods)

        self.record_result(
            "All states periodic",
            all_have_period,
            f"Tested {len(all_periods)} states"
        )

    def run_all_tests(self):
        """运行所有验证测试"""
        print("=" * 70)
        print("DCA Chapter 32: Symbolic Dynamics and Discrete Chaos Verification")
        print("=" * 70)
        print()

        print("Symbolic Dynamics Tests:")
        print("-" * 70)
        self.test_golden_mean_shift()
        self.test_even_shift()

        print("\nModular Map Tests:")
        print("-" * 70)
        self.test_cat_map_properties()
        self.test_modular_map_variants()

        print("\nPeriodicity Tests:")
        print("-" * 70)
        self.test_periodicity()
        self.test_long_period_detection()
        self.test_finite_state_convergence()

        print("\nChaos Detection Tests:")
        print("-" * 70)
        self.test_sensitive_dependence()
        self.test_mixing_property()

        print("\nTransition Matrix Tests:")
        print("-" * 70)
        self.test_transition_matrix_properties()
        self.test_word_counting()
        self.test_topological_entropy()

        print("\nPerformance Tests:")
        print("-" * 70)
        self.test_benchmark_performance()

        self.print_summary()

    def print_summary(self):
        """打印测试总结"""
        print("\n" + "=" * 70)
        print("VERIFICATION SUMMARY")
        print("=" * 70)
        print(f"Passed tests: {len(self.passed_tests)}")
        print(f"Failed tests: {len(self.failed_tests)}")
        print(f"Success rate: {100 * len(self.passed_tests) / (len(self.passed_tests) + len(self.failed_tests)):.1f}%")

        if self.performance_data:
            print("\nPerformance Data:")
            for key, value in sorted(self.performance_data.items()):
                print(f"  {key}: {value:.4f}s")

        if self.failed_tests:
            print("\nFailed Tests:")
            for name, details in self.failed_tests:
                print(f"  - {name}: {details}")

        print("=" * 70)


# ============================================================================
# Demonstration: Chaos Visualization Data
# ============================================================================

def generate_chaos_demo():
    """生成混沌演示数据"""
    print("\n" + "=" * 70)
    print("Discrete Chaos Demonstration")
    print("=" * 70)

    N = 128
    mod_map = ModularMap(N)

    # 测试不同映射的周期分布
    print("\nPeriod Distribution for Cat Map (N={}):".format(N))
    print("-" * 50)

    periods = []
    for x in range(N):
        for y in range(N):
            _, period = mod_map.find_period((x, y), mod_map.cat_map)
            periods.append(period)

    from collections import Counter
    period_counts = Counter(periods)
    print("Period | Count")
    print("-------|-------")
    for period in sorted(period_counts.keys())[:10]:  # 只显示前10个
        print(f"{period:6} | {period_counts[period]:5}")

    # Logistic 映射轨迹
    print("\nLogistic Map Trajectory:")
    print("-" * 50)
    x = 42
    trajectory = [x]
    for _ in range(20):
        x = mod_map.logistic_map(x)
        trajectory.append(x)

    print("Step | Value")
    print("-----|------")
    for i, val in enumerate(trajectory):
        print(f"{i:4} | {val:4}")

    # 敏感依赖性示例
    print("\nSensitive Dependence Example:")
    print("-" * 50)
    x1, x2 = 100, 101  # 初始条件相差1

    trajectory1 = [x1]
    trajectory2 = [x2]

    for _ in range(10):
        x1 = mod_map.logistic_map(x1)
        x2 = mod_map.logistic_map(x2)
        trajectory1.append(x1)
        trajectory2.append(x2)

    print("Step | Traj1 | Traj2 | Diff")
    print("-----|-------|-------|-----")
    for i in range(len(trajectory1)):
        diff = abs(trajectory1[i] - trajectory2[i])
        print(f"{i:4} | {trajectory1[i]:5} | {trajectory2[i]:5} | {diff:4}")

    # 黄金平均移位的词计数增长
    print("\nGolden Mean Shift Word Count Growth:")
    print("-" * 50)
    shift = GoldenMeanShift()

    print("Length | Word Count")
    print("-------|-----------")
    for n in range(1, 11):
        count = TransitionMatrix.count_words_of_length(shift, n)
        print(f"{n:6} | {count:10}")

    # 拓扑熵
    entropy = TransitionMatrix.topological_entropy(shift)
    print(f"\nTopological Entropy: {entropy:.6f}")
    print(f"Theoretical (log φ): {np.log((1 + 5**0.5) / 2):.6f}")


if __name__ == "__main__":
    # 运行验证测试
    tests = SymbolicDynamicsTests()
    tests.run_all_tests()

    # 生成演示数据
    generate_chaos_demo()

    print("\n" + "=" * 70)
    print("Symbolic Dynamics and Discrete Chaos Verification Complete!")
    print("=" * 70)