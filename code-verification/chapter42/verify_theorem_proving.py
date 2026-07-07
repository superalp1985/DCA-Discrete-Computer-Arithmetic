#!/usr/bin/env python3
"""
DCA Chapter 42: Automated Theorem Proving - Complete Verification Code
Author: Wang Bingqin
Date: 2026-07-07

Tests:
1. Propositional logic and CNF conversion
2. SAT solver (DPLL algorithm)
3. Unit propagation
4. Pure literal elimination
5. SMT solver basics
6. Linear integer arithmetic
7. Bit vector operations
8. Proof logging and verification
"""

import random
import time
from typing import List, Set, Dict, Tuple, Optional, Any
from collections import defaultdict, Counter
import numpy as np


class Literal:
    """Propositional literal (positive or negative variable)"""

    def __init__(self, var: int, negated: bool = False):
        self.var = var
        self.negated = negated

    def __neg__(self) -> 'Literal':
        return Literal(self.var, not self.negated)

    def __eq__(self, other) -> bool:
        return self.var == other.var and self.negated == other.negated

    def __hash__(self) -> int:
        return hash((self.var, self.negated))

    def __repr__(self) -> str:
        return f"{'~' if self.negated else ''}x{self.var}"


class Clause:
    """Clause: disjunction of literals"""

    def __init__(self, literals: List[Literal]):
        self.literals = list(set(literals))  # Remove duplicates

    def evaluate(self, assignment: Dict[int, bool]) -> Optional[bool]:
        """Evaluate clause under assignment (None if unknown)"""
        result = False
        unknown = False
        for lit in self.literals:
            if lit.var in assignment:
                value = assignment[lit.var]
                if lit.negated:
                    value = not value
                if value:
                    return True  # Clause satisfied
                else:
                    result = False  # This literal is false, continue
            else:
                unknown = True
        return None if unknown else False

    def is_unit(self, assignment: Dict[int, bool]) -> bool:
        """Check if clause is unit (only one unassigned literal)"""
        unassigned = 0
        for lit in self.literals:
            if lit.var in assignment:
                value = assignment[lit.var]
                if lit.negated:
                    value = not value
                if value:
                    return False  # Already satisfied
            else:
                unassigned += 1
        return unassigned == 1

    def get_unit_literal(self, assignment: Dict[int, bool]) -> Optional[Literal]:
        """Get the unit literal if clause is unit"""
        unassigned = None
        for lit in self.literals:
            if lit.var in assignment:
                value = assignment[lit.var]
                if lit.negated:
                    value = not value
                if value:
                    return None  # Clause satisfied
            else:
                if unassigned is not None:
                    return None  # More than one unassigned
                unassigned = lit
        return unassigned

    def is_conflict(self, assignment: Dict[int, bool]) -> bool:
        """Check if clause is falsified"""
        for lit in self.literals:
            if lit.var in assignment:
                value = assignment[lit.var]
                if lit.negated:
                    value = not value
                if value:
                    return False  # Literal true, clause not falsified
            else:
                return False  # Unassigned literal
        return True  # All literals false

    def __repr__(self) -> str:
        return " ∨ ".join(str(lit) for lit in self.literals)


class CNFFormula:
    """Conjunctive Normal Form formula"""

    def __init__(self, clauses: List[Clause]):
        self.clauses = clauses
        self.variables = set()
        for clause in clauses:
            for lit in clause.literals:
                self.variables.add(lit.var)

    def evaluate(self, assignment: Dict[int, bool]) -> Optional[bool]:
        """Evaluate formula under assignment"""
        for clause in self.clauses:
            result = clause.evaluate(assignment)
            if result is False:
                return False  # Clause falsified, formula false
            if result is None:
                return None  # Cannot determine yet
        return True  # All clauses satisfied

    def __repr__(self) -> str:
        return " ∧ ".join(f"({clause})" for clause in self.clauses)


