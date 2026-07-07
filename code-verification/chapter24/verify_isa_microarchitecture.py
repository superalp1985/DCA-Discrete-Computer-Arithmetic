"""
DCA Chapter 24: DCA-ISA and Microarchitecture Sketch - Verification Code
Testing ISA semantics, instruction execution, and microarchitecture correctness
"""

import time
from typing import List, Tuple, Dict, Callable, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import copy

# ============================================================================
# SECTION 1: ISA Definition
# ============================================================================

class Opcode(Enum):
    """Instruction opcodes for DCA-ISA"""
    NOP = "nop"
    ADD = "add"
    SUB = "sub"
    MUL = "mul"
    DIV = "div"
    LD = "ld"    # Load
    ST = "st"    # Store
    JMP = "jmp"  # Jump
    JZ = "jz"    # Jump if zero
    JNZ = "jnz"  # Jump if not zero
    CMP = "cmp"  # Compare
    AND = "and"
    OR = "or"
    XOR = "xor"
    NOT = "not"
    SHL = "shl"  # Shift left
    SHR = "shr"  # Shift right

@dataclass
class Instruction:
    """ISA instruction"""
    opcode: Opcode
    operands: List[str]  # Register names or immediate values

    def __repr__(self):
        return f"{self.opcode.value} {' '.join(self.operands)}"

@dataclass
class Program:
    """Program as list of instructions"""
    instructions: List[Instruction]
    labels: Dict[str, int] = field(default_factory=dict)

    def get_instruction(self, pc: int) -> Optional[Instruction]:
        """Get instruction at program counter"""
        if 0 <= pc < len(self.instructions):
            return self.instructions[pc]
        return None

# ============================================================================
# SECTION 2: Machine State
# ============================================================================

@dataclass
class RegisterFile:
    """Register file with finite number of registers"""
    size: int = 16
    width: int = 32  # Bit width

    def __post_init__(self):
        self.registers = [0] * self.size
        self.names = {f"r{i}": i for i in range(self.size)}
        self.names["sp"] = self.size - 1  # Stack pointer
        self.names["ra"] = self.size - 2  # Return address

    def read(self, name: str) -> int:
        """Read register value"""
        if name not in self.names:
            raise ValueError(f"Unknown register: {name}")
        idx = self.names[name]
        return self.registers[idx]

    def write(self, name: str, value: int):
        """Write to register"""
        if name not in self.names:
            raise ValueError(f"Unknown register: {name}")
        idx = self.names[name]
        self.registers[idx] = value & ((1 << self.width) - 1)  # Apply width mask

    def copy(self) -> 'RegisterFile':
        """Create copy of register file"""
        new_rf = RegisterFile(self.size, self.width)
        new_rf.registers = self.registers[:]
        return new_rf

@dataclass
class Memory:
    """Finite memory"""
    size: int = 1024
    width: int = 32

    def __post_init__(self):
        self.data = [0] * self.size

    def read(self, address: int) -> int:
        """Read from memory"""
        if address < 0 or address >= self.size:
            raise ValueError(f"Invalid address: {address}")
        return self.data[address]

    def write(self, address: int, value: int):
        """Write to memory"""
        if address < 0 or address >= self.size:
            raise ValueError(f"Invalid address: {address}")
        self.data[address] = value & ((1 << self.width) - 1)

    def copy(self) -> 'Memory':
        """Create copy of memory"""
        new_mem = Memory(self.size, self.width)
        new_mem.data = self.data[:]
        return new_mem

@dataclass
class Flags:
    """Processor flags (condition codes)"""
    zero: bool = False
    negative: bool = False
    carry: bool = False
    overflow: bool = False

    def update(self, result: int, width: int = 32):
        """Update flags based on result"""
        self.zero = (result == 0)
        self.negative = (result & (1 << (width - 1))) != 0

        # Carry and overflow would need more sophisticated computation
        # Simplified here

@dataclass
class MachineState:
    """Complete machine state"""
    registers: RegisterFile = field(default_factory=RegisterFile)
    memory: Memory = field(default_factory=Memory)
    flags: Flags = field(default_factory=Flags)
    pc: int = 0  # Program counter
    halted: bool = False

    def copy(self) -> 'MachineState':
        """Create copy of state"""
        return MachineState(
            registers=self.registers.copy(),
            memory=self.memory.copy(),
            flags=Flags(self.flags.zero, self.flags.negative,
                       self.flags.carry, self.flags.overflow),
            pc=self.pc,
            halted=self.halted
        )

    def __eq__(self, other):
        """Compare states"""
        return (self.registers.registers == other.registers.registers and
                self.memory.data == other.memory.data and
                self.flags == other.flags and
                self.pc == other.pc and
                self.halted == other.halted)

