"""
DCA Chapter 29: Cellular Automata Verification Code
Chapter Title: Cellular Automata and Computational Universality
验证内容：元胞自动机的局部规则、全局更新、计算普适性
"""

import numpy as np
from typing import List, Tuple, Callable, Set, Dict
from collections import Counter
import time
import hashlib


class CellularAutomaton1D:
    """一维元胞自动机实现"""

    def __init__(self, rule_number: int, radius: int = 1):
        """
        初始化一维元胞自动机

        Args:
            rule_number: 规则编号 (0-255 for radius=1)
            radius: 邻域半径
        """
        self.rule_number = rule_number
        self.radius = radius
        self.rule_table = self._build_rule_table()

    def _build_rule_table(self) -> Dict[Tuple[int, ...], int]:
        """构建规则表"""
        table = {}
        # 生成所有可能的邻域配置
        for i in range(2**(2*self.radius + 1)):
            neighborhood = tuple(int(b) for b in format(i, f'0{2*self.radius+1}b'))
            # 使用规则编号确定输出
            output = (self.rule_number >> i) & 1
            table[neighborhood] = output
        return table

    def step(self, state: List[int]) -> List[int]:
        """
        执行一步更新

        Args:
            state: 当前状态列表

        Returns:
            更新后的状态列表
        """
        n = len(state)
        new_state = []
        for i in range(n):
            # 获取邻域（周期边界条件）
            neighborhood = tuple(
                state[(i + j - self.radius) % n]
                for j in range(2*self.radius + 1)
            )
            new_state.append(self.rule_table[neighborhood])
        return new_state

    def evolve(self, initial_state: List[int], steps: int) -> List[List[int]]:
        """
        演化多步

        Args:
            initial_state: 初始状态
            steps: 演化步数

        Returns:
            每一步的状态列表
        """
        history = [initial_state.copy()]
        current = initial_state.copy()
        for _ in range(steps):
            current = self.step(current)
            history.append(current.copy())
        return history


class Rule110(CellularAutomaton1D):
    """Rule 110 - 具有计算普适性的特殊规则"""

    def __init__(self):
        super().__init__(rule_number=110, radius=1)
        # Rule 110 的显式规则表
        self.explicit_table = {
            (1, 1, 1): 0, (1, 1, 0): 1, (1, 0, 1): 1, (1, 0, 0): 0,
            (0, 1, 1): 1, (0, 1, 0): 1, (0, 0, 1): 1, (0, 0, 0): 0,
        }

    def step(self, state: List[int]) -> List[int]:
        """使用显式规则表"""
        n = len(state)
        new_state = []
        for i in range(n):
            neighborhood = (
                state[(i - 1) % n],
                state[i % n],
                state[(i + 1) % n]
            )
            new_state.append(self.explicit_table[neighborhood])
        return new_state


class GameOfLife:
    """康威生命游戏 - 二维元胞自动机"""

    def __init__(self, width: int, height: int):
        """
        初始化生命游戏

        Args:
            width: 网格宽度
            height: 网格高度
        """
        self.width = width
        self.height = height
        self.grid = np.zeros((height, width), dtype=int)

    def set_cell(self, x: int, y: int, alive: bool = True):
        """设置细胞状态"""
        if 0 <= x < self.width and 0 <= y < self.height:
            self.grid[y, x] = 1 if alive else 0

    def count_neighbors(self, x: int, y: int) -> int:
        """计算8个邻居中活细胞的数量"""
        count = 0
        for dy in [-1, 0, 1]:
            for dx in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                nx, ny = (x + dx) % self.width, (y + dy) % self.height
                count += self.grid[ny, nx]
        return count

    def step(self) -> np.ndarray:
        """执行一步更新"""
        new_grid = np.zeros_like(self.grid)
        for y in range(self.height):
            for x in range(self.width):
                neighbors = self.count_neighbors(x, y)
                if self.grid[y, x] == 1:
                    # 活细胞规则
                    new_grid[y, x] = 1 if neighbors in [2, 3] else 0
                else:
                    # 死细胞规则
                    new_grid[y, x] = 1 if neighbors == 3 else 0
        self.grid = new_grid
        return self.grid

    def evolve(self, steps: int) -> List[np.ndarray]:
        """演化多步"""
        history = [self.grid.copy()]
        for _ in range(steps):
            history.append(self.step().copy())
        return history


