"""
DCA Chapter 18: Discrete Automatic Differentiation - Verification Code
Testing automatic differentiation on finite computation graphs
"""

import time
from typing import List, Tuple, Dict, Callable, Optional, Any
from dataclasses import dataclass, field
from enum import Enum

# ============================================================================
# SECTION 1: Computation Graph Nodes
# ============================================================================

class OpType(Enum):
    """Operation types for computation graph"""
    CONSTANT = "constant"
    VARIABLE = "variable"
    ADD = "add"
    SUBTRACT = "subtract"
    MULTIPLY = "multiply"
    DIVIDE = "divide"
    POWER = "power"
    SIN = "sin"
    COS = "cos"
    EXP = "exp"
    LOG = "log"
    RELU = "relu"
    SIGMOID = "sigmoid"

@dataclass
class Node:
    """
    Node in computation graph
    Represents a value and its gradient during automatic differentiation
    """
    id: int
    value: float = 0.0
    grad: float = 0.0
    op_type: OpType = OpType.VARIABLE
    parents: List['Node'] = field(default_factory=list)
    children: List['Node'] = field(default_factory=list)

    def __add__(self, other: 'Node') -> 'Node':
        """Addition operation"""
        result = Node(
            id=id(self) + id(other),
            value=self.value + other.value,
            op_type=OpType.ADD,
            parents=[self, other]
        )
        self.children.append(result)
        other.children.append(result)
        return result

    def __sub__(self, other: 'Node') -> 'Node':
        """Subtraction operation"""
        result = Node(
            id=id(self) + id(other) + 1,
            value=self.value - other.value,
            op_type=OpType.SUBTRACT,
            parents=[self, other]
        )
        self.children.append(result)
        other.children.append(result)
        return result

    def __mul__(self, other: 'Node') -> 'Node':
        """Multiplication operation"""
        result = Node(
            id=id(self) + id(other) + 2,
            value=self.value * other.value,
            op_type=OpType.MULTIPLY,
            parents=[self, other]
        )
        self.children.append(result)
        other.children.append(result)
        return result

    def __truediv__(self, other: 'Node') -> 'Node':
        """Division operation"""
        result = Node(
            id=id(self) + id(other) + 3,
            value=self.value / other.value if other.value != 0 else 0,
            op_type=OpType.DIVIDE,
            parents=[self, other]
        )
        self.children.append(result)
        other.children.append(result)
        return result

    def __pow__(self, other: 'Node') -> 'Node':
        """Power operation"""
        result = Node(
            id=id(self) + id(other) + 4,
            value=self.value ** other.value,
            op_type=OpType.POWER,
            parents=[self, other]
        )
        self.children.append(result)
        other.children.append(result)
        return result

    def relu(self) -> 'Node':
        """ReLU activation"""
        result = Node(
            id=id(self) + 1000,
            value=max(0, self.value),
            op_type=OpType.RELU,
            parents=[self]
        )
        self.children.append(result)
        return result

    def sigmoid(self) -> 'Node':
        """Sigmoid activation"""
        import math
        sig = 1 / (1 + math.exp(-self.value))
        result = Node(
            id=id(self) + 1001,
            value=sig,
            op_type=OpType.SIGMOID,
            parents=[self]
        )
        self.children.append(result)
        return result

    def __repr__(self):
        return f"Node({self.value:.4f}, grad={self.grad:.4f})"

# ============================================================================
# SECTION 2: Forward Mode Automatic Differentiation
# ============================================================================

