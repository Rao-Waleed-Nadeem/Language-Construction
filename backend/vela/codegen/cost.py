"""Target Instruction Cost Model.

Defined per:
- docs/11_TARGET_CODE_AND_VM_SPECIFICATION.md §2.3
- Master Spec P7-03
- Acceptance criterion AC-C2: Sum of per-instruction costs equals total cost.
"""

from __future__ import annotations

from typing import Any

OPCODE_BASE_COSTS: dict[str, int] = {
    "LABEL": 0,
    "HLT": 0,
    "MOV": 1,
    "LOAD": 2,
    "STORE": 2,
    "ADD": 1,
    "SUB": 1,
    "NEG": 1,
    "NOT": 1,
    "CMP": 1,
    "MUL": 3,
    "DIV": 5,
    "MOD": 5,
    "JMP": 1,
    "JE": 1,
    "JNE": 1,
    "JL": 1,
    "JLE": 1,
    "JG": 1,
    "JGE": 1,
    "CALL": 2,
    "RET": 2,
    "PUSH": 1,
    "POP": 1,
    "SYS_SHOW": 1,
    "SYS_SHOW_NL": 1,
    "SYS_READ": 1,
    "SYS_ALLOC": 3,
}


def get_instruction_cost(
    opcode: str,
    dst: Any = None,
    src1: Any = None,
    src2: Any = None,
) -> int:
    """Calculate the cycle cost for an instruction based on opcode and operands."""
    base_cost = OPCODE_BASE_COSTS.get(opcode, 1)

    # Memory operands add a cache/bus penalty
    cost = base_cost
    for operand in (dst, src1, src2):
        if operand is not None and hasattr(operand, "base") and operand.base is not None:
            # Memory reference
            cost += 1
            break

    return cost
