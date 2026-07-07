#!/usr/bin/env python3
"""
Chapter 4: Discrete Geometry - Verification Code

This module implements and verifies discrete geometry concepts including:
- Discrete points and vectors
- Distance metrics (Manhattan, Hamming, graph distance)
- Discrete lines and circles
- Polygon operations
- Geometric intersections
- Grid-based algorithms
"""

import math
from typing import List, Tuple, Set, Optional, Dict
from dataclasses import dataclass
from collections import deque
import heapq


# ============================================================================
# Section 1: Basic Geometric Primitives
# ============================================================================

@dataclass
class Point:
    """A discrete point in Z^d space."""
    coords: Tuple[int, ...]

    def __init__(self, *coords: int):
        self.coords = tuple(coords)
        self.dimension = len(coords)

    def __repr__(self):
        return f"Point{self.coords}"

    def __eq__(self, other):
        return self.coords == other.coords

    def __lt__(self, other):
        """Less than for heap comparison."""
        return self.coords < other.coords

    def __hash__(self):
        return hash(self.coords)

    def __add__(self, other):
        """Vector addition."""
        if self.dimension != other.dimension:
            raise ValueError("Dimension mismatch")
        return Point(*(a + b for a, b in zip(self.coords, other.coords)))

    def __sub__(self, other):
        """Vector subtraction."""
        if self.dimension != other.dimension:
            raise ValueError("Dimension mismatch")
        return Point(*(a - b for a, b in zip(self.coords, other.coords)))

    def __mul__(self, scalar):
        """Scalar multiplication."""
        return Point(*(int(c * scalar) for c in self.coords))

    def manhattan_distance(self, other: 'Point') -> int:
        """Compute Manhattan (L1) distance between two points."""
        if self.dimension != other.dimension:
            raise ValueError("Dimension mismatch")
        return sum(abs(a - b) for a, b in zip(self.coords, other.coords))

    def chebyshev_distance(self, other: 'Point') -> int:
        """Compute Chebyshev (L-infinity) distance."""
        if self.dimension != other.dimension:
            raise ValueError("Dimension mismatch")
        return max(abs(a - b) for a, b in zip(self.coords, other.coords))

    def squared_euclidean_distance(self, other: 'Point') -> int:
        """Compute squared Euclidean distance (avoids irrational numbers)."""
        if self.dimension != other.dimension:
            raise ValueError("Dimension mismatch")
        return sum((a - b) ** 2 for a, b in zip(self.coords, other.coords))


class DiscreteLine:
    """A discrete line represented by point and direction."""

    def __init__(self, start: Point, direction: Point):
        self.start = start
        self.direction = direction

    def get_point(self, t: int) -> Point:
        """Get point at parameter t (integer)."""
        return self.start + self.direction * t

    def get_points(self, t_min: int, t_max: int) -> List[Point]:
        """Get all points in parameter range."""
        return [self.get_point(t) for t in range(t_min, t_max + 1)]

    def is_between(self, p: Point) -> bool:
        """Check if point p lies on the line segment between integer points."""
        rel = p - self.start
        # Check if relative position is parallel to direction
        if self.direction.dimension == 2:
            dx, dy = self.direction.coords
            px, py = rel.coords
            if dx == 0:
                return px == 0
            if dy == 0:
                return py == 0
            return px * dy == py * dx
        return False


class DiscreteCircle:
    """A discrete circle using Manhattan or squared Euclidean metric."""

    def __init__(self, center: Point, radius: int, metric: str = 'manhattan'):
        self.center = center
        self.radius = radius
        self.metric = metric

    def contains(self, p: Point) -> bool:
        """Check if point is on the circle boundary."""
        if self.metric == 'manhattan':
            return self.center.manhattan_distance(p) == self.radius
        elif self.metric == 'euclidean_sq':
            return self.center.squared_euclidean_distance(p) == self.radius ** 2
        return False

    def boundary_points(self) -> Set[Point]:
        """Get all points on the circle boundary."""
        points = set()
        # Search in bounding box
        d = self.center.dimension
        if d == 2 and self.metric == 'manhattan':
            cx, cy = self.center.coords
            for r in range(self.radius + 1):
                s = self.radius - r
                points.add(Point(cx + r, cy + s))
                points.add(Point(cx + r, cy - s))
                points.add(Point(cx - r, cy + s))
                points.add(Point(cx - r, cy - s))
        return points

    def interior_points(self) -> Set[Point]:
        """Get all points strictly inside the circle."""
        points = set()
        d = self.center.dimension
        if d == 2 and self.metric == 'manhattan':
            cx, cy = self.center.coords
            for dx in range(-self.radius, self.radius + 1):
                for dy in range(-self.radius, self.radius + 1):
                    if abs(dx) + abs(dy) < self.radius:
                        points.add(Point(cx + dx, cy + dy))
        return points