class ForwardAD:
    """Forward mode automatic differentiation using dual numbers"""

    @dataclass
    class Dual:
        """Dual number: a + b*epsilon"""
        real: float
        dual: float

        def __add__(self, other: 'ForwardAD.Dual') -> 'ForwardAD.Dual':
            return ForwardAD.Dual(
                self.real + other.real,
                self.dual + other.dual
            )

        def __sub__(self, other: 'ForwardAD.Dual') -> 'ForwardAD.Dual':
            return ForwardAD.Dual(
                self.real - other.real,
                self.dual - other.dual
            )

        def __mul__(self, other: 'ForwardAD.Dual') -> 'ForwardAD.Dual':
            return ForwardAD.Dual(
                self.real * other.real,
                self.real * other.dual + self.dual * other.real
            )

        def __truediv__(self, other: 'ForwardAD.Dual') -> 'ForwardAD.Dual':
            if other.real == 0:
                raise ValueError("Division by zero")
            return ForwardAD.Dual(
                self.real / other.real,
                (self.dual * other.real - self.real * other.dual) / (other.real ** 2)
            )

        def __rmul__(self, other: 'ForwardAD.Dual') -> 'ForwardAD.Dual':
            # Handle scalar * Dual
            if isinstance(other, (int, float)):
                return ForwardAD.Dual(other * self.real, other * self.dual)
            return self.__mul__(other)

        def __radd__(self, other: 'ForwardAD.Dual') -> 'ForwardAD.Dual':
            # Handle scalar + Dual
            if isinstance(other, (int, float)):
                return ForwardAD.Dual(other + self.real, self.dual)
            return self.__add__(other)

        def __rsub__(self, other: 'ForwardAD.Dual') -> 'ForwardAD.Dual':
            # Handle scalar - Dual
            if isinstance(other, (int, float)):
                return ForwardAD.Dual(other - self.real, -self.dual)
            return ForwardAD.Dual(self.real - other.real, self.dual - other.dual)

        def __pow__(self, n: float) -> 'ForwardAD.Dual':
            if isinstance(n, (int, float)):
                return ForwardAD.Dual(
                    self.real ** n,
                    n * (self.real ** (n - 1)) * self.dual
                )
            return ForwardAD.Dual(self.real ** n.real, n.real * (self.real ** (n.real - 1)) * self.dual)

        def exp(self) -> 'ForwardAD.Dual':
            import math
            e = math.exp(self.real)
            return ForwardAD.Dual(e, e * self.dual)

        def log(self) -> 'ForwardAD.Dual':
            import math
            if self.real <= 0:
                raise ValueError("Log of non-positive number")
            return ForwardAD.Dual(
                math.log(self.real),
                self.dual / self.real
            )

    @staticmethod
    def derivative(f: Callable, x0: float, h: float = 1e-6) -> float:
        """Compute derivative using forward mode AD"""
        # Create dual number with epsilon coefficient
        dual_x = ForwardAD.Dual(x0, 1.0)
        dual_result = f(dual_x)
        return dual_result.dual if hasattr(dual_result, 'dual') else 0.0

    @staticmethod
    def gradient(f: Callable, x: List[float]) -> List[float]:
        """Compute gradient using forward mode AD"""
        grad = []
        for i in range(len(x)):
            # Create dual variables
            dual_vars = []
            for j, val in enumerate(x):
                if j == i:
                    dual_vars.append(ForwardAD.Dual(val, 1.0))
                else:
                    dual_vars.append(ForwardAD.Dual(val, 0.0))

            dual_result = f(dual_vars)
            grad.append(dual_result.dual if hasattr(dual_result, 'dual') else 0.0)

        return grad

# ============================================================================
# SECTION 3: Reverse Mode Automatic Differentiation (Backpropagation)
# ============================================================================

