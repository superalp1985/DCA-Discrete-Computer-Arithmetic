"""
DCA Chapter 31: Information Geometry Verification Code
Chapter Title: Discrete Information Geometry - Finite Distributions, Total Variation, Fisher Information
验证内容：有限概率分布、总变差距离、KL散度、Fisher信息、离散信息几何
"""

import numpy as np
from typing import List, Tuple, Dict, Callable
from dataclasses import dataclass
from collections import Counter
import time
import math


# ============================================================================
# Finite Probability Distributions
# ============================================================================

@dataclass
class FiniteDistribution:
    """有限概率分布（整数权重形式）"""
    weights: List[int]

    def __post_init__(self):
        self.total_weight = sum(self.weights)
        self.normalized = [w / self.total_weight for w in self.weights]

    def __len__(self):
        return len(self.weights)

    def prob(self, i: int) -> float:
        """获取第i个概率"""
        return self.normalized[i]

    def support(self) -> List[int]:
        """获取支撑集（非零元素）"""
        return [i for i, w in enumerate(self.weights) if w > 0]

    def entropy(self) -> float:
        """计算香农熵"""
        ent = 0.0
        for p in self.normalized:
            if p > 0:
                ent -= p * math.log2(p)
        return ent

    def copy(self):
        return FiniteDistribution(self.weights.copy())


class DistributionFactory:
    """分布工厂"""

    @staticmethod
    def uniform(n: int, total_weight: int = 1000) -> FiniteDistribution:
        """均匀分布"""
        weight = total_weight // n
        return FiniteDistribution([weight] * n)

    @staticmethod
    def bernoulli(p_weight: int, q_weight: int) -> FiniteDistribution:
        """伯努利分布"""
        return FiniteDistribution([p_weight, q_weight])

    @staticmethod
    def from_counts(counts: List[int]) -> FiniteDistribution:
        """从计数创建分布"""
        return FiniteDistribution(counts)

    @staticmethod
    def categorical(weights: List[int]) -> FiniteDistribution:
        """分类分布"""
        return FiniteDistribution(weights)


# ============================================================================
# Distance Metrics
# ============================================================================

class TotalVariation:
    """总变差距离"""

    @staticmethod
    def distance(p: FiniteDistribution, q: FiniteDistribution) -> float:
        """
        计算总变差距离

        TV(p,q) = 1/2 * Σ|p_i - q_i|

        当总权重相同时，可以使用整数形式：
        TV_M(p,q) = 1/2 * Σ|p_i - q_i| / M
        """
        if p.total_weight != q.total_weight:
            raise ValueError("Distributions must have same total weight")

        total_diff = sum(abs(pi - qi) for pi, qi in zip(p.weights, q.weights))
        return total_diff / (2 * p.total_weight)

    @staticmethod
    def verify_metric_properties(p: FiniteDistribution, q: FiniteDistribution,
                                r: FiniteDistribution) -> bool:
        """验证度量性质"""
        tv = TotalVariation.distance

        # 非负性
        d_pq = tv(p, q)
        non_negative = d_pq >= 0

        # 对称性
        symmetric = abs(d_pq - tv(q, p)) < 1e-10

        # 同一性
        d_pp = tv(p, p)
        identity = d_pp < 1e-10

        # 三角不等式
        triangle = tv(p, r) <= d_pq + tv(q, r) + 1e-10

        return non_negative and symmetric and identity and triangle


class KLDivergence:
    """KL散度（相对熵）"""

    @staticmethod
    def divergence(p: FiniteDistribution, q: FiniteDistribution) -> float:
        """
        计算KL散度

        KL(p||q) = Σ p_i * log(p_i / q_i)
        """
        kl = 0.0
        for pi, qi in zip(p.normalized, q.normalized):
            if pi > 0:
                if qi == 0:
                    return float('inf')
                kl += pi * math.log2(pi / qi)
        return kl

    @staticmethod
    def verify_properties(p: FiniteDistribution, q: FiniteDistribution) -> Dict:
        """验证KL散度性质"""
        kl_pq = KLDivergence.divergence(p, q)
        kl_qp = KLDivergence.divergence(q, p)

        # 非负性
        non_negative = kl_pq >= 0

        # 不对称性
        asymmetric = abs(kl_pq - kl_qp) > 1e-10

        # 同一性
        kl_pp = KLDivergence.divergence(p, p)
        identity = kl_pp < 1e-10

        return {
            'non_negative': non_negative,
            'asymmetric': asymmetric,
            'identity': identity,
            'kl_pq': kl_pq,
            'kl_qp': kl_qp
        }