# ============================================================================
# Section 2: Distance Metrics and Properties
# ============================================================================

class HammingDistance:
    """Hamming distance for binary vectors."""

    @staticmethod
    def distance(x: int, y: int, bits: int) -> int:
        """Compute Hamming distance between two integers."""
        return bin(x ^ y & ((1 << bits) - 1)).count('1')

    @staticmethod
    def distance_bytes(x: bytes, y: bytes) -> int:
        """Compute Hamming distance between two byte sequences."""
        if len(x) != len(y):
            raise ValueError("Length mismatch")
        return sum((xb ^ yb).bit_count() for xb, yb in zip(x, y))


class GraphDistance:
    """Graph distance computation."""

    def __init__(self, adjacency: Dict[int, Set[int]]):
        self.adjacency = adjacency

    def distance(self, start: int, end: int) -> Optional[int]:
        """Compute shortest path distance using BFS."""
        if start not in self.adjacency or end not in self.adjacency:
            return None

        queue = deque([(start, 0)])
        visited = {start}

        while queue:
            node, dist = queue.popleft()
            if node == end:
                return dist

            for neighbor in self.adjacency.get(node, set()):
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, dist + 1))

        return None  # No path exists

    def all_distances(self, start: int) -> Dict[int, int]:
        """Compute distances from start to all reachable nodes."""
        distances = {start: 0}
        queue = deque([start])

        while queue:
            node = queue.popleft()
            for neighbor in self.adjacency.get(node, set()):
                if neighbor not in distances:
                    distances[neighbor] = distances[node] + 1
                    queue.append(neighbor)

        return distances


# ============================================================================
# Section 3: Metric Axioms Verification
# ============================================================================

def verify_manhattan_metric_axioms():
    """Verify that Manhattan distance satisfies metric axioms."""
    print("Testing Manhattan Distance Metric Axioms...")

    test_points = [
        Point(0, 0), Point(1, 2), Point(-1, 3),
        Point(5, 5), Point(-3, -2), Point(0, 7)
    ]

    tests_passed = 0
    tests_total = 0

    # Axiom 1: Non-negativity
    tests_total += 1
    all_non_negative = True
    for p in test_points:
        for q in test_points:
            if p.manhattan_distance(q) < 0:
                all_non_negative = False
                break
    if all_non_negative:
        tests_passed += 1
        print("  ✓ Non-negativity holds")
    else:
        print("  ✗ Non-negativity failed")

    # Axiom 2: Identity of indiscernibles
    tests_total += 1
    identity_holds = True
    for p in test_points:
        if p.manhattan_distance(p) != 0:
            identity_holds = False
            break
        for q in test_points:
            if p != q and p.manhattan_distance(q) == 0:
                identity_holds = False
                break
    if identity_holds:
        tests_passed += 1
        print("  ✓ Identity of indiscernibles holds")
    else:
        print("  ✗ Identity of indiscernibles failed")

    # Axiom 3: Symmetry
    tests_total += 1
    symmetry_holds = True
    for p in test_points:
        for q in test_points:
            if p.manhattan_distance(q) != q.manhattan_distance(p):
                symmetry_holds = False
                break
        if not symmetry_holds:
            break
    if symmetry_holds:
        tests_passed += 1
        print("  ✓ Symmetry holds")
    else:
        print("  ✗ Symmetry failed")

    # Axiom 4: Triangle inequality
    tests_total += 1
    triangle_holds = True
    for p in test_points:
        for q in test_points:
            for r in test_points:
                if p.manhattan_distance(r) > p.manhattan_distance(q) + q.manhattan_distance(r):
                    triangle_holds = False
                    break
            if not triangle_holds:
                break
        if not triangle_holds:
            break
    if triangle_holds:
        tests_passed += 1
        print("  ✓ Triangle inequality holds")
    else:
        print("  ✗ Triangle inequality failed")

    return tests_passed, tests_total


