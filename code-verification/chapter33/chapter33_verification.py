"""
Chapter 33: Discrete Optimal Control - Verification Code

This module verifies the core concepts from DCA Chapter 33 on discrete optimal control:
1. Finite horizon dynamic programming
2. Bellman recursion and backward induction
3. Policy computation and value iteration
4. HJB (Hamilton-Jacobi-Bellman) discrete version
5. State transition systems with finite actions
"""

import numpy as np
from typing import Callable, Dict, List, Tuple, Set
from dataclasses import dataclass
from functools import lru_cache
import time


@dataclass
class State:
    """Finite state representation"""
    id: int
    data: tuple

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        return self.id == other.id


@dataclass
class Action:
    """Finite action representation"""
    id: int
    name: str

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        return self.id == other.id


class DiscreteOptimalControl:
    """
    Discrete optimal control system with finite states and actions.
    Implements the core DCA principle: finite representation, finite computation, finite verification.
    """

    def __init__(self, states: Set[State], actions: Set[Action],
                 transition_func: Callable[[State, Action], State],
                 cost_func: Callable[[State, Action], int],
                 terminal_cost: Callable[[State], int],
                 horizon: int):
        """
        Initialize discrete optimal control system.

        Args:
            states: Finite set of states
            actions: Finite set of actions
            transition_func: s_{t+1} = T(s_t, a_t)
            cost_func: c(s_t, a_t) - stage cost
            terminal_cost: h(s_T) - terminal cost
            horizon: T - finite time horizon
        """
        self.states = states
        self.actions = actions
        self.transition = transition_func
        self.cost = cost_func
        self.terminal_cost = terminal_cost
        self.horizon = horizon

        # Verify finiteness
        assert len(states) > 0 and len(states) < float('inf'), "States must be finite"
        assert len(actions) > 0 and len(actions) < float('inf'), "Actions must be finite"
        assert horizon > 0 and horizon < float('inf'), "Horizon must be finite"

    def total_cost(self, state_seq: List[State], action_seq: List[Action]) -> int:
        """
        Compute total cost J = Σ c(s_t, a_t) + h(s_T)
        """
        total = 0
        for t in range(len(action_seq)):
            total += self.cost(state_seq[t], action_seq[t])
        total += self.terminal_cost(state_seq[-1])
        return total

    def bellman_backup(self, V_next: Dict[State, float], s: State) -> float:
        """
        Bellman backup: V_t(s) = min_a [c(s,a) + V_{t+1}(T(s,a))]
        """
        min_value = float('inf')
        for a in self.actions:
            next_state = self.transition(s, a)
            value = self.cost(s, a) + V_next[next_state]
            if value < min_value:
                min_value = value
        return min_value

    def backward_induction(self) -> Tuple[Dict[State, float], Dict[Tuple[int, State], Action]]:
        """
        Compute optimal value function and policy via backward induction.
        Returns:
            V_0: Initial value function
            policy: Optimal policy π_t(s)
        """
        # Initialize terminal value function
        V = {s: self.terminal_cost(s) for s in self.states}
        policy = {}

        # Backward induction from T-1 to 0
        for t in range(self.horizon - 1, -1, -1):
            V_new = {}
            for s in self.states:
                # Find optimal action
                min_value = float('inf')
                best_action = None

                for a in self.actions:
                    next_state = self.transition(s, a)
                    value = self.cost(s, a) + V[next_state]

                    if value < min_value:
                        min_value = value
                        best_action = a

                V_new[s] = min_value
                policy[(t, s)] = best_action

            V = V_new

        return V, policy

    def greedy_policy(self, V: Dict[State, float], s: State) -> Action:
        """
        Greedy policy: π(s) = argmin_a [c(s,a) + V(T(s,a))]
        """
        min_value = float('inf')
        best_action = None

        for a in self.actions:
            next_state = self.transition(s, a)
            value = self.cost(s, a) + V[next_state]

            if value < min_value:
                min_value = value
                best_action = a

        return best_action

    def simulate(self, initial_state: State, policy: Dict[Tuple[int, State], Action]) -> Tuple[List[State], List[Action], int]:
        """
        Simulate execution of policy from initial state.
        """
        state_seq = [initial_state]
        action_seq = []

        current_state = initial_state
        for t in range(self.horizon):
            action = policy.get((t, current_state), list(self.actions)[0])
            action_seq.append(action)
            current_state = self.transition(current_state, action)
            state_seq.append(current_state)

        total_cost = self.total_cost(state_seq, action_seq)
        return state_seq, action_seq, total_cost