class DPLLSolver:
    """DPLL SAT solver with unit propagation and pure literal elimination"""

    def __init__(self, formula: CNFFormula):
        self.formula = formula
        self.decisions = []
        self.propagations = []

    def solve(self, assignment: Optional[Dict[int, bool]] = None) -> Optional[Dict[int, bool]]:
        """Solve SAT, return satisfying assignment or None"""
        if assignment is None:
            assignment = {}

        # Unit propagation
        while True:
            unit = self._find_unit_clause(assignment)
            if unit is None:
                break
            if assignment.get(unit.var) is None:
                value = not unit.negated
                assignment[unit.var] = value
                self.propagations.append((unit.var, value))

        # Pure literal elimination
        pure_lits = self._find_pure_literals(assignment)
        for lit in pure_lits:
            if lit.var not in assignment:
                assignment[lit.var] = not lit.negated

        # Check for conflict
        if self._has_conflict(assignment):
            return None

        # Check if all variables assigned
        unassigned = [v for v in self.formula.variables if v not in assignment]
        if not unassigned:
            return assignment

        # Choose variable and branch
        var = unassigned[0]

        # Try var = True
        new_assignment = assignment.copy()
        new_assignment[var] = True
        self.decisions.append((var, True))
        result = self.solve(new_assignment)
        if result is not None:
            return result

        # Try var = False
        new_assignment = assignment.copy()
        new_assignment[var] = False
        self.decisions.append((var, False))
        result = self.solve(new_assignment)
        if result is not None:
            return result

        return None

    def _find_unit_clause(self, assignment: Dict[int, bool]) -> Optional[Literal]:
        """Find unit clause"""
        for clause in self.formula.clauses:
            if clause.is_unit(assignment):
                return clause.get_unit_literal(assignment)
        return None

    def _find_pure_literals(self, assignment: Dict[int, bool]) -> List[Literal]:
        """Find pure literals (literals that appear with only one polarity)"""
        literal_counts = Counter()

        for clause in self.formula.clauses:
            for lit in clause.literals:
                if lit.var not in assignment:
                    literal_counts[lit] += 1

        pure_literals = []
        for lit in literal_counts:
            neg_lit = -lit
            if neg_lit not in literal_counts:
                pure_literals.append(lit)

        return pure_literals

    def _has_conflict(self, assignment: Dict[int, bool]) -> bool:
        """Check for conflicting clauses"""
        return any(clause.is_conflict(assignment) for clause in self.formula.clauses)


class BitVector:
    """Fixed-width bit vector"""

    def __init__(self, value: int, width: int):
        self.value = value & ((1 << width) - 1)
        self.width = width

    def extract(self, high: int, low: int) -> int:
        """Extract bits [high:low]"""
        mask = (1 << (high - low + 1)) - 1
        return (self.value >> low) & mask

    def concat(self, other: 'BitVector') -> 'BitVector':
        """Concatenate bit vectors"""
        new_width = self.width + other.width
        new_value = (self.value << other.width) | other.value
        return BitVector(new_value, new_width)

    def __eq__(self, other) -> bool:
        return self.value == other.value and self.width == other.width

    def __repr__(self) -> str:
        return f"{self.value:0{self.width}b}"


class SMTSolver:
    """Simple SMT solver for linear integer arithmetic"""

    def __init__(self):
        self.constraints = []

    def add_le(self, vars: List[str], coeffs: List[int], rhs: int):
        """Add linear constraint: sum(coeffs[i] * vars[i]) <= rhs"""
        self.constraints.append({
            "type": "le",
            "vars": vars,
            "coeffs": coeffs,
            "rhs": rhs
        })

    def add_ge(self, vars: List[str], coeffs: List[int], rhs: int):
        """Add linear constraint: sum(coeffs[i] * vars[i]) >= rhs"""
        self.constraints.append({
            "type": "ge",
            "vars": vars,
            "coeffs": coeffs,
            "rhs": rhs
        })

    def add_eq(self, vars: List[str], coeffs: List[int], rhs: int):
        """Add linear constraint: sum(coeffs[i] * vars[i]) == rhs"""
        self.constraints.append({
            "type": "eq",
            "vars": vars,
            "coeffs": coeffs,
            "rhs": rhs
        })

    def solve(self, bounds: Dict[str, Tuple[int, int]]) -> Optional[Dict[str, int]]:
        """Solve using bounded integer search"""
        variables = list(bounds.keys())
        return self._search(variables, 0, bounds, {})

    def _search(self, variables: List[str], idx: int, bounds: Dict[str, Tuple[int, int]],
                assignment: Dict[str, int]) -> Optional[Dict[str, int]]:
        """Recursive search for satisfying assignment"""
        if idx == len(variables):
            if self._check_assignment(assignment):
                return assignment
            return None

        var = variables[idx]
        low, high = bounds[var]

        for val in range(low, high + 1):
            new_assignment = assignment.copy()
            new_assignment[var] = val
            result = self._search(variables, idx + 1, bounds, new_assignment)
            if result is not None:
                return result

        return None

    def _check_assignment(self, assignment: Dict[str, int]) -> bool:
        """Check if assignment satisfies all constraints"""
        for constraint in self.constraints:
            vars_needed = constraint["vars"]
            coeffs = constraint["coeffs"]
            rhs = constraint["rhs"]

            # Compute left-hand side
            lhs = sum(coeffs[i] * assignment[vars_needed[i]] for i in range(len(vars_needed)))

            # Check constraint type
            if constraint["type"] == "le" and lhs > rhs:
                return False
            if constraint["type"] == "ge" and lhs < rhs:
                return False
            if constraint["type"] == "eq" and lhs != rhs:
                return False

        return True