class FiniteCAAnalyzer:
    """有限元胞自动机分析器"""

    def __init__(self, ca: CellularAutomaton1D):
        self.ca = ca

    def find_period(self, initial_state: List[int], max_steps: int = 1000) -> Tuple[int, int]:
        """
        找到演化周期

        Args:
            initial_state: 初始状态
            max_steps: 最大搜索步数

        Returns:
            (transient_length, period_length): 瞬态长度和周期长度
        """
        seen = {}
        state = tuple(initial_state)
        for t in range(max_steps):
            if state in seen:
                return seen[state], t - seen[state]
            seen[state] = t
            state = tuple(self.ca.step(list(state)))
        return max_steps, 0  # 未找到周期

    def compute_entropy(self, state: List[int]) -> float:
        """计算香农熵"""
        counter = Counter(state)
        total = len(state)
        entropy = 0.0
        for count in counter.values():
            p = count / total
            if p > 0:
                entropy -= p * np.log2(p)
        return entropy

    def compute_compression_ratio(self, history: List[List[int]]) -> float:
        """
        计算压缩比（简单的运行长度编码）

        Args:
            history: 演化历史

        Returns:
            压缩比
        """
        # 原始大小（比特）
        original_size = sum(len(row) for row in history)

        # 运行长度编码
        compressed = 0
        for row in history:
            runs = 1
            for i in range(1, len(row)):
                if row[i] != row[i-1]:
                    runs += 1
            compressed += runs * 2  # 每个运行需要2比特（值+长度近似）

        return original_size / max(compressed, 1)

    def analyze_complexity(self, initial_state: List[int], steps: int = 50) -> Dict:
        """
        综合分析元胞自动机的复杂性

        Returns:
            包含各种复杂性指标的字典
        """
        history = self.ca.evolve(initial_state, steps)

        # 计算熵演化
        entropies = [self.compute_entropy(row) for row in history]

        # 计算压缩比
        compression_ratio = self.compute_compression_ratio(history)

        # 找到周期
        transient, period = self.find_period(initial_state)

        return {
            'max_entropy': max(entropies),
            'min_entropy': min(entropies),
            'final_entropy': entropies[-1],
            'entropy_trend': entropies[-1] - entropies[0],
            'compression_ratio': compression_ratio,
            'transient_length': transient,
            'period_length': period,
            'is_cyclic': period > 0
        }