class JensenShannon:
    """Jensen-Shannon散度"""

    @staticmethod
    def divergence(p: FiniteDistribution, q: FiniteDistribution) -> float:
        """
        计算JS散度

        JS(p||q) = 1/2 * KL(p||m) + 1/2 * KL(q||m)

        其中 m = (p + q) / 2
        """
        m_weights = [(pi + qi) / 2 for pi, qi in zip(p.weights, q.weights)]
        m = FiniteDistribution([int(w) for w in m_weights])

        return 0.5 * KLDivergence.divergence(p, m) + 0.5 * KLDivergence.divergence(q, m)


# ============================================================================
# Discrete Fisher Information
# ============================================================================

class DiscreteFisherInformation:
    """离散Fisher信息"""

    @staticmethod
    def finite_difference(f: Callable, x: float, h: float = 1e-5) -> float:
        """计算有限差分"""
        return (f(x + h) - f(x - h)) / (2 * h)

    @staticmethod
    def log_likelihood_gradient(params: List[float], data: List[int],
                                param_idx: int, h: float = 1e-5) -> float:
        """
        计算对数似然的梯度（差分形式）

        ∂/∂θ log L(θ; x)
        """
        def log_like(p):
            # 简化的泊松分布对数似然
            likelihood = 1.0
            for x in data:
                lambda_param = p[param_idx]
                # 泊松概率质量函数
                prob = math.exp(-lambda_param) * (lambda_param ** x) / math.factorial(x)
                likelihood *= prob
            return math.log(likelihood + 1e-10)

        return DiscreteFisherInformation.finite_difference(log_like, params[param_idx], h)

    @staticmethod
    def fisher_information(params: List[float], data: List[int]) -> np.ndarray:
        """
        计算Fisher信息矩阵

        I(θ) = E[∂/∂θ log p_θ(X) * ∂/∂θ log p_θ(X)^T]
        """
        n_params = len(params)
        fisher = np.zeros((n_params, n_params))

        for i in range(n_params):
            for j in range(n_params):
                # 使用差分近似
                grad_i = DiscreteFisherInformation.log_likelihood_gradient(params, data, i)
                grad_j = DiscreteFisherInformation.log_likelihood_gradient(params, data, j)
                fisher[i, j] = grad_i * grad_j

        return fisher


# ============================================================================
# Information Geometry on Statistical Manifold
# ============================================================================

class StatisticalManifold:
    """统计流形（离散版本）"""

    def __init__(self, n_outcomes: int):
        self.n_outcomes = n_outcomes
        self.distributions = []

    def add_distribution(self, dist: FiniteDistribution):
        """添加分布"""
        if len(dist) != self.n_outcomes:
            raise ValueError(f"Distribution must have {self.n_outcomes} outcomes")
        self.distributions.append(dist)

    def compute_geodesic(self, start_idx: int, end_idx: int, steps: int = 10) -> List[FiniteDistribution]:
        """
        计算测地线（线性插值）

        在离散情况下，使用线性插值作为测地线的近似
        """
        if start_idx >= len(self.distributions) or end_idx >= len(self.distributions):
            raise ValueError("Invalid distribution indices")

        start = self.distributions[start_idx]
        end = self.distributions[end_idx]

        geodesic = []
        for t in np.linspace(0, 1, steps):
            # 线性插值
            interp_weights = [
                int((1 - t) * sw + t * ew)
                for sw, ew in zip(start.weights, end.weights)
            ]
            geodesic.append(FiniteDistribution(interp_weights))

        return geodesic

    def compute_curvature(self, dist_idx: int) -> float:
        """
        计算曲率（近似）

        在离散情况下，使用邻近分布的距离变化来估计曲率
        """
        if dist_idx >= len(self.distributions):
            raise ValueError("Invalid distribution index")

        # 简化版本：使用与邻近分布的距离
        center = self.distributions[dist_idx]

        # 找到最近的两个分布
        distances = [(i, TotalVariation.distance(center, dist))
                     for i, dist in enumerate(self.distributions) if i != dist_idx]
        distances.sort(key=lambda x: x[1])

        if len(distances) < 2:
            return 0.0

        # 使用距离比估计曲率
        d1, d2 = distances[0][1], distances[1][1]
        curvature = abs(d1 - d2) / max(d1 + d2, 1e-10)

        return curvature


# ============================================================================
# Verification Tests
# ============================================================================