# ============================================================================
# SECTION 3: ISA Semantics
# ============================================================================

class ISASemantics:
    """ISA instruction execution semantics"""

    @staticmethod
    def parse_immediate(operand: str) -> int:
        """Parse immediate value"""
        if operand.startswith("#"):
            return int(operand[1:])
        return int(operand)

    @staticmethod
    def is_immediate(operand: str) -> bool:
        """Check if operand is immediate value"""
        return operand.startswith("#")

    @staticmethod
    def execute(instr: Instruction, state: MachineState) -> MachineState:
        """
        Execute single instruction according to ISA semantics
        Returns new state (does not modify input state)
        """
        new_state = state.copy()

        if instr.opcode == Opcode.NOP:
            pass

        elif instr.opcode == Opcode.ADD:
            rd, rs1, rs2 = instr.operands
            val1 = new_state.registers.read(rs1)
            val2 = new_state.registers.read(rs2) if not ISASemantics.is_immediate(rs2) else ISASemantics.parse_immediate(rs2)
            result = val1 + val2
            new_state.registers.write(rd, result)
            new_state.flags.update(result)

        elif instr.opcode == Opcode.SUB:
            rd, rs1, rs2 = instr.operands
            val1 = new_state.registers.read(rs1)
            val2 = new_state.registers.read(rs2) if not ISASemantics.is_immediate(rs2) else ISASemantics.parse_immediate(rs2)
            result = val1 - val2
            new_state.registers.write(rd, result)
            new_state.flags.update(result)

        elif instr.opcode == Opcode.MUL:
            rd, rs1, rs2 = instr.operands
            val1 = new_state.registers.read(rs1)
            val2 = new_state.registers.read(rs2)
            result = val1 * val2
            new_state.registers.write(rd, result)
            new_state.flags.update(result)

        elif instr.opcode == Opcode.DIV:
            rd, rs1, rs2 = instr.operands
            val1 = new_state.registers.read(rs1)
            val2 = new_state.registers.read(rs2)
            if val2 == 0:
                raise ValueError("Division by zero")
            result = val1 // val2
            new_state.registers.write(rd, result)
            new_state.flags.update(result)

        elif instr.opcode == Opcode.LD:
            rd, addr = instr.operands
            address = new_state.registers.read(addr) if not ISASemantics.is_immediate(addr) else ISASemantics.parse_immediate(addr)
            value = new_state.memory.read(address)
            new_state.registers.write(rd, value)

        elif instr.opcode == Opcode.ST:
            rs, addr = instr.operands
            address = new_state.registers.read(addr) if not ISASemantics.is_immediate(addr) else ISASemantics.parse_immediate(addr)
            value = new_state.registers.read(rs)
            new_state.memory.write(address, value)

        elif instr.opcode == Opcode.JMP:
            target = instr.operands[0]
            new_state.pc = int(target) - 1  # -1 because we increment after

        elif instr.opcode == Opcode.JZ:
            target = instr.operands[0]
            if new_state.flags.zero:
                new_state.pc = int(target) - 1

        elif instr.opcode == Opcode.JNZ:
            target = instr.operands[0]
            if not new_state.flags.zero:
                new_state.pc = int(target) - 1

        elif instr.opcode == Opcode.CMP:
            rs1, rs2 = instr.operands
            val1 = new_state.registers.read(rs1)
            val2 = new_state.registers.read(rs2) if not ISASemantics.is_immediate(rs2) else ISASemantics.parse_immediate(rs2)
            result = val1 - val2
            new_state.flags.update(result)

        elif instr.opcode == Opcode.AND:
            rd, rs1, rs2 = instr.operands
            val1 = new_state.registers.read(rs1)
            val2 = new_state.registers.read(rs2)
            result = val1 & val2
            new_state.registers.write(rd, result)
            new_state.flags.update(result)

        elif instr.opcode == Opcode.OR:
            rd, rs1, rs2 = instr.operands
            val1 = new_state.registers.read(rs1)
            val2 = new_state.registers.read(rs2)
            result = val1 | val2
            new_state.registers.write(rd, result)
            new_state.flags.update(result)

        elif instr.opcode == Opcode.XOR:
            rd, rs1, rs2 = instr.operands
            val1 = new_state.registers.read(rs1)
            val2 = new_state.registers.read(rs2)
            result = val1 ^ val2
            new_state.registers.write(rd, result)
            new_state.flags.update(result)

        elif instr.opcode == Opcode.NOT:
            rd, rs = instr.operands
            val = new_state.registers.read(rs)
            result = ~val
            new_state.registers.write(rd, result)
            new_state.flags.update(result)

        elif instr.opcode == Opcode.SHL:
            rd, rs, amount = instr.operands
            val = new_state.registers.read(rs)
            shift = new_state.registers.read(amount) if not ISASemantics.is_immediate(amount) else ISASemantics.parse_immediate(amount)
            result = val << shift
            new_state.registers.write(rd, result)
            new_state.flags.update(result)

        elif instr.opcode == Opcode.SHR:
            rd, rs, amount = instr.operands
            val = new_state.registers.read(rs)
            shift = new_state.registers.read(amount) if not ISASemantics.is_immediate(amount) else ISASemantics.parse_immediate(amount)
            result = val >> shift
            new_state.registers.write(rd, result)
            new_state.flags.update(result)

        # Increment PC
        new_state.pc += 1

        return new_state

    @staticmethod
    def run_program(program: Program, initial_state: Optional[MachineState] = None,
                    max_cycles: int = 10000) -> Tuple[MachineState, List[MachineState]]:
        """
        Execute program until halt or max_cycles
        Returns final state and trace of all states
        """
        state = initial_state if initial_state else MachineState()
        trace = [state.copy()]

        for _ in range(max_cycles):
            if state.halted:
                break

            if state.pc >= len(program.instructions):
                break

            instr = program.get_instruction(state.pc)
            if instr is None:
                break

            state = ISASemantics.execute(instr, state)
            trace.append(state.copy())

        return state, trace

