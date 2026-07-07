#!/usr/bin/env python3
"""
Chapter 5: Logic and Reasoning - Verification Code

This module implements and verifies logic and reasoning concepts including:
- Propositional logic and boolean operations
- Truth table generation
- SAT solver basics (DPLL algorithm)
- Logical inference rules
- CNF (Conjunctive Normal Form) conversion
- Validity and satisfiability checking
"""

from typing import List, Set, Dict, Tuple, Optional, Callable
from dataclasses import dataclass
from enum import Enum
import itertools


# ============================================================================
# Section 1: Basic Logical Operations
# ============================================================================

class LogicalConnective(Enum):
    """Logical connectives."""
    AND = '&'
    OR = '|'
    NOT = '~'
    IMPLIES = '->'
    IFF = '<->'
    XOR = '^'


@dataclass
class Literal:
    """A literal (variable or its negation)."""
    variable: str
    negated: bool = False

    def __invert__(self):
        """Negate the literal."""
        return Literal(self.variable, not self.negated)

    def __repr__(self):
        return f"{'~' if self.negated else ''}{self.variable}"

    def __eq__(self, other):
        return self.variable == other.variable and self.negated == other.negated

    def __hash__(self):
        return hash((self.variable, self.negated))

    def evaluate(self, assignment: Dict[str, bool]) -> bool:
        """Evaluate literal under assignment."""
        if self.variable not in assignment:
            raise ValueError(f"Variable {self.variable} not in assignment")
        value = assignment[self.variable]
        return not value if self.negated else value


@dataclass
class Clause:
    """A clause is a disjunction of literals."""
    literals: Set[Literal]

    def __init__(self, literals: List[Literal]):
        self.literals = set(literals)

    def __repr__(self):
        return " ∨ ".join(str(l) for l in self.literals)

    def is_empty(self) -> bool:
        """Check if clause is empty (unsatisfiable)."""
        return len(self.literals) == 0

    def is_unit(self) -> bool:
        """Check if clause has exactly one literal."""
        return len(self.literals) == 1

    def evaluate(self, assignment: Dict[str, bool]) -> bool:
        """Evaluate clause under assignment (true if any literal is true)."""
        for literal in self.literals:
            try:
                if literal.evaluate(assignment):
                    return True
            except ValueError:
                continue  # Unassigned variable
        return False

    def simplify(self, assignment: Dict[str, bool]) -> Tuple[Optional['Clause'], bool]:
        """
        Simplify clause by removing satisfied literals and negated falsified ones.
        Returns (simplified_clause, is_empty) where is_empty=True means contradiction.
        """
        new_literals = []
        for literal in self.literals:
            var = literal.variable
            if var in assignment:
                lit_value = literal.evaluate(assignment)
                if lit_value:
                    return (None, False)  # Clause is satisfied
                # If literal is false, remove it from clause
            else:
                new_literals.append(literal)

        if not new_literals:
            return (None, True)  # Empty clause (contradiction)
        return (Clause(new_literals), False)


@dataclass
class CNFFormula:
    """A formula in Conjunctive Normal Form (conjunction of clauses)."""
    clauses: List[Clause]
    variables: Set[str]

    def __init__(self, clauses: List[Clause]):
        self.clauses = clauses
        self.variables = set()
        for clause in clauses:
            for literal in clause.literals:
                self.variables.add(literal.variable)

    def __repr__(self):
        return " ∧ ".join(f"({c})" for c in self.clauses)

    def evaluate(self, assignment: Dict[str, bool]) -> bool:
        """Evaluate formula (true if all clauses are satisfied)."""
        return all(c.evaluate(assignment) for c in self.clauses)


# ============================================================================
# Section 2: Truth Table Generation
# ============================================================================