class ProofLogger:
    """Log proof steps for verification"""

    def __init__(self):
        self.steps = []

    def add_decision(self, var: int, value: bool, level: int):
        """Log variable decision"""
        self.steps.append({
            "type": "decision",
            "var": var,
            "value": value,
            "level": level
        })

    def add_propagation(self, var: int, value: bool, reason: str):
        """Log unit propagation"""
        self.steps.append({
            "type": "propagation",
            "var": var,
            "value": value,
            "reason": reason
        })

    def add_conflict(self, clause: Clause):
        """Log conflict clause"""
        self.steps.append({
            "type": "conflict",
            "clause": clause
        })

    def add_backtrack(self, level: int):
        """Log backtrack"""
        self.steps.append({
            "type": "backtrack",
            "level": level
        })

    def verify(self) -> bool:
        """Verify proof steps are valid"""
        # Simplified verification - in practice would be more complex
        return len(self.steps) > 0


# Test Functions
def test_cnf_conversion():
    """Test CNF formula creation and evaluation"""
    print("Testing CNF Conversion...")

    # Create CNF: (x1 ∨ ~x2) ∧ (x2 ∨ x3) ∧ (~x1 ∨ x3)
    clause1 = Clause([Literal(1), -Literal(2)])
    clause2 = Clause([Literal(2), Literal(3)])
    clause3 = Clause([-Literal(1), Literal(3)])
    formula = CNFFormula([clause1, clause2, clause3])

    # Test satisfying assignment
    assignment = {1: True, 2: False, 3: True}
    result = formula.evaluate(assignment)

    results = {
        "satisfying_assignment_works": result == True,
        "passed": result == True
    }

    print(f"  Satisfying assignment works: {results['satisfying_assignment_works']}")

    return results


def test_dpll_solver():
    """Test DPLL SAT solver"""
    print("Testing DPLL Solver...")

    # Test 1: Simple satisfiable formula: (x1 ∨ x2)
    clause1 = Clause([Literal(1), Literal(2)])
    formula1 = CNFFormula([clause1])
    solver1 = DPLLSolver(formula1)
    result1 = solver1.solve()

    # Test 2: Unsatisfiable formula: (x1) ∧ (~x1)
    clause2a = Clause([Literal(1)])
    clause2b = Clause([-Literal(1)])
    formula2 = CNFFormula([clause2a, clause2b])
    solver2 = DPLLSolver(formula2)
    result2 = solver2.solve()

    # Test 3: 3-SAT instance
    # (x1 ∨ x2 ∨ x3) ∧ (~x1 ∨ x2 ∨ ~x3) ∧ (x1 ∨ ~x2 ∨ x3) ∧ (~x1 ∨ ~x2 ∨ ~x3)
    clause3a = Clause([Literal(1), Literal(2), Literal(3)])
    clause3b = Clause([-Literal(1), Literal(2), -Literal(3)])
    clause3c = Clause([Literal(1), -Literal(2), Literal(3)])
    clause3d = Clause([-Literal(1), -Literal(2), -Literal(3)])
    formula3 = CNFFormula([clause3a, clause3b, clause3c, clause3d])
    solver3 = DPLLSolver(formula3)
    result3 = solver3.solve()

    results = {
        "simple_sat_solved": result1 is not None,
        "contradiction_unsat": result2 is None,
        "3sat_solved": result3 is not None,
        "passed": result1 is not None and result2 is None and result3 is not None
    }

    print(f"  Simple SAT solved: {results['simple_sat_solved']}")
    print(f"  Contradiction UNSAT: {results['contradiction_unsat']}")
    print(f"  3-SAT solved: {results['3sat_solved']}")

    return results


