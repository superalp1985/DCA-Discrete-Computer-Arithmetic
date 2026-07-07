"""
DCA Chapter 22: Finite-Dimensional Operator Algebras - Verification Code
Testing matrix operators, norms, and linear transformations on graphs
"""

import time
import math
from typing import List, Tuple, Dict, Set, Callable, Optional
import itertools

# ============================================================================
# SECTION 1: Matrix Representation and Operations
# ============================================================================

class Matrix:
    """Matrix representation for finite-dimensional operators"""

    def __init__(self, data: List[List[int]], mod: Optional[int] = None):
        """
        Initialize matrix
        Args:
            data: 2D list of integers
            mod: Optional modulus for modular arithmetic
        """
        self.data = [row[:] for row in data]  # Deep copy
        self.mod = mod
        self.rows = len(data)
        self.cols = len(data[0]) if data else 0

        # Validate rectangular shape
        for row in data:
            if len(row) != self.cols:
                raise ValueError("All rows must have the same length")

        # Apply modulus if specified
        if mod is not None:
            self._apply_mod()

    def _apply_mod(self):
        """Apply modular arithmetic to all entries"""
        if self.mod is not None:
            for i in range(self.rows):
                for j in range(self.cols):
                    self.data[i][j] %= self.mod

    def __add__(self, other):
        """Matrix addition"""
        if self.rows != other.rows or self.cols != other.cols:
            raise ValueError("Matrix dimensions must match for addition")

        result = [
            [self.data[i][j] + other.data[i][j] for j in range(self.cols)]
            for i in range(self.rows)
        ]

        return Matrix(result, self.mod)

    def __sub__(self, other):
        """Matrix subtraction"""
        if self.rows != other.rows or self.cols != other.cols:
            raise ValueError("Matrix dimensions must match for subtraction")

        result = [
            [self.data[i][j] - other.data[i][j] for j in range(self.cols)]
            for i in range(self.rows)
        ]

        return Matrix(result, self.mod)

    def __mul__(self, other):
        """Matrix multiplication"""
        if isinstance(other, (int, float)):
            # Scalar multiplication
            result = [
                [self.data[i][j] * other for j in range(self.cols)]
                for i in range(self.rows)
            ]
            return Matrix(result, self.mod)

        if isinstance(other, Matrix):
            # Matrix multiplication
            if self.cols != other.rows:
                raise ValueError("Matrix dimensions must be compatible for multiplication")

            result = [
                [
                    sum(self.data[i][k] * other.data[k][j] for k in range(self.cols))
                    for j in range(other.cols)
                ]
                for i in range(self.rows)
            ]
            return Matrix(result, self.mod)

        raise TypeError("Unsupported operand type")

    def __pow__(self, power: int):
        """Matrix power"""
        if self.rows != self.cols:
            raise ValueError("Matrix must be square for exponentiation")

        if power < 0:
            raise ValueError("Power must be non-negative")

        if power == 0:
            return Matrix.identity(self.rows, self.mod)

        if power == 1:
            return Matrix(self.data, self.mod)

        # Binary exponentiation
        result = Matrix.identity(self.rows, self.mod)
        base = Matrix(self.data, self.mod)

        while power > 0:
            if power % 2 == 1:
                result = result * base
            base = base * base
            power //= 2

        return result

    def transpose(self):
        """Matrix transpose"""
        result = [
            [self.data[j][i] for j in range(self.rows)]
            for i in range(self.cols)
        ]
        return Matrix(result, self.mod)

    def trace(self) -> int:
        """Matrix trace (sum of diagonal elements)"""
        if self.rows != self.cols:
            raise ValueError("Matrix must be square for trace")
        return sum(self.data[i][i] for i in range(self.rows))

    def determinant(self) -> int:
        """Compute determinant using Laplace expansion"""
        if self.rows != self.cols:
            raise ValueError("Matrix must be square for determinant")

        if self.rows == 1:
            return self.data[0][0]

        if self.rows == 2:
            return self.data[0][0] * self.data[1][1] - self.data[0][1] * self.data[1][0]

        # Laplace expansion along first row
        det = 0
        for j in range(self.cols):
            sign = (-1) ** j
            minor = self._minor(0, j)
            det += sign * self.data[0][j] * minor.determinant()

        return det

    def _minor(self, row: int, col: int):
        """Get minor matrix by removing specified row and column"""
        minor_data = [
            [self.data[i][j] for j in range(self.cols) if j != col]
            for i in range(self.rows) if i != row
        ]
        return Matrix(minor_data, self.mod)

    @classmethod
    def identity(cls, n: int, mod: Optional[int] = None):
        """Create identity matrix"""
        data = [[1 if i == j else 0 for j in range(n)] for i in range(n)]
        return cls(data, mod)

    @classmethod
    def zero(cls, rows: int, cols: int, mod: Optional[int] = None):
        """Create zero matrix"""
        data = [[0 for _ in range(cols)] for _ in range(rows)]
        return cls(data, mod)

    @classmethod
    def random(cls, rows: int, cols: int, max_val: int = 10, mod: Optional[int] = None):
        """Create random matrix"""
        import random
        data = [[random.randint(0, max_val) for _ in range(cols)] for _ in range(rows)]
        return cls(data, mod)

    def __eq__(self, other):
        """Matrix equality"""
        if not isinstance(other, Matrix):
            return False
        if self.rows != other.rows or self.cols != other.cols:
            return False
        for i in range(self.rows):
            for j in range(self.cols):
                if self.data[i][j] != other.data[i][j]:
                    return False
        return True

    def __str__(self):
        """String representation"""
        return '\n'.join(['\t'.join(map(str, row)) for row in self.data])

    def __repr__(self):
        return f"Matrix({self.rows}x{self.cols}, mod={self.mod})"