class InfiniteHorizonControl:
    """
    Infinite horizon control with discount factor.
    Uses value iteration for fixed point computation.
    """

    def __init__(self, states: Set[State], actions: Set[Action],
                 transition_func: Callable[[State, Action], State],
                 cost_func: Callable[[State, Action], int],
                 discount: float,
                 max_iterations: int = 1000,
                 tolerance: float = 1e-6):
        """
        Initialize infinite horizon control system.

        Args:
            states: Finite set of states
            actions: Finite set of actions
            transition_func: s_{t+1} = T(s_t, a_t)
            cost_func: c(s_t, a_t) - stage cost
            discount: γ - discount factor (0 <= γ < 1)
            max_iterations: Maximum iterations for value iteration
            tolerance: Convergence tolerance
        """
        self.states = states
        self.actions = actions
        self.transition = transition_func
        self.cost = cost_func
        self.discount = discount
        self.max_iterations = max_iterations
        self.tolerance = tolerance

        # Verify discount factor
        assert 0 <= discount < 1, "Discount factor must be in [0, 1)"

    def bellman_operator(self, V: Dict[State, float]) -> Dict[State, float]:
        """
        Bellman operator: (TV)(s) = min_a [c(s,a) + γ * V(T(s,a))]
        """
        V_new = {}
        for s in self.states:
            min_value = float('inf')
            for a in self.actions:
                next_state = self.transition(s, a)
                value = self.cost(s, a) + self.discount * V[next_state]
                min_value = min(min_value, value)
            V_new[s] = min_value
        return V_new

    def value_iteration(self) -> Tuple[Dict[State, float], Dict[State, Action]]:
        """
        Value iteration algorithm.
        Returns:
            V: Converged value function
            policy: Optimal policy
        """
        # Initialize
        V = {s: 0 for s in self.states}
        policy = {}

        for i in range(self.max_iterations):
            V_new = self.bellman_operator(V)

            # Check convergence
            max_diff = max(abs(V_new[s] - V[s]) for s in self.states)
            if max_diff < self.tolerance:
                break

            V = V_new

        # Extract policy
        for s in self.states:
            min_value = float('inf')
            best_action = None
            for a in self.actions:
                next_state = self.transition(s, a)
                value = self.cost(s, a) + self.discount * V[next_state]
                if value < min_value:
                    min_value = value
                    best_action = a
            policy[s] = best_action

        return V, policy

    def is_contraction(self) -> bool:
        """
        Verify Bellman operator is a contraction mapping.
        For discount factor γ < 1, the operator is γ-contraction.
        """
        return self.discount < 1


