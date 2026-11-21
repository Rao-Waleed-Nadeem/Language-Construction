"""Loop-Invariant Code Motion (LICM) Optimization Pass.

Defined per:
- docs/10_CODE_OPTIMIZATION.md §5.7
- Master Spec P6-09
- Hoists computations that produce identical results on every loop iteration out of the loop.
"""

from __future__ import annotations

from vela.ir.tac import TACInstruction, TACProgram
from vela.opt.blocks import partition_into_blocks
from vela.opt.cfg import build_cfg
from vela.opt.dataflow import get_def_var, get_use_vars
from vela.opt.dominators import compute_dominators
from vela.opt.passes import OptimizationChange
from vela.opt.passes.dce import SIDE_EFFECT_OPS


def run_loop_invariant_code_motion(program: TACProgram) -> tuple[TACProgram, list[OptimizationChange]]:
    """Identify loop-invariant instructions and hoist them out of natural loops."""
    partition = partition_into_blocks(program.instructions)
    cfg = build_cfg(partition)
    dom_info = compute_dominators(cfg)

    changes: list[OptimizationChange] = []
    if not dom_info.natural_loops:
        return program, changes

    # Collect all loops sorted by size (inner loops first)
    sorted_loops = sorted(dom_info.natural_loops.items(), key=lambda item: len(item[1]))

    # We work on instruction list
    current_instructions = list(program.instructions)

    for (src, header_id), loop_block_ids in sorted_loops:
        header_block = cfg.blocks[header_id]
        header_start_instr = header_block.instructions[0]

        # Find header position in current_instructions
        header_pos = -1
        for idx, instr in enumerate(current_instructions):
            if instr is header_start_instr:
                header_pos = idx
                break

        if header_pos == -1:
            continue

        # Collect all variables modified anywhere inside the loop
        loop_defs: dict[str, int] = {}

        for b_id in loop_block_ids:
            if b_id not in cfg.blocks:
                continue
            b = cfg.blocks[b_id]
            for instr in b.instructions:
                d = get_def_var(instr)
                if d is not None:
                    loop_defs[d] = loop_defs.get(d, 0) + 1

        # Find invariant instructions inside loop blocks
        # An instruction is invariant if:
        # 1. Opcode is pure computation (not in SIDE_EFFECT_OPS)
        # 2. Result variable is assigned only once inside loop
        # 3. All used variables are defined outside loop (i.e. not in loop_defs)
        hoisted_instrs: list[TACInstruction] = []

        for b_id in loop_block_ids:
            # Don't hoist loop conditional jumps in header
            if b_id not in cfg.blocks:
                continue
            b = cfg.blocks[b_id]
            for instr in b.instructions:
                if instr.opcode in SIDE_EFFECT_OPS:
                    continue

                d = get_def_var(instr)
                if d is None or loop_defs.get(d, 0) != 1:
                    continue

                uses = get_use_vars(instr)
                # All operands must either be constants or defined outside loop
                operands_invariant = all(u not in loop_defs for u in uses)

                if operands_invariant:
                    hoisted_instrs.append(instr)
                    # Once hoisted, d is no longer considered defined inside loop
                    loop_defs.pop(d, None)
                    changes.append(
                        OptimizationChange(
                            pass_name="Loop-Invariant Code Motion",
                            description=f"Hoisted {instr} out of loop at header Block {header_id}",
                            original=str(instr),
                            transformed=f"<hoisted before header Block {header_id}>",
                            instr_index=header_pos,
                        )
                    )

        if hoisted_instrs:
            # Remove hoisted instrs from loop and insert before header_pos
            remaining_instructions = [i for i in current_instructions if i not in hoisted_instrs]
            # Find new header_pos in remaining_instructions
            new_header_pos = remaining_instructions.index(header_start_instr)
            current_instructions = (
                remaining_instructions[:new_header_pos] + hoisted_instrs + remaining_instructions[new_header_pos:]
            )

    return TACProgram(instructions=current_instructions), changes