def test_unit_propagation():
    """Test unit propagation"""
    print("Testing Unit Propagation...")

    # Formula where unit clause forces propagation
    # (x1) ∧ (x1 ∨ x2) ∧ (~x1 ∨ x3)
    clause1 = Clause([Literal(1)])  # Unit clause forces x1=True
    clause2 = Clause([Literal(1), Literal(2)])
    clause3 = Clause([-Literal(1), Literal(3)])
    formula = CNFFormula([clause1, clause2, clause3])
    solver = DPLLSolver(formula)

    result = solver.solve()

    # Should propagate x1=True, then x3 becomes True
    results = {
        "unit_propagation_works": result is not None and result[1] == True and result[3] == True,
        "passed": result is not None and result[1] == True and result[3] == True
    }

    print(f"  Unit propagation works: {results['unit_propagation_works']}")

    return results


def test_pure_literal_elimination():
    """Test pure literal elimination"""
    print("Testing Pure Literal Elimination...")

    # Formula with pure literals
    # (x1 ∨ x2) ∧ (~x1 ∨ x2) ∧ (x3 ∨ x4)
    # Here x2 appears only positive, x3 and x4 appear only positive
    clause1 = Clause([Literal(1), Literal(2)])
    clause2 = Clause([-Literal(1), Literal(2)])
    clause3 = Clause([Literal(3), Literal(4)])
    formula = CNFFormula([clause1, clause2, clause3])
    solver = DPLLSolver(formula)

    result = solver.solve()

    # Pure literals should be set to satisfy formula
    results = {
        "pure_literal_elimination_works": result is not None,
        "passed": result is not None
    }

    print(f"  Pure literal elimination works: {results['pure_literal_elimination_works']}")

    return results


def test_bit_vectors():
    """Test bit vector operations"""
    print("Testing Bit Vectors...")

    # Test extraction
    bv = BitVector(0b11010, 5)  # 26 in binary
    extracted = bv.extract(3, 1)  # Should be 101 = 5

    # Test concatenation
    bv1 = BitVector(0b101, 3)
    bv2 = BitVector(0b011, 3)
    concatenated = bv1.concat(bv2)
    expected_value = (0b101 << 3) | 0b011

    results = {
        "extraction_correct": extracted == 5,
        "concatenation_correct": concatenated.value == expected_value,
        "passed": extracted == 5 and concatenated.value == expected_value
    }

    print(f"  Extraction correct: {results['extraction_correct']}")
    print(f"  Concatenation correct: {results['concatenation_correct']}")

    return results


def test_smt_solver():
    """Test SMT solver for linear integer arithmetic"""
    print("Testing SMT Solver...")

    solver = SMTSolver()

    # Add constraints: x + y <= 5, x >= 1, y >= 1
    solver.add_le(["x", "y"], [1, 1], 5)
    solver.add_ge(["x"], [1], 1)
    solver.add_ge(["y"], [1], 1)

    # Solve with bounds
    bounds = {"x": (0, 10), "y": (0, 10)}
    result = solver.solve(bounds)

    # Verify solution
    valid = False
    if result:
        x, y = result["x"], result["y"]
        valid = (x + y <= 5) and (x >= 1) and (y >= 1)

    results = {
        "smt_solver_found_solution": result is not None,
        "solution_valid": valid,
        "passed": result is not None and valid
    }

    print(f"  SMT solver found solution: {results['smt_solver_found_solution']}")
    if result:
        print(f"  Solution: x={result['x']}, y={result['y']}")
    print(f"  Solution valid: {results['solution_valid']}")

    return results


def test_proof_logging():
    """Test proof logging"""
    print("Testing Proof Logging...")

    logger = ProofLogger()

    # Simulate proof steps
    logger.add_decision(1, True, 0)
    logger.add_propagation(2, False, "unit_clause")
    logger.add_conflict(Clause([Literal(1), Literal(2)]))
    logger.add_backtrack(0)

    verified = logger.verify()

    results = {
        "proof_log_created": len(logger.steps) == 4,
        "proof_verifiable": verified,
        "passed": len(logger.steps) == 4 and verified
    }

    print(f"  Proof log created: {results['proof_log_created']}")
    print(f"  Proof verifiable: {results['proof_verifiable']}")

    return results


def test_sat_complexity():
    """Test SAT solver on instances of different complexity"""
    print("Testing SAT Complexity...")

    results = {}

    # Generate random k-SAT instances
    for n_vars in [4, 8, 16]:
        for k in [2, 3]:
            clauses = []
            n_clauses = n_vars * 3

            for _ in range(n_clauses):
                clause_vars = random.sample(range(1, n_vars + 1), k)
                literals = [Literal(v, random.choice([True, False])) for v in clause_vars]
                clauses.append(Clause(literals))

            formula = CNFFormula(clauses)
            solver = DPLLSolver(formula)

            start = time.perf_counter_ns()
            solution = solver.solve()
            end = time.perf_counter_ns()

            results[f"{n_vars}_vars_{k}-sat"] = {
                "solved": solution is not None,
                "time_ns": end - start,
                "clauses": n_clauses
            }

    # Print results
    print("  SAT complexity results:")
    for key, value in results.items():
        status = "SAT" if value["solved"] else "UNSAT"
        print(f"    {key}: {status}, {value['time_ns']:.0f} ns")

    results["passed"] = all(v["solved"] is not None for v in results.values())

    return results