# ============================================================================
# SECTION 2: Matrix Norms
# ============================================================================

class MatrixNorms:
    """Matrix norms for finite-dimensional operators"""

    @staticmethod
    def norm_one(A: Matrix) -> int:
        """
        L1 norm (maximum absolute column sum)
        ||A||_1 = max_j sum_i |A_{ij}|
        """
        max_sum = 0
        for j in range(A.cols):
            col_sum = sum(abs(A.data[i][j]) for i in range(A.rows))
            max_sum = max(max_sum, col_sum)
        return max_sum

    @staticmethod
    def norm_infinity(A: Matrix) -> int:
        """
        L-infinity norm (maximum absolute row sum)
        ||A||_∞ = max_i sum_j |A_{ij}|
        """
        max_sum = 0
        for i in range(A.rows):
            row_sum = sum(abs(A.data[i][j]) for j in range(A.cols))
            max_sum = max(max_sum, row_sum)
        return max_sum

    @staticmethod
    def norm_frobenius(A: Matrix) -> float:
        """
        Frobenius norm (Euclidean norm of matrix entries)
        ||A||_F = sqrt(sum_{i,j} |A_{ij}|^2)
        """
        sum_squares = sum(A.data[i][j] ** 2 for i in range(A.rows) for j in range(A.cols))
        return math.sqrt(sum_squares)

    @staticmethod
    def verify_submultiplicativity(A: Matrix, B: Matrix, norm_func: Callable) -> Tuple[bool, str]:
        """
        Verify submultiplicativity: ||AB|| <= ||A|| * ||B||
        """
        AB = A * B
        norm_AB = norm_func(AB)
        norm_A = norm_func(A)
        norm_B = norm_func(B)

        if norm_AB <= norm_A * norm_B:
            return True, f"Submultiplicativity holds: {norm_AB} <= {norm_A} * {norm_B} = {norm_A * norm_B}"
        else:
            return False, f"Submultiplicativity violated: {norm_AB} > {norm_A} * {norm_B} = {norm_A * norm_B}"

    @staticmethod
    def verify_triangle_inequality(A: Matrix, B: Matrix, norm_func: Callable) -> Tuple[bool, str]:
        """
        Verify triangle inequality: ||A + B|| <= ||A|| + ||B||
        """
        sum_AB = A + B
        norm_sum = norm_func(sum_AB)
        norm_A = norm_func(A)
        norm_B = norm_func(B)

        if norm_sum <= norm_A + norm_B:
            return True, f"Triangle inequality holds: {norm_sum} <= {norm_A} + {norm_B} = {norm_A + norm_B}"
        else:
            return False, f"Triangle inequality violated: {norm_sum} > {norm_A} + {norm_B} = {norm_A + norm_B}"

