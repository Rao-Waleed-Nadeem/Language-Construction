"""Target Code Generation Package (Phase 7).

Defined per:
- docs/11_TARGET_CODE_AND_VM_SPECIFICATION.md
- Master Spec P7-01..P7-07
"""

from vela.codegen.cost import OPCODE_BASE_COSTS, get_instruction_cost
from vela.codegen.isa import (
    ALL_REGS,
    ALLOCATABLE_REGS,
    FP,
    PC,
    R0,
    R1,
    R2,
    R3,
    R4,
    R5,
    R6,
    R7,
    SP,
    Immediate,
    MemoryRef,
    Register,
    TargetInstruction,
    TargetOperand,
    TargetProgram,
)
from vela.codegen.selector import InstructionSelector

__all__ = [
    "ALLOCATABLE_REGS",
    "ALL_REGS",
    "FP",
    "OPCODE_BASE_COSTS",
    "PC",
    "R0",
    "R1",
    "R2",
    "R3",
    "R4",
    "R5",
    "R6",
    "R7",
    "SP",
    "Immediate",
    "InstructionSelector",
    "MemoryRef",
    "Register",
    "TargetInstruction",
    "TargetOperand",
    "TargetProgram",
    "get_instruction_cost",
]