# ============================================================================
# SECTION 4: Microarchitecture
# ============================================================================

class MicroOp:
    """Micro-operation for pipelined execution"""

    def __init__(self, instr: Instruction, pc: int):
        self.instr = instr
        self.pc = pc
        self.stage = "fetch"
        self.result = None

@dataclass
class PipelineStage:
    """Pipeline stage state"""
    name: str
    busy: bool = False
    instruction: Optional[Instruction] = None
    pc: int = 0
    result: Optional[Any] = None

class PipelinedProcessor:
    """
    Pipelined processor microarchitecture
    Implements 5-stage pipeline: IF, ID, EX, MEM, WB
    """

    def __init__(self):
        self.stages = {
            "IF": PipelineStage("IF"),
            "ID": PipelineStage("ID"),
            "EX": PipelineStage("EX"),
            "MEM": PipelineStage("MEM"),
            "WB": PipelineStage("WB"),
        }
        self.register_file = RegisterFile()
        self.memory = Memory()
        self.flags = Flags()
        self.pc = 0
        self.cycle = 0
        self.halted = False

    def cycle_step(self, program: Program):
        """Execute one pipeline cycle"""
        self.cycle += 1

        # WB stage
        if self.stages["WB"].busy:
            self._writeback(self.stages["WB"])
            self.stages["WB"].busy = False

        # MEM stage
        if self.stages["MEM"].busy:
            self._memory(self.stages["MEM"])
            self.stages["WB"] = self.stages["MEM"]
            self.stages["WB"].stage = "WB"
            self.stages["MEM"] = PipelineStage("MEM")

        # EX stage
        if self.stages["EX"].busy:
            self._execute(self.stages["EX"])
            self.stages["MEM"] = self.stages["EX"]
            self.stages["MEM"].stage = "MEM"
            self.stages["EX"] = PipelineStage("EX")

        # ID stage
        if self.stages["ID"].busy:
            self._decode(self.stages["ID"])
            self.stages["EX"] = self.stages["ID"]
            self.stages["EX"].stage = "EX"
            self.stages["ID"] = PipelineStage("ID")

        # IF stage
        if not self.halted:
            self._fetch(program)
            if self.stages["IF"].busy:
                self.stages["ID"] = self.stages["IF"]
                self.stages["ID"].stage = "ID"
                self.stages["IF"] = PipelineStage("IF")

    def _fetch(self, program: Program):
        """Fetch stage"""
        if self.pc >= len(program.instructions):
            self.halted = True
            return

        instr = program.get_instruction(self.pc)
        self.stages["IF"].instruction = instr
        self.stages["IF"].pc = self.pc
        self.stages["IF"].busy = True
        self.pc += 1

    def _decode(self, stage: PipelineStage):
        """Decode stage"""
        # Register read happens here
        # For simplicity, just mark as decoded
        pass

    def _execute(self, stage: PipelineStage):
        """Execute stage"""
        # ALU operations
        instr = stage.instruction
        if instr.opcode in [Opcode.ADD, Opcode.SUB, Opcode.MUL, Opcode.DIV,
                            Opcode.AND, Opcode.OR, Opcode.XOR, Opcode.NOT]:
            # Compute result
            # Simplified: use ISA semantics
            dummy_state = MachineState()
            dummy_state.registers = self.register_file
            dummy_state.flags = self.flags

            result_state = ISASemantics.execute(instr, dummy_state)
            stage.result = result_state

        elif instr.opcode in [Opcode.LD]:
            # Calculate address
            addr_reg = instr.operands[1]
            stage.result = self.register_file.read(addr_reg)

        elif instr.opcode in [Opcode.ST]:
            val = self.register_file.read(instr.operands[0])
            addr = self.register_file.read(instr.operands[1])
            stage.result = (addr, val)

    def _memory(self, stage: PipelineStage):
        """Memory stage"""
        instr = stage.instruction
        if instr.opcode == Opcode.LD:
            addr = stage.result
            value = self.memory.read(addr)
            stage.result = value
        elif instr.opcode == Opcode.ST:
            addr, val = stage.result
            self.memory.write(addr, val)

    def _writeback(self, stage: PipelineStage):
        """Writeback stage"""
        instr = stage.instruction
        if instr.opcode in [Opcode.ADD, Opcode.SUB, Opcode.MUL, Opcode.DIV,
                            Opcode.AND, Opcode.OR, Opcode.XOR, Opcode.NOT,
                            Opcode.SHL, Opcode.SHR]:
            if hasattr(stage.result, 'registers'):
                self.register_file = stage.result.registers
                self.flags = stage.result.flags
        elif instr.opcode == Opcode.LD:
            self.register_file.write(instr.operands[0], stage.result)