class ReverseAD:
    """Reverse mode automatic differentiation (backpropagation)"""

    def __init__(self):
        self.nodes: List[Node] = []
        self.node_id = 0

    def variable(self, value: float) -> Node:
        """Create a variable node"""
        node = Node(id=self.node_id, value=value, op_type=OpType.VARIABLE)
        self.node_id += 1
        self.nodes.append(node)
        return node

    def constant(self, value: float) -> Node:
        """Create a constant node"""
        node = Node(id=self.node_id, value=value, op_type=OpType.CONSTANT)
        self.node_id += 1
        self.nodes.append(node)
        return node

    def zero_grad(self):
        """Zero out all gradients"""
        for node in self.nodes:
            node.grad = 0.0

    def backward(self, output_node: Node):
        """Perform backward pass (backpropagation)"""
        # Set output gradient
        output_node.grad = 1.0

        # Process nodes in reverse topological order
        visited = set()

        def propagate_grad(node: Node):
            if node.id in visited:
                return
            visited.add(node.id)

            # Propagate gradient to parents based on operation type
            if node.op_type == OpType.ADD:
                # For c = a + b: dc/da = 1, dc/db = 1
                if len(node.parents) >= 2:
                    node.parents[0].grad += node.grad
                    node.parents[1].grad += node.grad

            elif node.op_type == OpType.SUBTRACT:
                # For c = a - b: dc/da = 1, dc/db = -1
                if len(node.parents) >= 2:
                    node.parents[0].grad += node.grad
                    node.parents[1].grad -= node.grad

            elif node.op_type == OpType.MULTIPLY:
                # For c = a * b: dc/da = b, dc/db = a
                if len(node.parents) >= 2:
                    node.parents[0].grad += node.grad * node.parents[1].value
                    node.parents[1].grad += node.grad * node.parents[0].value

            elif node.op_type == OpType.DIVIDE:
                # For c = a / b: dc/da = 1/b, dc/db = -a/b^2
                if len(node.parents) >= 2:
                    a, b = node.parents[0], node.parents[1]
                    if b.value != 0:
                        node.parents[0].grad += node.grad / b.value
                        node.parents[1].grad -= node.grad * a.value / (b.value ** 2)

            elif node.op_type == OpType.POWER:
                # For c = a^b: dc/da = b*a^(b-1), dc/db = a^b * log(a)
                if len(node.parents) >= 2:
                    a, b = node.parents[0], node.parents[1]
                    if a.value > 0:
                        node.parents[0].grad += node.grad * b.value * (a.value ** (b.value - 1))
                        import math
                        node.parents[1].grad += node.grad * (a.value ** b.value) * math.log(a.value)

            elif node.op_type == OpType.RELU:
                # For c = relu(a): dc/da = 1 if a > 0 else 0
                if len(node.parents) >= 1:
                    if node.parents[0].value > 0:
                        node.parents[0].grad += node.grad

            elif node.op_type == OpType.SIGMOID:
                # For c = sigmoid(a): dc/da = c * (1 - c)
                if len(node.parents) >= 1:
                    sig = node.value
                    node.parents[0].grad += node.grad * sig * (1 - sig)

            # Recursively propagate to parents
            for parent in node.parents:
                propagate_grad(parent)

        propagate_grad(output_node)

# ============================================================================
# SECTION 4: Computational Graph Management
# ============================================================================

class ComputationGraph:
    """Manage computational graph for automatic differentiation"""

    def __init__(self):
        self.reverse_ad = ReverseAD()
        self.operations: List[Callable] = []

    def variable(self, value: float) -> Node:
        """Create a variable in the graph"""
        return self.reverse_ad.variable(value)

    def constant(self, value: float) -> Node:
        """Create a constant in the graph"""
        return self.reverse_ad.constant(value)

    def compute_gradients(self, output: Node) -> Dict[int, float]:
        """Compute gradients for all variables"""
        self.reverse_ad.zero_grad()
        self.reverse_ad.backward(output)

        gradients = {}
        for node in self.reverse_ad.nodes:
            if node.op_type == OpType.VARIABLE:
                gradients[node.id] = node.grad

        return gradients

# ============================================================================
# SECTION 5: Finite Difference Verification
# ============================================================================

class FiniteDifference:
    """Finite difference methods for verification"""

    @staticmethod
    def forward_difference(f: Callable, x: float, h: float = 1e-6) -> float:
        """Forward difference: (f(x+h) - f(x)) / h"""
        return (f(x + h) - f(x)) / h

    @staticmethod
    def central_difference(f: Callable, x: float, h: float = 1e-6) -> float:
        """Central difference: (f(x+h) - f(x-h)) / (2h)"""
        return (f(x + h) - f(x - h)) / (2 * h)

    @staticmethod
    def gradient_fd(f: Callable, x: List[float], h: float = 1e-6) -> List[float]:
        """Compute gradient using finite differences"""
        grad = []
        for i in range(len(x)):
            x_plus = x.copy()
            x_plus[i] += h
            x_minus = x.copy()
            x_minus[i] -= h
            grad.append((f(x_plus) - f(x_minus)) / (2 * h))
        return grad

    @staticmethod
    def verify_ad_gradient(ad_grad: float, fd_grad: float, tolerance: float = 1e-4) -> bool:
        """Verify AD gradient against finite difference"""
        return abs(ad_grad - fd_grad) < tolerance

