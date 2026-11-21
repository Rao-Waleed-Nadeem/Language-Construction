"""Copy Propagation Optimization Pass.

Defined per:
- docs/10_CODE_OPTIMIZATION.md §5.3
- Master Spec P6-08
- Replaces uses of x with y following copy x = y when no intervening redefinition occurs.
"""

from __future__ import annotations

from typing import Any

from vela.ir.tac import TACInstruction, TACProgram, Temporary, Variable
from vela.opt.blocks import partition_into_blocks
from vela.opt.cfg import build_cfg
from vela.opt.dataflow import get_def_var, solve_available_copies
from vela.opt.passes import OptimizationChange


def _replace_operand_if_copy(op: Any, env: dict[str, str]) -> tuple[Any, bool]:
    if isinstance(op, (Variable, Temporary)):
        name = str(op)
        if name in env:
            target_name = env[name]
            if isinstance(op, Temporary):
                tid = int(target_name[1:]) if target_name.startswith("t") and target_name[1:].isdigit() else op.id
                return Temporary(id=tid), True
            return Variable(target_name), True
    return op, False


def run_copy_propagation(program: TACProgram) -> tuple[TACProgram, list[OptimizationChange]]:
    """Propagate copy assignments x = y locally and globally."""
    partition = partition_into_blocks(program.instructions)
    cfg = build_cfg(partition)
    copies_res = solve_available_copies(cfg)

    new_instructions: list[TACInstruction] = []
    changes: list[OptimizationChange] = []
    global_idx = 0

    for bid in sorted(cfg.blocks.keys()):
        block = cfg.blocks[bid]
        local_copies: dict[str, str] = {}

        # Pre-seed with available copies entering this block
        in_copies = copies_res.in_sets.get(bid, set())
        for c in in_copies:
            local_copies[c.dest] = c.src

        for instr in block.instructions:
            orig_text = str(instr)
            changed = False

            new_arg1 = instr.arg1
            new_arg2 = instr.arg2

            if new_arg1 is not None:
                new_arg1, c1 = _replace_operand_if_copy(new_arg1, local_copies)
                if c1:
                    changed = True

            if new_arg2 is not None:
                new_arg2, c2 = _replace_operand_if_copy(new_arg2, local_copies)
                if c2:
                    changed = True

            if changed:
                new_instr = TACInstruction(
                    opcode=instr.opcode,
                    arg1=new_arg1,
                    arg2=new_arg2,
                    result=instr.result,
                    src_span=instr.src_span,
                    ast_id=instr.ast_id,
                    rule_id="OPT-COPY-PROP",
                )
                new_instructions.append(new_instr)
                changes.append(
                    OptimizationChange(
                        pass_name="Copy Propagation",
                        description=f"Propagated copy into {orig_text}",
                        original=orig_text,
                        transformed=str(new_instr),
                        instr_index=global_idx,
                    )
                )
                curr_instr = new_instr
            else:
                new_instructions.append(instr)
                curr_instr = instr

            # Update local_copies
            if curr_instr.opcode == "CALL":
                # Function calls can modify any global variable
                local_copies = {dest: src for dest, src in local_copies.items() if "_" in dest and "_" in src}

            d = get_def_var(curr_instr)
            if d:
                # Any copy where d is destination or source is invalidated
                local_copies = {dest: src for dest, src in local_copies.items() if dest != d and src != d}

            # If curr_instr is a new copy statement x = y
            if (
                curr_instr.opcode == "ASSIGN"
                and isinstance(curr_instr.result, (Variable, Temporary))
                and isinstance(curr_instr.arg1, (Variable, Temporary))
            ):
                dest_str = str(curr_instr.result)
                src_str = str(curr_instr.arg1)
                if dest_str != src_str:
                    local_copies[dest_str] = src_str

            global_idx += 1

    return TACProgram(instructions=new_instructions), changes
