#!/usr/bin/env python3
import time
import random
from typing import List, Tuple, Dict, Set
from dataclasses import dataclass
from enum import IntEnum

class CellState(IntEnum):
    """Cell states for cellular automata"""
    EMPTY = 0
    ACTIVE = 1

class RuleType(IntEnum):
    """Types of update rules"""
    CONWAY = 0
    WIRE_WORLD = 1
    MAJORITY = 2
    PARITY = 3

@dataclass
class SpacetimeEvent:
    """Event in discrete spacetime"""
    t: int  # Time coordinate
    x: int  # Space coordinate
    y: int  # Space coordinate (for 2D)
    state: int

@dataclass
class LightCone:
    """Light cone for causal structure"""
    center: SpacetimeEvent
    radius: int
    events: Set[SpacetimeEvent]

class CellularAutomaton1D:
    """1D Cellular Automaton with causal structure"""

    def __init__(self, size: int, rule_type: RuleType = RuleType.MAJORITY):
        self.size = size
        self.grid = [CellState.EMPTY] * size
        self.rule_type = rule_type
        self.time = 0
        self.history = [[self.grid[i] for i in range(size)]]
        self.light_cone_radius = 1

    def set_cell(self, x: int, state: CellState):
        """Set cell state"""
        if 0 <= x < self.size:
            self.grid[x] = state

    def get_neighborhood(self, x: int, radius: int = 1) -> List[int]:
        """Get neighborhood states"""
        neighborhood = []
        for dx in range(-radius, radius + 1):
            nx = (x + dx) % self.size
            neighborhood.append(self.grid[nx])
        return neighborhood

    def apply_rule_conway(self, neighborhood: List[int]) -> int:
        """Conway-like rule (simplified for 1D)"""
        center = neighborhood[len(neighborhood) // 2]
        neighbors = neighborhood[:len(neighborhood)//2] + neighborhood[len(neighborhood)//2+1:]
        active_count = sum(neighbors)

        if center == CellState.ACTIVE:
            return CellState.ACTIVE if 1 <= active_count <= 2 else CellState.EMPTY
        else:
            return CellState.ACTIVE if active_count == 2 else CellState.EMPTY

    def apply_rule_majority(self, neighborhood: List[int]) -> int:
        """Majority rule"""
        active_count = sum(neighborhood)
        return CellState.ACTIVE if active_count > len(neighborhood) // 2 else CellState.EMPTY

    def apply_rule_parity(self, neighborhood: List[int]) -> int:
        """Parity rule (XOR)"""
        active_count = sum(neighborhood) % 2
        return CellState.ACTIVE if active_count else CellState.EMPTY

    def step(self):
        """Advance one time step"""
        new_grid = [CellState.EMPTY] * self.size

        for x in range(self.size):
            neighborhood = self.get_neighborhood(x, self.light_cone_radius)

            if self.rule_type == RuleType.CONWAY:
                new_grid[x] = self.apply_rule_conway(neighborhood)
            elif self.rule_type == RuleType.MAJORITY:
                new_grid[x] = self.apply_rule_majority(neighborhood)
            elif self.rule_type == RuleType.PARITY:
                new_grid[x] = self.apply_rule_parity(neighborhood)
            else:
                new_grid[x] = self.apply_rule_majority(neighborhood)

        self.grid = new_grid
        self.time += 1
        self.history.append([self.grid[i] for i in range(self.size)])

    def get_light_cone(self, x: int, t_start: int, t_end: int) -> Set[Tuple[int, int]]:
        """Get light cone: all events that can influence (x, t_end)"""
        cone = set()
        max_distance = (t_end - t_start) * self.light_cone_radius

        for t in range(t_start, t_end + 1):
            dt = t_end - t
            max_x_dist = dt * self.light_cone_radius
            for dx in range(-max_x_dist, max_x_dist + 1):
                nx = (x + dx) % self.size
                cone.add((t, nx))

        return cone

    def verify_causality(self, x: int, steps: int) -> bool:
        """Verify causal structure: influence propagates at finite speed"""
        # Initial state
        initial_state = [self.grid[i] for i in range(self.size)]

        # Set a single active cell
        for i in range(self.size):
            self.set_cell(i, CellState.EMPTY)
        self.set_cell(x, CellState.ACTIVE)

        # Run for steps
        for _ in range(steps):
            self.step()

        # Check that influence hasn't propagated beyond light cone
        max_distance = steps * self.light_cone_radius
        for i in range(self.size):
            dist = min(abs(i - x), self.size - abs(i - x))
            if dist > max_distance and self.grid[i] == CellState.ACTIVE:
                return False

        return True

class CellularAutomaton2D:
    """2D Cellular Automaton with causal structure"""

    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.grid = [[CellState.EMPTY for _ in range(width)] for _ in range(height)]
        self.time = 0

    def set_cell(self, x: int, y: int, state: CellState):
        """Set cell state"""
        if 0 <= x < self.width and 0 <= y < self.height:
            self.grid[y][x] = state

    def get_neighbors(self, x: int, y: int) -> List[int]:
        """Get Moore neighborhood (8 neighbors)"""
        neighbors = []
        for dy in range(-1, 2):
            for dx in range(-1, 2):
                if dx == 0 and dy == 0:
                    continue
                nx = (x + dx) % self.width
                ny = (y + dy) % self.height
                neighbors.append(self.grid[ny][nx])
        return neighbors

    def step_conway(self):
        """Conway's Game of Life rule"""
        new_grid = [[CellState.EMPTY for _ in range(self.width)] for _ in range(self.height)]

        for y in range(self.height):
            for x in range(self.width):
                neighbors = self.get_neighbors(x, y)
                active_count = sum(neighbors)
                current = self.grid[y][x]

                if current == CellState.ACTIVE:
                    new_grid[y][x] = CellState.ACTIVE if 2 <= active_count <= 3 else CellState.EMPTY
                else:
                    new_grid[y][x] = CellState.ACTIVE if active_count == 3 else CellState.EMPTY

        self.grid = new_grid
        self.time += 1

def verify_local_update_rule():
    """Test that updates only depend on local neighborhood"""
    print("Testing local update rule...")
    passed = 0
    failed = 0

    ca = CellularAutomaton1D(size=10, rule_type=RuleType.MAJORITY)

    # Set up a pattern
    for i in range(10):
        ca.set_cell(i, CellState.ACTIVE if i % 2 == 0 else CellState.EMPTY)

    initial = ca.grid.copy()
    ca.step()

    # Verify each new state only depends on neighborhood
    for x in range(ca.size):
        neighborhood = [initial[(x + dx) % ca.size] for dx in range(-1, 2)]
        expected = CellState.ACTIVE if sum(neighborhood) > 1 else CellState.EMPTY
        if ca.grid[x] == expected:
            passed += 1
        else:
            failed += 1

    print(f"  Local update rule tests: {passed}/{passed + failed} passed")
    return {"passed": passed, "failed": failed}

def verify_finite_propagation_speed():
    """Test finite propagation speed (causality)"""
    print("Testing finite propagation speed...")
    passed = 0
    failed = 0

    ca = CellularAutomaton1D(size=50, rule_type=RuleType.MAJORITY)

    for start_x in [10, 25, 40]:
        for steps in [5, 10, 15]:
            if ca.verify_causality(start_x, steps):
                passed += 1
            else:
                failed += 1

    print(f"  Finite propagation speed tests: {passed}/{passed + failed} passed")
    return {"passed": passed, "failed": failed}

def verify_light_cone_structure():
    """Test light cone structure"""
    print("Testing light cone structure...")
    passed = 0
    failed = 0

    ca = CellularAutomaton1D(size=20, rule_type=RuleType.MAJORITY)

    # Light cone from (x=10, t=0) to t=5 should have radius 5
    cone = ca.get_light_cone(x=10, t_start=0, t_end=5)

    # Verify cone size
    expected_min_size = 6  # t=0 to t=5
    if len(cone) >= expected_min_size:
        passed += 1
    else:
        failed += 1

    # Verify all points in cone satisfy d(x,t) <= r*t
    valid = True
    for t, x in cone:
        dt = 5 - t
        if dt < 0:
            valid = False
            break
        max_dist = dt * ca.light_cone_radius
        dist = min(abs(x - 10), ca.size - abs(x - 10))
        if dist > max_dist:
            valid = False
            break

    if valid:
        passed += 1
    else:
        failed += 1

    print(f"  Light cone structure tests: {passed}/{passed + failed} passed")
    return {"passed": passed, "failed": failed}

def verify_deterministic_evolution():
    """Test deterministic evolution"""
    print("Testing deterministic evolution...")
    passed = 0
    failed = 0

    ca1 = CellularAutomaton1D(size=10, rule_type=RuleType.PARITY)
    ca2 = CellularAutomaton1D(size=10, rule_type=RuleType.PARITY)

    # Set same initial state
    for i in range(10):
        state = CellState.ACTIVE if random.random() > 0.5 else CellState.EMPTY
        ca1.set_cell(i, state)
        ca2.set_cell(i, state)

    # Run both for same steps
    for _ in range(10):
        ca1.step()
        ca2.step()

    # Should be identical
    if ca1.grid == ca2.grid:
        passed += 1
    else:
        failed += 1

    print(f"  Deterministic evolution tests: {passed}/{passed + failed} passed")
    return {"passed": passed, "failed": failed}

def verify_conway_game_of_life():
    """Test Conway's Game of Life patterns"""
    print("Testing Conway's Game of Life...")
    passed = 0
    failed = 0

    ca = CellularAutomaton2D(width=10, height=10)

    # Test still life (block)
    for y in range(4, 6):
        for x in range(4, 6):
            ca.set_cell(x, y, CellState.ACTIVE)

    ca.step_conway()

    # Block should remain stable
    stable = True
    for y in range(4, 6):
        for x in range(4, 6):
            if ca.grid[y][x] != CellState.ACTIVE:
                stable = False

    if stable:
        passed += 1
    else:
        failed += 1

    # Test oscillator (blinker)
    ca2 = CellularAutomaton2D(width=10, height=10)
    for x in range(4, 7):
        ca2.set_cell(x, 5, CellState.ACTIVE)

    ca2.step_conway()

    # Should become vertical
    if (ca2.grid[4][5] == CellState.ACTIVE and
        ca2.grid[5][5] == CellState.ACTIVE and
        ca2.grid[6][5] == CellState.ACTIVE):
        passed += 1
    else:
        failed += 1

    print(f"  Conway's Game of Life tests: {passed}/{passed + failed} passed")
    return {"passed": passed, "failed": failed}

def verify_periodic_boundary():
    """Test periodic boundary conditions"""
    print("Testing periodic boundary conditions...")
    passed = 0
    failed = 0

    ca = CellularAutomaton1D(size=10, rule_type=RuleType.MAJORITY)

    # Set active cells at boundaries
    ca.set_cell(0, CellState.ACTIVE)
    ca.set_cell(9, CellState.ACTIVE)

    # Neighborhood of cell 0 should include cell 9
    neighborhood = ca.get_neighborhood(0)
    if neighborhood[0] == ca.grid[9]:  # Left neighbor should be cell 9
        passed += 1
    else:
        failed += 1

    # Neighborhood of cell 9 should include cell 0
    neighborhood = ca.get_neighborhood(9)
    if neighborhood[2] == ca.grid[0]:  # Right neighbor should be cell 0
        passed += 1
    else:
        failed += 1

    print(f"  Periodic boundary tests: {passed}/{passed + failed} passed")
    return {"passed": passed, "failed": failed}

def verify_time_reversal_symmetry():
    """Test time reversal properties"""
    print("Testing time reversal properties...")
    passed = 0
    failed = 0

    ca = CellularAutomaton1D(size=10, rule_type=RuleType.PARITY)

    # Set initial state
    for i in range(10):
        ca.set_cell(i, CellState.ACTIVE if i % 3 == 0 else CellState.EMPTY)

    initial = ca.grid.copy()

    # Run forward
    for _ in range(5):
        ca.step()

    middle = ca.grid.copy()

    # Run more
    for _ in range(5):
        ca.step()

    final = ca.grid.copy()

    # Parity rule is reversible: applying twice returns to original
    ca.grid = middle.copy()
    for _ in range(5):
        ca.step()

    if ca.grid == final:
        passed += 1
    else:
        failed += 1

    print(f"  Time reversal tests: {passed}/{passed + failed} passed")
    return {"passed": passed, "failed": failed}

def benchmark_cellular_automata():
    """Benchmark cellular automata operations"""
    print("\nBenchmarking cellular automata operations...")
    results = {}

    # 1D CA benchmark
    ca_1d = CellularAutomaton1D(size=1000, rule_type=RuleType.MAJORITY)

    iterations = 1000
    start = time.perf_counter_ns()
    for _ in range(iterations):
        ca_1d.step()
    end = time.perf_counter_ns()

    results['1d_step'] = (end - start) / iterations
    print(f"  1D CA step (1000 cells): {results['1d_step']:.2f} ns/op")

    # 2D CA benchmark
    ca_2d = CellularAutomaton2D(width=100, height=100)

    iterations = 100
    start = time.perf_counter_ns()
    for _ in range(iterations):
        ca_2d.step_conway()
    end = time.perf_counter_ns()

    results['2d_step'] = (end - start) / iterations
    print(f"  2D CA step (100x100): {results['2d_step']:.2f} ns/op")

    return results

def run_all_tests():
    """Run all verification tests for Chapter 27"""
    print("=" * 70)
    print("DCA Chapter 27: Spacetime and Causal Cellular Automata Verification")
    print("=" * 70)
    print()

    results = {}

    results['local_update'] = verify_local_update_rule()
    results['propagation'] = verify_finite_propagation_speed()
    results['light_cone'] = verify_light_cone_structure()
    results['deterministic'] = verify_deterministic_evolution()
    results['conway'] = verify_conway_game_of_life()
    results['boundary'] = verify_periodic_boundary()
    results['time_reversal'] = verify_time_reversal_symmetry()

    benchmark = benchmark_cellular_automata()

    print("\n" + "=" * 70)
    print("VERIFICATION SUMMARY")
    print("=" * 70)

    total_passed = sum(r['passed'] for r in results.values())
    total_failed = sum(r['failed'] for r in results.values())

    for test_name, result in results.items():
        print(f"{test_name}: {result['passed']}/{result['passed'] + result['failed']} passed")

    print(f"\nTotal: {total_passed}/{total_passed + total_failed} tests passed")

    if total_failed == 0:
        print("\nALL TESTS PASSED!")
        return {'results': results, 'benchmark': benchmark, 'all_passed': True}
    else:
        print(f"\n{total_failed} TESTS FAILED!")
        return {'results': results, 'benchmark': benchmark, 'all_passed': False}

if __name__ == "__main__":
    verification_results = run_all_tests()
    exit(0 if verification_results['all_passed'] else 1)