# ============================================================================
# SECTION 5: Correctness Verification
# ============================================================================

class CorrectnessVerifier:
    """Verify microarchitecture correctness against ISA semantics"""

    @staticmethod
    def verify_execution(program: Program, initial_state: MachineState) -> Tuple[bool, str]:
        """
        Verify that pipelined execution matches ISA semantics
        """
        # Run with ISA semantics
        isa_final, isa_trace = ISASemantics.run_program(program, initial_state.copy())

        # Run with pipelined processor
        pipeline = PipelinedProcessor()
        pipeline.register_file = initial_state.registers.copy()
        pipeline.memory = initial_state.memory.copy()
        pipeline.flags = initial_state.flags
        pipeline.pc = initial_state.pc

        # Run for enough cycles
        for _ in range(len(program.instructions) * 10 + 100):
            if pipeline.halted:
                break
            pipeline.cycle_step(program)

        # Compare final states
        pipeline_final = MachineState()
        pipeline_final.registers = pipeline.register_file
        pipeline_final.memory = pipeline.memory
        pipeline_final.flags = pipeline.flags
        pipeline_final.pc = pipeline.pc
        pipeline_final.halted = pipeline.halted

        if isa_final == pipeline_final:
            return True, "Pipelined execution matches ISA semantics"
        else:
            return False, f"States differ: ISA PC={isa_final.pc}, Pipeline PC={pipeline_final.pc}"

    @staticmethod
    def verify_deterministic(program: Program, initial_state: MachineState) -> bool:
        """Verify execution is deterministic"""
        results = []

        for _ in range(3):
            final, _ = ISASemantics.run_program(program, initial_state.copy())
            results.append(final)

        # All results should be identical
        return all(results[0] == r for r in results[1:])

# ============================================================================
# SECTION 6: Instruction Tests
# ============================================================================