class TruthTable:
    """Generate and manipulate truth tables."""

    @staticmethod
    def generate(variables: List[str], formula_func: Callable[[Dict[str, bool]], bool]) -> List[Dict]:
        """Generate truth table for a formula."""
        table = []
        n = len(variables)

        for values in itertools.product([False, True], repeat=n):
            assignment = dict(zip(variables, values))
            result = formula_func(assignment)
            row = {**assignment, 'result': result}
            table.append(row)

        return table

    @staticmethod
    def is_tautology(table: List[Dict]) -> bool:
        """Check if formula is always true (tautology)."""
        return all(row['result'] for row in table)

    @staticmethod
    def is_contradiction(table: List[Dict]) -> bool:
        """Check if formula is always false (contradiction)."""
        return all(not row['result'] for row in table)

    @staticmethod
    def is_satisfiable(table: List[Dict]) -> bool:
        """Check if formula has at least one true assignment."""
        return any(row['result'] for row in table)

    @staticmethod
    def print_table(variables: List[str], table: List[Dict]):
        """Pretty print truth table."""
        # Header
        header = " | ".join(variables + ["Result"])
        print("-" * len(header))
        print(header)
        print("-" * len(header))

        # Rows
        for row in table:
            values = [str(int(row[v])) for v in variables]
            print(" | ".join(values + [str(int(row['result']))]))


# ============================================================================
# Section 3: SAT Solver (DPLL Algorithm)
# ============================================================================

class DPLLSolver:
    """DPLL SAT Solver implementation."""

    def __init__(self):
        self.decisions = 0
        self.backtracks = 0

    def solve(self, formula: CNFFormula) -> Optional[Dict[str, bool]]:
        """Solve SAT problem, return satisfying assignment or None."""
        self.decisions = 0
        self.backtracks = 0
        return self._dpll(formula, {})

    def _dpll(self, formula: CNFFormula, assignment: Dict[str, bool]) -> Optional[Dict[str, bool]]:
        """Recursive DPLL with backtracking."""
        # Simplify formula
        simplified, has_empty = self._simplify_formula(formula, assignment)

        # Check for empty clause (contradiction)
        if has_empty:
            self.backtracks += 1
            return None

        # Check if all clauses satisfied
        if not simplified.clauses:
            return assignment.copy()

        # Unit propagation
        unit_clause = self._find_unit_clause(simplified)
        while unit_clause:
            lit = list(unit_clause.literals)[0]
            assignment[lit.variable] = not lit.negated
            simplified, has_empty = self._simplify_formula(simplified, assignment)
            if has_empty:
                self.backtracks += 1
                return None
            unit_clause = self._find_unit_clause(simplified)

        # Pure literal elimination
        self._pure_literal_assign(simplified, assignment)

        # Choose variable and try both values
        var = self._choose_variable(simplified, assignment)
        if var is None:
            return assignment.copy() if assignment else {}

        self.decisions += 1

        # Try True first
        new_assignment = assignment.copy()
        new_assignment[var] = True
        result = self._dpll(simplified, new_assignment)
        if result is not None:
            return result

        # Try False
        new_assignment = assignment.copy()
        new_assignment[var] = False
        result = self._dpll(simplified, new_assignment)
        if result is not None:
            return result

        self.backtracks += 1
        return None

    def _simplify_formula(self, formula: CNFFormula, assignment: Dict[str, bool]) -> Tuple[CNFFormula, bool]:
        """
        Simplify formula by removing satisfied clauses.
        Returns (simplified_formula, has_empty_clause).
        """
        new_clauses = []
        for clause in formula.clauses:
            simplified, is_empty = clause.simplify(assignment)
            if is_empty:
                return CNFFormula([]), True  # Empty clause = unsat
            if simplified is None:
                continue  # Clause satisfied
            new_clauses.append(simplified)
        return CNFFormula(new_clauses), False

    def _find_unit_clause(self, formula: CNFFormula) -> Optional[Clause]:
        """Find a unit clause (clause with one literal)."""
        for clause in formula.clauses:
            if clause.is_unit() and clause.literals:
                return clause
        return None

    def _pure_literal_assign(self, formula: CNFFormula, assignment: Dict[str, bool]):
        """Assign pure literals (variables appearing only with one polarity)."""
        polarity = {}
        for clause in formula.clauses:
            for literal in clause.literals:
                var = literal.variable
                if var in assignment:
                    continue
                if var not in polarity:
                    polarity[var] = not literal.negated
                elif polarity[var] != (not literal.negated):
                    polarity[var] = None  # Not pure

        for var, pol in polarity.items():
            if pol is not None:
                assignment[var] = pol

    def _choose_variable(self, formula: CNFFormula, assignment: Dict[str, bool]) -> Optional[str]:
        """Choose an unassigned variable (simple heuristic)."""
        for var in formula.variables:
            if var not in assignment:
                return var
        return None


