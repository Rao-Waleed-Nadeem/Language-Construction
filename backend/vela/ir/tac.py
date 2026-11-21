"""Three-Address Code (TAC) data model and instructions.

Defined per:
- docs/09_TAC_SPECIFICATION.md
- Master Spec P5-01..P5-11
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from vela.common.source import Span


@dataclass(frozen=True)
class Constant:
    """Literal constant operand."""

    value: Any
    type_name: str

    def __str__(self) -> str:
        if self.type_name == "string":
            return f'"{self.value}"'
        if self.type_name == "char":
            return f"'{self.value}'"
        if self.type_name == "bool":
            return "true" if self.value else "false"
        return str(self.value)

    def to_dict(self) -> dict[str, Any]:
        return {"kind": "constant", "value": self.value, "type": self.type_name}


@dataclass(frozen=True)
class Variable:
    """Named variable operand."""

    name: str

    def __str__(self) -> str:
        return self.name

    def to_dict(self) -> dict[str, Any]:
        return {"kind": "variable", "name": self.name}


@dataclass(frozen=True)
class Temporary:
    """Compiler-generated temporary variable."""

    id: int
    type_name: str = "any"

    def __str__(self) -> str:
        return f"t{self.id}"

    def to_dict(self) -> dict[str, Any]:
        return {"kind": "temporary", "id": self.id, "name": f"t{self.id}", "type": self.type_name}


@dataclass(frozen=True)
class Label:
    """Symbolic jump target operand."""

    name: str

    def __str__(self) -> str:
        return self.name

    def to_dict(self) -> dict[str, Any]:
        return {"kind": "label", "name": self.name}


TACOperand = Constant | Variable | Temporary | Label


@dataclass
class TACInstruction:
    """A single Three-Address Code quadruple."""

    opcode: str
    arg1: TACOperand | None = None
    arg2: TACOperand | None = None
    result: TACOperand | None = None
    src_span: Span = field(default_factory=Span.zero)
    ast_id: int = 0
    rule_id: str = "TAC-RAW"

    def to_dict(self) -> dict[str, Any]:
        return {
            "opcode": self.opcode,
            "arg1": self.arg1.to_dict() if self.arg1 is not None else None,
            "arg2": self.arg2.to_dict() if self.arg2 is not None else None,
            "result": self.result.to_dict() if self.result is not None else None,
            "src_span": self.src_span.to_dict(),
            "ast_id": self.ast_id,
            "rule_id": self.rule_id,
            "text": str(self),
        }

    def __str__(self) -> str:
        op = self.opcode
        a1 = str(self.arg1) if self.arg1 is not None else ""
        a2 = str(self.arg2) if self.arg2 is not None else ""
        res = str(self.result) if self.result is not None else ""

        if op == "LABEL":
            return f"{res}:"
        if op == "ASSIGN":
            return f"{res} = {a1}"
        if op in ("ADD", "SUB", "MUL", "DIV", "MOD", "LT", "LE", "GT", "GE", "EQ", "NE"):
            sym = {
                "ADD": "+",
                "SUB": "-",
                "MUL": "*",
                "DIV": "/",
                "MOD": "%",
                "LT": "<",
                "LE": "<=",
                "GT": ">",
                "GE": ">=",
                "EQ": "==",
                "NE": "!=",
            }[op]
            return f"{res} = {a1} {sym} {a2}"
        if op == "NEG":
            return f"{res} = -{a1}"
        if op == "NOT":
            return f"{res} = !{a1}"
        if op == "JUMP":
            return f"goto {res}"
        if op == "JUMP_IF":
            return f"if {a1} goto {res}"
        if op == "JUMP_IF_FALSE":
            return f"ifFalse {a1} goto {res}"
        if op == "FUNC_BEGIN":
            return f"func {res}:"
        if op == "FUNC_END":
            return f"endfunc {res}"
        if op == "PARAM":
            return f"param {a1}"
        if op == "CALL":
            return f"{res} = call {a1}, {a2}" if res else f"call {a1}, {a2}"
        if op == "RETURN":
            return f"return {a1}" if a1 else "return"
        if op == "ARRAY_GET":
            return f"{res} = {a1}[{a2}]"
        if op == "ARRAY_SET":
            return f"{a1}[{a2}] = {res}"
        if op == "CAST":
            return f"{res} = cast({a1}, {a2})"
        if op == "SHOW":
            return f"show {a1}"
        if op == "SHOW_NL":
            return "show_nl"
        if op == "READ":
            return f"read {res}"

        return f"{op} {a1} {a2} {res}".strip()


@dataclass
class TACProgram:
    """Complete collection of TAC instructions for a compilation unit."""

    instructions: list[TACInstruction]

    def get_labels(self) -> set[str]:
        """Collect all defined label names."""
        labels = set()
        for instr in self.instructions:
            if instr.opcode == "LABEL" and isinstance(instr.result, Label):
                labels.add(instr.result.name)
        return labels

    def get_jump_targets(self) -> set[str]:
        """Collect all jump target names referenced by instructions."""
        targets = set()
        for instr in self.instructions:
            if instr.opcode in ("JUMP", "JUMP_IF", "JUMP_IF_FALSE") and isinstance(instr.result, Label):
                targets.add(instr.result.name)
        return targets

    def validate_labels(self) -> list[str]:
        """Verify that every jump target label is defined.

        Returns a list of missing label names (empty if valid).
        """
        defined = self.get_labels()
        targeted = self.get_jump_targets()
        missing = [t for t in targeted if t not in defined]
        return missing

    def contains_plain_boolean_ops(self) -> bool:
        """Verify that no forbidden plain AND/OR opcodes exist."""
        forbidden = {"AND", "OR"}
        return any(instr.opcode in forbidden for instr in self.instructions)

    def to_text(self) -> str:
        """Render instructions into formatted TAC text."""
        lines: list[str] = []
        for instr in self.instructions:
            s = str(instr)
            if instr.opcode in ("LABEL", "FUNC_BEGIN", "FUNC_END"):
                lines.append(s)
            else:
                lines.append(f"    {s}")
        return "\n".join(lines)

    def to_dict(self) -> dict[str, Any]:
        return {
            "instruction_count": len(self.instructions),
            "instructions": [instr.to_dict() for instr in self.instructions],
            "text": self.to_text(),
        }