# ============================================================================
# SECTION 3: Linear Transformations
# ============================================================================

class LinearTransformation:
    """Linear transformation represented by matrix"""

    def __init__(self, matrix: Matrix):
        self.matrix = matrix

    def apply(self, vector: List[int]) -> List[int]:
        """Apply linear transformation to vector"""
        if len(vector) != self.matrix.cols:
            raise ValueError("Vector dimension must match matrix columns")

        result = []
        for i in range(self.matrix.rows):
            result.append(
                sum(self.matrix.data[i][j] * vector[j] for j in range(self.matrix.cols))
            )

        return result

    def compose(self, other):
        """Compose with another linear transformation"""
        if self.matrix.cols != other.matrix.rows:
            raise ValueError("Cannot compose: dimension mismatch")

        return LinearTransformation(other.matrix * self.matrix)

    def is_invertible(self) -> bool:
        """Check if transformation is invertible (determinant non-zero)"""
        if self.matrix.rows != self.matrix.cols:
            return False
        return self.matrix.determinant() != 0

# ============================================================================
# SECTION 4: Graph Laplacian and Adjacency Matrices
# ============================================================================

class GraphMatrices:
    """Matrices associated with graphs"""

    @staticmethod
    def adjacency_matrix(n: int, edges: List[Tuple[int, int]]) -> Matrix:
        """Create adjacency matrix for undirected graph"""
        data = [[0] * n for _ in range(n)]
        for i, j in edges:
            if 0 <= i < n and 0 <= j < n:
                data[i][j] = 1
                data[j][i] = 1  # Undirected
        return Matrix(data)

    @staticmethod
    def degree_matrix(n: int, edges: List[Tuple[int, int]]) -> Matrix:
        """Create degree matrix (diagonal matrix of vertex degrees)"""
        degrees = [0] * n
        for i, j in edges:
            if 0 <= i < n and 0 <= j < n:
                degrees[i] += 1
                degrees[j] += 1

        data = [[0] * n for _ in range(n)]
        for i in range(n):
            data[i][i] = degrees[i]

        return Matrix(data)

    @staticmethod
    def laplacian_matrix(n: int, edges: List[Tuple[int, int]]) -> Matrix:
        """Create Laplacian matrix L = D - A"""
        D = GraphMatrices.degree_matrix(n, edges)
        A = GraphMatrices.adjacency_matrix(n, edges)
        return D - A

    @staticmethod
    def verify_laplacian_properties(L: Matrix) -> Dict[str, Tuple[bool, str]]:
        """Verify Laplacian matrix properties"""
        results = {}

        # Property 1: Symmetric
        LT = L.transpose()
        results["symmetry"] = (L == LT, "Laplacian is symmetric")

        # Property 2: Row sums are zero
        row_sums_zero = True
        for i in range(L.rows):
            row_sum = sum(L.data[i][j] for j in range(L.cols))
            if row_sum != 0:
                row_sums_zero = False
                break
        results["zero_row_sums"] = (row_sums_zero, "All row sums are zero")

        # Property 3: Diagonal entries are non-negative
        diag_nonneg = all(L.data[i][i] >= 0 for i in range(L.rows))
        results["nonnegative_diagonal"] = (diag_nonneg, "Diagonal entries are non-negative")

        # Property 4: Off-diagonal entries are non-positive
        offdiag_nonpos = True
        for i in range(L.rows):
            for j in range(L.cols):
                if i != j and L.data[i][j] > 0:
                    offdiag_nonpos = False
                    break
        results["nonpositive_offdiagonal"] = (offdiag_nonpos, "Off-diagonal entries are non-positive")

        return results

# ============================================================================
# SECTION 5: Matrix Properties over Finite Fields
# ============================================================================

