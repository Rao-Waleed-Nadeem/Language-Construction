"""Three-Address Code (TAC) Interpreter and Oracle.

Implements independent execution of TAC with exact runtime semantics:
- 32-bit two's complement integer arithmetic with wrap-around
- Truncating integer division (toward zero) and dividend-sign remainder
- IEEE double-precision floats
- Runtime diagnostics:
  VL-RUN-001: division or modulo by zero
  VL-RUN-002: array index out of bounds
  VL-RUN-003: input exhausted
  VL-RUN-004: invalid input format
  VL-RUN-005: conversion out of range
  VL-RUN-006: call stack overflow (depth > 1000)
  VL-RUN-007: instruction budget exceeded (budget: 1,000,000)
  VL-RUN-008: output limit exceeded (limit: 100,000 chars)

Defined per:
- docs/01_LANGUAGE_SPECIFICATION.md §10–§11, §16.4
- docs/09_TAC_SPECIFICATION.md
- Master Spec P5-12
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from vela.common.diagnostics import Diagnostic
from vela.common.source import Span
from vela.ir.tac import Constant, Label, TACOperand, TACProgram, Temporary, Variable

INT32_MIN = -2147483648
INT32_MAX = 2147483647


def wrap32(n: int) -> int:
    """Simulate 32-bit two's complement signed integer wrap-around."""
    n = n & 0xFFFFFFFF
    if n >= 0x80000000:
        n -= 0x100000000
    return n


class TACRuntimeError(Exception):
    """Runtime error during TAC interpretation."""

    def __init__(self, code: str, message: str, span: Span) -> None:
        super().__init__(f"[{code}] {message} at {span}")
        self.code = code
        self.message = message
        self.span = span

    def to_diagnostic(self) -> Diagnostic:
        return Diagnostic.create(
            code=self.code,
            span=self.span,
            message=self.message,
            severity="error",
            phase="runtime",
        )


@dataclass
class CallFrame:
    """Activation record for a function call."""

    func_name: str
    return_pc: int
    return_target: TACOperand | None
    locals: dict[str, Any] = field(default_factory=dict)
    incoming_params: list[Any] = field(default_factory=list)


@dataclass
class ExecutionResult:
    """Result of running TAC instructions."""

    stdout: str
    instructions_executed: int
    diagnostics: list[Diagnostic] = field(default_factory=list)
    success: bool = True
    exit_code: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "stdout": self.stdout,
            "instructions_executed": self.instructions_executed,
            "success": self.success,
            "exit_code": self.exit_code,
            "diagnostics": [d.to_dict() for d in self.diagnostics],
        }