def verify_hamming_distance_properties():
    """Verify Hamming distance properties."""
    print("\nTesting Hamming Distance Properties...")

    tests_passed = 0
    tests_total = 0

    # Test byte-level Hamming distance
    tests_total += 1
    x = bytes([0b10101010, 0b11001100])
    y = bytes([0b11110000, 0b10101010])

    expected = 4 + 4  # First byte: 4 bits differ, second byte: 4 bits differ
    actual = HammingDistance.distance_bytes(x, y)

    if actual == expected:
        tests_passed += 1
        print(f"  ✓ Byte Hamming distance correct: {actual}")
    else:
        print(f"  ✗ Expected {expected}, got {actual}")

    # Test metric properties
    tests_total += 1
    metric_holds = True

    for a in range(8):
        for b in range(8):
            d1 = HammingDistance.distance(a, b, 3)
            d2 = HammingDistance.distance(b, a, 3)
            if d1 != d2:  # Symmetry
                metric_holds = False
                break
            if a == b and d1 != 0:  # Identity
                metric_holds = False
                break
            if d1 < 0:  # Non-negativity
                metric_holds = False
                break

    if metric_holds:
        tests_passed += 1
        print("  ✓ Hamming distance metric properties hold")
    else:
        print("  ✗ Hamming distance metric properties failed")

    return tests_passed, tests_total


# ============================================================================
# Section 4: Polygon Operations
# ============================================================================

class Polygon:
    """A discrete polygon represented by ordered vertices."""

    def __init__(self, vertices: List[Point]):
        if len(vertices) < 3:
            raise ValueError("Polygon needs at least 3 vertices")
        self.vertices = vertices

    def perimeter(self) -> int:
        """Compute perimeter using Manhattan distance."""
        perim = 0
        n = len(self.vertices)
        for i in range(n):
            perim += self.vertices[i].manhattan_distance(self.vertices[(i + 1) % n])
        return perim

    def area_shoelace(self) -> float:
        """Compute area using shoelace formula."""
        n = len(self.vertices)
        area = 0
        for i in range(n):
            x1, y1 = self.vertices[i].coords
            x2, y2 = self.vertices[(i + 1) % n].coords
            area += x1 * y2 - x2 * y1
        return abs(area) / 2

    def contains_point(self, p: Point) -> bool:
        """Check if point is inside polygon using ray casting."""
        if len(p.coords) < 2:
            return False

        x, y = p.coords
        inside = False
        n = len(self.vertices)

        for i in range(n):
            x1, y1 = self.vertices[i].coords
            x2, y2 = self.vertices[(i + 1) % n].coords

            # Check if point is on an edge
            if self.point_on_segment(p, self.vertices[i], self.vertices[(i + 1) % n]):
                return True

            # Ray casting
            if ((y1 > y) != (y2 > y)) and (x < (x2 - x1) * (y - y1) / (y2 - y1) + x1):
                inside = not inside

        return inside

    def point_on_segment(self, p: Point, a: Point, b: Point) -> bool:
        """Check if point p lies on segment ab."""
        if len(p.coords) < 2 or len(a.coords) < 2 or len(b.coords) < 2:
            return False

        px, py = p.coords
        ax, ay = a.coords
        bx, by = b.coords

        # Check collinearity and bounding box
        cross = (bx - ax) * (py - ay) - (by - ay) * (px - ax)
        if cross != 0:
            return False

        # Check bounding box
        if min(ax, bx) <= px <= max(ax, bx) and min(ay, by) <= py <= max(ay, by):
            return True

        return False

    def bounding_box(self) -> Tuple[Point, Point]:
        """Get axis-aligned bounding box."""
        min_coords = [float('inf')] * self.vertices[0].dimension
        max_coords = [float('-inf')] * self.vertices[0].dimension

        for v in self.vertices:
            for i, c in enumerate(v.coords):
                min_coords[i] = min(min_coords[i], c)
                max_coords[i] = max(max_coords[i], c)

        return Point(*[int(c) for c in min_coords]), Point(*[int(c) for c in max_coords])