class FiniteFieldMatrix:
    """Matrix operations over finite fields"""

    @staticmethod
    def rank(A: Matrix) -> int:
        """Compute matrix rank using Gaussian elimination"""
        # Copy matrix to avoid modifying original
        data = [row[:] for row in A.data]
        rows = A.rows
        cols = A.cols
        mod = A.mod

        rank = 0
        row = 0

        for col in range(cols):
            # Find pivot
            pivot = None
            for i in range(row, rows):
                if data[i][col] != 0:
                    pivot = i
                    break

            if pivot is None:
                continue

            # Swap rows
            data[row], data[pivot] = data[pivot], data[row]

            # Normalize pivot row
            if mod is not None:
                # Find modular inverse
                pivot_val = data[row][col]
                inv = None
                for x in range(1, mod):
                    if (x * pivot_val) % mod == 1:
                        inv = x
                        break
                if inv is not None:
                    data[row] = [(val * inv) % mod for val in data[row]]

            # Eliminate column
            for i in range(rows):
                if i != row and data[i][col] != 0:
                    if mod is not None:
                        factor = data[i][col]
                        data[i] = [(data[i][j] - factor * data[row][j]) % mod for j in range(cols)]
                    else:
                        factor = data[i][col] / data[row][col]
                        data[i] = [data[i][j] - factor * data[row][j] for j in range(cols)]

            row += 1
            rank += 1

            if row >= rows:
                break

        return rank

    @staticmethod
    def nullity(A: Matrix) -> int:
        """Compute nullity using rank-nullity theorem"""
        return A.cols - FiniteFieldMatrix.rank(A)

    @staticmethod
    def verify_rank_nullity_theorem(A: Matrix) -> Tuple[bool, str]:
        """Verify rank(A) + nullity(A) = n (number of columns)"""
        rank = FiniteFieldMatrix.rank(A)
        nullity = FiniteFieldMatrix.nullity(A)
        n = A.cols

        if rank + nullity == n:
            return True, f"Rank-nullity holds: {rank} + {nullity} = {n}"
        else:
            return False, f"Rank-nullity violated: {rank} + {nullity} != {n}"

# ============================================================================
# SECTION 6: Eigenvalue-like Properties (Integer Versions)
# ============================================================================

class IntegerSpectralProperties:
    """Integer versions of spectral properties"""

    @staticmethod
    def characteristic_polynomial(A: Matrix) -> List[int]:
        """Compute characteristic polynomial coefficients (for small matrices)"""
        if A.rows != A.cols or A.rows > 4:
            raise ValueError("Only implemented for small matrices (up to 4x4)")

        n = A.rows
        if n == 1:
            return [-A.data[0][0], 1]

        if n == 2:
            return [
                A.determinant(),
                -(A.data[0][0] + A.data[1][1]),
                1
            ]

        if n == 3:
            # For 3x3, compute using trace and adjugate
            det = A.determinant()
            trace = A.trace()

            # Sum of principal minors
            sum_minors = 0
            for i in range(n):
                minor = A._minor(i, i)
                sum_minors += minor.determinant()

            return [det, -sum_minors, trace, -1]

        if n == 4:
            # Simplified computation
            det = A.determinant()
            trace = A.trace()
            return [det, 0, 0, -trace, 1]

        return []

    @staticmethod
    def cayley_hamilton_verification(A: Matrix) -> Tuple[bool, str]:
        """Verify Cayley-Hamilton theorem (for small matrices)"""
        if A.rows != A.cols or A.rows > 3:
            return False, "Verification only for small matrices (up to 3x3)"

        coeffs = IntegerSpectralProperties.characteristic_polynomial(A)
        n = A.rows

        # Compute p(A) = det(A - λI) evaluated at A
        # p(A) = c₀I + c₁A + c₂A² + ... + cₙAⁿ
        result = Matrix.zero(n, n, A.mod)

        for i, coeff in enumerate(coeffs):
            if i == 0:
                term = Matrix.identity(n, A.mod) * coeff
            else:
                term = (A ** i) * coeff

            result = result + term

        # Check if result is zero matrix
        is_zero = all(result.data[i][j] == 0 for i in range(n) for j in range(n))

        if is_zero:
            return True, "Cayley-Hamilton theorem verified: p(A) = 0"
        else:
            return False, "Cayley-Hamilton verification failed"

# ============================================================================
# SECTION 7: Performance Benchmarking
# ============================================================================