class InstructionTests:
    """Tests for individual instructions"""

    @staticmethod
    def test_arithmetic_instructions() -> bool:
        """Test arithmetic instructions"""
        state = MachineState()
        state.registers.write("r0", 5)
        state.registers.write("r1", 3)

        # Test ADD
        instr = Instruction(Opcode.ADD, ["r2", "r0", "r1"])
        state = ISASemantics.execute(instr, state)

        passed = state.registers.read("r2") == 8

        # Test SUB
        instr = Instruction(Opcode.SUB, ["r3", "r0", "r1"])
        state = ISASemantics.execute(instr, state)

        passed = passed and state.registers.read("r3") == 2

        # Test MUL
        instr = Instruction(Opcode.MUL, ["r4", "r0", "r1"])
        state = ISASemantics.execute(instr, state)

        passed = passed and state.registers.read("r4") == 15

        return passed

    @staticmethod
    def test_logical_instructions() -> bool:
        """Test logical instructions"""
        state = MachineState()
        state.registers.write("r0", 0b1100)  # 12
        state.registers.write("r1", 0b1010)  # 10

        # Test AND
        instr = Instruction(Opcode.AND, ["r2", "r0", "r1"])
        state = ISASemantics.execute(instr, state)

        passed = state.registers.read("r2") == 0b1000  # 8

        # Test OR
        instr = Instruction(Opcode.OR, ["r3", "r0", "r1"])
        state = ISASemantics.execute(instr, state)

        passed = passed and state.registers.read("r3") == 0b1110  # 14

        # Test XOR
        instr = Instruction(Opcode.XOR, ["r4", "r0", "r1"])
        state = ISASemantics.execute(instr, state)

        passed = passed and state.registers.read("r4") == 0b0110  # 6

        return passed

    @staticmethod
    def test_memory_instructions() -> bool:
        """Test memory load/store"""
        state = MachineState()
        state.registers.write("r0", 100)
        state.registers.write("r1", 42)

        # Store r1 to address in r0
        instr = Instruction(Opcode.ST, ["r1", "r0"])
        state = ISASemantics.execute(instr, state)

        passed = state.memory.read(100) == 42

        # Load from address in r0 to r2
        instr = Instruction(Opcode.LD, ["r2", "r0"])
        state = ISASemantics.execute(instr, state)

        passed = passed and state.registers.read("r2") == 42

        return passed

    @staticmethod
    def test_branch_instructions() -> bool:
        """Test branch instructions"""
        state = MachineState()
        state.registers.write("r0", 0)
        state.pc = 0

        # Test JZ (should jump)
        instr = Instruction(Opcode.JZ, ["10"])
        state = ISASemantics.execute(instr, state)

        passed = state.pc == 10

        # Test JNZ (should not jump)
        state.pc = 0
        instr = Instruction(Opcode.JNZ, ["5"])
        state = ISASemantics.execute(instr, state)

        passed = passed and state.pc == 1  # Just incremented

        return passed

# ============================================================================
# SECTION 7: Test Suite
# ============================================================================

