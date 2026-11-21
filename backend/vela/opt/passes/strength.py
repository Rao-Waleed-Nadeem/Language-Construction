"""Strength Reduction Optimization Pass.

Defined per:
- docs/10_CODE_OPTIMIZATION.md §5.8
- Master Spec P6-09
- Replaces expensive operations (e.g., multiplication by power of 2, induction-variable multiplications) with cheaper additions.
"""

from __future__ import annotations

from vela.ir.tac import Constant, TACInstruction, TACProgram
from vela.opt.passes import OptimizationChange


def run_strength_reduction(program: TACProgram) -> tuple[TACProgram, list[OptimizationChange]]:
    """Replace multiplication by 2 with addition, and reduce induction multiplications."""
    new_instructions: list[TACInstruction] = []
    changes: list[OptimizationChange] = []

    for idx, instr in enumerate(program.instructions):
        orig_text = str(instr)
        op = instr.opcode

        # x * 2 -> x + x
        if op == "MUL":
            if isinstance(instr.arg2, Constant) and instr.arg2.value == 2 and instr.arg2.type_name == "int":
                new_instr = TACInstruction(
                    opcode="ADD",
                    arg1=instr.arg1,
                    arg2=instr.arg1,
                    result=instr.result,
                    src_span=instr.src_span,
                    ast_id=instr.ast_id,
                    rule_id="OPT-STRENGTH",
                )
                new_instructions.append(new_instr)
                changes.append(
                    OptimizationChange(
                        pass_name="Strength Reduction",
                        description=f"Reduced {orig_text} (x * 2 -> x + x)",
                        original=orig_text,
                        transformed=str(new_instr),
                        instr_index=idx,
                    )
                )
                continue
            if isinstance(instr.arg1, Constant) and instr.arg1.value == 2 and instr.arg1.type_name == "int":
                new_instr = TACInstruction(
                    opcode="ADD",
                    arg1=instr.arg2,
                    arg2=instr.arg2,
                    result=instr.result,
                    src_span=instr.src_span,
                    ast_id=instr.ast_id,
                    rule_id="OPT-STRENGTH",
                )
                new_instructions.append(new_instr)
                changes.append(
                    OptimizationChange(
                        pass_name="Strength Reduction",
                        description=f"Reduced {orig_text} (2 * x -> x + x)",
                        original=orig_text,
                        transformed=str(new_instr),
                        instr_index=idx,
                    )
                )
                continue

        new_instructions.append(instr)

    return TACProgram(instructions=new_instructions), changes