class PerformanceBenchmarks:
    """Performance benchmarks for matrix operations"""

    @staticmethod
    def benchmark_matrix_multiplication(size: int, n_iterations: int = 100) -> Dict[str, float]:
        """Benchmark matrix multiplication"""
        print(f"Benchmarking {size}x{size} matrix multiplication ({n_iterations} iterations)...")

        A = Matrix.random(size, size, 10)
        B = Matrix.random(size, size, 10)

        start = time.time()
        for _ in range(n_iterations):
            C = A * B
        elapsed = time.time() - start

        # Count operations
        ops_per_mult = size * size * size  # Multiplications
        total_ops = ops_per_mult * n_iterations

        return {
            "total_time": elapsed,
            "time_per_multiplication": elapsed / n_iterations,
            "multiplications_per_second": n_iterations / elapsed,
            "operations_per_second": total_ops / elapsed
        }

    @staticmethod
    def benchmark_matrix_norm(size: int, n_iterations: int = 1000) -> Dict[str, float]:
        """Benchmark matrix norm computation"""
        print(f"Benchmarking {size}x{size} matrix norm computation ({n_iterations} iterations)...")

        A = Matrix.random(size, size, 10)

        start = time.time()
        for _ in range(n_iterations):
            norm = MatrixNorms.norm_one(A)
        elapsed = time.time() - start

        return {
            "total_time": elapsed,
            "norms_per_second": n_iterations / elapsed,
            "time_per_norm": elapsed / n_iterations
        }

    @staticmethod
    def benchmark_determinant(size: int, n_iterations: int = 100) -> Dict[str, float]:
        """Benchmark determinant computation"""
        print(f"Benchmarking {size}x{size} determinant ({n_iterations} iterations)...")

        A = Matrix.random(size, size, 10)

        start = time.time()
        for _ in range(n_iterations):
            det = A.determinant()
        elapsed = time.time() - start

        return {
            "total_time": elapsed,
            "determinants_per_second": n_iterations / elapsed,
            "time_per_determinant": elapsed / n_iterations
        }

# ============================================================================
# SECTION 8: Comprehensive Test Suite
# ============================================================================

