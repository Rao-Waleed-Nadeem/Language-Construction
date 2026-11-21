"""Virtual Machine Simulation Engine and Step Reversibility.

Defined per:
- docs/11_TARGET_CODE_AND_VM_SPECIFICATION.md §4
- Master Spec P7-07
- Acceptance criteria:
  - AC-V1: stdout equals expected output for all valid examples.
  - AC-V2: stepping backward restores previous register values exactly.
  - AC-V3: runtime errors highlight faulting instruction with exact code.
  - AC-V4: programs over 5,000 steps truncate snapshot history without breaking execution.
  - AC-V5: unified stdin consumption.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from typing import Any

from vela.codegen.isa import (
    Immediate,
    MemoryRef,
    Register,
    TargetProgram,
)
from vela.common.diagnostics import Diagnostic
from vela.common.limits import INT32_MAX, INT32_MIN, LIMITS, wrap32
from vela.common.source import Span
from vela.vm.cpu import CPUState
from vela.vm.memory import VMMemory


@dataclass
class VMSnapshot:
    """Historical state snapshot for stepping forward and backward."""

    step: int
    pc: int
    instruction_text: str
    registers: dict[str, Any]
    flags: dict[str, bool]
    stdout_length: int
    call_depth: int
    stack: list[Any] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "step": self.step,
            "pc": self.pc,
            "instruction_text": self.instruction_text,
            "registers": dict(self.registers),
            "flags": dict(self.flags),
            "stdout_length": self.stdout_length,
            "call_depth": self.call_depth,
            "stack": list(self.stack[-8:]),  # Show top 8 stack elements in UI
        }


@dataclass
class VMResult:
    """Complete result of executing a target program in the Virtual Machine."""

    stdout: str
    exit_code: int
    steps_executed: int
    snapshots: list[VMSnapshot] = field(default_factory=list)
    truncated_snapshots: bool = False
    diagnostics: list[Diagnostic] = field(default_factory=list)
    total_cost: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "stdout": self.stdout,
            "exit_code": self.exit_code,
            "steps_executed": self.steps_executed,
            "snapshots_count": len(self.snapshots),
            "truncated_snapshots": self.truncated_snapshots,
            "total_cost": self.total_cost,
            "diagnostics": [d.to_dict() for d in self.diagnostics],
            "snapshots": [s.to_dict() for s in self.snapshots],
        }


class VirtualMachine:
    """Register Machine Virtual Machine implementing Phase 7 execution."""

    def __init__(self) -> None:
        self.cpu = CPUState()
        self.memory = VMMemory()
        self.program: TargetProgram = TargetProgram()
        self.stdout: str = ""
        self.stdin: str = ""
        self.stdin_pos: int = 0
        self.call_stack: list[tuple[int, int, dict[str, Any]]] = []  # stack of (return PC, FP, saved regs)
        self.param_queue: list[Any] = []  # argument passing queue
        self.snapshots: list[VMSnapshot] = []
        self.history: list[tuple[CPUState, VMMemory, str, int, list[Any], list[tuple[int, int, dict[str, Any]]]]] = []
        self.steps_executed: int = 0
        self.total_cost: int = 0
        self.diagnostics: list[Diagnostic] = []
        self.exit_code: int = 0
        self.halted: bool = False

    def load(self, program: TargetProgram, stdin: str = "") -> None:
        """Load target program and reset CPU/memory state."""
        self.cpu = CPUState()
        self.memory = VMMemory()
        self.program = program
        self.stdout = ""
        self.stdin = stdin
        self.stdin_pos = 0
        self.call_stack = []
        self.param_queue = []
        self.snapshots = []
        self.history = []
        self.steps_executed = 0
        self.total_cost = 0
        self.diagnostics = []
        self.exit_code = 0
        self.halted = False

    def _resolve_operand(self, op: Any) -> Any:
        if op is None:
            return None
        if isinstance(op, Immediate):
            return op.value
        if isinstance(op, Register):
            return self.cpu.get_reg(op.name)
        if isinstance(op, MemoryRef):
            # Resolve memory reference
            if op.symbol is not None:
                return self.memory.globals.get(op.symbol, 0)
            if op.base is not None:
                base_val = self.cpu.get_reg(op.base.name)
                # Stack displacement: base + offset
                addr = base_val + op.offset
                return self.memory.stack.get(addr, 0)
        if isinstance(op, str):
            # Check if variable in globals
            if op in self.memory.globals:
                return self.memory.globals[op]
            return op
        return op

    def _set_operand(self, op: Any, val: Any) -> None:
        if isinstance(op, Register):
            self.cpu.set_reg(op.name, val)
        elif isinstance(op, MemoryRef):
            if op.symbol is not None:
                self.memory.globals[op.symbol] = val
            elif op.base is not None:
                base_val = self.cpu.get_reg(op.base.name)
                addr = base_val + op.offset
                self.memory.stack[addr] = val
        elif isinstance(op, str):
            self.memory.globals[op] = val

    # Stdin stream parsing helpers
    def _skip_whitespace(self) -> None:
        while self.stdin_pos < len(self.stdin) and self.stdin[self.stdin_pos].isspace():
            self.stdin_pos += 1

    def _read_next_token(self) -> str:
        self._skip_whitespace()
        if self.stdin_pos >= len(self.stdin):
            return ""
        start = self.stdin_pos
        while self.stdin_pos < len(self.stdin) and not self.stdin[self.stdin_pos].isspace():
            self.stdin_pos += 1
        return self.stdin[start : self.stdin_pos]

    def _read_next_char(self) -> str:
        self._skip_whitespace()
        if self.stdin_pos >= len(self.stdin):
            return ""
        ch = self.stdin[self.stdin_pos]
        self.stdin_pos += 1
        return ch

    def _cast_value(self, val: Any, target_type: str) -> Any:
        if target_type == "int":
            if isinstance(val, float):
                trunc = int(val)
                if not (INT32_MIN <= trunc <= INT32_MAX):
                    self._error("VL-RUN-005", "conversion out of range")
                    return None
                return trunc
            if isinstance(val, str):
                return ord(val)
            if isinstance(val, bool):
                return 1 if val else 0
            return int(val)

        if target_type == "float":
            return float(val)

        if target_type == "char":
            c_int = int(val)
            if not (0 <= c_int <= 255):
                self._error("VL-RUN-005", "conversion out of range")
                return None
            return chr(c_int)

        if target_type == "string":
            if isinstance(val, bool):
                return "true" if val else "false"
            return str(val)

        if target_type == "bool":
            return bool(val)

        return val

    def step(self) -> bool:
        """Execute a single target instruction. Returns True if execution continues."""
        if self.halted or self.cpu.pc >= len(self.program.instructions):
            self.halted = True
            return False

        if self.steps_executed >= LIMITS.MAX_VM_INSTRUCTIONS:
            self._error("VL-RUN-007", "instruction budget exceeded (1,000,000 steps)")
            return False

        if len(self.call_stack) >= LIMITS.MAX_VM_CALL_DEPTH:
            self._error("VL-RUN-006", "call stack overflow (depth > 1000)")
            return False

        if len(self.stdout) >= LIMITS.MAX_VM_OUTPUT_LENGTH:
            self._error("VL-RUN-008", "output length limit exceeded (100,000 chars)")
            return False

        instr = self.program.instructions[self.cpu.pc]
        op = instr.opcode

        # Save historical snapshot for reversible debugging (capped at MAX_VM_SNAPSHOTS)
        if len(self.snapshots) < LIMITS.MAX_VM_SNAPSHOTS:
            self.history.append((copy.deepcopy(self.cpu), copy.deepcopy(self.memory), self.stdout, self.stdin_pos, list(self.param_queue), copy.deepcopy(self.call_stack)))
            self.snapshots.append(
                VMSnapshot(
                    step=self.steps_executed + 1,
                    pc=self.cpu.pc,
                    instruction_text=str(instr).strip(),
                    registers=dict(self.cpu.registers),
                    flags={"ZF": self.cpu.zf, "SF": self.cpu.sf},
                    stdout_length=len(self.stdout),
                    call_depth=len(self.call_stack),
                    stack=list(self.param_queue[-8:]),
                )
            )

        self.steps_executed += 1
        self.total_cost += instr.cost
        self.cpu.pc += 1

        # Instruction execution dispatch
        if op == "LABEL":
            return True

        if op == "HLT":
            self.halted = True
            return False

        if op == "MOV":
            val = self._resolve_operand(instr.src1)
            self._set_operand(instr.dst, val)

        elif op == "LOAD":
            val = self._resolve_operand(instr.src1)
            # If array index operand present in src2
            if instr.src2 is not None:
                idx_val = self._resolve_operand(instr.src2)
                try:
                    val = self.memory.read_array(int(val), int(idx_val))
                except (IndexError, KeyError) as err:
                    self._error("VL-RUN-002", str(err))
                    return False
            self._set_operand(instr.dst, val)

        elif op == "STORE":
            # If array element store: dst is array handle, src1 is index, src2 is value
            if instr.src2 is not None:
                handle = self._resolve_operand(instr.dst)
                idx_val = self._resolve_operand(instr.src1)
                val = self._resolve_operand(instr.src2)
                try:
                    self.memory.write_array(int(handle), int(idx_val), val)
                except (IndexError, KeyError) as err:
                    self._error("VL-RUN-002", str(err))
                    return False
            else:
                val = self._resolve_operand(instr.src1)
                self._set_operand(instr.dst, val)

        elif op in ("ADD", "SUB", "MUL", "DIV", "MOD"):
            v1 = self._resolve_operand(instr.src1)
            v2 = self._resolve_operand(instr.src2)

            if op in ("DIV", "MOD") and v2 == 0:
                self._error("VL-RUN-001", "division or modulo by zero")
                return False

            if op == "ADD":
                if isinstance(v1, str) or isinstance(v2, str):
                    res = f"{v1}{v2}"
                elif isinstance(v1, float) or isinstance(v2, float):
                    res = float(v1) + float(v2)
                else:
                    res = wrap32(int(v1) + int(v2))
            elif op == "SUB":
                if isinstance(v1, float) or isinstance(v2, float):
                    res = float(v1) - float(v2)
                else:
                    res = wrap32(int(v1) - int(v2))
            elif op == "MUL":
                if isinstance(v1, float) or isinstance(v2, float):
                    res = float(v1) * float(v2)
                else:
                    res = wrap32(int(v1) * int(v2))
            elif op == "DIV":
                if isinstance(v1, float) or isinstance(v2, float):
                    res = float(v1) / float(v2)
                else:
                    res = wrap32(int(int(v1) / int(v2)))
            elif op == "MOD":
                div = int(int(v1) / int(v2))
                res = wrap32(int(v1) - div * int(v2))

            self._set_operand(instr.dst, res)

        elif op == "NEG":
            v = self._resolve_operand(instr.src1)
            res = -float(v) if isinstance(v, float) else wrap32(-int(v))
            self._set_operand(instr.dst, res)

        elif op == "NOT":
            v = self._resolve_operand(instr.src1)
            self._set_operand(instr.dst, not bool(v))

        elif op == "CMP":
            v1 = self._resolve_operand(instr.src1)
            v2 = self._resolve_operand(instr.src2)
            self.cpu.zf = v1 == v2
            self.cpu.sf = v1 < v2 if not isinstance(v1, str) else str(v1) < str(v2)

        elif op == "JMP":
            target = str(instr.dst)
            if target in self.program.labels:
                self.cpu.pc = self.program.labels[target]

        elif op == "JE":
            if self.cpu.zf:
                target = str(instr.dst)
                if target in self.program.labels:
                    self.cpu.pc = self.program.labels[target]

        elif op == "JNE":
            if not self.cpu.zf:
                target = str(instr.dst)
                if target in self.program.labels:
                    self.cpu.pc = self.program.labels[target]

        elif op == "JL":
            if self.cpu.sf and not self.cpu.zf:
                target = str(instr.dst)
                if target in self.program.labels:
                    self.cpu.pc = self.program.labels[target]

        elif op == "JLE":
            if self.cpu.sf or self.cpu.zf:
                target = str(instr.dst)
                if target in self.program.labels:
                    self.cpu.pc = self.program.labels[target]

        elif op == "JG":
            if not self.cpu.sf and not self.cpu.zf:
                target = str(instr.dst)
                if target in self.program.labels:
                    self.cpu.pc = self.program.labels[target]

        elif op == "JGE":
            if not self.cpu.sf:
                target = str(instr.dst)
                if target in self.program.labels:
                    self.cpu.pc = self.program.labels[target]

        elif op == "CALL":
            target = str(instr.dst)
            self.call_stack.append((self.cpu.pc, self.cpu.fp, dict(self.cpu.registers)))
            self.cpu.fp -= 256
            if target in self.program.labels:
                self.cpu.pc = self.program.labels[target]

        elif op == "RET":
            if self.call_stack:
                ret_pc, old_fp, old_regs = self.call_stack.pop()
                ret_val = self.cpu.registers.get("R0", 0)
                self.cpu.pc = ret_pc
                self.cpu.fp = old_fp
                self.cpu.registers = old_regs
                self.cpu.registers["R0"] = ret_val
            else:
                self.halted = True
                return False

        elif op == "PUSH":
            val = self._resolve_operand(instr.src1)
            self.param_queue.append(val)
            self.cpu.sp = len(self.param_queue)

        elif op == "POP":
            val = self.param_queue.pop(0) if self.param_queue else 0
            self._set_operand(instr.dst, val)
            self.cpu.sp = len(self.param_queue)

        elif op == "SYS_SHOW":
            val = self._resolve_operand(instr.src1)
            if isinstance(val, bool):
                self.stdout += "true" if val else "false"
            elif isinstance(val, float):
                # Float output formatting matching Python/Vela
                self.stdout += f"{val:.6g}" if abs(val) < 1e-4 else f"{val}"
            else:
                self.stdout += str(val)

        elif op == "SYS_SHOW_NL":
            self.stdout += "\n"

        elif op == "SYS_READ":
            tok = self._read_next_token()
            if not tok:
                self._error("VL-RUN-003", "unexpected end of standard input on read")
                return False
            val: Any = 0
            if tok in ("true", "false"):
                val = tok == "true"
            elif "." in tok:
                val = float(tok)
            else:
                try:
                    num = int(tok)
                    if not (INT32_MIN <= num <= INT32_MAX):
                        self._error("VL-RUN-004", f"integer '{tok}' does not fit in 32 bits")
                        return False
                    val = num
                except ValueError:
                    val = tok
            self._set_operand(instr.dst, val)

        elif op == "SYS_ALLOC":
            size_val = int(self._resolve_operand(instr.src1))
            res_val = self._resolve_operand(instr.src2)
            fill_val = 0 if res_val is None else res_val
            handle = self.memory.alloc_array(size_val, fill_val)
            self._set_operand(instr.dst, handle)

        elif op == "CAST":
            val = self._resolve_operand(instr.src1)
            target_type = str(self._resolve_operand(instr.src2))
            res = self._cast_value(val, target_type)
            if res is None and self.halted:
                return False
            self._set_operand(instr.dst, res)

        return True

    def step_back(self) -> bool:
        """Roll back state to the previous snapshot (reversible debugging)."""
        if not self.history:
            return False
        prev_cpu, prev_mem, prev_out, prev_pos, prev_params, prev_call_stack = self.history.pop()
        self.cpu = prev_cpu
        self.memory = prev_mem
        self.stdout = prev_out
        self.stdin_pos = prev_pos
        self.param_queue = prev_params
        self.call_stack = prev_call_stack
        self.halted = False
        if self.snapshots:
            self.snapshots.pop()
        return True

    def _error(self, code: str, message: str) -> None:
        self.halted = True
        self.exit_code = 1
        span = Span.zero()
        self.diagnostics.append(
            Diagnostic(
                code=code,
                message=message,
                span=span,
                severity="error",
                phase="runtime",
            )
        )

    def run(self, stdin: str = "") -> VMResult:
        """Run target program to completion."""
        self.stdin = stdin
        while self.step():
            pass

        return VMResult(
            stdout=self.stdout,
            exit_code=self.exit_code,
            steps_executed=self.steps_executed,
            snapshots=self.snapshots,
            truncated_snapshots=self.steps_executed > LIMITS.MAX_VM_SNAPSHOTS,
            diagnostics=self.diagnostics,
            total_cost=self.total_cost,
        )
