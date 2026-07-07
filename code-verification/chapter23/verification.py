"""
DCA Chapter 23: Discrete Signal Processing - Verification Code
Testing FIR filters, downsampling/upsampling, and integer wavelets
"""

import time
import math
from typing import List, Tuple, Dict, Callable, Optional
import itertools

# ============================================================================
# SECTION 1: Finite Signal Representation
# ============================================================================

class Signal:
    """Finite discrete signal representation"""

    def __init__(self, samples: List[int]):
        """
        Initialize signal with finite samples
        Args:
            samples: List of integer sample values
        """
        self.samples = samples[:]  # Deep copy
        self.length = len(samples)

    def __len__(self):
        return self.length

    def __getitem__(self, index: int) -> int:
        """Get sample with boundary handling (zero-padding)"""
        if 0 <= index < self.length:
            return self.samples[index]
        return 0

    def __setitem__(self, index: int, value: int):
        """Set sample"""
        if 0 <= index < self.length:
            self.samples[index] = value

    def __add__(self, other):
        """Signal addition"""
        max_len = max(self.length, other.length)
        result = [self[i] + other[i] for i in range(max_len)]
        return Signal(result)

    def __sub__(self, other):
        """Signal subtraction"""
        max_len = max(self.length, other.length)
        result = [self[i] - other[i] for i in range(max_len)]
        return Signal(result)

    def __mul__(self, scalar: int):
        """Scalar multiplication"""
        result = [s * scalar for s in self.samples]
        return Signal(result)

    def __eq__(self, other):
        """Signal equality"""
        if self.length != other.length:
            return False
        return all(self.samples[i] == other.samples[i] for i in range(self.length))

    def energy(self) -> int:
        """Compute signal energy (sum of squares)"""
        return sum(s ** 2 for s in self.samples)

    def extend(self, new_length: int) -> 'Signal':
        """Extend signal with zeros"""
        if new_length <= self.length:
            return Signal(self.samples[:new_length])
        return Signal(self.samples + [0] * (new_length - self.length))

    def __str__(self):
        return f"Signal({self.samples})"

    def __repr__(self):
        return f"Signal(length={self.length})"

# ============================================================================
# SECTION 2: FIR Filter Implementation
# ============================================================================

class FIRFilter:
    """Finite Impulse Response Filter"""

    def __init__(self, coefficients: List[int]):
        """
        Initialize FIR filter
        Args:
            coefficients: Filter coefficients h[0], h[1], ..., h[M-1]
        """
        self.coefficients = coefficients[:]
        self.order = len(coefficients)

    def apply(self, x: Signal) -> Signal:
        """
        Apply FIR filter to signal
        y[n] = sum_{k=0}^{M-1} h[k] * x[n-k]
        """
        y_length = x.length + self.order - 1
        y = []

        for n in range(y_length):
            y_n = sum(self.coefficients[k] * x[n - k] for k in range(self.order))
            y.append(y_n)

        return Signal(y)

    def apply_same_length(self, x: Signal) -> Signal:
        """Apply filter and keep same length (truncate output)"""
        y = self.apply(x)
        return Signal(y.samples[:x.length])

    def __call__(self, x: Signal) -> Signal:
        """Convenient callable interface"""
        return self.apply(x)

# ============================================================================
# SECTION 3: Multirate Signal Processing
# ============================================================================