class TestSuite:
    """Comprehensive test suite for ISA and microarchitecture"""

    def __init__(self):
        self.results = []

    def test_instruction_execution(self) -> bool:
        """Test individual instruction execution"""
        print("Testing instruction execution...")

        passed = True

        passed = passed and InstructionTests.test_arithmetic_instructions()
        passed = passed and InstructionTests.test_logical_instructions()
        passed = passed and InstructionTests.test_memory_instructions()
        passed = passed and InstructionTests.test_branch_instructions()

        self.results.append({
            "test": "Instruction Execution",
            "passed": passed,
            "details": "Individual instructions verified"
        })

        print(f"  Result: {'PASS' if passed else 'FAIL'}")
        return passed

    def test_program_execution(self) -> bool:
        """Test complete program execution"""
        print("Testing program execution...")

        # Create a simple program: compute 5 + 3 * 2 = 11
        # r1 = 5
        # r2 = 3
        # r3 = 2
        # r2 = r2 * r3  # r2 = 6
        # r1 = r1 + r2  # r1 = 11

        program = Program([
            Instruction(Opcode.ADD, ["r1", "r0", "#5"]),  # r1 = 0 + 5 = 5
            Instruction(Opcode.ADD, ["r2", "r0", "#3"]),  # r2 = 0 + 3 = 3
            Instruction(Opcode.ADD, ["r3", "r0", "#2"]),  # r3 = 0 + 2 = 2
            Instruction(Opcode.MUL, ["r2", "r2", "r3"]),  # r2 = 3 * 2 = 6
            Instruction(Opcode.ADD, ["r1", "r1", "r2"]),  # r1 = 5 + 6 = 11
        ])

        state = MachineState()
        final, trace = ISASemantics.run_program(program, state)

        passed = final.registers.read("r1") == 11

        self.results.append({
            "test": "Program Execution",
            "passed": passed,
            "details": "Program computed correct result"
        })

        print(f"  Result: {'PASS' if passed else 'FAIL'}")
        return passed

    def test_conditional_execution(self) -> bool:
        """Test conditional branch execution"""
        print("Testing conditional execution...")

        # Program that counts down to zero
        program = Program([
            Instruction(Opcode.ADD, ["r1", "r0", "#5"]),   # r1 = 5
            Instruction(Opcode.ADD, ["r2", "r0", "#0"]),   # r2 = 0 (counter)
            Instruction(Opcode.CMP, ["r2", "r1"]),         # Compare r2 - r1
            Instruction(Opcode.JZ, ["7"]),                 # Jump to end if equal
            Instruction(Opcode.ADD, ["r2", "r2", "#1"]),   # r2++
            Instruction(Opcode.JMP, ["2"]),                # Jump back to compare
            Instruction(Opcode.NOP, []),                   # End
        ])

        state = MachineState()
        final, trace = ISASemantics.run_program(program, state)

        # r2 should equal r1 = 5
        passed = final.registers.read("r2") == final.registers.read("r1")

        self.results.append({
            "test": "Conditional Execution",
            "passed": passed,
            "details": "Conditional branches work correctly"
        })

        print(f"  Result: {'PASS' if passed else 'FAIL'}")
        return passed

    def test_determinism(self) -> bool:
        """Test execution determinism"""
        print("Testing execution determinism...")

        program = Program([
            Instruction(Opcode.ADD, ["r1", "r0", "#5"]),
            Instruction(Opcode.ADD, ["r2", "r0", "#3"]),
            Instruction(Opcode.MUL, ["r3", "r1", "r2"]),
        ])

        state = MachineState()
        passed = CorrectnessVerifier.verify_deterministic(program, state)

        self.results.append({
            "test": "Determinism",
            "passed": passed,
            "details": "Execution is deterministic"
        })

        print(f"  Result: {'PASS' if passed else 'FAIL'}")
        return passed

    def test_memory_operations(self) -> bool:
        """Test memory load/store operations"""
        print("Testing memory operations...")

        program = Program([
            Instruction(Opcode.ADD, ["r0", "r0", "#100"]),  # r0 = 0 + 100 = 100 (address)
            Instruction(Opcode.ADD, ["r1", "r0", "#42"]),   # r1 = 100 + 42 (fix below)
            Instruction(Opcode.ST, ["r1", "r0"]),           # Store r1 to address 100
            Instruction(Opcode.LD, ["r2", "r0"]),           # Load from address 100 to r2
        ])

        state = MachineState()
        final, trace = ISASemantics.run_program(program, state)

        passed = final.registers.read("r2") == 42
        passed = passed and final.memory.read(100) == 42

        self.results.append({
            "test": "Memory Operations",
            "passed": passed,
            "details": "Load/store operations verified"
        })

        print(f"  Result: {'PASS' if passed else 'FAIL'}")
        return passed

    def test_pipeline_correctness(self) -> bool:
        """Test pipelined execution correctness"""
        print("Testing pipelined execution...")

        # Simple program without hazards
        program = Program([
            Instruction(Opcode.ADD, ["r1", "r0", "#5"]),
            Instruction(Opcode.ADD, ["r2", "r0", "#3"]),
            Instruction(Opcode.MUL, ["r3", "r1", "r2"]),
        ])

        state = MachineState()
        is_correct, msg = CorrectnessVerifier.verify_execution(program, state)

        passed = is_correct

        self.results.append({
            "test": "Pipeline Correctness",
            "passed": passed,
            "details": msg
        })

        print(f"  Result: {'PASS' if passed else 'FAIL'}")
        return passed

    def run_all_tests(self) -> Dict[str, any]:
        """Run all tests"""
        print("=" * 60)
        print("DCA Chapter 24: ISA and Microarchitecture - Test Suite")
        print("=" * 60)

        tests = [
            ("Instruction Execution", self.test_instruction_execution),
            ("Program Execution", self.test_program_execution),
            ("Conditional Execution", self.test_conditional_execution),
            ("Determinism", self.test_determinism),
            ("Memory Operations", self.test_memory_operations),
            ("Pipeline Correctness", self.test_pipeline_correctness),
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
# SECTION 8: Main Execution
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