class TestSuite:
    """Comprehensive test suite for finite-dimensional operator algebras"""

    def __init__(self):
        self.results = []
        self.benchmarks = []

    def test_matrix_operations(self) -> bool:
        """Test basic matrix operations"""
        print("Testing matrix operations...")

        passed = True

        # Test addition
        A = Matrix([[1, 2], [3, 4]])
        B = Matrix([[5, 6], [7, 8]])
        C = A + B
        expected = Matrix([[6, 8], [10, 12]])

        if C != expected:
            passed = False
            print(f"  Addition failed: {C.data} != {expected.data}")

        # Test multiplication
        A = Matrix([[1, 2], [3, 4]])
        B = Matrix([[2, 0], [1, 2]])
        C = A * B
        expected = Matrix([[4, 4], [10, 8]])

        if C != expected:
            passed = False
            print(f"  Multiplication failed: {C.data} != {expected.data}")

        # Test identity
        I = Matrix.identity(2)
        A = Matrix([[1, 2], [3, 4]])
        C = I * A
        if C != A:
            passed = False
            print(f"  Identity multiplication failed")

        # Test transpose
        A = Matrix([[1, 2, 3], [4, 5, 6]])
        AT = A.transpose()
        expected = Matrix([[1, 4], [2, 5], [3, 6]])

        if AT != expected:
            passed = False
            print(f"  Transpose failed")

        self.results.append({
            "test": "Matrix Operations",
            "passed": passed,
            "details": "Basic matrix operations verified"
        })

        print(f"  Result: {'PASS' if passed else 'FAIL'}")
        return passed

    def test_norm_properties(self) -> bool:
        """Test matrix norm properties"""
        print("Testing matrix norm properties...")

        A = Matrix([[1, -2, 3], [-4, 5, -6]])
        B = Matrix([[2, -1, 0], [1, 3, -2]])

        tests_passed = []

        # Test submultiplicativity for L1 norm
        result, msg = MatrixNorms.verify_submultiplicativity(A, B, MatrixNorms.norm_one)
        tests_passed.append(result)
        print(f"  L1 submultiplicativity: {msg}")

        # Test triangle inequality for L1 norm
        result, msg = MatrixNorms.verify_triangle_inequality(A, B, MatrixNorms.norm_one)
        tests_passed.append(result)
        print(f"  L1 triangle inequality: {msg}")

        # Test submultiplicativity for L-infinity norm
        result, msg = MatrixNorms.verify_submultiplicativity(A, B, MatrixNorms.norm_infinity)
        tests_passed.append(result)
        print(f"  L∞ submultiplicativity: {msg}")

        # Test triangle inequality for L-infinity norm
        result, msg = MatrixNorms.verify_triangle_inequality(A, B, MatrixNorms.norm_infinity)
        tests_passed.append(result)
        print(f"  L∞ triangle inequality: {msg}")

        passed = all(tests_passed)

        self.results.append({
            "test": "Norm Properties",
            "passed": passed,
            "details": f"{len(tests_passed)} norm property tests"
        })

        print(f"  Result: {'PASS' if passed else 'FAIL'}")
        return passed

    def test_linear_transformations(self) -> bool:
        """Test linear transformations"""
        print("Testing linear transformations...")

        # Test transformation application
        A = Matrix([[2, 0], [0, 3]])
        T = LinearTransformation(A)

        result = T.apply([1, 2])
        expected = [2, 6]

        passed = result == expected
        print(f"  Apply: {result} == {expected}: {passed}")

        # Test composition
        B = Matrix([[1, 1], [0, 1]])
        S = LinearTransformation(B)

        # Apply S then T: T(S(v))
        v = [1, 1]
        sv = S.apply(v)
        tsv = T.apply(sv)

        # Compose transformations
        TS = T.compose(S)
        composed = TS.apply(v)

        passed = passed and (composed == tsv)
        print(f"  Composition: {passed}")

        # Test invertibility
        A = Matrix([[1, 2], [3, 4]])
        T = LinearTransformation(A)
        is_inv = T.is_invertible()
        det = A.determinant()
        expected_inv = (det != 0)

        passed = passed and (is_inv == expected_inv)
        print(f"  Invertibility: {is_inv} (det={det}): {passed}")

        self.results.append({
            "test": "Linear Transformations",
            "passed": passed,
            "details": "Linear transformation properties verified"
        })

        print(f"  Result: {'PASS' if passed else 'FAIL'}")
        return passed

    def test_graph_matrices(self) -> bool:
        """Test graph matrices"""
        print("Testing graph matrices...")

        # Create a simple graph
        n = 4
        edges = [(0, 1), (1, 2), (2, 3), (3, 0), (0, 2)]

        A = GraphMatrices.adjacency_matrix(n, edges)
        L = GraphMatrices.laplacian_matrix(n, edges)

        results = GraphMatrices.verify_laplacian_properties(L)

        tests_passed = [result[0] for result in results.values()]
        passed = all(tests_passed)

        for prop, (success, msg) in results.items():
            print(f"  {prop}: {msg}")

        self.results.append({
            "test": "Graph Matrices",
            "passed": passed,
            "details": f"Laplacian properties: {len(tests_passed)} tests"
        })

        print(f"  Result: {'PASS' if passed else 'FAIL'}")
        return passed

    def test_modular_arithmetic(self) -> bool:
        """Test matrix operations over finite fields"""
        print("Testing modular arithmetic...")

        # Test over GF(7)
        A = Matrix([[3, 5], [2, 4]], mod=7)
        B = Matrix([[6, 1], [3, 2]], mod=7)

        # Addition
        C = A + B
        expected_data = [[(3+6)%7, (5+1)%7], [(2+3)%7, (4+2)%7]]
        expected = Matrix(expected_data, mod=7)

        passed = (C == expected)
        print(f"  Modular addition: {passed}")

        # Multiplication
        C = A * B
        expected_data = [
            [(3*6 + 5*3) % 7, (3*1 + 5*2) % 7],
            [(2*6 + 4*3) % 7, (2*1 + 4*2) % 7]
        ]
        expected = Matrix(expected_data, mod=7)

        passed = passed and (C == expected)
        print(f"  Modular multiplication: {passed}")

        self.results.append({
            "test": "Modular Arithmetic",
            "passed": passed,
            "details": "Matrix operations over finite fields"
        })

        print(f"  Result: {'PASS' if passed else 'FAIL'}")
        return passed

    def test_determinant_and_inverse(self) -> bool:
        """Test determinant computation"""
        print("Testing determinant and rank...")

        # Test determinant
        A = Matrix([[1, 2], [3, 4]])
        det = A.determinant()
        expected = -2

        passed = (det == expected)
        print(f"  Determinant: {det} == {expected}: {passed}")

        # Test rank
        B = Matrix([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
        rank = FiniteFieldMatrix.rank(B)

        passed = passed and (rank == 2)  # Rows are linearly dependent
        print(f"  Rank of singular matrix: {rank} == 2: {passed}")

        # Test rank-nullity theorem
        result, msg = FiniteFieldMatrix.verify_rank_nullity_theorem(B)
        passed = passed and result
        print(f"  Rank-nullity theorem: {msg}")

        self.results.append({
            "test": "Determinant and Rank",
            "passed": passed,
            "details": "Matrix invariants verified"
        })

        print(f"  Result: {'PASS' if passed else 'FAIL'}")
        return passed

    def test_cayley_hamilton(self) -> bool:
        """Test Cayley-Hamilton theorem"""
        print("Testing Cayley-Hamilton theorem...")

        A = Matrix([[2, 1], [1, 2]])
        result, msg = IntegerSpectralProperties.cayley_hamilton_verification(A)

        passed = result
        print(f"  Cayley-Hamilton: {msg}")

        self.results.append({
            "test": "Cayley-Hamilton Theorem",
            "passed": passed,
            "details": msg
        })

        print(f"  Result: {'PASS' if passed else 'FAIL'}")
        return passed

    def run_all_tests(self) -> Dict[str, any]:
        """Run all tests"""
        print("=" * 60)
        print("DCA Chapter 22: Finite-Dimensional Operator Algebras - Test Suite")
        print("=" * 60)

        tests = [
            ("Matrix Operations", self.test_matrix_operations),
            ("Norm Properties", self.test_norm_properties),
            ("Linear Transformations", self.test_linear_transformations),
            ("Graph Matrices", self.test_graph_matrices),
            ("Modular Arithmetic", self.test_modular_arithmetic),
            ("Determinant and Rank", self.test_determinant_and_inverse),
            ("Cayley-Hamilton Theorem", self.test_cayley_hamilton),
        ]

        for name, test_func in tests:
            print(f"\nRunning: {name}")
            print("-" * 40)
            try:
                test_func()
            except Exception as e:
                print(f"  ERROR: {e}")
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

        # Benchmark 1: Matrix multiplication
        print("\nBenchmark 1: Matrix Multiplication")
        print("-" * 40)
        for size in [4, 8, 16, 32]:
            result = PerformanceBenchmarks.benchmark_matrix_multiplication(size)
            self.benchmarks.append({
                "name": f"Matrix Multiplication ({size}x{size})",
                "result": result
            })
            print(f"  {size}x{size}: {result['multiplications_per_second']:.0f} mult/sec")

        # Benchmark 2: Matrix norms
        print("\nBenchmark 2: Matrix Norm Computation")
        print("-" * 40)
        for size in [16, 32, 64, 128]:
            result = PerformanceBenchmarks.benchmark_matrix_norm(size)
            self.benchmarks.append({
                "name": f"Matrix Norm ({size}x{size})",
                "result": result
            })
            print(f"  {size}x{size}: {result['norms_per_second']:.0f} norms/sec")

        # Benchmark 3: Determinant
        print("\nBenchmark 3: Determinant Computation")
        print("-" * 40)
        for size in [4, 8, 12, 16]:
            result = PerformanceBenchmarks.benchmark_determinant(size)
            self.benchmarks.append({
                "name": f"Determinant ({size}x{size})",
                "result": result
            })
            print(f"  {size}x{size}: {result['determinants_per_second']:.0f} det/sec")

        return {
            "benchmarks": self.benchmarks
        }

# ============================================================================
# SECTION 9: Main Execution
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