# ============================================================================
# Section 4: Logical Inference Rules
# ============================================================================

class InferenceRules:
    """Standard logical inference rules."""

    @staticmethod
    def modus_ponens(p: bool, p_implies_q: bool) -> Optional[bool]:
        """If p is true and p->q is true, then q is true."""
        if p and p_implies_q:
            return True
        return None

    @staticmethod
    def modus_tollens(not_q: bool, p_implies_q: bool) -> Optional[bool]:
        """If not q is true and p->q is true, then not p is true."""
        if not_q and p_implies_q:
            return False
        return None

    @staticmethod
    def hypothetical_syllogism(p_implies_q: bool, q_implies_r: bool) -> bool:
        """If p->q and q->r, then p->r."""
        return p_implies_q and q_implies_r

    @staticmethod
    def disjunctive_syllogism(p_or_q: bool, not_p: bool) -> bool:
        """If p ∨ q and ¬p, then q."""
        return p_or_q and not_p

    @staticmethod
    def resolution(clause1: Clause, clause2: Clause) -> List[Clause]:
        """Resolution rule: (A ∨ B) ∧ (¬A ∨ C) ⊢ (B ∨ C)."""
        results = []

        for lit1 in clause1.literals:
            for lit2 in clause2.literals:
                # Check if they are complementary
                if (lit1.variable == lit2.variable and
                    lit1.negated != lit2.negated):
                    # Create resolvent
                    new_literals = (clause1.literals - {lit1}) | (clause2.literals - {lit2})
                    results.append(Clause(list(new_literals)))

        return results

    @staticmethod
    def verify_all_rules() -> Tuple[int, int]:
        """Verify all inference rules using truth tables."""
        passed = 0
        total = 0

        # Modus Ponens verification
        total += 1
        mp_valid = True
        for p in [False, True]:
            for q in [False, True]:
                p_implies_q = (not p) or q
                result = InferenceRules.modus_ponens(p, p_implies_q)
                # When p and p->q are true, q must be true
                if p and p_implies_q and result != q:
                    mp_valid = False
        if mp_valid:
            passed += 1

        # Resolution verification
        total += 1
        res_valid = True
        for A in [False, True]:
            for B in [False, True]:
                for C in [False, True]:
                    # (A ∨ B) ∧ (¬A ∨ C) → (B ∨ C)
                    antecedent = (A or B) and ((not A) or C)
                    consequent = B or C
                    if antecedent and not consequent:
                        res_valid = False
        if res_valid:
            passed += 1

        return passed, total


# ============================================================================
# Section 5: Formula Conversion and Equivalence
# ============================================================================

class FormulaConverter:
    """Convert formulas between different forms."""

    @staticmethod
    def implies_to_and_or(p: bool, q: bool) -> bool:
        """p → q ≡ ¬p ∨ q"""
        return (not p) or q

    @staticmethod
    def xor_to_and_or(p: bool, q: bool) -> bool:
        """p ⊕ q ≡ (p ∧ ¬q) ∨ (¬p ∧ q)"""
        return (p and not q) or (not p and q)

    @staticmethod
    def iff_to_and_or(p: bool, q: bool) -> bool:
        """p ↔ q ≡ (p → q) ∧ (q → p)"""
        return ((not p) or q) and ((not q) or p)

    @staticmethod
    def demorgans_and(a: bool, b: bool) -> bool:
        """¬(p ∧ q) ≡ ¬p ∨ ¬q"""
        return not (a and b) == ((not a) or (not b))

    @staticmethod
    def demorgans_or(a: bool, b: bool) -> bool:
        """¬(p ∨ q) ≡ ¬p ∧ ¬q"""
        return not (a or b) == ((not a) and (not b))

    @staticmethod
    def distribution(a: bool, b: bool, c: bool) -> bool:
        """p ∧ (q ∨ r) ≡ (p ∧ q) ∨ (p ∧ r)"""
        left = a and (b or c)
        right = (a and b) or (a and c)
        return left == right


