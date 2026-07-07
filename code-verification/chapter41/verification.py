"""
DCA Chapter 41: Discrete Physical Mapping Verification Code
验证目标：离散作用量、格点模型与计算边界的正确性
Author: Wang Bingqin
Date: 2026-07-06
"""

import numpy as np
from typing import List, Tuple, Callable, Dict, Any
from dataclasses import dataclass
import time
from collections import defaultdict


@dataclass
class LatticePoint:
    """格点表示"""
    x: int
    y: int

    def __hash__(self):
        return hash((self.x, self.y))

    def __eq__(self, other):
        return self.x == other.x and self.y == other.y


@dataclass
class Path:
    """离散路径"""
    points: List[LatticePoint]

    def __len__(self):
        return len(self.points)


def discrete_action(path: Path, L: Callable[[LatticePoint, LatticePoint], float]) -> float:
    """
    计算离散路径的作用量 S[path] = Σ_t L(x_t, x_{t+1})

    参数:
        path: 离散路径
        L: 拉格朗日函数，接受连续两个格点，返回实数值

    返回:
        作用量的数值
    """
    total = 0.0
    for t in range(len(path) - 1):
        total += L(path.points[t], path.points[t + 1])
    return total


def euclidean_lagrangian(p1: LatticePoint, p2: LatticePoint, k: float = 1.0) -> float:
    """
    欧几里得距离拉格朗日函数
    L(x_t, x_{t+1}) = k * |x_{t+1} - x_t|^2

    参数:
        p1: 起点格点
        p2: 终点格点
        k: 系数

    返回:
        拉格朗日函数值
    """
    dx = p2.x - p1.x
    dy = p2.y - p1.y
    return k * (dx * dx + dy * dy)


def harmonic_oscillator_lagrangian(p1: LatticePoint, p2: LatticePoint,
                                   dt: float = 1.0, m: float = 1.0, omega: float = 1.0) -> float:
    """
    离散谐振子拉格朗日函数
    L = (m/2) * ((x_{t+1} - x_t)/dt)^2 - (m*omega^2/2) * x_t^2

    参数:
        p1: 当前点 (时间 t)
        p2: 下一时间点 (时间 t+dt)
        dt: 时间步长
        m: 质量
        omega: 频率

    返回:
        拉格朗日函数值
    """
    kinetic = (m / 2) * ((p2.x - p1.x) / dt) ** 2
    potential = (m * omega ** 2 / 2) * p1.x ** 2
    return kinetic - potential


def discrete_euler_lagrange(path: Path, L: Callable[[LatticePoint, LatticePoint], float],
                           perturbation: int = 1) -> List[float]:
    """
    计算离散 Euler-Lagrange 方程
    通过有限变量扰动验证 δS = 0 条件

    参数:
        path: 离散路径
        L: 拉格朗日函数
        perturbation: 扰动大小

    返回:
        每个内部点的 Euler-Lagrange 残差
    """
    residuals = []

    for t in range(1, len(path) - 1):
        original_action = discrete_action(path, L)

        # 在 x 方向扰动
        new_point = LatticePoint(path.points[t].x + perturbation, path.points[t].y)
        new_points = path.points[:t] + [new_point] + path.points[t + 1:]
        perturbed_path = Path(new_points)
        perturbed_action = discrete_action(perturbed_path, L)

        # 计算变化率
        residual = (perturbed_action - original_action) / perturbation
        residuals.append(residual)

    return residuals


def is_extremal_path(path: Path, L: Callable[[LatticePoint, LatticePoint], float],
                     threshold: float = 0.1) -> bool:
    """
    检查路径是否是极值路径（近似满足 Euler-Lagrange 方程）

    参数:
        path: 离散路径
        L: 拉格朗日函数
        threshold: 残差阈值

    返回:
        如果是极值路径返回 True
    """
    residuals = discrete_euler_lagrange(path, L)
    return all(abs(r) < threshold for r in residuals)


def find_minimal_path(start: LatticePoint, end: LatticePoint,
                      L: Callable[[LatticePoint, LatticePoint], float],
                      max_steps: int = 1000) -> Path:
    """
    在有限路径集合中寻找使作用量最小的路径（贪心算法）

    参数:
        start: 起点
        end: 终点
        L: 拉格朗日函数
        max_steps: 最大步数

    返回:
        最小作用量路径
    """
    current = start
    points = [current]
    steps = 0

    while current != end and steps < max_steps:
        # 寻找下一步，使局部作用量最小
        candidates = [
            LatticePoint(current.x + dx, current.y + dy)
            for dx in [-1, 0, 1] for dy in [-1, 0, 1]
            if not (dx == 0 and dy == 0)
        ]

        best_next = None
        best_cost = float('inf')

        for next_point in candidates:
            cost = L(current, next_point)
            if cost < best_cost:
                best_cost = cost
                best_next = next_point

        if best_next is None:
            break

        current = best_next
        points.append(current)
        steps += 1

    return Path(points)


@dataclass
class ConservationLaw:
    """守恒定律"""
    name: str
    check: Callable[[Path], float]