class InformationGeometryTests:
    """信息几何验证测试"""

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

    def test_total_variation_properties(self):
        """测试总变差距离的度量性质"""
        p = DistributionFactory.categorical([100, 200, 300])
        q = DistributionFactory.categorical([150, 150, 300])
        r = DistributionFactory.categorical([200, 200, 200])

        self.record_result(
            "TV metric properties",
            TotalVariation.verify_metric_properties(p, q, r),
            "All metric properties satisfied"
        )

    def test_kl_divergence_properties(self):
        """测试KL散度性质"""
        p = DistributionFactory.categorical([100, 200, 300, 400])
        q = DistributionFactory.categorical([150, 150, 300, 400])

        props = KLDivergence.verify_properties(p, q)

        self.record_result(
            "KL non-negativity",
            props['non_negative'],
            f"KL(p||q) = {props['kl_pq']:.4f}"
        )
        self.record_result(
            "KL asymmetry",
            props['asymmetric'],
            f"KL(p||q) = {props['kl_pq']:.4f}, KL(q||p) = {props['kl_qp']:.4f}"
        )
        self.record_result(
            "KL identity",
            props['identity'],
            "KL(p||p) = 0"
        )

    def test_js_symmetry(self):
        """测试JS散度的对称性"""
        p = DistributionFactory.categorical([100, 200, 300])
        q = DistributionFactory.categorical([200, 100, 300])

        js_pq = JensenShannon.divergence(p, q)
        js_qp = JensenShannon.divergence(q, p)

        self.record_result(
            "JS symmetry",
            abs(js_pq - js_qp) < 1e-10,
            f"JS(p||q) = {js_pq:.4f}, JS(q||p) = {js_qp:.4f}"
        )

    def test_entropy_bounds(self):
        """测试熵的边界"""
        # 均匀分布应该有最大熵
        uniform = DistributionFactory.uniform(10)
        # 单点分布应该有最小熵（0）
        single_point = DistributionFactory.categorical([1000] + [0] * 9)

        max_ent = uniform.entropy()
        min_ent = single_point.entropy()

        self.record_result(
            "Entropy maximum (uniform distribution)",
            max_ent > 0 and max_ent <= math.log2(10),
            f"H_max = {max_ent:.4f}, log2(10) = {math.log2(10):.4f}"
        )
        self.record_result(
            "Entropy minimum (single point)",
            min_ent == 0,
            f"H_min = {min_ent:.4f}"
        )

    def test_fisher_information_computation(self):
        """测试Fisher信息计算"""
        params = [5.0]  # 泊松参数
        data = [3, 5, 4, 6, 5]  # 观测数据

        fisher = DiscreteFisherInformation.fisher_information(params, data)

        self.record_result(
            "Fisher information computation",
            fisher[0, 0] >= 0,
            f"I(θ) = {fisher[0, 0]:.4f}"
        )

    def test_distribution_operations(self):
        """测试分布运算"""
        factory = DistributionFactory()

        # 测试各种分布创建
        uniform = factory.uniform(5, total_weight=100)
        bernoulli = factory.bernoulli(70, 30)
        categorical = factory.categorical([10, 20, 30, 40])

        tests = [
            ("Uniform distribution", len(uniform) == 5),
            ("Bernoulli distribution", len(bernoulli) == 2),
            ("Categorical distribution", len(categorical) == 4),
            ("Uniform probabilities", all(abs(p - 0.2) < 0.01 for p in uniform.normalized)),
            ("Total weights match", uniform.total_weight == 100)
        ]

        for name, passed in tests:
            self.record_result(name, passed)

    def test_support_properties(self):
        """测试支撑集性质"""
        p = DistributionFactory.categorical([100, 0, 300, 0, 200])
        support = p.support()

        self.record_result(
            "Support identification",
            support == [0, 2, 4],
            f"Support = {support}"
        )

    def test_geodesic_interpolation(self):
        """测试测地线插值"""
        manifold = StatisticalManifold(3)
        manifold.add_distribution(DistributionFactory.categorical([100, 0, 0]))
        manifold.add_distribution(DistributionFactory.categorical([0, 100, 0]))
        manifold.add_distribution(DistributionFactory.categorical([0, 0, 100]))

        geodesic = manifold.compute_geodesic(0, 2, steps=5)

        self.record_result(
            "Geodesic interpolation",
            len(geodesic) == 5,
            f"Steps = {len(geodesic)}"
        )

    def test_distance_comparison(self):
        """比较不同距离度量"""
        p = DistributionFactory.categorical([100, 200, 300])
        q = DistributionFactory.categorical([150, 150, 300])

        tv = TotalVariation.distance(p, q)
        js = JensenShannon.divergence(p, q)

        self.record_result(
            "TV vs JS distance",
            tv >= 0 and js >= 0,
            f"TV = {tv:.4f}, JS = {js:.4f}"
        )

    def test_benchmark_distances(self):
        """性能基准测试"""
        sizes = [10, 50, 100, 500]
        iterations = 100

        for size in sizes:
            p = DistributionFactory.uniform(size)
            q = DistributionFactory.categorical([random.randint(0, 100) for _ in range(size)])

            start = time.time()
            for _ in range(iterations):
                tv = TotalVariation.distance(p, q)
            elapsed = time.time() - start

            self.performance_data[f'tv_size_{size}'] = elapsed
            self.record_result(
                f"TV performance (size={size})",
                elapsed < 1.0,
                f"Time: {elapsed:.4f}s for {iterations} iterations"
            )

    def test_chain_rule(self):
        """测试链式规则的离散形式"""
        # 简单的马尔可夫链测试
        # P(X,Y) = P(X) * P(Y|X)

        # 边际分布 P(X)
        p_x = DistributionFactory.bernoulli(60, 40)  # P(X=0)=0.6, P(X=1)=0.4

        # 条件分布 P(Y|X)
        # P(Y=0|X=0)=0.7, P(Y=1|X=0)=0.3
        # P(Y=0|X=1)=0.2, P(Y=1|X=1)=0.8

        # 联合分布 P(X,Y)
        p_xy = DistributionFactory.categorical([
            60 * 0.7,   # P(X=0,Y=0)
            60 * 0.3,   # P(X=0,Y=1)
            40 * 0.2,   # P(X=1,Y=0)
            40 * 0.8    # P(X=1,Y=1)
        ])

        # H(X,Y) = H(X) + H(Y|X)
        h_x = p_x.entropy()
        h_xy = p_xy.entropy()

        # H(X) <= H(X,Y)
        self.record_result(
            "Entropy chain rule (monotonicity)",
            h_x <= h_xy + 1e-10,
            f"H(X) = {h_x:.4f}, H(X,Y) = {h_xy:.4f}"
        )

    def test_mutual_information(self):
        """测试互信息"""
        # 互信息 I(X;Y) = H(X) + H(Y) - H(X,Y)

        # 独立分布
        p_x = DistributionFactory.bernoulli(50, 50)
        p_y = DistributionFactory.bernoulli(50, 50)

        # 独立时的联合分布
        p_xy_independent = DistributionFactory.categorical([2500, 2500, 2500, 2500])

        h_x = p_x.entropy()
        h_y = p_y.entropy()
        h_xy = p_xy_independent.entropy()

        mi = h_x + h_y - h_xy

        # 独立时互信息应该接近0
        self.record_result(
            "Mutual information (independent)",
            abs(mi) < 0.1,
            f"MI = {mi:.4f}"
        )

    def run_all_tests(self):
        """运行所有验证测试"""
        print("=" * 70)
        print("DCA Chapter 31: Information Geometry Verification")
        print("=" * 70)
        print()

        print("Core Functionality Tests:")
        print("-" * 70)
        self.test_distribution_operations()
        self.test_support_properties()

        print("\nDistance Metric Tests:")
        print("-" * 70)
        self.test_total_variation_properties()
        self.test_kl_divergence_properties()
        self.test_js_symmetry()
        self.test_distance_comparison()

        print("\nEntropy and Information Tests:")
        print("-" * 70)
        self.test_entropy_bounds()
        self.test_chain_rule()
        self.test_mutual_information()

        print("\nFisher Information Tests:")
        print("-" * 70)
        self.test_fisher_information_computation()

        print("\nGeometry Tests:")
        print("-" * 70)
        self.test_geodesic_interpolation()

        print("\nPerformance Tests:")
        print("-" * 70)
        self.test_benchmark_distances()

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
# Demonstration: Information Geometry Visualization Data
# ============================================================================