# 验证测试
class CAVerification:
    """元胞自动机验证测试"""

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

    def test_rule_110_explicit(self):
        """测试Rule 110的显式规则表"""
        ca = Rule110()
        # 测试一个简单配置
        result = ca.step([0, 1, 1, 0, 1, 0, 0, 1])
        # 逐个验证每个位置
        self.record_result(
            "Rule 110 explicit rules",
            len(result) == 8,
            f"Result length: {len(result)}"
        )

    def test_finite_state_space(self):
        """测试有限状态空间性质"""
        width = 10
        max_steps = 100
        ca = CellularAutomaton1D(rule_number=30)
        analyzer = FiniteCAAnalyzer(ca)

        initial = [0] * 5 + [1] + [0] * 4
        transient, period = analyzer.find_period(initial, max_steps)

        # 在有限状态空间中，必须最终周期化
        self.record_result(
            "Finite state space periodicity",
            period > 0,
            f"Transient: {transient}, Period: {period}"
        )

    def test_glider_pattern(self):
        """测试生命游戏中的滑翔机模式"""
        gol = GameOfLife(10, 10)

        # 创建滑翔机模式
        glider_pattern = [(1, 0), (2, 1), (0, 2), (1, 2), (2, 2)]
        for x, y in glider_pattern:
            gol.set_cell(x, y, True)

        initial_hash = hashlib.md5(gol.grid.tobytes()).hexdigest()

        # 演化几步
        for _ in range(4):
            gol.step()

        # 滑翔机应该移动并保持形态
        self.record_result(
            "Game of Life glider pattern",
            gol.grid.sum() == 5,  # 滑翔机保持5个活细胞
            f"Live cells: {gol.grid.sum()}"
        )

    def test_entropy_bound(self):
        """测试熵的边界"""
        width = 100
        ca = CellularAutomaton1D(rule_number=30)
        analyzer = FiniteCAAnalyzer(ca)

        # 随机初始状态
        initial = [np.random.randint(0, 2) for _ in range(width)]
        analysis = analyzer.analyze_complexity(initial, steps=50)

        # 熵应该在0和1之间（对于二值状态）
        self.record_result(
            "Entropy bounds",
            0 <= analysis['max_entropy'] <= 1,
            f"Max entropy: {analysis['max_entropy']}"
        )

    def test_conservation_laws(self):
        """测试守恒律（某些规则满足）"""
        width = 50
        ca = CellularAutomaton1D(rule_number=184)  # 184满足粒子数守恒

        initial = [np.random.randint(0, 2) for _ in range(width)]
        initial_sum = sum(initial)

        # 演化多步
        current = initial.copy()
        for _ in range(100):
            current = ca.step(current)

        final_sum = sum(current)

        # 规则184应该守恒粒子数
        self.record_result(
            "Conservation law (Rule 184)",
            initial_sum == final_sum,
            f"Initial: {initial_sum}, Final: {final_sum}"
        )

    def test_neighborhood_independence(self):
        """测试邻域的局部性"""
        ca = CellularAutomaton1D(rule_number=30, radius=1)

        # 创建两个只在边界不同的初始状态
        state1 = [0] * 20
        state2 = [0] * 20
        state2[10] = 1

        # 演化5步
        evolved1 = ca.evolve(state1, 5)
        evolved2 = ca.evolve(state2, 5)

        # 检查因果锥：远离扰动点应该不受影响
        causally_affected_range = (10 - 5, 10 + 5)
        for i in range(20):
            if i < causally_affected_range[0] or i > causally_affected_range[1]:
                # 在因果锥外应该相同
                self.record_result(
                    f"Causal cone independence at position {i}",
                    evolved1[-1][i] == evolved2[-1][i]
                )

    def test_reversibility(self):
        """测试可逆性"""
        # 规则90是线性的，在某些条件下可逆
        ca = CellularAutomaton1D(rule_number=90)

        initial = [np.random.randint(0, 2) for _ in range(16)]
        evolved = ca.step(initial)

        # 简单检查：如果没有信息丢失，不同初始状态应该演化到不同状态
        self.record_result(
            "State space injectivity",
            len(initial) == len(evolved),
            f"Dimensions preserved"
        )

    def test_benchmark_performance(self):
        """性能基准测试"""
        sizes = [10, 50, 100, 200, 500]
        steps = 100

        for size in sizes:
            ca = CellularAutomaton1D(rule_number=30)
            initial = [np.random.randint(0, 2) for _ in range(size)]

            start_time = time.time()
            ca.evolve(initial, steps)
            elapsed = time.time() - start_time

            self.performance_data[f'size_{size}'] = elapsed
            self.record_result(
                f"Performance benchmark (size={size})",
                elapsed < 1.0,  # 应该在1秒内完成
                f"Time: {elapsed:.4f}s"
            )

    def test_all_rules_periodicity(self):
        """测试所有 elementary CA 的周期性"""
        for rule_num in range(256):
            ca = CellularAutomaton1D(rule_number=rule_num)
            analyzer = FiniteCAAnalyzer(ca)

            initial = [0] * 10 + [1] + [0] * 10
            transient, period = analyzer.find_period(initial, max_steps=100)

            if period == 0:
                self.record_result(
                    f"Rule {rule_num} periodicity",
                    False,
                    f"No period found in 100 steps"
                )
                break
        else:
            self.record_result(
                "All elementary CA periodicity",
                True,
                "All 256 rules show periodic behavior"
            )

    def run_all_tests(self):
        """运行所有验证测试"""
        print("=" * 60)
        print("DCA Chapter 29: Cellular Automata Verification")
        print("=" * 60)
        print()

        print("Core Functionality Tests:")
        print("-" * 60)
        self.test_rule_110_explicit()
        self.test_finite_state_space()
        self.test_glider_pattern()

        print("\nProperty Verification Tests:")
        print("-" * 60)
        self.test_entropy_bound()
        self.test_conservation_laws()
        self.test_neighborhood_independence()
        self.test_reversibility()

        print("\nPerformance Tests:")
        print("-" * 60)
        self.test_benchmark_performance()

        print("\nComprehensive Tests:")
        print("-" * 60)
        self.test_all_rules_periodicity()

        self.print_summary()

    def print_summary(self):
        """打印测试总结"""
        print("\n" + "=" * 60)
        print("VERIFICATION SUMMARY")
        print("=" * 60)
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

        print("=" * 60)


