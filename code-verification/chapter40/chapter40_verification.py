"""
Chapter 40: DCA Bootstrap Interpreter - Verification Code

This module verifies the core concepts from DCA Chapter 40 on bootstrap interpreter:
1. Finite syntax tree representation
2. Program encoding
3. Interpreter state management
4. Fuel-based termination
5. Small-step semantics
"""

import numpy as np
from typing import List, Tuple, Set, Dict, Optional, Any
from dataclasses import dataclass
from enum import Enum
import time


class Opcode(Enum):
    """Bytecode opcodes"""
    NOP = 0
    LOAD_CONST = 1
    LOAD_VAR = 2
    STORE_VAR = 3
    ADD = 4
    SUB = 5
    MUL = 6
    DIV = 7
    JMP = 8
    JZ = 9  # Jump if zero
    CALL = 10
    RET = 11
    HALT = 12


@dataclass
class Instruction:
    """Single bytecode instruction"""
    opcode: Opcode
    operands: Tuple[int, ...]

    def encode(self) -> str:
        """Encode instruction as string"""
        return f"{self.opcode.value}:{','.join(map(str, self.operands))}"

    @classmethod
    def decode(cls, s: str) -> 'Instruction':
        """Decode from string"""
        parts = s.split(':')
        opcode = Opcode(int(parts[0]))
        operands = tuple(int(x) for x in parts[1].split(',')) if len(parts) > 1 and parts[1] else ()
        return cls(opcode, operands)


@dataclass
class Program:
    """Program as finite list of instructions"""
    instructions: List[Instruction]
    constants: List[int]

    def encode(self) -> str:
        """Encode program as finite string"""
        inst_str = "|".join(inst.encode() for inst in self.instructions)
        const_str = ",".join(map(str, self.constants))
        return f"I:{inst_str}|C:{const_str}"

    @classmethod
    def decode(cls, s: str) -> 'Program':
        """Decode from string"""
        # Parse instructions
        i_start = s.find("I:") + 2
        i_end = s.find("|C:")
        inst_str = s[i_start:i_end]

        instructions = []
        if inst_str:
            for part in inst_str.split("|"):
                instructions.append(Instruction.decode(part))

        # Parse constants
        c_start = s.find("C:") + 2
        const_str = s[c_start:]
        constants = [int(x) for x in const_str.split(",")] if const_str else []

        return cls(instructions, constants)

    def size(self) -> int:
        """Return program size"""
        return len(self.encode())


@dataclass
class InterpreterState:
    """Interpreter execution state"""
    pc: int  # Program counter
    stack: List[int]  # Value stack
    variables: Dict[str, int]  # Variable storage
    fuel: int  # Remaining fuel (steps)
    status: str  # "running", "halted", "out_of_fuel"