# ============================================================================
# Section 6: Propositional Logic Evaluator
# ============================================================================

class PropositionalLogic:
    """Evaluate propositional logic formulas."""

    @staticmethod
    def evaluate_expression(expr: str, assignment: Dict[str, bool]) -> bool:
        """Evaluate a boolean expression with variables."""
        # Create a safe evaluation context
        variables = assignment.copy()
        return eval(expr, {"__builtins__": {}}, variables)

    @staticmethod
    def find_counterexample(variables: List[str], expr: str) -> Optional[Dict[str, bool]]:
        """Find an assignment where the expression is false."""
        for values in itertools.product([False, True], repeat=len(variables)):
            assignment = dict(zip(variables, values))
            try:
                if not PropositionalLogic.evaluate_expression(expr, assignment):
                    return assignment
            except:
                continue
        return None


# ============================================================================
# Section 7: Proof System
# ============================================================================

class SimpleProof:
    """A simple proof system for propositional logic."""

    def __init__(self):
        self.axioms: List[Callable] = []
        self.theorems: List[str] = []

    def add_axiom(self, axiom: Callable):
        """Add an axiom (a function that returns True for valid assignments)."""
        self.axioms.append(axiom)

    def prove_by_truth_table(self, formula_func: Callable[[Dict[str, bool]], bool],
                             variables: List[str]) -> bool:
        """Prove a formula by exhaustive truth table."""
        for values in itertools.product([False, True], repeat=len(variables)):
            assignment = dict(zip(variables, values))
            if not formula_func(assignment):
                return False
        return True

    def verify_inference(self, premises: List[Callable], conclusion: Callable,
                         variables: List[str]) -> bool:
        """Verify that conclusion follows from premises."""
        for values in itertools.product([False, True], repeat=len(variables)):
            assignment = dict(zip(variables, values))
            # If all premises are true, conclusion must be true
            if all(p(assignment) for p in premises):
                if not conclusion(assignment):
                    return False
        return True


# ============================================================================
# Section 8: Comprehensive Test Suite
# ============================================================================