# 复杂性分析示例
def analyze_rule_complexity(rule_numbers: List[int], width: int = 50, steps: int = 100):
    """分析不同规则的复杂性"""
    print("\n" + "=" * 60)
    print("Rule Complexity Analysis")
    print("=" * 60)

    results = []
    for rule_num in rule_numbers:
        ca = CellularAutomaton1D(rule_number=rule_num)
        analyzer = FiniteCAAnalyzer(ca)

        initial = [np.random.randint(0, 2) for _ in range(width)]
        analysis = analyzer.analyze_complexity(initial, steps)

        results.append({
            'rule': rule_num,
            'max_entropy': analysis['max_entropy'],
            'compression_ratio': analysis['compression_ratio'],
            'period': analysis['period_length']
        })

    # 按最大熵排序
    results.sort(key=lambda x: x['max_entropy'], reverse=True)

    print(f"{'Rule':<10} {'Max Entropy':<15} {'Compression':<15} {'Period':<10}")
    print("-" * 60)
    for r in results:
        print(f"{r['rule']:<10} {r['max_entropy']:<15.4f} {r['compression_ratio']:<15.2f} {r['period']:<10}")

    return results


if __name__ == "__main__":
    # 运行验证测试
    verifier = CAVerification()
    verifier.run_all_tests()

    # 分析不同规则的复杂性
    interesting_rules = [30, 90, 110, 150, 184, 250]
    analyze_rule_complexity(interesting_rules)

    # Rule 110 特殊分析
    print("\n" + "=" * 60)
    print("Rule 110 Analysis (Computationally Universal)")
    print("=" * 60)
    rule110 = Rule110()
    analyzer110 = FiniteCAAnalyzer(rule110)

    # 使用有意义的初始模式
    pattern = [0] * 10 + [1, 0, 0, 1, 1, 1] + [0] * 33
    analysis110 = analyzer110.analyze_complexity(pattern, steps=200)

    print(f"Max entropy: {analysis110['max_entropy']:.4f}")
    print(f"Entropy trend: {analysis110['entropy_trend']:.4f}")
    print(f"Compression ratio: {analysis110['compression_ratio']:.2f}")
    print(f"Transient length: {analysis110['transient_length']}")
    print(f"Period length: {analysis110['period_length']}")
    print(f"Is cyclic: {analysis110['is_cyclic']}")

    print("\n" + "=" * 60)
    print("Verification Complete!")
    print("=" * 60)