class TACInterpreter:
    """Executes Three-Address Code with complete language runtime semantics."""

    def __init__(
        self,
        max_instructions: int = 1_000_000,
        max_call_depth: int = 1_000,
        max_output_chars: int = 100_000,
    ) -> None:
        self.max_instructions = max_instructions
        self.max_call_depth = max_call_depth
        self.max_output_chars = max_output_chars

    def interpret(self, program: TACProgram, stdin: str = "") -> ExecutionResult:
        """Interpret a TACProgram to completion or runtime error."""
        instructions = program.instructions
        if not instructions:
            return ExecutionResult(stdout="", instructions_executed=0)

        # 1. Build label and function entry map
        label_map: dict[str, int] = {}
        func_entries: dict[str, int] = {}
        for idx, instr in enumerate(instructions):
            if instr.opcode == "LABEL" and isinstance(instr.result, Label):
                label_map[instr.result.name] = idx
            elif instr.opcode == "FUNC_BEGIN" and isinstance(instr.result, Label):
                func_entries[instr.result.name] = idx

        # 2. State setup
        globals_mem: dict[str, Any] = {}
        call_stack: list[CallFrame] = []
        pending_args: list[Any] = []
        stdout_parts: list[str] = []
        total_output_chars = 0
        instructions_executed = 0

        # Tokenize stdin as a unified stream of characters/tokens
        stdin_pos = 0

        def skip_whitespace() -> None:
            nonlocal stdin_pos
            while stdin_pos < len(stdin) and stdin[stdin_pos].isspace():
                stdin_pos += 1

        def read_next_char() -> str:
            nonlocal stdin_pos
            skip_whitespace()
            if stdin_pos >= len(stdin):
                raise TACRuntimeError("VL-RUN-003", "input exhausted", current_span)
            ch = stdin[stdin_pos]
            stdin_pos += 1
            return ch

        def read_next_token() -> str:
            nonlocal stdin_pos
            skip_whitespace()
            if stdin_pos >= len(stdin):
                raise TACRuntimeError("VL-RUN-003", "input exhausted", current_span)
            start = stdin_pos
            while stdin_pos < len(stdin) and not stdin[stdin_pos].isspace():
                stdin_pos += 1
            return stdin[start:stdin_pos]

        def get_op_val(operand: TACOperand | None) -> Any:
            if operand is None:
                return None
            if isinstance(operand, Constant):
                return operand.value
            if isinstance(operand, Variable):
                name = operand.name
                if call_stack and name in call_stack[-1].locals:
                    return call_stack[-1].locals[name]
                if name in globals_mem:
                    return globals_mem[name]
                # Default value if uninitialized
                return 0
            if isinstance(operand, Temporary):
                key = f"t{operand.id}"
                if call_stack and key in call_stack[-1].locals:
                    return call_stack[-1].locals[key]
                return globals_mem.get(key, 0)
            if isinstance(operand, Label):
                return operand.name
            return None

        def set_op_val(operand: TACOperand | None, val: Any) -> None:
            if operand is None:
                return
            if isinstance(operand, Variable):
                name = operand.name
                if call_stack:
                    # If this variable is in locals or if it was declared locally
                    if name in call_stack[-1].locals or "_" in name:
                        call_stack[-1].locals[name] = val
                        return
                    if name in globals_mem:
                        globals_mem[name] = val
                        return
                    call_stack[-1].locals[name] = val
                else:
                    globals_mem[name] = val
            elif isinstance(operand, Temporary):
                key = f"t{operand.id}"
                if call_stack:
                    call_stack[-1].locals[key] = val
                else:
                    globals_mem[key] = val

        pc = 0
        current_span = Span.zero()

        try:
            while pc < len(instructions):
                instr = instructions[pc]
                current_span = instr.src_span
                instructions_executed += 1

                if instructions_executed > self.max_instructions:
                    raise TACRuntimeError(
                        "VL-RUN-007",
                        f"instruction budget exceeded ({self.max_instructions} limit)",
                        current_span,
                    )

                op = instr.opcode

                if op == "LABEL":
                    pc += 1

                elif op == "ASSIGN":
                    val = get_op_val(instr.arg1)
                    set_op_val(instr.result, val)
                    pc += 1

                elif op == "ADD":
                    v1 = get_op_val(instr.arg1)
                    v2 = get_op_val(instr.arg2)
                    if isinstance(v1, str) or isinstance(v2, str):
                        res = str(v1) + str(v2)
                    elif isinstance(v1, float) or isinstance(v2, float):
                        res = float(v1) + float(v2)
                    else:
                        res = wrap32(int(v1) + int(v2))
                    set_op_val(instr.result, res)
                    pc += 1

                elif op == "SUB":
                    v1 = get_op_val(instr.arg1)
                    v2 = get_op_val(instr.arg2)
                    if isinstance(v1, float) or isinstance(v2, float):
                        res = float(v1) - float(v2)
                    else:
                        res = wrap32(int(v1) - int(v2))
                    set_op_val(instr.result, res)
                    pc += 1

                elif op == "MUL":
                    v1 = get_op_val(instr.arg1)
                    v2 = get_op_val(instr.arg2)
                    if isinstance(v1, float) or isinstance(v2, float):
                        res = float(v1) * float(v2)
                    else:
                        res = wrap32(int(v1) * int(v2))
                    set_op_val(instr.result, res)
                    pc += 1

                elif op == "DIV":
                    v1 = get_op_val(instr.arg1)
                    v2 = get_op_val(instr.arg2)
                    if isinstance(v1, float) or isinstance(v2, float):
                        if float(v2) == 0.0:
                            raise TACRuntimeError("VL-RUN-001", "division by zero", current_span)
                        res = float(v1) / float(v2)
                    else:
                        if int(v2) == 0:
                            raise TACRuntimeError("VL-RUN-001", "division by zero", current_span)
                        res = wrap32(int(int(v1) / int(v2)))
                    set_op_val(instr.result, res)
                    pc += 1

                elif op == "MOD":
                    v1 = get_op_val(instr.arg1)
                    v2 = get_op_val(instr.arg2)
                    if int(v2) == 0:
                        raise TACRuntimeError("VL-RUN-001", "modulo by zero", current_span)
                    # C99/Vela remainder has sign of dividend: a - (int(a / b) * b)
                    a = int(v1)
                    b = int(v2)
                    rem = a - (int(a / b) * b)
                    set_op_val(instr.result, wrap32(rem))
                    pc += 1

                elif op == "NEG":
                    v1 = get_op_val(instr.arg1)
                    if isinstance(v1, float):
                        res = -v1
                    else:
                        res = wrap32(-int(v1))
                    set_op_val(instr.result, res)
                    pc += 1

                elif op == "NOT":
                    v1 = get_op_val(instr.arg1)
                    set_op_val(instr.result, not bool(v1))
                    pc += 1

                elif op in ("LT", "LE", "GT", "GE", "EQ", "NE"):
                    v1 = get_op_val(instr.arg1)
                    v2 = get_op_val(instr.arg2)
                    if isinstance(v1, str) and isinstance(v2, str):
                        c1, c2 = v1, v2
                    elif isinstance(v1, float) or isinstance(v2, float):
                        c1, c2 = float(v1), float(v2)
                    else:
                        c1, c2 = v1, v2

                    if op == "LT":
                        res = c1 < c2
                    elif op == "LE":
                        res = c1 <= c2
                    elif op == "GT":
                        res = c1 > c2
                    elif op == "GE":
                        res = c1 >= c2
                    elif op == "EQ":
                        res = c1 == c2
                    elif op == "NE":
                        res = c1 != c2
                    set_op_val(instr.result, res)
                    pc += 1

                elif op == "JUMP":
                    target_name = instr.result.name if isinstance(instr.result, Label) else str(instr.result)
                    pc = label_map[target_name]

                elif op == "JUMP_IF":
                    cond = bool(get_op_val(instr.arg1))
                    if cond:
                        target_name = instr.result.name if isinstance(instr.result, Label) else str(instr.result)
                        pc = label_map[target_name]
                    else:
                        pc += 1

                elif op == "JUMP_IF_FALSE":
                    cond = bool(get_op_val(instr.arg1))
                    if not cond:
                        target_name = instr.result.name if isinstance(instr.result, Label) else str(instr.result)
                        pc = label_map[target_name]
                    else:
                        pc += 1

                elif op == "ALLOC_ARRAY":
                    size = int(get_op_val(instr.arg1))
                    def_val = get_op_val(instr.arg2)
                    arr = [def_val for _ in range(size)]
                    set_op_val(instr.result, arr)
                    pc += 1

                elif op == "ARRAY_GET":
                    arr = get_op_val(instr.arg1)
                    idx = int(get_op_val(instr.arg2))
                    if not isinstance(arr, list) or idx < 0 or idx >= len(arr):
                        sz = len(arr) if isinstance(arr, list) else 0
                        raise TACRuntimeError(
                            "VL-RUN-002",
                            f"array index {idx} out of bounds for array of size {sz}",
                            current_span,
                        )
                    set_op_val(instr.result, arr[idx])
                    pc += 1

                elif op == "ARRAY_SET":
                    val = get_op_val(instr.arg1)
                    idx = int(get_op_val(instr.arg2))
                    arr = get_op_val(instr.result)
                    if not isinstance(arr, list) or idx < 0 or idx >= len(arr):
                        sz = len(arr) if isinstance(arr, list) else 0
                        raise TACRuntimeError(
                            "VL-RUN-002",
                            f"array index {idx} out of bounds for array of size {sz}",
                            current_span,
                        )
                    arr[idx] = val
                    pc += 1

                elif op == "CAST":
                    val = get_op_val(instr.arg1)
                    target_type = (
                        instr.arg2.value
                        if isinstance(instr.arg2, Constant)
                        else (instr.arg2.name if isinstance(instr.arg2, (Variable, Label)) else str(instr.arg2))
                    )
                    res = self._cast_value(val, str(target_type), current_span)
                    set_op_val(instr.result, res)
                    pc += 1

                elif op == "PARAM":
                    pending_args.append(get_op_val(instr.arg1))
                    pc += 1

                elif op == "CALL":
                    target_func = instr.arg1.name if isinstance(instr.arg1, Label) else str(instr.arg1)
                    n_args = int(get_op_val(instr.arg2))
                    passed_args = pending_args[-n_args:] if n_args > 0 else []
                    if n_args > 0:
                        del pending_args[-n_args:]

                    if len(call_stack) >= self.max_call_depth:
                        raise TACRuntimeError(
                            "VL-RUN-006",
                            f"call stack overflow (depth > {self.max_call_depth})",
                            current_span,
                        )

                    entry_pc = func_entries.get(target_func)
                    if entry_pc is None:
                        # Fallback to label_map
                        entry_pc = label_map.get(target_func)

                    if entry_pc is None:
                        raise TACRuntimeError("VL-RUN-000", f"undefined function '{target_func}'", current_span)

                    frame = CallFrame(
                        func_name=target_func,
                        return_pc=pc + 1,
                        return_target=instr.result,
                        incoming_params=passed_args,
                    )
                    call_stack.append(frame)
                    pc = entry_pc + 1  # jump past FUNC_BEGIN

                elif op == "RECEIVE":
                    if call_stack and call_stack[-1].incoming_params:
                        param_val = call_stack[-1].incoming_params.pop(0)
                        set_op_val(instr.result, param_val)
                    pc += 1

                elif op == "RETURN":
                    ret_val = get_op_val(instr.arg1) if instr.arg1 is not None else None
                    if not call_stack:
                        # Return at global startup terminates program execution
                        break
                    frame = call_stack.pop()
                    if frame.return_target is not None:
                        set_op_val(frame.return_target, ret_val)
                    pc = frame.return_pc

                elif op in ("FUNC_BEGIN", "FUNC_END"):
                    pc += 1

                elif op == "SHOW":
                    val = get_op_val(instr.arg1)
                    formatted = self._format_output(val)
                    stdout_parts.append(formatted)
                    total_output_chars += len(formatted)
                    if total_output_chars > self.max_output_chars:
                        raise TACRuntimeError(
                            "VL-RUN-008",
                            f"output limit exceeded ({self.max_output_chars} chars)",
                            current_span,
                        )
                    pc += 1

                elif op == "SHOW_NL":
                    stdout_parts.append("\n")
                    total_output_chars += 1
                    if total_output_chars > self.max_output_chars:
                        raise TACRuntimeError(
                            "VL-RUN-008",
                            f"output limit exceeded ({self.max_output_chars} chars)",
                            current_span,
                        )
                    pc += 1

                elif op == "READ":
                    target_type = (
                        instr.arg1.value
                        if isinstance(instr.arg1, Constant)
                        else (str(instr.arg1) if instr.arg1 is not None else "string")
                    )
                    val = self._read_value(target_type, read_next_token, read_next_char, current_span)
                    set_op_val(instr.result, val)
                    pc += 1

                else:
                    pc += 1

        except TACRuntimeError as err:
            diag = err.to_diagnostic()
            return ExecutionResult(
                stdout="".join(stdout_parts),
                instructions_executed=instructions_executed,
                diagnostics=[diag],
                success=False,
                exit_code=1,
            )

        return ExecutionResult(
            stdout="".join(stdout_parts),
            instructions_executed=instructions_executed,
            diagnostics=[],
            success=True,
            exit_code=0,
        )

    def _cast_value(self, val: Any, target_type: str, span: Span) -> Any:
        if target_type == "int":
            if isinstance(val, float):
                # Truncates toward zero
                trunc = int(val)
                if not (INT32_MIN <= trunc <= INT32_MAX):
                    raise TACRuntimeError("VL-RUN-005", "conversion out of range", span)
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
                raise TACRuntimeError("VL-RUN-005", "conversion out of range", span)
            return chr(c_int)

        if target_type == "string":
            if isinstance(val, bool):
                return "true" if val else "false"
            return str(val)

        if target_type == "bool":
            return bool(val)

        return val

    def _format_output(self, val: Any) -> str:
        if isinstance(val, bool):
            return "true" if val else "false"
        if isinstance(val, float):
            # Shortest round-tripping string per Language Spec §10
            return str(val)
        return str(val)

    def _read_value(
        self,
        target_type: str,
        read_token: Any,
        read_char: Any,
        span: Span,
    ) -> Any:
        if target_type == "char":
            return read_char()

        tok = read_token()
        if target_type == "int":
            if not re.fullmatch(r"[+-]?[0-9]+", tok):
                raise TACRuntimeError("VL-RUN-004", f"invalid input format for int: '{tok}'", span)
            num = int(tok)
            if not (INT32_MIN <= num <= INT32_MAX):
                raise TACRuntimeError("VL-RUN-004", f"integer '{tok}' does not fit in 32 bits", span)
            return num

        if target_type == "float":
            if not re.fullmatch(r"[+-]?[0-9]+(\.[0-9]+)?", tok):
                raise TACRuntimeError("VL-RUN-004", f"invalid input format for float: '{tok}'", span)
            return float(tok)

        if target_type == "bool":
            if tok not in ("true", "false"):
                raise TACRuntimeError("VL-RUN-004", f"invalid input format for bool: '{tok}'", span)
            return tok == "true"

        return tok