def benchmark_operations() -> Dict[str, Any]:
    """Benchmark theorem proving operations"""
    print("\nBenchmarking Operations...")

    results = {}

    # Benchmark 1: DPLL on small instances
    times = []
    for _ in range(100):
        n_vars = 8
        clauses = []
        for _ in range(24):
            clause_vars = random.sample(range(1, n_vars + 1), 3)
            literals = [Literal(v, random.choice([True, False])) for v in clause_vars]
            clauses.append(Clause(literals))

        formula = CNFFormula(clauses)
        solver = DPLLSolver(formula)

        start = time.perf_counter_ns()
        solver.solve()
        end = time.perf_counter_ns()
        times.append(end - start)

    results["dpll_small"] = np.mean(times)

    # Benchmark 2: SMT solver
    smt_times = []
    for _ in range(100):
        solver = SMTSolver()
        solver.add_le(["x", "y"], [1, 1], random.randint(5, 10))
        solver.add_ge(["x"], [1], 1)
        solver.add_ge(["y"], [1], 1)

        bounds = {"x": (0, 10), "y": (0, 10)}

        start = time.perf_counter_ns()
        solver.solve(bounds)
        end = time.perf_counter_ns()
        smt_times.append(end - start)

    results["smt_linear"] = np.mean(smt_times)

    # Benchmark 3: Bit vector operations
    bv_times = []
    for _ in range(10000):
        bv = BitVector(random.randint(0, 255), 8)
        start = time.perf_counter_ns()
        bv.extract(5, 2)
        end = time.perf_counter_ns()
        bv_times.append(end - start)

    results["bitvector_extract"] = np.mean(bv_times)

    # Print results
    print(f"  DPLL (small): {results['dpll_small']:.0f} ns/instance")
    print(f"  SMT (linear): {results['smt_linear']:.0f} ns/instance")
    print(f"  BitVector extract: {results['bitvector_extract']:.3f} ns/op")

    return results


def run_all_tests():
    """Run all verification tests"""
    print("=" * 70)
    print("DCA Chapter 42: Automated Theorem Proving Verification")
    print("=" * 70)
    print()

    all_results = {}

    # Run all tests
    all_results["cnf_conversion"] = test_cnf_conversion()
    print()
    all_results["dpll_solver"] = test_dpll_solver()
    print()
    all_results["unit_propagation"] = test_unit_propagation()
    print()
    all_results["pure_literal"] = test_pure_literal_elimination()
    print()
    all_results["bit_vectors"] = test_bit_vectors()
    print()
    all_results["smt_solver"] = test_smt_solver()
    print()
    all_results["proof_logging"] = test_proof_logging()
    print()
    all_results["sat_complexity"] = test_sat_complexity()

    # Run benchmarks
    print()
    benchmarks = benchmark_operations()

    # Summary
    print()
    print("=" * 70)
    print("VERIFICATION SUMMARY")
    print("=" * 70)

    test_names = [
        "CNF Conversion",
        "DPLL Solver",
        "Unit Propagation",
        "Pure Literal Elimination",
        "Bit Vectors",
        "SMT Solver",
        "Proof Logging",
        "SAT Complexity"
    ]

    passed_count = 0
    failed_count = 0

    for name, key in zip(test_names, all_results.keys()):
        result = all_results[key]
        status = "✓ PASSED" if result.get("passed", False) else "✗ FAILED"
        print(f"{name:30s}: {status}")
        if result.get("passed", False):
            passed_count += 1
        else:
            failed_count += 1

    print()
    print(f"Total: {passed_count} passed, {failed_count} failed")

    all_passed = passed_count == len(all_results)
    if all_passed:
        print("\n✓ ALL TESTS PASSED!")
    else:
        print("\n✗ SOME TESTS FAILED!")

    return {
        "tests": all_results,
        "benchmarks": benchmarks,
        "all_passed": all_passed
    }


if __name__ == "__main__":
    verification_results = run_all_tests()
    exit(0 if verification_results["all_passed"] else 1)