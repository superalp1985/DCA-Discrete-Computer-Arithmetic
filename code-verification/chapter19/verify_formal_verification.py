"""
DCA Chapter 19: From Definitions to Formal Verification - Verification Code
Testing specifications, implementations, and formal verification methods
"""

import time
from typing import List, Tuple, Dict, Callable, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import itertools

# ============================================================================
# SECTION 1: Specification and Implementation Framework
# ============================================================================

class SpecType(Enum):
    """Types of formal specifications"""
    FUNCTIONAL = "functional"  # Input-output behavior
    STATEFUL = "stateful"       # State transition properties
    INVARIANT = "invariant"     # Properties that always hold
    TEMPORAL = "temporal"       # Temporal properties

@dataclass
class Specification:
    """
    Formal specification of a component
    Defines what the component should do (not how)
    """
    name: str
    spec_type: SpecType
    preconditions: List[Callable] = field(default_factory=list)
    postconditions: List[Callable] = field(default_factory=list)
    invariants: List[Callable] = field(default_factory=list)

    def check_preconditions(self, *args, **kwargs) -> Tuple[bool, List[str]]:
        """Check if all preconditions are satisfied"""
        errors = []
        for precond in self.preconditions:
            try:
                if not precond(*args, **kwargs):
                    errors.append(f"Precondition failed: {precond.__name__}")
            except Exception as e:
                errors.append(f"Precondition error: {e}")
        return len(errors) == 0, errors

    def check_postconditions(self, result, *args, **kwargs) -> Tuple[bool, List[str]]:
        """Check if all postconditions are satisfied"""
        errors = []
        for postcond in self.postconditions:
            try:
                if not postcond(result, *args, **kwargs):
                    errors.append(f"Postcondition failed: {postcond.__name__}")
            except Exception as e:
                errors.append(f"Postcondition error: {e}")
        return len(errors) == 0, errors

@dataclass
class Implementation:
    """
    Implementation that should satisfy a specification
    """
    name: str
    function: Callable
    specification: Optional[Specification] = None

    def verify(self, test_cases: List[Tuple]) -> Dict[str, Any]:
        """Verify implementation against specification"""
        if self.specification is None:
            return {"valid": True, "message": "No specification to verify against"}

        results = []
        for test_case in test_cases:
            args = test_case[:-1] if isinstance(test_case[-1], dict) else test_case
            kwargs = test_case[-1] if isinstance(test_case[-1], dict) else {}

            # Check preconditions
            pre_ok, pre_errors = self.specification.check_preconditions(*args, **kwargs)
            if not pre_ok:
                results.append({
                    "test_case": test_case,
                    "passed": False,
                    "errors": pre_errors
                })
                continue

            # Execute function
            try:
                result = self.function(*args, **kwargs)

                # Check postconditions
                post_ok, post_errors = self.specification.check_postconditions(
                    result, *args, **kwargs
                )

                results.append({
                    "test_case": test_case,
                    "passed": post_ok,
                    "result": result,
                    "errors": post_errors
                })
            except Exception as e:
                results.append({
                    "test_case": test_case,
                    "passed": False,
                    "errors": [f"Exception: {e}"]
                })

        passed_count = sum(1 for r in results if r["passed"])
        return {
            "valid": passed_count == len(results),
            "passed": passed_count,
            "total": len(results),
            "results": results
        }

# ============================================================================
# SECTION 2: Bit and Word Specifications
# ============================================================================