# ============================================================================
# Section 5: Grid Algorithms
# ============================================================================

class Grid:
    """A 2D discrete grid for geometric operations."""

    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.obstacles: Set[Point] = set()

    def add_obstacle(self, p: Point):
        """Add an obstacle at point p."""
        if 0 <= p.coords[0] < self.width and 0 <= p.coords[1] < self.height:
            self.obstacles.add(p)

    def is_free(self, p: Point) -> bool:
        """Check if point is free (no obstacle)."""
        if not (0 <= p.coords[0] < self.width and 0 <= p.coords[1] < self.height):
            return False
        return p not in self.obstacles

    def neighbors(self, p: Point) -> List[Point]:
        """Get 4-connected neighbors."""
        x, y = p.coords
        candidates = [Point(x + 1, y), Point(x - 1, y), Point(x, y + 1), Point(x, y - 1)]
        return [c for c in candidates if self.is_free(c)]

    def shortest_path(self, start: Point, end: Point) -> Optional[List[Point]]:
        """Find shortest path using BFS (Manhattan moves)."""
        if not self.is_free(start) or not self.is_free(end):
            return None

        queue = deque([(start, [start])])
        visited = {start}

        while queue:
            current, path = queue.popleft()

            if current == end:
                return path

            for neighbor in self.neighbors(current):
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, path + [neighbor]))

        return None

    def shortest_path_astar(self, start: Point, end: Point) -> Optional[List[Point]]:
        """Find shortest path using A* with Manhattan heuristic."""
        if not self.is_free(start) or not self.is_free(end):
            return None

        def heuristic(p: Point) -> int:
            return p.manhattan_distance(end)

        heap = [(heuristic(start), 0, start, [start])]
        visited = {start: 0}

        while heap:
            est, g, current, path = heapq.heappop(heap)

            if current == end:
                return path

            if g > visited.get(current, float('inf')):
                continue

            for neighbor in self.neighbors(current):
                new_g = g + 1
                if new_g < visited.get(neighbor, float('inf')):
                    visited[neighbor] = new_g
                    heapq.heappush(heap, (new_g + heuristic(neighbor), new_g, neighbor, path + [neighbor]))

        return None


# ============================================================================
# Section 6: Intersection Tests
# ============================================================================

class Intersections:
    """Geometric intersection tests."""

    @staticmethod
    def line_segments_intersect(p1: Point, p2: Point, p3: Point, p4: Point) -> bool:
        """Check if line segments p1-p2 and p3-p4 intersect."""
        def orientation(a: Point, b: Point, c: Point) -> int:
            """Cross product orientation."""
            if len(a.coords) < 2 or len(b.coords) < 2 or len(c.coords) < 2:
                return 0
            ax, ay = a.coords
            bx, by = b.coords
            cx, cy = c.coords
            return (bx - ax) * (cy - ay) - (by - ay) * (cx - ax)

        def on_segment(a: Point, b: Point, c: Point) -> bool:
            """Check if point b lies on segment a-c."""
            if len(a.coords) < 2 or len(b.coords) < 2 or len(c.coords) < 2:
                return False
            ax, ay = a.coords
            bx, by = b.coords
            cx, cy = c.coords
            return (min(ax, cx) <= bx <= max(ax, cx) and
                    min(ay, cy) <= by <= max(ay, cy))

        o1 = orientation(p1, p2, p3)
        o2 = orientation(p1, p2, p4)
        o3 = orientation(p3, p4, p1)
        o4 = orientation(p3, p4, p2)

        # General case
        if o1 * o2 < 0 and o3 * o4 < 0:
            return True

        # Special cases
        if o1 == 0 and on_segment(p1, p3, p2):
            return True
        if o2 == 0 and on_segment(p1, p4, p2):
            return True
        if o3 == 0 and on_segment(p3, p1, p4):
            return True
        if o4 == 0 and on_segment(p3, p2, p4):
            return True

        return False

    @staticmethod
    def point_in_circle(p: Point, circle: DiscreteCircle) -> bool:
        """Check if point is inside or on circle."""
        if circle.metric == 'manhattan':
            return circle.center.manhattan_distance(p) <= circle.radius
        elif circle.metric == 'euclidean_sq':
            return circle.center.squared_euclidean_distance(p) <= circle.radius ** 2
        return False


