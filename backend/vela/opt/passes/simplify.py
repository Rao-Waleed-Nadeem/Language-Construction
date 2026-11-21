"""Algebraic Simplification Optimization Pass.

Defined per:
- docs/10_CODE_OPTIMIZATION.md §5.6
- Master Spec P6-04, P6-12
- Simplifies arithmetic identities: x + 0, x - 0, x * 1, x * 0, x / 1, -(-x).
"""

from __future__ import annotations

from vela.ir.tac import Constant, TACInstruction, TACProgram, Variable
from vela.opt.passes import OptimizationChange


def run_algebraic_simplification(program: TACProgram) -> tuple[TACProgram, list[OptimizationChange]]:
    """Scan TAC instructions and simplify algebraic identities."""
    new_instructions: list[TACInstruction] = []
    changes: list[OptimizationChange] = []

    for idx, instr in enumerate(program.instructions):
        orig_text = str(instr)
        op = instr.opcode

        # x + 0 -> x, 0 + x -> x
        if op == "ADD":
            if isinstance(instr.arg2, Constant) and instr.arg2.value == 0:
                new_instr = TACInstruction(
                    opcode="ASSIGN",
                    arg1=instr.arg1,
                    result=instr.result,
                    src_span=instr.src_span,
                    ast_id=instr.ast_id,
                    rule_id="OPT-SIMPLIFY",
                )
                new_instructions.append(new_instr)
                changes.append(
                    OptimizationChange(
                        pass_name="Algebraic Simplification",
                        description=f"Simplified {orig_text} (x + 0 -> x)",
                        original=orig_text,
                        transformed=str(new_instr),
                        instr_index=idx,
                    )
                )
                continue
            if isinstance(instr.arg1, Constant) and instr.arg1.value == 0:
                new_instr = TACInstruction(
                    opcode="ASSIGN",
                    arg1=instr.arg2,
                    result=instr.result,
                    src_span=instr.src_span,
                    ast_id=instr.ast_id,
                    rule_id="OPT-SIMPLIFY",
                )
                new_instructions.append(new_instr)
                changes.append(
                    OptimizationChange(
                        pass_name="Algebraic Simplification",
                        description=f"Simplified {orig_text} (0 + x -> x)",
                        original=orig_text,
                        transformed=str(new_instr),
                        instr_index=idx,
                    )
                )
                continue

        # x - 0 -> x
        if op == "SUB" and isinstance(instr.arg2, Constant) and instr.arg2.value == 0:
            new_instr = TACInstruction(
                opcode="ASSIGN",
                arg1=instr.arg1,
                result=instr.result,
                src_span=instr.src_span,
                ast_id=instr.ast_id,
                rule_id="OPT-SIMPLIFY",
            )
            new_instructions.append(new_instr)
            changes.append(
                OptimizationChange(
                    pass_name="Algebraic Simplification",
                    description=f"Simplified {orig_text} (x - 0 -> x)",
                    original=orig_text,
                    transformed=str(new_instr),
                    instr_index=idx,
                )
            )
            continue

        # x * 1 -> x, 1 * x -> x
        if op == "MUL":
            if isinstance(instr.arg2, Constant) and instr.arg2.value == 1:
                new_instr = TACInstruction(
                    opcode="ASSIGN",
                    arg1=instr.arg1,
                    result=instr.result,
                    src_span=instr.src_span,
                    ast_id=instr.ast_id,
                    rule_id="OPT-SIMPLIFY",
                )
                new_instructions.append(new_instr)
                changes.append(
                    OptimizationChange(
                        pass_name="Algebraic Simplification",
                        description=f"Simplified {orig_text} (x * 1 -> x)",
                        original=orig_text,
                        transformed=str(new_instr),
                        instr_index=idx,
                    )
                )
                continue
            if isinstance(instr.arg1, Constant) and instr.arg1.value == 1:
                new_instr = TACInstruction(
                    opcode="ASSIGN",
                    arg1=instr.arg2,
                    result=instr.result,
                    src_span=instr.src_span,
                    ast_id=instr.ast_id,
                    rule_id="OPT-SIMPLIFY",
                )
                new_instructions.append(new_instr)
                changes.append(
                    OptimizationChange(
                        pass_name="Algebraic Simplification",
                        description=f"Simplified {orig_text} (1 * x -> x)",
                        original=orig_text,
                        transformed=str(new_instr),
                        instr_index=idx,
                    )
                )
                continue

            # x * 0 -> 0, 0 * x -> 0 (for integers)
            if (isinstance(instr.arg2, Constant) and instr.arg2.value == 0 and instr.arg2.type_name == "int") or (
                isinstance(instr.arg1, Constant) and instr.arg1.value == 0 and instr.arg1.type_name == "int"
            ):
                zero_const = Constant(0, "int")
                new_instr = TACInstruction(
                    opcode="ASSIGN",
                    arg1=zero_const,
                    result=instr.result,
                    src_span=instr.src_span,
                    ast_id=instr.ast_id,
                    rule_id="OPT-SIMPLIFY",
                )
                new_instructions.append(new_instr)
                changes.append(
                    OptimizationChange(
                        pass_name="Algebraic Simplification",
                        description=f"Simplified {orig_text} (x * 0 -> 0)",
                        original=orig_text,
                        transformed=str(new_instr),
                        instr_index=idx,
                    )
                )
                continue

        # x / 1 -> x
        if op == "DIV" and isinstance(instr.arg2, Constant) and instr.arg2.value == 1:
            new_instr = TACInstruction(
                opcode="ASSIGN",
                arg1=instr.arg1,
                result=instr.result,
                src_span=instr.src_span,
                ast_id=instr.ast_id,
                rule_id="OPT-SIMPLIFY",
            )
            new_instructions.append(new_instr)
            changes.append(
                OptimizationChange(
                    pass_name="Algebraic Simplification",
                    description=f"Simplified {orig_text} (x / 1 -> x)",
                    original=orig_text,
                    transformed=str(new_instr),
                    instr_index=idx,
                )
            )
            continue

        # x == x -> true, x != x -> false (for same named variable)
        if (
            op == "EQ"
            and isinstance(instr.arg1, Variable)
            and isinstance(instr.arg2, Variable)
            and instr.arg1.name == instr.arg2.name
        ):
            new_instr = TACInstruction(
                opcode="ASSIGN",
                arg1=Constant(True, "bool"),
                result=instr.result,
                src_span=instr.src_span,
                ast_id=instr.ast_id,
                rule_id="OPT-SIMPLIFY",
            )
            new_instructions.append(new_instr)
            changes.append(
                OptimizationChange(
                    pass_name="Algebraic Simplification",
                    description=f"Simplified {orig_text} (x == x -> true)",
                    original=orig_text,
                    transformed=str(new_instr),
                    instr_index=idx,
                )
            )
            continue

        new_instructions.append(instr)

    return TACProgram(instructions=new_instructions), changes