class BitSpecs:
    """Specifications for bit-level operations"""

    @staticmethod
    def add_spec_w(a: int, b: int, w: int) -> int:
        """
        Specification for w-bit addition
        add_spec(a, b, w) = (a + b) mod 2^w
        """
        return (a + b) % (1 << w)

    @staticmethod
    def multiply_spec_w(a: int, b: int, w: int) -> int:
        """
        Specification for w-bit multiplication
        mul_spec(a, b, w) = (a * b) mod 2^w
        """
        return (a * b) % (1 << w)

    @staticmethod
    def verify_add_impl(impl: Callable, w: int) -> Dict[str, Any]:
        """Verify addition implementation against specification"""
        errors = []

        # Test all possible values for small w
        if w <= 8:
            for a in range(1 << w):
                for b in range(1 << w):
                    expected = BitSpecs.add_spec_w(a, b, w)
                    actual = impl(a, b, w)
                    if actual != expected:
                        errors.append(f"Failed: {a} + {b} (w={w}): expected {expected}, got {actual}")
        else:
            # For larger w, test sample values
            import random
            for _ in range(1000):
                a = random.randint(0, (1 << w) - 1)
                b = random.randint(0, (1 << w) - 1)
                expected = BitSpecs.add_spec_w(a, b, w)
                actual = impl(a, b, w)
                if actual != expected:
                    errors.append(f"Failed: {a} + {b} (w={w}): expected {expected}, got {actual}")
                    break

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "w": w
        }

    @staticmethod
    def verify_multiply_impl(impl: Callable, w: int) -> Dict[str, Any]:
        """Verify multiplication implementation against specification"""
        errors = []

        # Test sample values
        import random
        for _ in range(min(1000, (1 << w) ** 2)):
            a = random.randint(0, (1 << w) - 1)
            b = random.randint(0, (1 << w) - 1)
            expected = BitSpecs.multiply_spec_w(a, b, w)
            actual = impl(a, b, w)
            if actual != expected:
                errors.append(f"Failed: {a} * {b} (w={w}): expected {expected}, got {actual}")
                break

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "w": w
        }

# ============================================================================
# SECTION 3: Finite Vector and Matrix Specifications
# ============================================================================

class FiniteLinearSpecs:
    """Specifications for finite linear algebra operations"""

    @staticmethod
    def vec_add_spec(a: List[int], b: List[int], mod: Optional[int] = None) -> List[int]:
        """Specification for vector addition"""
        if len(a) != len(b):
            raise ValueError("Vector dimensions must match")

        result = [(a[i] + b[i]) for i in range(len(a))]
        if mod is not None:
            result = [x % mod for x in result]
        return result

    @staticmethod
    def vec_dot_spec(a: List[int], b: List[int], mod: Optional[int] = None) -> int:
        """Specification for vector dot product"""
        if len(a) != len(b):
            raise ValueError("Vector dimensions must match")

        result = sum(a[i] * b[i] for i in range(len(a)))
        if mod is not None:
            result = result % mod
        return result

    @staticmethod
    def mat_mul_spec(A: List[List[int]], B: List[List[int]], mod: Optional[int] = None) -> List[List[int]]:
        """Specification for matrix multiplication"""
        rows_A = len(A)
        cols_A = len(A[0]) if A else 0
        rows_B = len(B)
        cols_B = len(B[0]) if B else 0

        if cols_A != rows_B:
            raise ValueError("Matrix dimensions incompatible for multiplication")

        result = [[0] * cols_B for _ in range(rows_A)]
        for i in range(rows_A):
            for j in range(cols_B):
                sum_val = 0
                for k in range(cols_A):
                    sum_val += A[i][k] * B[k][j]
                if mod is not None:
                    sum_val = sum_val % mod
                result[i][j] = sum_val

        return result

# ============================================================================
# SECTION 4: State Machine Verification
# ============================================================================

@dataclass
class StateTransition:
    """Single state transition"""
    from_state: str
    to_state: str
    condition: Optional[Callable] = None
    action: Optional[Callable] = None

@dataclass
class StateMachine:
    """Finite state machine specification"""
    initial_state: str
    states: List[str]
    transitions: List[StateTransition]

    def verify_reachability(self, target_state: str) -> bool:
        """Check if a state is reachable from initial state"""
        visited = set()
        queue = [self.initial_state]

        while queue:
            current = queue.pop(0)
            if current == target_state:
                return True
            if current in visited:
                continue
            visited.add(current)

            for trans in self.transitions:
                if trans.from_state == current and trans.to_state not in visited:
                    queue.append(trans.to_state)

        return False

    def verify_determinism(self) -> bool:
        """Check if transitions are deterministic"""
        for state in self.states:
            outgoing = [t for t in self.transitions if t.from_state == state]
            # Check for non-deterministic transitions (same from_state with no exclusive conditions)
            if len(outgoing) > 1:
                conditions = [t.condition for t in outgoing if t.condition is not None]
                if len(conditions) != len(outgoing):
                    return False  # Some transitions lack conditions
        return True

# ============================================================================
# SECTION 5: Loop Invariant Verification
# ============================================================================