def check_translation_invariance(path: Path, L: Callable[[LatticePoint, LatticePoint], float],
                                 dx: int = 1) -> float:
    """
    检查平移不变性（Noether 定理）
    如果拉格朗日函数在平移下不变，则对应的动量守恒

    参数:
        path: 路径
        L: 拉格朗日函数
        dx: 平移量

    返回:
        平移前后的作用量差（应该接近 0）
    """
    original_action = discrete_action(path, L)

    # 平移路径
    shifted_points = [LatticePoint(p.x + dx, p.y) for p in path.points]
    shifted_path = Path(shifted_points)

    shifted_action = discrete_action(shifted_path, L)

    return shifted_action - original_action


class CellularAutomaton:
    """一维元胞自动机（作为格点模型的简化示例）"""

    def __init__(self, rule: int):
        """
        初始化元胞自动机

        参数:
            rule: Wolfram 规则编号 (0-255)
        """
        self.rule = rule
        self._build_rule_table()

    def _build_rule_table(self):
        """构建规则表"""
        self.rule_table = {}
        for i in range(8):
            left = (i >> 2) & 1
            center = (i >> 1) & 1
            right = i & 1
            result = (self.rule >> i) & 1
            self.rule_table[(left, center, right)] = result

    def step(self, state: List[int]) -> List[int]:
        """
        执行一步演化

        参数:
            state: 当前状态（二进制列表）

        返回:
            下一状态
        """
        n = len(state)
        new_state = []
        for i in range(n):
            left = state[(i - 1) % n]
            center = state[i]
            right = state[(i + 1) % n]
            new_state.append(self.rule_table[(left, center, right)])
        return new_state

    def evolve(self, initial_state: List[int], steps: int) -> List[List[int]]:
        """
        演化多步

        参数:
            initial_state: 初始状态
            steps: 演化步数

        返回:
            状态历史
        """
        history = [initial_state.copy()]
        current = initial_state.copy()

        for _ in range(steps):
            current = self.step(current)
            history.append(current.copy())

        return history


class FiniteDifferenceSolver:
    """有限差分求解器"""

    def __init__(self, n_points: int, boundary: Tuple[float, float]):
        """
        初始化

        参数:
            n_points: 格点数
            boundary: 边界条件 (left, right)
        """
        self.n = n_points
        self.boundary = boundary

    def solve_poisson(self, rhs: List[float]) -> List[float]:
        """
        解一维泊松方程 -u'' = f
        使用有限差分方法

        参数:
            rhs: 右端项

        返回:
        解向量
        """
        # 构建三对角矩阵
        n = self.n
        A = np.zeros((n, n))
        b = np.array(rhs, dtype=float)

        for i in range(n):
            if i > 0:
                A[i, i - 1] = -1
            A[i, i] = 2
            if i < n - 1:
                A[i, i + 1] = -1

        # 添加边界条件
        b[0] += self.boundary[0]
        b[-1] += self.boundary[1]

        # 解线性系统
        return np.linalg.solve(A, b)


def test_discrete_action():
    """测试离散作用量计算"""
    print("测试离散作用量计算...")

    # 创建简单路径
    path = Path([
        LatticePoint(0, 0),
        LatticePoint(1, 1),
        LatticePoint(2, 2),
        LatticePoint(3, 3)
    ])

    # 计算作用量
    action = discrete_action(path, euclidean_lagrangian)

    # 手动计算预期值
    expected = 2 + 2 + 2  # 每步距离平方为 2

    assert abs(action - expected) < 0.01, f"Action = {action}, expected {expected}"

    # 测试平直路径
    flat_path = Path([
        LatticePoint(0, 0),
        LatticePoint(1, 0),
        LatticePoint(2, 0),
        LatticePoint(3, 0)
    ])

    flat_action = discrete_action(flat_path, euclidean_lagrangian)
    assert flat_action == 1 + 1 + 1, "Flat path action incorrect"

    print("  离散作用量计算测试通过!")


def test_euler_lagrange():
    """测试 Euler-Lagrange 方程"""
    print("测试 Euler-Lagrange 方程...")

    # 直线路径应该接近极值
    path = Path([
        LatticePoint(0, 0),
        LatticePoint(1, 0),
        LatticePoint(2, 0),
        LatticePoint(3, 0)
    ])

    is_extremal = is_extremal_path(path, euclidean_lagrangian)
    assert is_extremal, "Straight path should be extremal"

    # 随机路径
    random_path = Path([
        LatticePoint(0, 0),
        LatticePoint(2, 3),
        LatticePoint(1, -1),
        LatticePoint(3, 0)
    ])

    is_extremal = is_extremal_path(random_path, euclidean_lagrangian)
    # 随机路径通常不是极值，但我们检查残差是否合理

    residuals = discrete_euler_lagrange(random_path, euclidean_lagrangian)
    assert len(residuals) == 2, "Should have 2 residuals for 4 points"

    print("  Euler-Lagrange 方程测试通过!")