# ============================================================================
# Section 7: Benchmark Tests
# ============================================================================

class PerformanceBenchmarks:
    """Performance benchmarks for discrete geometry operations."""

    @staticmethod
    def benchmark_distance_computation(iterations: int = 10000):
        """Benchmark distance computations."""
        import time

        points = [Point(i, i * 2) for i in range(100)]

        start = time.time()
        for _ in range(iterations):
            for i in range(len(points)):
                for j in range(i + 1, len(points)):
                    points[i].manhattan_distance(points[j])
        elapsed = time.time() - start

        return elapsed

    @staticmethod
    def benchmark_pathfinding(grid_size: int = 20):
        """Benchmark pathfinding algorithms."""
        import time

        grid = Grid(grid_size, grid_size)
        # Add some random obstacles
        for i in range(grid_size // 2):
            grid.add_obstacle(Point(i, i))

        start = Point(0, 0)
        end = Point(grid_size - 1, grid_size - 1)

        # BFS
        t0 = time.time()
        path_bfs = grid.shortest_path(start, end)
        bfs_time = time.time() - t0

        # A*
        t0 = time.time()
        path_astar = grid.shortest_path_astar(start, end)
        astar_time = time.time() - t0

        return bfs_time, astar_time, len(path_bfs) if path_bfs else 0


# ============================================================================
# Section 8: Comprehensive Test Suite
# ============================================================================

def run_all_tests():
    """Run comprehensive test suite for Chapter 4."""
    print("=" * 70)
    print("CHAPTER 4: DISCRETE GEOMETRY - VERIFICATION TEST SUITE")
    print("=" * 70)

    total_passed = 0
    total_tests = 0

    # Test 1: Point operations
    print("\n[TEST 1] Point Operations")
    p1 = Point(3, 4)
    p2 = Point(1, 2)
    p3 = p1 + p2
    p4 = p1 - p2

    assert p3.coords == (4, 6), f"Point addition failed: {p3.coords}"
    assert p4.coords == (2, 2), f"Point subtraction failed: {p4.coords}"
    assert p1.manhattan_distance(p2) == 4, f"Manhattan distance failed"
    assert p1.squared_euclidean_distance(p2) == 8, f"Squared Euclidean distance failed"

    print("  ✓ All point operations passed")
    total_passed += 1
    total_tests += 1

    # Test 2: Discrete Line
    print("\n[TEST 2] Discrete Line")
    line = DiscreteLine(Point(0, 0), Point(1, 1))
    points = line.get_points(0, 5)

    assert len(points) == 6, f"Line points count failed"
    assert points[3].coords == (3, 3), f"Line point generation failed"

    print("  ✓ Discrete line operations passed")
    total_passed += 1
    total_tests += 1

    # Test 3: Discrete Circle
    print("\n[TEST 3] Discrete Circle")
    circle = DiscreteCircle(Point(0, 0), 3, 'manhattan')
    boundary = circle.boundary_points()
    interior = circle.interior_points()

    assert len(boundary) > 0, "Circle boundary is empty"
    assert len(interior) > 0, "Circle interior is empty"
    assert Point(0, 0) in interior, "Origin should be in interior"

    print(f"  ✓ Discrete circle: {len(boundary)} boundary, {len(interior)} interior points")
    total_passed += 1
    total_tests += 1

    # Test 4: Polygon
    print("\n[TEST 4] Polygon Operations")
    square = Polygon([Point(0, 0), Point(4, 0), Point(4, 4), Point(0, 4)])

    perimeter = square.perimeter()
    area = square.area_shoelace()

    assert perimeter == 16, f"Perimeter failed: {perimeter}"
    assert area == 16, f"Area failed: {area}"
    assert square.contains_point(Point(2, 2)), "Should contain center point"
    assert not square.contains_point(Point(5, 5)), "Should not contain outside point"

    print(f"  ✓ Polygon: perimeter={perimeter}, area={area}")
    total_passed += 1
    total_tests += 1

    # Test 5: Hamming Distance
    print("\n[TEST 5] Hamming Distance")
    passed, total = verify_hamming_distance_properties()
    total_passed += passed
    total_tests += total

    # Test 6: Manhattan Metric Axioms
    print("\n[TEST 6] Manhattan Distance Metric Axioms")
    passed, total = verify_manhattan_metric_axioms()
    total_passed += passed
    total_tests += total

    # Test 7: Grid Pathfinding
    print("\n[TEST 7] Grid Pathfinding")
    grid = Grid(10, 10)
    start = Point(0, 0)
    end = Point(9, 9)

    path_bfs = grid.shortest_path(start, end)
    path_astar = grid.shortest_path_astar(start, end)

    assert path_bfs is not None, "BFS should find path"
    assert path_astar is not None, "A* should find path"
    assert len(path_bfs) == len(path_astar), "Both should find same length path"

    print(f"  ✓ Pathfinding: BFS and A* both found path of length {len(path_bfs)}")
    total_passed += 1
    total_tests += 1

    # Test 8: Intersections
    print("\n[TEST 8] Intersection Tests")
    # Crossing segments
    assert Intersections.line_segments_intersect(
        Point(0, 0), Point(2, 2), Point(0, 2), Point(2, 0)
    ), "Crossing segments should intersect"

    # Non-crossing segments
    assert not Intersections.line_segments_intersect(
        Point(0, 0), Point(1, 1), Point(2, 0), Point(3, 1)
    ), "Non-crossing segments should not intersect"

    print("  ✓ Intersection tests passed")
    total_passed += 1
    total_tests += 1

    # Test 9: Graph Distance
    print("\n[TEST 9] Graph Distance")
    graph = {
        0: {1, 2},
        1: {0, 3},
        2: {0, 3},
        3: {1, 2, 4},
        4: {3}
    }
    gd = GraphDistance(graph)

    assert gd.distance(0, 4) == 3, f"Graph distance failed: {gd.distance(0, 4)}"
    assert gd.distance(0, 0) == 0, "Self distance should be 0"

    print("  ✓ Graph distance tests passed")
    total_passed += 1
    total_tests += 1

    # Test 10: Chebyshev Distance
    print("\n[TEST 10] Chebyshev Distance")
    p1 = Point(0, 0)
    p2 = Point(3, 5)

    cheb = p1.chebyshev_distance(p2)
    assert cheb == 5, f"Chebyshev distance failed: {cheb}"

    print(f"  ✓ Chebyshev distance: {cheb}")
    total_passed += 1
    total_tests += 1

    # Performance Benchmarks
    print("\n" + "=" * 70)
    print("PERFORMANCE BENCHMARKS")
    print("=" * 70)

    print("\n[Benchmark 1] Distance Computation")
    dist_time = PerformanceBenchmarks.benchmark_distance_computation(1000)
    print(f"  1000 iterations: {dist_time:.4f} seconds")

    print("\n[Benchmark 2] Pathfinding Algorithms")
    bfs_time, astar_time, path_len = PerformanceBenchmarks.benchmark_pathfinding(20)
    print(f"  Grid size 20x20:")
    print(f"    BFS:  {bfs_time:.6f} seconds")
    print(f"    A*:   {astar_time:.6f} seconds")
    print(f"    Path length: {path_len}")

    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"Tests passed: {total_passed}/{total_tests}")
    print(f"Success rate: {100 * total_passed / total_tests:.1f}%")

    if total_passed == total_tests:
        print("\n[PASS] ALL TESTS PASSED")
        return True
    else:
        print(f"\n[FAIL] {total_tests - total_passed} TESTS FAILED")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