class BootstrapInterpreter:
    """
    DCA Bootstrap interpreter with fuel-based termination
    """

    def __init__(self, program: Program, initial_fuel: int = 10000):
        self.program = program
        self.initial_fuel = initial_fuel
        self.reset()

    def reset(self):
        """Reset interpreter to initial state"""
        self.state = InterpreterState(
            pc=0,
            stack=[],
            variables={},
            fuel=self.initial_fuel,
            status="running"
        )

    def step(self) -> bool:
        """
        Execute one instruction

        Returns:
            True if instruction executed, False if halted or out of fuel
        """
        if self.state.status != "running":
            return False

        if self.state.fuel <= 0:
            self.state.status = "out_of_fuel"
            return False

        if self.state.pc >= len(self.program.instructions):
            self.state.status = "halted"
            return False

        # Fetch instruction
        inst = self.program.instructions[self.state.pc]

        # Decode and execute
        self.execute(inst)

        # Consume fuel
        self.state.fuel -= 1

        return True

    def execute(self, inst: Instruction):
        """Execute a single instruction"""
        op = inst.opcode

        if op == Opcode.NOP:
            self.state.pc += 1

        elif op == Opcode.LOAD_CONST:
            const_idx = inst.operands[0]
            if 0 <= const_idx < len(self.program.constants):
                self.state.stack.append(self.program.constants[const_idx])
            self.state.pc += 1

        elif op == Opcode.LOAD_VAR:
            var_name = f"v{inst.operands[0]}"
            val = self.state.variables.get(var_name, 0)
            self.state.stack.append(val)
            self.state.pc += 1

        elif op == Opcode.STORE_VAR:
            var_name = f"v{inst.operands[0]}"
            if self.state.stack:
                val = self.state.stack.pop()
                self.state.variables[var_name] = val
            self.state.pc += 1

        elif op == Opcode.ADD:
            if len(self.state.stack) >= 2:
                b = self.state.stack.pop()
                a = self.state.stack.pop()
                self.state.stack.append(a + b)
            self.state.pc += 1

        elif op == Opcode.SUB:
            if len(self.state.stack) >= 2:
                b = self.state.stack.pop()
                a = self.state.stack.pop()
                self.state.stack.append(a - b)
            self.state.pc += 1

        elif op == Opcode.MUL:
            if len(self.state.stack) >= 2:
                b = self.state.stack.pop()
                a = self.state.stack.pop()
                self.state.stack.append(a * b)
            self.state.pc += 1

        elif op == Opcode.DIV:
            if len(self.state.stack) >= 2:
                b = self.state.stack.pop()
                a = self.state.stack.pop()
                self.state.stack.append(a // b if b != 0 else 0)
            self.state.pc += 1

        elif op == Opcode.JMP:
            target = inst.operands[0]
            self.state.pc = target

        elif op == Opcode.JZ:
            target = inst.operands[0]
            if self.state.stack and self.state.stack.pop() == 0:
                self.state.pc = target
            else:
                self.state.pc += 1

        elif op == Opcode.HALT:
            self.state.status = "halted"

        else:
            self.state.pc += 1

    def run(self, max_steps: Optional[int] = None) -> InterpreterState:
        """
        Run program until halt or fuel exhausted

        Args:
            max_steps: Maximum steps to execute (None = use fuel)
        """
        steps = 0
        while self.step():
            steps += 1
            if max_steps and steps >= max_steps:
                break
        return self.state

    def get_result(self) -> Optional[int]:
        """Get result from stack top"""
        if self.state.stack:
            return self.state.stack[-1]
        return None


def verify_program_encoding():
    """
    Verify program has finite encoding
    """
    print("Testing Program Encoding...")

    # Create simple program
    prog = Program(
        instructions=[
            Instruction(Opcode.LOAD_CONST, (0,)),
            Instruction(Opcode.LOAD_CONST, (1,)),
            Instruction(Opcode.ADD, ()),
            Instruction(Opcode.HALT, ())
        ],
        constants=[5, 3]
    )

    # Encoding should be finite
    encoding = prog.encode()
    assert isinstance(encoding, str)
    assert len(encoding) < float('inf')

    # Decoding should work
    decoded = Program.decode(encoding)
    assert len(decoded.instructions) == len(prog.instructions)
    assert decoded.constants == prog.constants

    print("  ✓ Program encoding verified")
    return True


def verify_instruction_encoding():
    """
    Verify instruction encoding/decoding
    """
    print("Testing Instruction Encoding...")

    inst = Instruction(Opcode.LOAD_CONST, (0,))

    # Encode
    encoded = inst.encode()
    assert encoded == "1:0"

    # Decode
    decoded = Instruction.decode(encoded)
    assert decoded.opcode == inst.opcode
    assert decoded.operands == inst.operands

    print("  ✓ Instruction encoding verified")
    return True


def verify_fuel_based_termination():
    """
    Verify fuel-based termination guarantee
    """
    print("Testing Fuel-Based Termination...")

    # Create infinite loop program
    prog = Program(
        instructions=[
            Instruction(Opcode.LOAD_CONST, (0,)),
            Instruction(Opcode.JMP, (0,))  # Jump back
        ],
        constants=[1]
    )

    interp = BootstrapInterpreter(prog, initial_fuel=100)
    state = interp.run()

    # Should terminate due to fuel exhaustion
    assert state.status == "out_of_fuel" or state.status == "halted"
    assert state.fuel <= 0 or state.pc >= len(prog.instructions)

    print("  ✓ Fuel-based termination verified")
    return True


def verify_arithmetic_operations():
    """
    Verify arithmetic operations
    """
    print("Testing Arithmetic Operations...")

    # Program: 5 + 3
    prog = Program(
        instructions=[
            Instruction(Opcode.LOAD_CONST, (0,)),
            Instruction(Opcode.LOAD_CONST, (1,)),
            Instruction(Opcode.ADD, ()),
            Instruction(Opcode.HALT, ())
        ],
        constants=[5, 3]
    )

    interp = BootstrapInterpreter(prog)
    interp.run()

    result = interp.get_result()
    assert result == 8

    # Program: 10 - 4
    prog2 = Program(
        instructions=[
            Instruction(Opcode.LOAD_CONST, (0,)),
            Instruction(Opcode.LOAD_CONST, (1,)),
            Instruction(Opcode.SUB, ()),
            Instruction(Opcode.HALT, ())
        ],
        constants=[10, 4]
    )

    interp2 = BootstrapInterpreter(prog2)
    interp2.run()
    assert interp2.get_result() == 6

    print("  ✓ Arithmetic operations verified")
    return True


def verify_variable_storage():
    """
    Verify variable storage and retrieval
    """
    print("Testing Variable Storage...")

    # Program: store 42 in v0, then load it
    prog = Program(
        instructions=[
            Instruction(Opcode.LOAD_CONST, (0,)),
            Instruction(Opcode.STORE_VAR, (0,)),
            Instruction(Opcode.LOAD_VAR, (0,)),
            Instruction(Opcode.HALT, ())
        ],
        constants=[42]
    )

    interp = BootstrapInterpreter(prog)
    interp.run()

    result = interp.get_result()
    assert result == 42

    print("  ✓ Variable storage verified")
    return True


def verify_conditional_jumps():
    """
    Verify conditional jumps
    """
    print("Testing Conditional Jumps...")

    # Program: load 0, jump if zero to label (skip)
    prog = Program(
        instructions=[
            Instruction(Opcode.LOAD_CONST, (0,)),
            Instruction(Opcode.LOAD_CONST, (1,)),  # This is skipped
            Instruction(Opcode.JZ, (4,)),  # Jump to halt
            Instruction(Opcode.LOAD_CONST, (2,)),  # This is executed if not jumped
            Instruction(Opcode.HALT, ())
        ],
        constants=[0, 99, 88]
    )

    interp = BootstrapInterpreter(prog)
    interp.run()

    # Should jump to halt, so 99 is not on stack
    # Only 0 from first load
    result = interp.get_result()
    assert result == 0

    print("  ✓ Conditional jumps verified")
    return True


def verify_program_size():
    """
    Verify program size computation
    """
    print("Testing Program Size...")

    prog = Program(
        instructions=[
            Instruction(Opcode.LOAD_CONST, (0,)),
            Instruction(Opcode.ADD, ())
        ],
        constants=[5]
    )

    size = prog.size()
    assert size > 0
    assert size < float('inf')

    # Larger program should have larger size
    prog2 = Program(
        instructions=[
            Instruction(Opcode.LOAD_CONST, (0,)),
            Instruction(Opcode.LOAD_CONST, (1,)),
            Instruction(Opcode.ADD, ()),
            Instruction(Opcode.STORE_VAR, (0,)),
            Instruction(Opcode.HALT, ())
        ],
        constants=[5, 3]
    )

    assert prog2.size() > prog.size()

    print("  ✓ Program size verified")
    return True


def verify_interpreter_state():
    """
    Verify interpreter state management
    """
    print("Testing Interpreter State...")

    prog = Program(
        instructions=[
            Instruction(Opcode.LOAD_CONST, (0,)),
            Instruction(Opcode.HALT, ())
        ],
        constants=[42]
    )

    interp = BootstrapInterpreter(prog, initial_fuel=100)

    # Initial state
    assert interp.state.pc == 0
    assert interp.state.fuel == 100
    assert interp.state.status == "running"

    # After step
    interp.step()
    assert interp.state.pc == 1
    assert interp.state.fuel == 99
    assert 42 in interp.state.stack

    # After halt
    interp.step()
    assert interp.state.status == "halted"

    print("  ✓ Interpreter state verified")
    return True


def verify_small_step_semantics():
    """
    Verify small-step operational semantics
    """
    print("Testing Small-Step Semantics...")

    prog = Program(
        instructions=[
            Instruction(Opcode.LOAD_CONST, (0,)),
            Instruction(Opcode.LOAD_CONST, (1,)),
            Instruction(Opcode.ADD, ()),
            Instruction(Opcode.HALT, ())
        ],
        constants=[5, 3]
    )

    interp = BootstrapInterpreter(prog)

    # Track each step
    states = []
    while interp.step():
        states.append((interp.state.pc, interp.state.stack.copy()))

    # Should have executed multiple steps
    assert len(states) == 4  # 3 loads/add + 1 halt check

    # Final state
    assert interp.state.status == "halted"
    assert interp.get_result() == 8

    print("  ✓ Small-step semantics verified")
    return True


def verify_interpreter_determinism():
    """
    Verify interpreter is deterministic
    """
    print("Testing Interpreter Determinism...")

    prog = Program(
        instructions=[
            Instruction(Opcode.LOAD_CONST, (0,)),
            Instruction(Opcode.LOAD_CONST, (1,)),
            Instruction(Opcode.ADD, ()),
            Instruction(Opcode.MUL, ()),
            Instruction(Opcode.HALT, ())
        ],
        constants=[5, 3]
    )

    # Run twice
    interp1 = BootstrapInterpreter(prog)
    interp1.run()
    result1 = interp1.get_result()

    interp2 = BootstrapInterpreter(prog)
    interp2.run()
    result2 = interp2.get_result()

    # Results should be identical
    assert result1 == result2

    print("  ✓ Interpreter determinism verified")
    return True


def benchmark_interpreter_performance():
    """
    Benchmark interpreter performance
    """
    print("Benchmarking Interpreter Performance...")

    results = []

    for n in [100, 1000, 10000]:
        # Create program with n operations
        instructions = []
        for _ in range(n):
            instructions.append(Instruction(Opcode.LOAD_CONST, (0,)))
            instructions.append(Instruction(Opcode.ADD, ()))
        instructions.append(Instruction(Opcode.HALT, ()))

        prog = Program(instructions, constants=[1])

        interp = BootstrapInterpreter(prog, initial_fuel=n*2 + 1000)

        start = time.time()
        interp.run()
        elapsed = time.time() - start

        results.append((n, elapsed))
        print(f"  n={n}: time={elapsed:.4f}s")

    return results


class TestSuite:
    """Comprehensive test suite for Chapter 40"""

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
    print("CHAPTER 40: DCA BOOTSTRAP INTERPRETER VERIFICATION")
    print("="*60)
    print()

    suite = TestSuite()

    # Core concept tests
    suite.run_test(verify_program_encoding, "Program Encoding")
    suite.run_test(verify_instruction_encoding, "Instruction Encoding")
    suite.run_test(verify_fuel_based_termination, "Fuel-Based Termination")
    suite.run_test(verify_arithmetic_operations, "Arithmetic Operations")
    suite.run_test(verify_variable_storage, "Variable Storage")
    suite.run_test(verify_conditional_jumps, "Conditional Jumps")
    suite.run_test(verify_program_size, "Program Size")
    suite.run_test(verify_interpreter_state, "Interpreter State")
    suite.run_test(verify_small_step_semantics, "Small-Step Semantics")
    suite.run_test(verify_interpreter_determinism, "Interpreter Determinism")

    # Performance benchmarks
    print()
    print("Performance Benchmarks:")
    print("-" * 40)
    benchmark_results = benchmark_interpreter_performance()

    # Summary
    print()
    suite.summary()

    return suite.results, benchmark_results


if __name__ == "__main__":
    main()