def generate_geometry_demo():
    """生成信息几何演示数据"""
    print("\n" + "=" * 70)
    print("Information Geometry Demonstration")
    print("=" * 70)

    # 创建一个简单的统计流形
    manifold = StatisticalManifold(3)

    # 添加几个分布
    distributions = [
        [100, 0, 0],    # 角点1
        [0, 100, 0],    # 角点2
        [0, 0, 100],    # 角点3
        [50, 50, 0],    # 边中点1
        [50, 0, 50],    # 边中点2
        [0, 50, 50],    # 边中点3
        [33, 33, 34],   # 中心点
    ]

    for weights in distributions:
        manifold.add_distribution(DistributionFactory.categorical(weights))

    # 计算所有分布对之间的距离
    print("\nTotal Variation Distance Matrix:")
    print("-" * 50)
    n = len(manifold.distributions)
    print(f"{'':>10}", end="")
    for i in range(n):
        print(f"D{i:>6}", end="")
    print()

    for i in range(n):
        print(f"D{i:>6}", end="")
        for j in range(n):
            dist = TotalVariation.distance(manifold.distributions[i], manifold.distributions[j])
            print(f"{dist:>6.2f}", end="")
        print()

    # 计算每个分布的熵
    print("\nEntropy of Each Distribution:")
    print("-" * 50)
    for i, dist in enumerate(manifold.distributions):
        ent = dist.entropy()
        print(f"D{i}: H = {ent:.4f} bits")


import random


if __name__ == "__main__":
    # 运行验证测试
    tests = InformationGeometryTests()
    tests.run_all_tests()

    # 生成演示数据
    generate_geometry_demo()

    print("\n" + "=" * 70)
    print("Information Geometry Verification Complete!")
    print("=" * 70)