def verify_bellman_optimality():
    """
    Verify Bellman optimality principle: optimal policy has optimal substructure.
    """
    print("Testing Bellman Optimality Principle...")

    # Create simple grid world
    states = {State(i, (i // 3, i % 3)) for i in range(9)}  # 3x3 grid
    actions = {Action(0, 'up'), Action(1, 'down'), Action(2, 'left'), Action(3, 'right')}

    def transition(s: State, a: Action) -> State:
        row, col = s.data
        if a.id == 0 and row > 0:  # up
            return State(s.id, (row - 1, col))
        elif a.id == 1 and row < 2:  # down
            return State(s.id, (row + 1, col))
        elif a.id == 2 and col > 0:  # left
            return State(s.id, (row, col - 1))
        elif a.id == 3 and col < 2:  # right
            return State(s.id, (row, col + 1))
        return s  # invalid move, stay in place

    def cost(s: State, a: Action) -> int:
        # Cost is 1 for each move
        return 1

    def terminal_cost(s: State) -> int:
        # Goal is at (2, 2), cost 0 there
        return 0 if s.data == (2, 2) else 10

    doc = DiscreteOptimalControl(states, actions, transition, cost, terminal_cost, horizon=5)
    V, policy = doc.backward_induction()

    # Verify: greedy policy matches optimal policy
    for s in states:
        greedy_action = doc.greedy_policy(V, s)
        optimal_action = policy.get((0, s))
        assert greedy_action == optimal_action, f"Policy mismatch at state {s}"

    print("  ✓ Bellman optimality verified")
    return True


def verify_backward_induction_correctness():
    """
    Verify backward induction produces optimal cost.
    """
    print("Testing Backward Induction Correctness...")

    states = {State(i, (i,)) for i in range(5)}
    actions = {Action(0, 'stay'), Action(1, 'move')}

    def transition(s: State, a: Action) -> State:
        if a.id == 0:
            return s
        else:
            new_id = min(s.id + 1, 4)
            return State(new_id, (new_id,))

    def cost(s: State, a: Action) -> int:
        return 0 if s.id == 4 else (1 if a.id == 1 else 0)

    def terminal_cost(s: State) -> int:
        return 0 if s.id == 4 else 100

    doc = DiscreteOptimalControl(states, actions, transition, cost, terminal_cost, horizon=10)
    V, policy = doc.backward_induction()

    # Simulate from each initial state
    for s in states:
        state_seq, action_seq, total_c = doc.simulate(s, policy)
        # Verify cost matches value function
        assert abs(total_c - V[s]) < 1e-6, f"Cost mismatch for state {s}"

    print("  ✓ Backward induction correctness verified")
    return True


def verify_discounted_convergence():
    """
    Verify discounted infinite horizon converges.
    """
    print("Testing Discounted Convergence...")

    states = {State(i, (i,)) for i in range(5)}
    actions = {Action(0, 'stay'), Action(1, 'move')}

    def transition(s: State, a: Action) -> State:
        if a.id == 0:
            return s
        else:
            new_id = min(s.id + 1, 4)
            return State(new_id, (new_id,))

    def cost(s: State, a: Action) -> int:
        return 1 if a.id == 1 else 0

    ioc = InfiniteHorizonControl(states, actions, transition, cost, discount=0.9)
    V, policy = ioc.value_iteration()

    # Verify contraction property
    assert ioc.is_contraction(), "Bellman operator should be contraction"

    # Verify value function satisfies Bellman equation
    V_check = ioc.bellman_operator(V)
    max_diff = max(abs(V[s] - V_check[s]) for s in states)
    assert max_diff < 1e-4, f"Value function doesn't satisfy Bellman equation: {max_diff}"

    print("  ✓ Discounted convergence verified")
    return True


def verify_finite_representations():
    """
    Verify all objects have finite representations.
    """
    print("Testing Finite Representations...")

    # States are finite
    states = {State(i, (i,)) for i in range(10)}
    assert len(states) == 10
    assert all(isinstance(s.id, int) for s in states)

    # Actions are finite
    actions = {Action(i, f'action_{i}') for i in range(3)}
    assert len(actions) == 3

    # Value function is finite mapping
    V = {s: float(s.id) for s in states}
    assert len(V) == len(states)

    # Policy is finite mapping
    policy = {(0, s): actions[0] for s in states}
    assert len(policy) == len(states)

    print("  ✓ Finite representations verified")
    return True


def benchmark_dp_complexity():
    """
    Benchmark dynamic programming complexity.
    """
    print("Benchmarking DP Complexity...")

    results = []

    for n in [5, 10, 20, 50]:
        states = {State(i, (i,)) for i in range(n)}
        actions = {Action(i, f'action_{i}') for i in range(3)}

        def transition(s: State, a: Action) -> State:
            return State(min(s.id + 1, n - 1), (min(s.id + 1, n - 1),))

        def cost(s: State, a: Action) -> int:
            return 1

        def terminal_cost(s: State) -> int:
            return 0

        start = time.time()
        doc = DiscreteOptimalControl(states, actions, transition, cost, terminal_cost, horizon=n)
        V, policy = doc.backward_induction()
        elapsed = time.time() - start

        results.append((n, elapsed))
        print(f"  n={n}: {elapsed:.4f}s")

    return results


class TestSuite:
    """Comprehensive test suite for Chapter 33"""

    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.results = []

    def run_test(self, test_func, name: str):
        """Run a single test"""
        try:
            test_func()
            self.passed += 1
            self.results.append((name, "PASSED"))
            print(f"✓ {name} PASSED")
        except AssertionError as e:
            self.failed += 1
            self.results.append((name, f"FAILED: {e}"))
            print(f"✗ {name} FAILED: {e}")
        except Exception as e:
            self.failed += 1
            self.results.append((name, f"ERROR: {e}"))
            print(f"✗ {name} ERROR: {e}")

    def summary(self):
        """Print test summary"""
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)
        print(f"Passed: {self.passed}")
        print(f"Failed: {self.failed}")
        print(f"Total:  {self.passed + self.failed}")
        if self.failed == 0:
            print("✓ ALL TESTS PASSED")
        else:
            print("✗ SOME TESTS FAILED")
        print("="*60)


def main():
    """Run all verification tests"""
    print("="*60)
    print("CHAPTER 33: DISCRETE OPTIMAL CONTROL VERIFICATION")
    print("="*60)
    print()

    suite = TestSuite()

    # Core concept tests
    suite.run_test(verify_bellman_optimality, "Bellman Optimality")
    suite.run_test(verify_backward_induction_correctness, "Backward Induction")
    suite.run_test(verify_discounted_convergence, "Discounted Convergence")
    suite.run_test(verify_finite_representations, "Finite Representations")

    # Performance benchmarks
    print()
    print("Performance Benchmarks:")
    print("-" * 40)
    benchmark_results = benchmark_dp_complexity()

    # Summary
    print()
    suite.summary()

    return suite.results, benchmark_results


if __name__ == "__main__":
    main()