class LoopInvariant:
    """Framework for verifying loop invariants"""

    @staticmethod
    def verify_sum_invariant() -> bool:
        """Verify invariant for sum loop: sum = sum of processed elements"""
        # Invariant: At iteration i, sum = arr[0] + ... + arr[i-1]

        def sum_with_invariant(arr: List[int]) -> int:
            sum_val = 0
            # Base case: before loop, sum = 0 (sum of empty prefix)
            invariant_holds = (sum_val == 0)
            if not invariant_holds:
                return False

            for i, val in enumerate(arr):
                sum_val += val
                # Check invariant: sum = arr[0] + ... + arr[i]
                expected = sum(arr[:i+1])
                if sum_val != expected:
                    return False

            # Final invariant: sum = total sum of array
            return sum_val

        # Test cases
        test_cases = [
            [1, 2, 3, 4, 5],
            [10, -5, 3],
            [0, 0, 0],
            [100]
        ]

        for arr in test_cases:
            result = sum_with_invariant(arr)
            if result is False:
                return False
            if result != sum(arr):
                return False

        return True

    @staticmethod
    def verify_max_invariant() -> bool:
        """Verify invariant for max-finding loop"""
        # Invariant: max = maximum of processed elements

        def max_with_invariant(arr: List[int]) -> int:
            if not arr:
                return None

            max_val = arr[0]
            # Base case: max is first element (max of single-element prefix)

            for i, val in enumerate(arr[1:], 1):
                if val > max_val:
                    max_val = val
                # Check invariant: max = max(arr[0:i+1])
                expected = max(arr[:i+1])
                if max_val != expected:
                    return False

            return max_val

        # Test cases
        test_cases = [
            [1, 5, 3, 9, 2],
            [10, 10, 10],
            [-5, -2, -10],
            [100]
        ]

        for arr in test_cases:
            result = max_with_invariant(arr)
            if result is False:
                return False
            if result != max(arr):
                return False

        return True

# ============================================================================
# SECTION 6: Property-Based Testing
# ============================================================================

class PropertyTester:
    """Property-based testing framework"""

    def __init__(self):
        self.properties = []

    def add_property(self, name: str, property_func: Callable, generators: Dict[str, Callable]):
        """Add a property to test"""
        self.properties.append({
            "name": name,
            "property": property_func,
            "generators": generators
        })

    def test_property(self, property_spec: Dict, n_tests: int = 100) -> Dict[str, Any]:
        """Test a single property with random inputs"""
        passed = 0
        failed = 0
        counterexamples = []

        for _ in range(n_tests):
            # Generate random inputs
            inputs = {}
            for param_name, generator in property_spec["generators"].items():
                inputs[param_name] = generator()

            # Test property
            try:
                result = property_spec["property"](**inputs)
                if result:
                    passed += 1
                else:
                    failed += 1
                    counterexamples.append(inputs)
            except Exception as e:
                failed += 1
                counterexamples.append({"inputs": inputs, "error": str(e)})

        return {
            "property": property_spec["name"],
            "passed": passed,
            "failed": failed,
            "total": n_tests,
            "counterexamples": counterexamples[:5]  # Limit counterexamples
        }

    def run_all_tests(self, n_tests: int = 100) -> List[Dict]:
        """Run all property tests"""
        results = []
        for prop_spec in self.properties:
            result = self.test_property(prop_spec, n_tests)
            results.append(result)
        return results

# ============================================================================
# SECTION 7: Model Checking for Finite State Systems
# ============================================================================

class ModelChecker:
    """Simple model checker for finite state systems"""

    @staticmethod
    def check_liveness(initial_states: List[str], transitions: Dict[str, List[str]],
                      target_states: List[str]) -> Dict[str, bool]:
        """Check if target states are reachable (liveness property)"""
        results = {}

        for target in target_states:
            reachable = False
            visited = set()
            queue = initial_states[:]

            while queue and not reachable:
                current = queue.pop(0)
                if current == target:
                    reachable = True
                    break
                if current in visited:
                    continue
                visited.add(current)

                if current in transitions:
                    queue.extend(transitions[current])

            results[target] = reachable

        return results

    @staticmethod
    def check_safety(states: List[str], transitions: Dict[str, List[str]],
                     unsafe_states: List[str]) -> bool:
        """Check if unsafe states are unreachable (safety property)"""
        # Check if any unsafe state is reachable from any state
        for unsafe in unsafe_states:
            reachability = ModelChecker.check_liveness(states, transitions, [unsafe])
            if reachability.get(unsafe, False):
                return False  # Unsafe state is reachable!
        return True

# ============================================================================
# SECTION 8: Proof Carrying Code
# ============================================================================

@dataclass
class ProofCertificate:
    """Proof certificate for code verification"""
    statement: str
    proof: List[str]
    verified: bool = False