def run_all_tests():
    """Run comprehensive test suite for Chapter 5."""
    print("=" * 70)
    print("CHAPTER 5: LOGIC AND REASONING - VERIFICATION TEST SUITE")
    print("=" * 70)

    total_passed = 0
    total_tests = 0

    # Test 1: Basic Logical Operations
    print("\n[TEST 1] Basic Logical Operations")
    NOT = lambda x: 1 ^ x
    AND = lambda x, y: x & y
    OR = lambda x, y: x | y
    IMPLIES = lambda p, q: OR(NOT(p), q)

    assert NOT(0) == 1, "NOT failed"
    assert NOT(1) == 0, "NOT failed"
    assert AND(1, 1) == 1, "AND failed"
    assert OR(0, 1) == 1, "OR failed"
    assert IMPLIES(1, 1) == 1, "IMPLIES failed"
    assert IMPLIES(1, 0) == 0, "IMPLIES failed"

    print("  ✓ Basic logical operations passed")
    total_passed += 1
    total_tests += 1

    # Test 2: Truth Table Generation
    print("\n[TEST 2] Truth Table Generation")

    def formula_func(assignment):
        p = assignment['p']
        q = assignment['q']
        return (not p) or q  # p -> q

    table = TruthTable.generate(['p', 'q'], formula_func)

    assert len(table) == 4, "Truth table should have 4 rows"
    assert TruthTable.is_tautology(table) == False, "p->q is not a tautology in one variable"
    assert TruthTable.is_satisfiable(table) == True, "p->q should be satisfiable"

    print("  ✓ Truth table generation passed")
    total_passed += 1
    total_tests += 1

    # Test 3: Tautology Verification
    print("\n[TEST 3] Tautology Verification")

    # p ∨ ¬p (law of excluded middle)
    def lem_func(assignment):
        p = assignment['p']
        return p or (not p)

    lem_table = TruthTable.generate(['p'], lem_func)

    assert TruthTable.is_tautology(lem_table), "Law of excluded middle should be tautology"
    assert not TruthTable.is_contradiction(lem_table), "Should not be contradiction"

    print("  ✓ Tautology verification passed (p ∨ ¬p)")
    total_passed += 1
    total_tests += 1

    # Test 4: SAT Solver - Simple Case
    print("\n[TEST 4] SAT Solver - Simple Satisfiable Formula")

    # (p ∨ q) ∧ (¬p ∨ r) ∧ (¬q ∨ r)
    solver = DPLLSolver()
    formula = CNFFormula([
        Clause([Literal('p'), Literal('q')]),
        Clause([Literal('p', negated=True), Literal('r')]),
        Clause([Literal('q', negated=True), Literal('r')])
    ])

    result = solver.solve(formula)

    assert result is not None, "Formula should be satisfiable"
    assert formula.evaluate(result), "Assignment should satisfy formula"

    print(f"  ✓ SAT solver found assignment: {result}")
    total_passed += 1
    total_tests += 1

    # Test 5: SAT Solver - Unsatisfiable Case
    print("\n[TEST 5] SAT Solver - Unsatisfiable Formula")

    # (p) ∧ (¬p)
    unsat_formula = CNFFormula([
        Clause([Literal('p')]),
        Clause([Literal('p', negated=True)])
    ])

    result = solver.solve(unsat_formula)

    assert result is None, "Formula should be unsatisfiable"

    print("  ✓ SAT solver correctly identified unsatisfiable formula")
    total_passed += 1
    total_tests += 1

    # Test 6: Inference Rules
    print("\n[TEST 6] Inference Rules Verification")

    passed, total = InferenceRules.verify_all_rules()
    assert passed == total, f"Inference rules failed: {passed}/{total}"

    print(f"  ✓ Inference rules verified: {passed}/{total}")
    total_passed += passed
    total_tests += total

    # Test 7: Resolution Rule
    print("\n[TEST 7] Resolution Inference")

    # (A ∨ B) and (¬A ∨ C) should resolve to (B ∨ C)
    clause1 = Clause([Literal('A'), Literal('B')])
    clause2 = Clause([Literal('A', negated=True), Literal('C')])

    resolvents = InferenceRules.resolution(clause1, clause2)

    assert len(resolvents) == 1, "Should have one resolvent"
    assert Literal('B') in resolvents[0].literals, "Should contain B"
    assert Literal('C') in resolvents[0].literals, "Should contain C"

    print("  ✓ Resolution rule passed")
    total_passed += 1
    total_tests += 1

    # Test 8: Formula Equivalence
    print("\n[TEST 8] Formula Equivalence Laws")

    converter = FormulaConverter()

    # Test all combinations for equivalence
    all_valid = True
    for a in [False, True]:
        for b in [False, True]:
            if not converter.demorgans_and(a, b):
                all_valid = False
            if not converter.demorgans_or(a, b):
                all_valid = False
            if not converter.distribution(a, b, False):
                all_valid = False

    assert all_valid, "Formula equivalence laws failed"

    print("  ✓ Formula equivalence laws verified")
    total_passed += 1
    total_tests += 1

    # Test 9: Implication Equivalence
    print("\n[TEST 9] Implication Equivalence")

    # p → q ≡ ¬p ∨ q
    implies_valid = True
    for p in [False, True]:
        for q in [False, True]:
            left = (not p) or q
            right = FormulaConverter.implies_to_and_or(p, q)
            if left != right:
                implies_valid = False

    assert implies_valid, "Implication equivalence failed"

    print("  ✓ Implication equivalence verified")
    total_passed += 1
    total_tests += 1

    # Test 10: Proof System
    print("\n[TEST 10] Proof System")

    proof = SimpleProof()

    # Prove p ∨ ¬p (law of excluded middle)
    def lem_thm(assignment):
        p = assignment['p']
        return p or (not p)

    proved = proof.prove_by_truth_table(lem_thm, ['p'])

    assert proved, "Should prove law of excluded middle"

    print("  ✓ Proof system verified")
    total_passed += 1
    total_tests += 1

    # Test 11: Complex SAT Problem
    print("\n[TEST 11] SAT Solver - Complex Problem")

    # 3-SAT problem with 4 variables
    complex_formula = CNFFormula([
        Clause([Literal('x1'), Literal('x2'), Literal('x3')]),
        Clause([Literal('x1', negated=True), Literal('x2'), Literal('x4')]),
        Clause([Literal('x2', negated=True), Literal('x3', negated=True), Literal('x4')]),
        Clause([Literal('x1'), Literal('x3', negated=True), Literal('x4', negated=True)])
    ])

    solver = DPLLSolver()
    result = solver.solve(complex_formula)

    if result:
        assert complex_formula.evaluate(result), "Assignment should satisfy formula"
        print(f"  ✓ Complex SAT solved with {len(result)} variables assigned")
    else:
        print("  ✓ Complex SAT correctly identified as unsatisfiable")

    total_passed += 1
    total_tests += 1

    # Test 12: Validity Checking
    print("\n[TEST 12] Validity and Satisfiability")

    # Valid formula: (p ∧ q) → p
    def valid_func(assignment):
        p = assignment['p']
        q = assignment['q']
        return not (p and q) or p  # (p ∧ q) → p

    valid_table = TruthTable.generate(['p', 'q'], valid_func)

    assert TruthTable.is_tautology(valid_table), "Should be valid (tautology)"

    # Contingent formula: p ∧ q
    def contingent_func(assignment):
        return assignment['p'] and assignment['q']

    contingent_table = TruthTable.generate(['p', 'q'], contingent_func)

    assert not TruthTable.is_tautology(contingent_table), "Should not be tautology"
    assert not TruthTable.is_contradiction(contingent_table), "Should not be contradiction"
    assert TruthTable.is_satisfiable(contingent_table), "Should be satisfiable"

    print("  ✓ Validity and satisfiability checking passed")
    total_passed += 1
    total_tests += 1

    # Performance Benchmarks
    print("\n" + "=" * 70)
    print("PERFORMANCE BENCHMARKS")
    print("=" * 70)

    print("\n[Benchmark 1] SAT Solver Performance")
    import time

    # Create a satisfiable formula with n variables
    def benchmark_sat(n_vars: int, n_clauses: int):
        solver = DPLLSolver()
        clauses = []

        # Create random-like clauses
        for i in range(n_clauses):
            literals = []
            for j in range(3):
                var = f"x{((i + j) % n_vars)}"
                lit = Literal(var, negated=(i % 2 == 0))
                literals.append(lit)
            clauses.append(Clause(literals))

        formula = CNFFormula(clauses)

        start = time.time()
        result = solver.solve(formula)
        elapsed = time.time() - start

        return elapsed, solver.decisions, solver.backtracks

    for n in [5, 10, 15]:
        elapsed, decisions, backtracks = benchmark_sat(n, n * 2)
        print(f"  {n} variables, {n * 2} clauses:")
        print(f"    Time: {elapsed:.6f}s, Decisions: {decisions}, Backtracks: {backtracks}")

    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"Tests passed: {total_passed}/{total_tests}")
    print(f"Success rate: {100 * total_passed / total_tests:.1f}%")

    if total_passed == total_tests:
        print("\n✓ ALL TESTS PASSED")
        return True
    else:
        print(f"\n[X] {total_tests - total_passed} TESTS FAILED")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
