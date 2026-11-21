"""Virtual Machine CPU Architecture and Register State.

Defined per:
- docs/11_TARGET_CODE_AND_VM_SPECIFICATION.md §2.1
- Master Spec P7-01, P7-07
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class CPUState:
    """Register set and flags for the Virtual Machine CPU."""

    registers: dict[str, Any] = field(
        default_factory=lambda: {
            "R0": 0,
            "R1": 0,
            "R2": 0,
            "R3": 0,
            "R4": 0,
            "R5": 0,
            "R6": 0,
            "R7": 0,
        }
    )
    sp: int = 10_000  # Stack Pointer
    fp: int = 10_000  # Frame Pointer
    pc: int = 0  # Program Counter
    zf: bool = False  # Zero Flag
    sf: bool = False  # Sign / Less-Than Flag

    def get_reg(self, name: str) -> Any:
        if name in self.registers:
            return self.registers[name]
        if name == "SP":
            return self.sp
        if name == "FP":
            return self.fp
        if name == "PC":
            return self.pc
        return 0

    def set_reg(self, name: str, val: Any) -> None:
        if name in self.registers:
            self.registers[name] = val
        elif name == "SP":
            self.sp = int(val)
        elif name == "FP":
            self.fp = int(val)
        elif name == "PC":
            self.pc = int(val)

    def to_dict(self) -> dict[str, Any]:
        return {
            "registers": dict(self.registers),
            "SP": self.sp,
            "FP": self.fp,
            "PC": self.pc,
            "ZF": self.zf,
            "SF": self.sf,
        }