# ============================================================================
# SECTION 6: Test Functions for Verification
# ============================================================================

class TestFunctions:
    """Standard test functions for AD verification"""

    @staticmethod
    def quadratic(x: List[float]) -> float:
        """f(x) = sum(x_i^2)"""
        return sum(xi ** 2 for xi in x)

    @staticmethod
    def rosenbrock(x: List[float]) -> float:
        """Rosenbrock function: f(x) = sum(100*(x_{i+1} - x_i^2)^2 + (1 - x_i)^2)"""
        result = 0.0
        for i in range(len(x) - 1):
            result += 100 * (x[i + 1] - x[i] ** 2) ** 2 + (1 - x[i]) ** 2
        return result

    @staticmethod
    def sphere(x: List[float]) -> float:
        """Sphere function: f(x) = sum(x_i^2)"""
        return sum(xi ** 2 for xi in x)

    @staticmethod
    def rastrigin(x: List[float]) -> float:
        """Rastrigin function: f(x) = 10*n + sum(x_i^2 - 10*cos(2*pi*x_i))"""
        import math
        n = len(x)
        result = 10 * n
        for xi in x:
            result += xi ** 2 - 10 * math.cos(2 * math.pi * xi)
        return result

# ============================================================================
# SECTION 7: Integer/Discrete Gradients
# ============================================================================

class DiscreteGradients:
    """Discrete gradients for integer/quantized operations"""

    @staticmethod
    def straight_through_estimator(x: float) -> int:
        """Straight-through estimator for quantization"""
        quantized = int(round(x))
        # Gradient passes through unchanged
        return quantized

    @staticmethod
    def sign_gradient(x: float) -> float:
        """Sign function with gradient: grad = 1 if |x| < 1 else 0"""
        if abs(x) < 1:
            return 1.0
        return 0.0

    @staticmethod
    def discrete_derivative(f: Callable, x: int) -> int:
        """Discrete derivative using finite differences"""
        return f(x + 1) - f(x)

# ============================================================================
# SECTION 8: Performance Benchmarks
# ============================================================================

class PerformanceBenchmarks:
    """Performance benchmarks for automatic differentiation"""

    @staticmethod
    def benchmark_forward_ad(n_dims: int, n_iterations: int = 100) -> Dict[str, float]:
        """Benchmark forward mode AD"""
        print(f"Benchmarking forward AD: dims={n_dims}, iterations={n_iterations}")

        def f(vars):
            result = vars[0]
            for v in vars[1:]:
                result = result * v
            return result

        x = [2.0] * n_dims

        start = time.time()
        for _ in range(n_iterations):
            ForwardAD.gradient(lambda vars: f(vars), x)
        elapsed = time.time() - start

        return {
            "total_time": elapsed,
            "iterations_per_second": n_iterations / elapsed,
            "time_per_iteration": elapsed / n_iterations
        }

    @staticmethod
    def benchmark_reverse_ad(n_dims: int, n_iterations: int = 100) -> Dict[str, float]:
        """Benchmark reverse mode AD"""
        print(f"Benchmarking reverse AD: dims={n_dims}, iterations={n_iterations}")

        start = time.time()
        for _ in range(n_iterations):
            graph = ComputationGraph()
            vars = [graph.variable(2.0) for _ in range(n_dims)]

            # Build computation: sum of squares
            result = vars[0] * vars[0]
            for v in vars[1:]:
                result = result + v * v

            graph.compute_gradients(result)
        elapsed = time.time() - start

        return {
            "total_time": elapsed,
            "iterations_per_second": n_iterations / elapsed,
            "time_per_iteration": elapsed / n_iterations
        }

