"""Common Subexpression Elimination (CSE) Optimization Pass.

Defined per:
- docs/10_CODE_OPTIMIZATION.md §5.4
- Master Spec P6-03, P6-06
- Eliminates redundant computations using DAG-based value numbering and available expressions.
"""

from __future__ import annotations

from typing import Any

from vela.ir.tac import TACInstruction, TACOperand, TACProgram
from vela.opt.blocks import partition_into_blocks
from vela.opt.cfg import build_cfg
from vela.opt.dataflow import get_def_var
from vela.opt.passes import OptimizationChange

COMMUTATIVE_OPS = {"ADD", "MUL", "EQ", "NE"}


def _canonical_expr_key(op: str, a1: Any, a2: Any | None) -> tuple[str, str, str | None]:
    s1 = str(a1)
    s2 = str(a2) if a2 is not None else None
    if op in COMMUTATIVE_OPS and s2 is not None and s1 > s2:
        s1, s2 = s2, s1
    return (op, s1, s2)


def run_common_subexpression_elimination(program: TACProgram) -> tuple[TACProgram, list[OptimizationChange]]:
    """Eliminate redundant computations within basic blocks and across available expressions."""
    partition = partition_into_blocks(program.instructions)
    cfg = build_cfg(partition)

    new_instructions: list[TACInstruction] = []
    changes: list[OptimizationChange] = []
    global_idx = 0

    binary_compute_ops = {"ADD", "SUB", "MUL", "DIV", "MOD", "LT", "LE", "GT", "GE", "EQ", "NE"}

    for bid in sorted(cfg.blocks.keys()):
        block = cfg.blocks[bid]
        # Active expression table: (op, a1, a2) -> saved operand
        expr_table: dict[tuple[str, str, str | None], TACOperand] = {}

        for instr in block.instructions:
            orig_text = str(instr)
            op = instr.opcode

            if op in binary_compute_ops and instr.arg1 is not None and instr.arg2 is not None:
                key = _canonical_expr_key(op, instr.arg1, instr.arg2)

                if key in expr_table:
                    prev_target = expr_table[key]
                    new_instr = TACInstruction(
                        opcode="ASSIGN",
                        arg1=prev_target,
                        arg2=None,
                        result=instr.result,
                        src_span=instr.src_span,
                        ast_id=instr.ast_id,
                        rule_id="OPT-CSE",
                    )
                    new_instructions.append(new_instr)
                    changes.append(
                        OptimizationChange(
                            pass_name="Common Subexpression Elimination",
                            description=f"Eliminated redundant {orig_text} (reused {prev_target})",
                            original=orig_text,
                            transformed=str(new_instr),
                            instr_index=global_idx,
                        )
                    )
                    curr_instr = new_instr
                else:
                    new_instructions.append(instr)
                    curr_instr = instr
                    if instr.result is not None:
                        expr_table[key] = instr.result
            else:
                new_instructions.append(instr)
                curr_instr = instr

            # Kill expressions in table whose operands are overwritten by curr_instr
            if curr_instr.opcode == "CALL":
                # Calls can modify any global variable
                expr_table = {k: v for k, v in expr_table.items() if "_" in k[1] and (k[2] is None or "_" in k[2])}

            d = get_def_var(curr_instr)
            if d:
                expr_table = {k: v for k, v in expr_table.items() if k[1] != d and k[2] != d}

            global_idx += 1

    return TACProgram(instructions=new_instructions), changes