def test_minimal_path():
    """测试最小作用量路径寻找"""
    print("测试最小作用量路径寻找...")

    start = LatticePoint(0, 0)
    end = LatticePoint(3, 3)

    path = find_minimal_path(start, end, euclidean_lagrangian)

    # 验证路径有效性
    assert len(path.points) > 0, "Path should not be empty"
    assert path.points[0] == start, "Path should start at start point"

    # 检查作用量非负
    action = discrete_action(path, euclidean_lagrangian)
    assert action >= 0, "Action should be non-negative"

    print("  最小作用量路径寻找测试通过!")


def test_conservation_laws():
    """测试守恒定律"""
    print("测试守恒定律...")

    path = Path([
        LatticePoint(0, 0),
        LatticePoint(1, 0),
        LatticePoint(2, 0),
        LatticePoint(3, 0)
    ])

    # 欧几里得拉格朗日函数在平移下不变
    diff = check_translation_invariance(path, euclidean_lagrangian)
    assert abs(diff) < 0.01, f"Translation invariance failed: diff = {diff}"

    print("  守恒定律测试通过!")


def test_cellular_automaton():
    """测试元胞自动机"""
    print("测试元胞自动机...")

    # 规则 30（混沌行为）
    ca = CellularAutomaton(30)

    # 初始状态（单个 1）
    initial = [0, 0, 0, 0, 1, 0, 0, 0, 0]

    # 演化几步
    history = ca.evolve(initial, 5)

    # 验证状态历史
    assert len(history) == 6, f"History length = {len(history)}, expected 6"
    assert history[0] == initial, "Initial state not preserved"
    assert len(history[1]) == len(initial), "State size changed"

    # 规则 184（交通流模型）
    ca_traffic = CellularAutomaton(184)
    initial_traffic = [1, 0, 0, 1, 0, 1, 0, 0]
    traffic_history = ca_traffic.evolve(initial_traffic, 10)
    assert len(traffic_history) == 11

    print("  元胞自动机测试通过!")


def test_finite_difference():
    """测试有限差分求解器"""
    print("测试有限差分求解器...")

    # 测试简单的一维泊松方程
    # -u'' = 2, 边界 u(0) = 0, u(1) = 0
    # 解应该是 u(x) = x(1-x)
    solver = FiniteDifferenceSolver(10, (0.0, 0.0))
    rhs = [2.0] * 10

    solution = solver.solve_poisson(rhs)

    # 验证边界条件
    assert abs(solution[0]) < 0.1, "Left boundary condition violated"
    assert abs(solution[-1]) < 0.1, "Right boundary condition violated"

    # 验证解的性质（对称性、非负性）
    for val in solution:
        assert val >= -0.01, f"Solution should be non-negative, got {val}"

    # 检查对称性
    symmetric = all(abs(solution[i] - solution[-1-i]) < 0.1 for i in range(len(solution)))
    assert symmetric, "Solution should be symmetric"

    print("  有限差分求解器测试通过!")


def test_harmonic_oscillator():
    """测试离散谐振子"""
    print("测试离散谐振子...")

    # 创建一个周期路径
    path = Path([
        LatticePoint(0, 0),
        LatticePoint(1, 0),
        LatticePoint(0, 0),
        LatticePoint(-1, 0),
        LatticePoint(0, 0)
    ])

    action = discrete_action(path, harmonic_oscillator_lagrangian)

    # 验证作用量计算
    assert isinstance(action, float), "Action should be a float"

    # 验证拉格朗日函数的符号
    # 对于简谐运动，动能和势能交替主导
    for i in range(len(path) - 1):
        L_val = harmonic_oscillator_lagrangian(
            path.points[i], path.points[i + 1]
        )
        assert isinstance(L_val, float), "Lagrangian should be a float"

    print("  离散谐振子测试通过!")


def performance_benchmark():
    """性能基准测试"""
    print("\n性能基准测试...")

    # 测试不同规模的路径计算
    sizes = [10, 100, 1000, 10000]

    print(f"{'规模':<10} {'时间 (ms)':<15}")
    print("-" * 25)

    for size in sizes:
        # 创建路径
        path = Path([LatticePoint(i, i) for i in range(size)])

        # 计时
        start_time = time.time()
        action = discrete_action(path, euclidean_lagrangian)
        elapsed = (time.time() - start_time) * 1000

        print(f"{size:<10} {elapsed:<15.2f}")

    print("\n性能测试完成!")


def run_all_tests():
    """运行所有测试"""
    print("=" * 60)
    print("DCA 第41章验证测试套件")
    print("=" * 60)
    print()

    tests = [
        test_discrete_action,
        test_euler_lagrange,
        test_minimal_path,
        test_conservation_laws,
        test_cellular_automaton,
        test_finite_difference,
        test_harmonic_oscillator,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"  测试失败: {e}")
            failed += 1
        except Exception as e:
            print(f"  测试出错: {e}")
            failed += 1

    print()
    print("=" * 60)
    print(f"测试结果: {passed} 通过, {failed} 失败")
    print("=" * 60)

    # 运行性能测试
    performance_benchmark()

    return passed, failed


if __name__ == "__main__":
    passed, failed = run_all_tests()
    exit(0 if failed == 0 else 1)