# ============================================================================
# SECTION 9: Comprehensive Test Suite
# ============================================================================

class TestSuite:
    """Comprehensive test suite for automatic differentiation"""

    def __init__(self):
        self.results = []
        self.benchmarks = []

    def test_dual_number_arithmetic(self) -> bool:
        """Test dual number arithmetic"""
        print("Testing dual number arithmetic...")

        passed = True

        # Test addition
        a = ForwardAD.Dual(3.0, 1.0)
        b = ForwardAD.Dual(2.0, 0.0)
        c = a + b
        passed = passed and (c.real == 5.0) and (c.dual == 1.0)

        # Test multiplication
        a = ForwardAD.Dual(3.0, 1.0)
        b = ForwardAD.Dual(2.0, 0.0)
        c = a * b
        passed = passed and (c.real == 6.0) and (c.dual == 2.0)

        # Test chain rule: (x^2)' at x=3 should be 6
        def f(x):
            return x * x

        derivative = ForwardAD.derivative(f, 3.0)
        passed = passed and abs(derivative - 6.0) < 1e-6

        self.results.append({
            "test": "Dual Number Arithmetic",
            "passed": passed,
            "details": "Dual number operations verified"
        })

        print(f"  Result: {'PASS' if passed else 'FAIL'}")
        return passed

    def test_forward_ad(self) -> bool:
        """Test forward mode automatic differentiation"""
        print("Testing forward mode AD...")

        passed = True

        # Test polynomial: f(x) = x^3 + 2x^2 + x + 1
        def poly(x):
            return x**3 + 2*x**2 + x + 1

        # Derivative: f'(x) = 3x^2 + 4x + 1
        # At x=2: f'(2) = 3*4 + 8 + 1 = 21
        derivative = ForwardAD.derivative(poly, 2.0)
        expected = 21.0
        passed = passed and abs(derivative - expected) < 1e-6

        # Test exponential
        def exp_func(x):
            import math
            return math.exp(x)

        derivative = ForwardAD.derivative(exp_func, 1.0)
        expected = 2.718281828  # e^1
        passed = passed and abs(derivative - expected) < 1e-5

        # Test gradient computation
        def f(vars):
            return sum(v * v for v in vars)

        x = [1.0, 2.0, 3.0]
        grad = ForwardAD.gradient(f, x)
        expected_grad = [2.0, 4.0, 6.0]

        passed = passed and all(abs(g - e) < 1e-6 for g, e in zip(grad, expected_grad))

        self.results.append({
            "test": "Forward Mode AD",
            "passed": passed,
            "details": "Forward differentiation verified"
        })

        print(f"  Result: {'PASS' if passed else 'FAIL'}")
        return passed

    def test_reverse_ad(self) -> bool:
        """Test reverse mode automatic differentiation"""
        print("Testing reverse mode AD...")

        passed = True

        # Test simple computation: f(x,y) = x^2 + y^2
        graph = ComputationGraph()
        x = graph.variable(2.0)
        y = graph.variable(3.0)

        x_squared = x * x
        y_squared = y * y
        result = x_squared + y_squared

        grads = graph.compute_gradients(result)

        # Expected gradients: df/dx = 2x = 4, df/dy = 2y = 6
        passed = passed and abs(list(grads.values())[0] - 4.0) < 1e-6
        passed = passed and abs(list(grads.values())[1] - 6.0) < 1e-6

        # Test chain rule: f(x) = (x^2)^3
        graph = ComputationGraph()
        x = graph.variable(2.0)
        x2 = x * x
        x6 = x2 * x2 * x2

        grads = graph.compute_gradients(x6)

        # Expected gradient: df/dx = 6x^5 = 6*32 = 192
        expected_grad = 192.0
        actual_grad = list(grads.values())[0]
        passed = passed and abs(actual_grad - expected_grad) < 1e-4

        self.results.append({
            "test": "Reverse Mode AD",
            "passed": passed,
            "details": "Backpropagation verified"
        })

        print(f"  Result: {'PASS' if passed else 'FAIL'}")
        return passed

    def test_activation_functions(self) -> bool:
        """Test activation function gradients"""
        print("Testing activation function gradients...")

        passed = True

        # Test ReLU gradient
        graph = ComputationGraph()
        x = graph.variable(5.0)
        relu_x = x.relu()

        grads = graph.compute_gradients(relu_x)
        # For x > 0, dReLU/dx = 1
        relu_grad = list(grads.values())[0]
        passed = passed and abs(relu_grad - 1.0) < 1e-6

        # Test ReLU at negative value
        graph = ComputationGraph()
        x = graph.variable(-5.0)
        relu_x = x.relu()

        grads = graph.compute_gradients(relu_x)
        # For x < 0, dReLU/dx = 0
        relu_grad = list(grads.values())[0]
        passed = passed and abs(relu_grad - 0.0) < 1e-6

        # Test sigmoid gradient
        graph = ComputationGraph()
        x = graph.variable(0.0)
        sig_x = x.sigmoid()

        grads = graph.compute_gradients(sig_x)
        # At x=0, sigmoid(0) = 0.5, gradient = 0.5 * 0.5 = 0.25
        sig_grad = list(grads.values())[0]
        passed = passed and abs(sig_grad - 0.25) < 1e-4

        self.results.append({
            "test": "Activation Functions",
            "passed": passed,
            "details": "ReLU and sigmoid gradients verified"
        })

        print(f"  Result: {'PASS' if passed else 'FAIL'}")
        return passed

    def test_finite_difference_verification(self) -> bool:
        """Verify AD against finite differences"""
        print("Testing finite difference verification...")

        passed = True

        # Test function: f(x) = x^3
        def f(x):
            return x ** 3

        x0 = 2.0

        # AD derivative
        ad_grad = ForwardAD.derivative(f, x0)

        # Finite difference derivative
        fd_grad = FiniteDifference.central_difference(f, x0)

        # Should match (f'(x) = 3x^2 = 12 at x=2)
        passed = passed and FiniteDifference.verify_ad_gradient(ad_grad, fd_grad)

        # Test multivariate
        def f_multi(x):
            return x[0]**2 + x[1]**2

        x = [3.0, 4.0]
        ad_grads = ForwardAD.gradient(f_multi, x)
        fd_grads = FiniteDifference.gradient_fd(f_multi, x)

        for ad_g, fd_g in zip(ad_grads, fd_grads):
            passed = passed and FiniteDifference.verify_ad_gradient(ad_g, fd_g, tolerance=1e-4)

        self.results.append({
            "test": "Finite Difference Verification",
            "passed": passed,
            "details": "AD verified against finite differences"
        })

        print(f"  Result: {'PASS' if passed else 'FAIL'}")
        return passed

    def test_chain_rule(self) -> bool:
        """Test chain rule in computation graph"""
        print("Testing chain rule...")

        passed = True

        # Test: f(g(x)) where g(x) = x^2 and f(y) = y^3
        # Result: h(x) = (x^2)^3 = x^6
        # h'(x) = 6x^5
        # At x=2: h'(2) = 6*32 = 192

        graph = ComputationGraph()
        x = graph.variable(2.0)
        g = x * x  # x^2
        h = g * g * g  # (x^2)^3 = x^6

        grads = graph.compute_gradients(h)
        actual = list(grads.values())[0]
        expected = 192.0

        passed = passed and abs(actual - expected) < 1e-4

        self.results.append({
            "test": "Chain Rule",
            "passed": passed,
            "details": "Chain rule propagation verified"
        })

        print(f"  Result: {'PASS' if passed else 'FAIL'}")
        return passed

    def test_test_functions(self) -> bool:
        """Test AD on standard optimization test functions"""
        print("Testing standard test functions...")

        passed = True

        # Test quadratic function gradient
        x = [1.0, 2.0, 3.0]
        ad_grads = ForwardAD.gradient(TestFunctions.quadratic, x)
        fd_grads = FiniteDifference.gradient_fd(TestFunctions.quadratic, x)

        for ad_g, fd_g in zip(ad_grads, fd_grads):
            passed = passed and FiniteDifference.verify_ad_gradient(ad_g, fd_g)

        # Test sphere function
        x = [0.5, -0.5, 1.0]
        ad_grads = ForwardAD.gradient(TestFunctions.sphere, x)
        fd_grads = FiniteDifference.gradient_fd(TestFunctions.sphere, x)

        for ad_g, fd_g in zip(ad_grads, fd_grads):
            passed = passed and FiniteDifference.verify_ad_gradient(ad_g, fd_g)

        self.results.append({
            "test": "Test Functions",
            "passed": passed,
            "details": "Standard test function gradients verified"
        })

        print(f"  Result: {'PASS' if passed else 'FAIL'}")
        return passed

    def run_all_tests(self) -> Dict[str, any]:
        """Run all tests"""
        print("=" * 60)
        print("DCA Chapter 18: Discrete Automatic Differentiation - Test Suite")
        print("=" * 60)

        tests = [
            ("Dual Number Arithmetic", self.test_dual_number_arithmetic),
            ("Forward Mode AD", self.test_forward_ad),
            ("Reverse Mode AD", self.test_reverse_ad),
            ("Activation Functions", self.test_activation_functions),
            ("Finite Difference Verification", self.test_finite_difference_verification),
            ("Chain Rule", self.test_chain_rule),
            ("Test Functions", self.test_test_functions),
        ]

        for name, test_func in tests:
            print(f"\nRunning: {name}")
            print("-" * 40)
            try:
                test_func()
            except Exception as e:
                print(f"  ERROR: {e}")
                import traceback
                traceback.print_exc()
                self.results.append({
                    "test": name,
                    "passed": False,
                    "details": f"Exception: {str(e)}"
                })

        passed_count = sum(1 for r in self.results if r["passed"])
        total_count = len(self.results)

        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        print(f"Passed: {passed_count}/{total_count}")
        print(f"Failed: {total_count - passed_count}/{total_count}")

        return {
            "total_tests": total_count,
            "passed_tests": passed_count,
            "failed_tests": total_count - passed_count,
            "results": self.results
        }

    def run_benchmarks(self) -> Dict[str, any]:
        """Run performance benchmarks"""
        print("\n" + "=" * 60)
        print("PERFORMANCE BENCHMARKS")
        print("=" * 60)

        self.benchmarks = []

        # Benchmark forward AD
        print("\nBenchmark 1: Forward Mode AD")
        print("-" * 40)
        for dims in [10, 50, 100]:
            result = PerformanceBenchmarks.benchmark_forward_ad(dims)
            self.benchmarks.append({
                "name": f"Forward AD ({dims}D)",
                "result": result
            })
            print(f"  {dims}D: {result['iterations_per_second']:.0f} iter/sec")

        # Benchmark reverse AD
        print("\nBenchmark 2: Reverse Mode AD")
        print("-" * 40)
        for dims in [10, 50, 100]:
            result = PerformanceBenchmarks.benchmark_reverse_ad(dims)
            self.benchmarks.append({
                "name": f"Reverse AD ({dims}D)",
                "result": result
            })
            print(f"  {dims}D: {result['iterations_per_second']:.0f} iter/sec")

        return {
            "benchmarks": self.benchmarks
        }

# ============================================================================
# SECTION 10: Main Execution
# ============================================================================

def main():
    """Main execution function"""
    suite = TestSuite()

    # Run tests
    test_results = suite.run_all_tests()

    # Run benchmarks
    benchmark_results = suite.run_benchmarks()

    # Print final summary
    print("\n" + "=" * 60)
    print("FINAL SUMMARY")
    print("=" * 60)
    print(f"Tests Passed: {test_results['passed_tests']}/{test_results['total_tests']}")
    print(f"Success Rate: {test_results['passed_tests']/test_results['total_tests']*100:.1f}%")

    return {
        "test_results": test_results,
        "benchmark_results": benchmark_results
    }

if __name__ == "__main__":
    results = main()
