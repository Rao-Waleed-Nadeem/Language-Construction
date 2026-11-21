"""Dead-Code Elimination (DCE) Optimization Pass.

Defined per:
- docs/10_CODE_OPTIMIZATION.md §5.5
- Master Spec P6-07
- Removes dead definitions and unused computations using backward liveness analysis.
"""

from __future__ import annotations

from vela.ir.tac import TACInstruction, TACProgram
from vela.opt.blocks import partition_into_blocks
from vela.opt.cfg import build_cfg
from vela.opt.dataflow import get_def_var, get_use_vars, solve_live_variables
from vela.opt.passes import OptimizationChange


def is_global_var(name: str) -> bool:
    """Return True if variable is a global program variable (not a scoped local or temporary)."""
    if name.startswith("t") and name[1:].isdigit():
        return False
    return "_" not in name


SIDE_EFFECT_OPS = {
    "CALL",
    "SHOW",
    "SHOW_NL",
    "READ",
    "RECEIVE",
    "RETURN",
    "JUMP",
    "JUMP_IF",
    "JUMP_IF_FALSE",
    "LABEL",
    "FUNC_BEGIN",
    "FUNC_END",
    "ALLOC_ARRAY",
    "ARRAY_SET",
}


def run_dead_code_elimination(program: TACProgram) -> tuple[TACProgram, list[OptimizationChange]]:
    """Remove assignments to variables/temporaries that are dead and have no side effects."""
    partition = partition_into_blocks(program.instructions)
    cfg = build_cfg(partition)
    liveness = solve_live_variables(cfg)

    new_instructions: list[TACInstruction] = []
    changes: list[OptimizationChange] = []
    global_idx = 0

    for bid in sorted(cfg.blocks.keys()):
        block = cfg.blocks[bid]
        # Active live set at end of block
        live: set[str] = set(liveness.out_sets.get(bid, set()))

        # Walk backward to identify dead instructions
        keep_flags = [True] * len(block.instructions)

        for i in range(len(block.instructions) - 1, -1, -1):
            instr = block.instructions[i]
            op = instr.opcode
            d = get_def_var(instr)

            # If it defines a variable not in live set, and has no side effects, and is not a global, it is dead
            if d is not None and d not in live and op not in SIDE_EFFECT_OPS and not is_global_var(d):
                keep_flags[i] = False
                changes.append(
                    OptimizationChange(
                        pass_name="Dead-Code Elimination",
                        description=f"Eliminated dead instruction {instr} (defining unused {d})",
                        original=str(instr),
                        transformed="<eliminated>",
                        instr_index=global_idx + i,
                    )
                )
            else:
                # Instruction is kept: update liveness
                if d is not None:
                    live.discard(d)
                for u in get_use_vars(instr):
                    live.add(u)

        # Append kept instructions
        for i, keep in enumerate(keep_flags):
            if keep:
                new_instructions.append(block.instructions[i])

        global_idx += len(block.instructions)

    return TACProgram(instructions=new_instructions), changes
