"""Validation of TAC Well-Formedness and Oracle Semantic Equivalence.

Defined per:
- docs/10_CODE_OPTIMIZATION.md §6
- Master Spec P6-13
- Verifies that optimizations preserve exact runtime semantics across all inputs.
"""

from __future__ import annotations

from vela.ir.interpreter import TACInterpreter
from vela.ir.tac import TACProgram


class TACValidationError(Exception):
    """Raised when an optimized TAC program violates well-formedness rules."""


def validate_tac_well_formedness(program: TACProgram) -> None:
    """Check TAC structural constraints (labels, branch targets, opcode rules)."""
    # 1. No plain boolean opcodes
    if program.contains_plain_boolean_ops():
        raise TACValidationError("TAC contains forbidden plain boolean opcodes ('AND' / 'OR')")

    # 2. All jump targets must exist
    missing_labels = program.validate_labels()
    if missing_labels:
        raise TACValidationError(f"TAC contains undefined jump target labels: {missing_labels}")

    # 3. Every instruction must have an opcode
    for idx, instr in enumerate(program.instructions):
        if not instr.opcode:
            raise TACValidationError(f"Instruction at index {idx} has empty opcode")


def verify_equivalence(
    original: TACProgram,
    optimized: TACProgram,
    stdin_data: str = "",
) -> tuple[bool, str]:
    """Execute both original and optimized TAC using the reference interpreter.

    Returns (True, message) if outputs and exit status match byte-for-byte;
    (False, diff) otherwise.
    """
    # Run original
    orig_res = TACInterpreter().interpret(original, stdin=stdin_data)
    # Run optimized
    opt_res = TACInterpreter().interpret(optimized, stdin=stdin_data)

    if orig_res.exit_code != opt_res.exit_code:
        return (
            False,
            f"Exit code mismatch: original exited with {orig_res.exit_code}, optimized exited with {opt_res.exit_code}",
        )

    if orig_res.stdout != opt_res.stdout:
        return (
            False,
            f"Output mismatch:\nOriginal:\n{orig_res.stdout}\nOptimized:\n{opt_res.stdout}",
        )

    return (True, "Oracle outputs and exit codes match byte-for-byte")
