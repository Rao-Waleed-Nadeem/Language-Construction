"""Target Instruction Set Architecture (ISA) Definition.

Defined per:
- docs/11_TARGET_CODE_AND_VM_SPECIFICATION.md §2
- Master Spec P7-01
- 8 General-Purpose Registers (R0-R7), SP, FP, PC, condition flags.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Register:
    """CPU Register identifier."""

    name: str

    def __str__(self) -> str:
        return self.name

    def to_dict(self) -> dict[str, Any]:
        return {"kind": "register", "name": self.name}


@dataclass(frozen=True)
class Immediate:
    """Immediate constant operand."""

    value: Any

    def __str__(self) -> str:
        if isinstance(self.value, str):
            return f'"{self.value}"'
        if isinstance(self.value, bool):
            return "true" if self.value else "false"
        return str(self.value)

    def to_dict(self) -> dict[str, Any]:
        return {"kind": "immediate", "value": self.value}


@dataclass(frozen=True)
class MemoryRef:
    """Memory address reference (displacement [base + offset] or direct [symbol])."""

    base: Register | None = None
    offset: int = 0
    symbol: str | None = None

    def __str__(self) -> str:
        if self.symbol is not None:
            if self.offset != 0:
                return f"[{self.symbol} + {self.offset}]"
            return f"[{self.symbol}]"
        if self.base is not None:
            if self.offset > 0:
                return f"[{self.base} + {self.offset}]"
            if self.offset < 0:
                return f"[{self.base} - {-self.offset}]"
            return f"[{self.base}]"
        return f"[{self.offset}]"

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": "memory",
            "base": self.base.name if self.base else None,
            "offset": self.offset,
            "symbol": self.symbol,
            "text": str(self),
        }


TargetOperand = Register | Immediate | MemoryRef | str


@dataclass
class TargetInstruction:
    """A single instruction in the target register-machine ISA."""

    opcode: str
    dst: TargetOperand | None = None
    src1: TargetOperand | None = None
    src2: TargetOperand | None = None
    cost: int = 1
    tac_index: int = 0
    rule_name: str = "DEFAULT"
    comment: str = ""

    def __str__(self) -> str:
        op = self.opcode
        if op == "LABEL":
            return f"{self.dst}:"

        operands: list[str] = []
        for oper in (self.dst, self.src1, self.src2):
            if oper is not None:
                operands.append(str(oper))

        ops_str = ", ".join(operands)
        line = f"    {op:<10} {ops_str}" if ops_str else f"    {op}"
        if self.comment:
            line += f"  ; {self.comment}"
        return line

    def to_dict(self) -> dict[str, Any]:
        return {
            "opcode": self.opcode,
            "dst": self.dst.to_dict() if hasattr(self.dst, "to_dict") else str(self.dst) if self.dst else None,
            "src1": self.src1.to_dict() if hasattr(self.src1, "to_dict") else str(self.src1) if self.src1 else None,
            "src2": self.src2.to_dict() if hasattr(self.src2, "to_dict") else str(self.src2) if self.src2 else None,
            "cost": self.cost,
            "tac_index": self.tac_index,
            "rule_name": self.rule_name,
            "comment": self.comment,
            "text": str(self).strip(),
        }


@dataclass
class TargetProgram:
    """Complete executable target machine program."""

    instructions: list[TargetInstruction] = field(default_factory=list)
    labels: dict[str, int] = field(default_factory=dict)

    def total_cost(self) -> int:
        """Calculate total base execution cost of the program."""
        return sum(instr.cost for instr in self.instructions)

    def to_text(self) -> str:
        return "\n".join(str(i) for i in self.instructions)

    def to_dict(self) -> dict[str, Any]:
        return {
            "instruction_count": len(self.instructions),
            "total_cost": self.total_cost(),
            "instructions": [i.to_dict() for i in self.instructions],
            "labels": self.labels,
            "text": self.to_text(),
        }


# Standard Register Constants
R0 = Register("R0")
R1 = Register("R1")
R2 = Register("R2")
R3 = Register("R3")
R4 = Register("R4")
R5 = Register("R5")
R6 = Register("R6")
R7 = Register("R7")
SP = Register("SP")
FP = Register("FP")
PC = Register("PC")

ALL_REGS = [R0, R1, R2, R3, R4, R5, R6, R7]
ALLOCATABLE_REGS = [R1, R2, R3, R4, R5, R6, R7, R0]