class ProofChecker:
    """Simple proof checker"""

    @staticmethod
    def check_addition_proof(a: int, b: int, w: int, certificate: ProofCertificate) -> bool:
        """Check proof certificate for w-bit addition"""
        # Verify the statement
        expected = (a + b) % (1 << w)
        # The proof should demonstrate this
        # In a full implementation, this would check formal proof steps
        return str(expected) in certificate.statement

    @staticmethod
    def verify_certificate(certificate: ProofCertificate) -> bool:
        """Verify a proof certificate"""
        # In a full implementation, this would:
        # 1. Parse the proof
        # 2. Check each step against inference rules
        # 3. Verify the conclusion matches the statement
        certificate.verified = True
        return True

# ============================================================================
# SECTION 9: Test Suite
# ============================================================================

class TestSuite:
    """Comprehensive test suite for formal verification"""

    def __init__(self):
        self.results = []
        self.benchmarks = []

    def test_bit_specs(self) -> bool:
        """Test bit-level operation specifications"""
        print("Testing bit-level specifications...")

        passed = True

        # Test addition specification
        for w in [8, 16, 32]:
            def add_impl(a: int, b: int, w: int) -> int:
                return (a + b) % (1 << w)

            result = BitSpecs.verify_add_impl(add_impl, w)
            passed = passed and result["valid"]

        # Test multiplication specification
        for w in [8, 16]:
            def mul_impl(a: int, b: int, w: int) -> int:
                return (a * b) % (1 << w)

            result = BitSpecs.verify_multiply_impl(mul_impl, w)
            passed = passed and result["valid"]

        self.results.append({
            "test": "Bit Specifications",
            "passed": passed,
            "details": "Bit-level operation specifications verified"
        })

        print(f"  Result: {'PASS' if passed else 'FAIL'}")
        return passed

    def test_linear_specs(self) -> bool:
        """Test linear algebra specifications"""
        print("Testing linear algebra specifications...")

        passed = True

        # Test vector addition
        a = [1, 2, 3]
        b = [4, 5, 6]
        expected = [5, 7, 9]
        actual = FiniteLinearSpecs.vec_add_spec(a, b)
        passed = passed and (actual == expected)

        # Test vector dot product
        a = [1, 2, 3]
        b = [4, 5, 6]
        expected = 1*4 + 2*5 + 3*6  # 32
        actual = FiniteLinearSpecs.vec_dot_spec(a, b)
        passed = passed and (actual == expected)

        # Test matrix multiplication
        A = [[1, 2], [3, 4]]
        B = [[5, 6], [7, 8]]
        expected = [[1*5+2*7, 1*6+2*8], [3*5+4*7, 3*6+4*8]]
        actual = FiniteLinearSpecs.mat_mul_spec(A, B)
        passed = passed and (actual == expected)

        # Test modular operations
        a = [1, 2, 3]
        b = [4, 5, 6]
        expected = [(1+4)%7, (2+5)%7, (3+6)%7]  # [5, 0, 2]
        actual = FiniteLinearSpecs.vec_add_spec(a, b, mod=7)
        passed = passed and (actual == expected)

        self.results.append({
            "test": "Linear Algebra Specifications",
            "passed": passed,
            "details": "Vector and matrix specifications verified"
        })

        print(f"  Result: {'PASS' if passed else 'FAIL'}")
        return passed

    def test_state_machines(self) -> bool:
        """Test state machine verification"""
        print("Testing state machine verification...")

        # Create a simple state machine
        transitions = [
            StateTransition("idle", "processing", lambda: True),
            StateTransition("processing", "done", lambda: True),
            StateTransition("done", "idle", lambda: True)
        ]

        sm = StateMachine(
            initial_state="idle",
            states=["idle", "processing", "done"],
            transitions=transitions
        )

        # Test reachability
        passed = sm.verify_reachability("done")
        passed = passed and sm.verify_determinism()

        self.results.append({
            "test": "State Machine Verification",
            "passed": passed,
            "details": "State machine properties verified"
        })

        print(f"  Result: {'PASS' if passed else 'FAIL'}")
        return passed

    def test_loop_invariants(self) -> bool:
        """Test loop invariant verification"""
        print("Testing loop invariant verification...")

        passed = True

        passed = passed and LoopInvariant.verify_sum_invariant()
        passed = passed and LoopInvariant.verify_max_invariant()

        self.results.append({
            "test": "Loop Invariants",
            "passed": passed,
            "details": "Loop invariant properties verified"
        })

        print(f"  Result: {'PASS' if passed else 'FAIL'}")
        return passed

    def test_property_based_testing(self) -> bool:
        """Test property-based testing"""
        print("Testing property-based testing...")

        tester = PropertyTester()

        # Property: addition is commutative
        import random
        tester.add_property(
            "addition_commutative",
            lambda a, b: a + b == b + a,
            {"a": lambda: random.randint(-100, 100), "b": lambda: random.randint(-100, 100)}
        )

        # Property: multiplication is associative
        tester.add_property(
            "multiplication_associative",
            lambda a, b, c: (a * b) * c == a * (b * c),
            {
                "a": lambda: random.randint(-10, 10),
                "b": lambda: random.randint(-10, 10),
                "c": lambda: random.randint(-10, 10)
            }
        )

        # Property: distributive law
        tester.add_property(
            "distributive_law",
            lambda a, b, c: a * (b + c) == a * b + a * c,
            {
                "a": lambda: random.randint(-10, 10),
                "b": lambda: random.randint(-10, 10),
                "c": lambda: random.randint(-10, 10)
            }
        )

        results = tester.run_all_tests(n_tests=100)
        passed = all(r["failed"] == 0 for r in results)

        self.results.append({
            "test": "Property-Based Testing",
            "passed": passed,
            "details": f"{len(results)} properties tested"
        })

        print(f"  Result: {'PASS' if passed else 'FAIL'}")
        return passed

    def test_model_checking(self) -> bool:
        """Test model checking"""
        print("Testing model checking...")

        # Create a simple transition system
        states = ["s0", "s1", "s2"]
        transitions = {
            "s0": ["s1"],
            "s1": ["s2"],
            "s2": ["s0"]
        }

        # Test liveness
        liveness = ModelChecker.check_liveness(["s0"], transitions, ["s2"])
        passed = liveness.get("s2", False)

        # Test safety
        unsafe = ["unsafe"]
        safe = ModelChecker.check_safety(states, transitions, unsafe)
        passed = passed and safe

        self.results.append({
            "test": "Model Checking",
            "passed": passed,
            "details": "Liveness and safety properties verified"
        })

        print(f"  Result: {'PASS' if passed else 'FAIL'}")
        return passed

    def test_specification_framework(self) -> bool:
        """Test specification and implementation framework"""
        print("Testing specification framework...")

        # Create a specification for addition
        add_spec = Specification(
            name="addition",
            spec_type=SpecType.FUNCTIONAL,
            preconditions=[
                lambda a, b: isinstance(a, (int, float)),
                lambda a, b: isinstance(b, (int, float))
            ],
            postconditions=[
                lambda result, a, b: abs(result - (a + b)) < 1e-9
            ]
        )

        # Create implementation
        def add_impl(a, b):
            return a + b

        impl = Implementation(
            name="add_implementation",
            function=add_impl,
            specification=add_spec
        )

        # Verify
        test_cases = [(1, 2), (0, 0), (-5, 10), (3.14, 2.86)]
        result = impl.verify(test_cases)

        passed = result["valid"]

        self.results.append({
            "test": "Specification Framework",
            "passed": passed,
            "details": "Spec-impl verification framework works"
        })

        print(f"  Result: {'PASS' if passed else 'FAIL'}")
        return passed

    def run_all_tests(self) -> Dict[str, any]:
        """Run all tests"""
        print("=" * 60)
        print("DCA Chapter 19: Formal Verification - Test Suite")
        print("=" * 60)

        tests = [
            ("Bit Specifications", self.test_bit_specs),
            ("Linear Algebra Specifications", self.test_linear_specs),
            ("State Machine Verification", self.test_state_machines),
            ("Loop Invariants", self.test_loop_invariants),
            ("Property-Based Testing", self.test_property_based_testing),
            ("Model Checking", self.test_model_checking),
            ("Specification Framework", self.test_specification_framework),
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

# ============================================================================
# SECTION 10: Main Execution
# ============================================================================

def main():
    """Main execution function"""
    suite = TestSuite()
    test_results = suite.run_all_tests()

    print("\n" + "=" * 60)
    print("FINAL SUMMARY")
    print("=" * 60)
    print(f"Tests Passed: {test_results['passed_tests']}/{test_results['total_tests']}")
    print(f"Success Rate: {test_results['passed_tests']/test_results['total_tests']*100:.1f}%")

    return test_results

if __name__ == "__main__":
    results = main()