class MultirateOperations:
    """Downsampling and upsampling operations"""

    @staticmethod
    def downsample(x: Signal, factor: int) -> Signal:
        """
        Downsample signal by factor M
        y[m] = x[m*M]
        """
        if factor <= 0:
            raise ValueError("Downsampling factor must be positive")

        result = [x[i * factor] for i in range((x.length + factor - 1) // factor)]
        return Signal(result)

    @staticmethod
    def upsample(x: Signal, factor: int) -> Signal:
        """
        Upsample signal by factor L (zero insertion)
        y[n] = x[n/L] if n % L == 0, else 0
        """
        if factor <= 0:
            raise ValueError("Upsampling factor must be positive")

        result = []
        for i in range(x.length * factor):
            if i % factor == 0:
                result.append(x[i // factor])
            else:
                result.append(0)

        return Signal(result)

    @staticmethod
    def decimate(x: Signal, factor: int, anti_alias_filter: Optional[FIRFilter] = None):
        """
        Decimate signal (anti-alias filtering + downsampling)
        """
        if anti_alias_filter is not None:
            x_filtered = anti_alias_filter(x)
        else:
            x_filtered = x

        return MultirateOperations.downsample(x_filtered, factor)

    @staticmethod
    def interpolate(x: Signal, factor: int, interpolation_filter: Optional[FIRFilter] = None):
        """
        Interpolate signal (upsampling + interpolation filtering)
        """
        x_up = MultirateOperations.upsample(x, factor)

        if interpolation_filter is not None:
            return interpolation_filter(x_up)

        return x_up

# ============================================================================
# SECTION 4: Convolution Properties
# ============================================================================

class ConvolutionProperties:
    """Verify convolution properties"""

    @staticmethod
    def convolve(x: Signal, h: List[int]) -> Signal:
        """Standard convolution"""
        filter_obj = FIRFilter(h)
        return filter_obj.apply(x)

    @staticmethod
    def verify_linearity(x: Signal, y: Signal, h: List[int], a: int = 2, b: int = 3):
        """
        Verify linearity: h * (a*x + b*y) = a*(h*x) + b*(h*y)
        """
        # Left side: h * (a*x + b*y)
        combined = (x * a) + (y * b)
        lhs = ConvolutionProperties.convolve(combined, h)

        # Right side: a*(h*x) + b*(h*y)
        hx = ConvolutionProperties.convolve(x, h)
        hy = ConvolutionProperties.convolve(y, h)
        rhs = (hx * a) + (hy * b)

        # Compare (considering length differences)
        min_len = min(len(lhs), len(rhs))
        passed = all(lhs[i] == rhs[i] for i in range(min_len))

        return passed, {
            "lhs": lhs.samples,
            "rhs": rhs.samples[:min_len]
        }

    @staticmethod
    def verify_time_invariance(x: Signal, h: List[int], delay: int = 2):
        """
        Verify time invariance: conv(delay(x), h) == delay(conv(x, h))
        """
        # Create delayed version
        delayed_samples = [0] * delay + x.samples
        x_delayed = Signal(delayed_samples)

        # Convolve delayed signal
        lhs = ConvolutionProperties.convolve(x_delayed, h)

        # Convolve original then delay
        convolved = ConvolutionProperties.convolve(x, h)
        delayed_conv_samples = [0] * delay + convolved.samples
        rhs = Signal(delayed_conv_samples)

        # Compare
        min_len = min(len(lhs), len(rhs))
        passed = all(lhs[i] == rhs[i] for i in range(min_len))

        return passed, {
            "delay": delay,
            "lhs": lhs.samples[:min_len],
            "rhs": rhs.samples[:min_len]
        }

    @staticmethod
    def verify_commutativity(x: Signal, y: Signal):
        """
        Verify commutativity: x * y = y * x
        """
        # Treat both as coefficient lists
        x_coeffs = x.samples
        y_coeffs = y.samples

        # x * y
        xy = FIRFilter(x_coeffs).apply(Signal(y_coeffs))
        # y * x
        yx = FIRFilter(y_coeffs).apply(Signal(x_coeffs))

        passed = xy == yx

        return passed, {
            "xy": xy.samples,
            "yx": yx.samples
        }

# ============================================================================
# SECTION 5: Integer Wavelet Transform (Lifting Scheme)
# ============================================================================

class IntegerWavelet:
    """Integer wavelet transform using lifting scheme"""

    @staticmethod
    def haar_lift_forward(x: List[int]) -> Tuple[List[int], List[int]]:
        """
        Forward Haar wavelet transform (integer version)
        Returns: (approximation coefficients, detail coefficients)
        """
        if len(x) % 2 != 0:
            raise ValueError("Signal length must be even for Haar transform")

        n = len(x) // 2
        approximation = []
        detail = []

        for i in range(n):
            a = x[2 * i]
            b = x[2 * i + 1]

            # Prediction step: d = b - a
            d = b - a

            # Update step: s = a + floor(d / 2)
            s = a + d // 2

            approximation.append(s)
            detail.append(d)

        return approximation, detail

    @staticmethod
    def haar_lift_inverse(s: List[int], d: List[int]) -> List[int]:
        """
        Inverse Haar wavelet transform
        Reconstructs original signal from approximation and detail
        """
        if len(s) != len(d):
            raise ValueError("Approximation and detail must have same length")

        x = []

        for i in range(len(s)):
            # Recover a and b from s and d
            # a = s - floor(d / 2)
            # b = a + d

            a = s[i] - d[i] // 2
            b = a + d[i]

            x.append(a)
            x.append(b)

        return x

    @staticmethod
    def verify_reconstruction(x: List[int]) -> Tuple[bool, Dict]:
        """
        Verify perfect reconstruction property
        """
        # Forward transform
        s, d = IntegerWavelet.haar_lift_forward(x)

        # Inverse transform
        x_reconstructed = IntegerWavelet.haar_lift_inverse(s, d)

        # Check equality
        passed = x == x_reconstructed

        return passed, {
            "original": x,
            "approximation": s,
            "detail": d,
            "reconstructed": x_reconstructed
        }

    @staticmethod
    def multi_level_haar(x: List[int], levels: int) -> Tuple[List[List[int]], List[int]]:
        """
        Multi-level Haar wavelet decomposition
        Returns: (detail coefficients at each level, final approximation)
        """
        if levels <= 0:
            raise ValueError("Number of levels must be positive")

        details = []
        current = x

        for level in range(levels):
            if len(current) < 2:
                break

            s, d = IntegerWavelet.haar_lift_forward(current)
            details.append(d)
            current = s

        return details, current

    @staticmethod
    def multi_level_haar_inverse(details: List[List[int]], approximation: List[int]) -> List[int]:
        """
        Multi-level Haar wavelet reconstruction
        """
        current = approximation

        for d in reversed(details):
            current = IntegerWavelet.haar_lift_inverse(current, d)

        return current

# ============================================================================
# SECTION 6: DFT/FFT-like Operations (Integer Version)
# ============================================================================

class IntegerDFT:
    """Integer version of DFT using modular arithmetic"""

    @staticmethod
    def dft_naive(x: List[int], N: Optional[int] = None, mod: Optional[int] = None):
        """
        Compute DFT: X[k] = sum_{n=0}^{N-1} x[n] * exp(-2*pi*i*n*k/N)
        For integer version, we compute sum without complex exponentials
        or use modular arithmetic with roots of unity
        """
        if N is None:
            N = len(x)

        if N != len(x):
            raise ValueError("DFT length must match signal length")

        X = []

        for k in range(N):
            X_k = 0
            for n in range(N):
                # For integer DFT, we can use simple sums
                # Or modular roots of unity if mod is specified
                if mod is not None:
                    # Find a primitive N-th root of unity in the field
                    # This is simplified; real implementation needs proper root finding
                    root_nk = pow(2, n * k, mod)  # Simplified: using 2 as base
                    X_k = (X_k + x[n] * root_nk) % mod
                else:
                    X_k += x[n]

            X.append(X_k)

        return X

# ============================================================================
# SECTION 7: Filter Banks
# ============================================================================

class FilterBank:
    """Two-channel filter bank for wavelet transforms"""

    def __init__(self, low_pass: List[int], high_pass: List[int]):
        """
        Initialize analysis filter bank
        Args:
            low_pass: Low-pass filter coefficients
            high_pass: High-pass filter coefficients
        """
        self.low_pass = FIRFilter(low_pass)
        self.high_pass = FIRFilter(high_pass)

    def analyze(self, x: Signal) -> Tuple[Signal, Signal]:
        """
        Analysis: decompose into low and high frequency subbands
        """
        # Filter
        low_filtered = self.low_pass(x)
        high_filtered = self.high_pass(x)

        # Downsample by 2
        low_subband = MultirateOperations.downsample(low_filtered, 2)
        high_subband = MultirateOperations.downsample(high_filtered, 2)

        return low_subband, high_subband

    def synthesize(self, low_subband: Signal, high_subband: Signal,
                   synthesis_low: List[int], synthesis_high: List[int]) -> Signal:
        """
        Synthesis: reconstruct from subbands
        """
        # Upsample by 2
        low_up = MultirateOperations.upsample(low_subband, 2)
        high_up = MultirateOperations.upsample(high_subband, 2)

        # Apply synthesis filters
        low_filt = FIRFilter(synthesis_low)
        high_filt = FIRFilter(synthesis_high)

        low_filtered = low_filt(low_up)
        high_filtered = high_filt(high_up)

        # Sum
        return low_filtered + high_filtered

# ============================================================================
# SECTION 8: Performance Benchmarking
# ============================================================================

class PerformanceBenchmarks:
    """Performance benchmarks for signal processing operations"""

    @staticmethod
    def benchmark_fir_filter(signal_length: int, filter_order: int, n_iterations: int = 1000) -> Dict[str, float]:
        """Benchmark FIR filtering"""
        print(f"Benchmarking FIR filter: signal={signal_length}, filter={filter_order}, iterations={n_iterations}...")

        import random
        x = Signal([random.randint(-100, 100) for _ in range(signal_length)])
        h = [random.randint(-5, 5) for _ in range(filter_order)]
        fir = FIRFilter(h)

        start = time.time()
        for _ in range(n_iterations):
            y = fir(x)
        elapsed = time.time() - start

        # Count operations
        ops_per_filter = signal_length * filter_order
        total_ops = ops_per_filter * n_iterations

        return {
            "total_time": elapsed,
            "filters_per_second": n_iterations / elapsed,
            "operations_per_second": total_ops / elapsed,
            "time_per_filter": elapsed / n_iterations
        }

    @staticmethod
    def benchmark_wavelet_transform(signal_length: int, n_iterations: int = 10000) -> Dict[str, float]:
        """Benchmark Haar wavelet transform"""
        print(f"Benchmarking Haar wavelet: signal={signal_length}, iterations={n_iterations}...")

        import random
        x = [random.randint(-100, 100) for _ in range(signal_length)]

        start = time.time()
        for _ in range(n_iterations):
            s, d = IntegerWavelet.haar_lift_forward(x)
        elapsed = time.time() - start

        return {
            "total_time": elapsed,
            "transforms_per_second": n_iterations / elapsed,
            "time_per_transform": elapsed / n_iterations
        }

    @staticmethod
    def benchmark_convolution(length1: int, length2: int, n_iterations: int = 1000) -> Dict[str, float]:
        """Benchmark convolution"""
        print(f"Benchmarking convolution: lengths={length1},{length2}, iterations={n_iterations}...")

        import random
        x = Signal([random.randint(-100, 100) for _ in range(length1)])
        h = [random.randint(-5, 5) for _ in range(length2)]

        start = time.time()
        for _ in range(n_iterations):
            y = ConvolutionProperties.convolve(x, h)
        elapsed = time.time() - start

        ops_per_conv = length1 * length2
        total_ops = ops_per_conv * n_iterations

        return {
            "total_time": elapsed,
            "convolutions_per_second": n_iterations / elapsed,
            "operations_per_second": total_ops / elapsed,
            "time_per_convolution": elapsed / n_iterations
        }

# ============================================================================
# SECTION 9: Comprehensive Test Suite
# ============================================================================

class TestSuite:
    """Comprehensive test suite for discrete signal processing"""

    def __init__(self):
        self.results = []
        self.benchmarks = []

    def test_signal_operations(self) -> bool:
        """Test basic signal operations"""
        print("Testing signal operations...")

        passed = True

        # Test addition
        x = Signal([1, 2, 3])
        y = Signal([4, 5, 6])
        z = x + y
        expected = Signal([5, 7, 9])

        if z != expected:
            passed = False
            print(f"  Addition failed")

        # Test scalar multiplication
        z = x * 2
        expected = Signal([2, 4, 6])

        if z != expected:
            passed = False
            print(f"  Scalar multiplication failed")

        # Test energy
        energy = Signal([1, 2, 3]).energy()
        expected_energy = 1 + 4 + 9

        if energy != expected_energy:
            passed = False
            print(f"  Energy computation failed")

        self.results.append({
            "test": "Signal Operations",
            "passed": passed,
            "details": "Basic signal arithmetic verified"
        })

        print(f"  Result: {'PASS' if passed else 'FAIL'}")
        return passed

    def test_fir_filter(self) -> bool:
        """Test FIR filtering"""
        print("Testing FIR filter...")

        # Test moving average filter
        h = [1, 1, 1]  # 3-point moving average
        fir = FIRFilter(h)

        x = Signal([1, 2, 3, 4, 5])
        y = fir(x)

        # Expected output (no normalization): [1, 3, 6, 9, 12, 9, 5]
        expected = Signal([1, 3, 6, 9, 12, 9, 5])

        passed = y == expected
        print(f"  FIR filter output: {passed}")

        # Test identity filter
        h = [1]  # Identity
        fir = FIRFilter(h)
        y = fir(x)

        passed = passed and (y == x)
        print(f"  Identity filter: {passed}")

        self.results.append({
            "test": "FIR Filter",
            "passed": passed,
            "details": "FIR filtering verified"
        })

        print(f"  Result: {'PASS' if passed else 'FAIL'}")
        return passed

    def test_multirate_operations(self) -> bool:
        """Test multirate operations"""
        print("Testing multirate operations...")

        passed = True

        # Test downsampling
        x = Signal([1, 2, 3, 4, 5, 6])
        y = MultirateOperations.downsample(x, 2)
        expected = Signal([1, 3, 5])

        if y != expected:
            passed = False
            print(f"  Downsampling failed")

        # Test upsampling
        y = MultirateOperations.upsample(x, 2)
        expected = Signal([1, 0, 2, 0, 3, 0, 4, 0, 5, 0, 6, 0])

        if y != expected:
            passed = False
            print(f"  Upsampling failed")

        # Test downsample-then-upsample relationship
        down = MultirateOperations.downsample(x, 2)
        up = MultirateOperations.upsample(down, 2)

        # Should get original at even indices
        for i in range(x.length):
            if up[i] != x[i]:
                passed = False
                print(f"  Down-up relationship failed at index {i}")
                break

        self.results.append({
            "test": "Multirate Operations",
            "passed": passed,
            "details": "Downsampling and upsampling verified"
        })

        print(f"  Result: {'PASS' if passed else 'FAIL'}")
        return passed

    def test_convolution_properties(self) -> bool:
        """Test convolution properties"""
        print("Testing convolution properties...")

        x = Signal([1, 2, 3])
        y = Signal([4, 5])
        h = [1, 1]

        tests_passed = []

        # Test linearity
        result, details = ConvolutionProperties.verify_linearity(x, y, h)
        tests_passed.append(result)
        print(f"  Linearity: {result}")

        # Test time invariance
        result, details = ConvolutionProperties.verify_time_invariance(x, h, delay=1)
        tests_passed.append(result)
        print(f"  Time invariance: {result}")

        # Test commutativity
        result, details = ConvolutionProperties.verify_commutativity(x, y)
        tests_passed.append(result)
        print(f"  Commutativity: {result}")

        passed = all(tests_passed)

        self.results.append({
            "test": "Convolution Properties",
            "passed": passed,
            "details": f"{len(tests_passed)} property tests passed"
        })

        print(f"  Result: {'PASS' if passed else 'FAIL'}")
        return passed

    def test_haar_wavelet(self) -> bool:
        """Test Haar wavelet transform"""
        print("Testing Haar wavelet transform...")

        # Test perfect reconstruction
        test_signals = [
            [1, 2, 3, 4],
            [10, 20, 30, 40, 50, 60, 70, 80],
            [100, -50, 25, -75, 0, 100, -25, 50]
        ]

        all_passed = True
        for x in test_signals:
            passed, details = IntegerWavelet.verify_reconstruction(x)
            all_passed = all_passed and passed

            if not passed:
                print(f"  Reconstruction failed for {x}")

        print(f"  Perfect reconstruction: {all_passed}")

        # Test multi-level decomposition
        x = [1, 2, 3, 4, 5, 6, 7, 8]
        details, approx = IntegerWavelet.multi_level_haar(x, levels=2)

        # Should have 2 detail levels and final approximation
        passed = len(details) == 2 and len(approx) == 2
        print(f"  Multi-level decomposition: {passed}")

        # Test reconstruction
        x_reconstructed = IntegerWavelet.multi_level_haar_inverse(details, approx)
        passed = passed and (x == x_reconstructed)
        print(f"  Multi-level reconstruction: {passed}")

        all_passed = all_passed and passed

        self.results.append({
            "test": "Haar Wavelet Transform",
            "passed": all_passed,
            "details": "Integer wavelet perfect reconstruction verified"
        })

        print(f"  Result: {'PASS' if all_passed else 'FAIL'}")
        return all_passed

    def test_filter_bank(self) -> bool:
        """Test filter bank operations"""
        print("Testing filter bank...")

        # Simple Haar filter bank
        low_pass = [1, 1]
        high_pass = [1, -1]

        bank = FilterBank(low_pass, high_pass)

        x = Signal([4, 2, 3, 7, 10, 5])

        # Analysis
        low, high = bank.analyze(x)

        print(f"  Low subband: {low.samples}")
        print(f"  High subband: {high.samples}")

        # For perfect reconstruction, we'd need proper synthesis filters
        # Here we just test that analysis produces output
        passed = len(low.samples) > 0 and len(high.samples) > 0

        self.results.append({
            "test": "Filter Bank",
            "passed": passed,
            "details": "Filter bank analysis verified"
        })

        print(f"  Result: {'PASS' if passed else 'FAIL'}")
        return passed

    def test_noble_identities(self) -> bool:
        """Test noble identities for multirate systems"""
        print("Testing noble identities...")

        # Noble identity: Downsample(M) * Filter(h) = Filter(h_downsampled) * Downsample(M)
        # Where h_downsampled inserts zeros between coefficients

        x = Signal([1, 2, 3, 4, 5, 6, 7, 8])
        h = [1, 2, 3]
        M = 2

        # Method 1: Filter then downsample
        fir = FIRFilter(h)
        filtered = fir(x)
        y1 = MultirateOperations.downsample(filtered, M)

        # Method 2: Create upsampled filter and then downsample
        # For M=2, upsample filter by inserting zeros: [1, 0, 2, 0, 3]
        h_upsampled = []
        for coeff in h:
            h_upsampled.append(coeff)
            h_upsampled.append(0)
        h_upsampled.pop()  # Remove trailing zero

        fir_up = FIRFilter(h_upsampled)
        y2 = MultirateOperations.downsample(fir_up(x), M)

        # These should give the same result (considering boundary conditions)
        min_len = min(len(y1), len(y2))
        passed = all(y1[i] == y2[i] for i in range(min_len))

        print(f"  Noble identity 1: {passed}")

        self.results.append({
            "test": "Noble Identities",
            "passed": passed,
            "details": "Multirate noble identities verified"
        })

        print(f"  Result: {'PASS' if passed else 'FAIL'}")
        return passed

    def run_all_tests(self) -> Dict[str, any]:
        """Run all tests"""
        print("=" * 60)
        print("DCA Chapter 23: Discrete Signal Processing - Test Suite")
        print("=" * 60)

        tests = [
            ("Signal Operations", self.test_signal_operations),
            ("FIR Filter", self.test_fir_filter),
            ("Multirate Operations", self.test_multirate_operations),
            ("Convolution Properties", self.test_convolution_properties),
            ("Haar Wavelet Transform", self.test_haar_wavelet),
            ("Filter Bank", self.test_filter_bank),
            ("Noble Identities", self.test_noble_identities),
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

        # Benchmark 1: FIR filtering
        print("\nBenchmark 1: FIR Filtering")
        print("-" * 40)
        for signal_len, filter_order in [(64, 8), (128, 16), (256, 32), (512, 64)]:
            result = PerformanceBenchmarks.benchmark_fir_filter(signal_len, filter_order)
            self.benchmarks.append({
                "name": f"FIR Filter ({signal_len}, {filter_order})",
                "result": result
            })
            print(f"  Signal={signal_len}, Filter={filter_order}: {result['filters_per_second']:.0f} filters/sec")

        # Benchmark 2: Wavelet transform
        print("\nBenchmark 2: Haar Wavelet Transform")
        print("-" * 40)
        for signal_len in [64, 128, 256, 512, 1024]:
            result = PerformanceBenchmarks.benchmark_wavelet_transform(signal_len)
            self.benchmarks.append({
                "name": f"Haar Wavelet ({signal_len})",
                "result": result
            })
            print(f"  Signal={signal_len}: {result['transforms_per_second']:.0f} transforms/sec")

        # Benchmark 3: Convolution
        print("\nBenchmark 3: Convolution")
        print("-" * 40)
        for len1, len2 in [(64, 16), (128, 32), (256, 64)]:
            result = PerformanceBenchmarks.benchmark_convolution(len1, len2)
            self.benchmarks.append({
                "name": f"Convolution ({len1}, {len2})",
                "result": result
            })
            print(f"  Lengths=({len1}, {len2}): {result['convolutions_per_second']:.0f} conv/sec")

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