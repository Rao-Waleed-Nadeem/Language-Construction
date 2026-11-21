"""Constant Propagation Optimization Pass.

Defined per:
- docs/10_CODE_OPTIMIZATION.md §5.2
- Master Spec P6-05
- Replaces uses of variables known to have constant values (local + global reaching definitions).
"""

from __future__ import annotations

from typing import Any

from vela.ir.tac import Constant, TACInstruction, TACProgram, Temporary, Variable
from vela.opt.blocks import partition_into_blocks
from vela.opt.cfg import build_cfg
from vela.opt.dataflow import solve_reaching_definitions
from vela.opt.passes import OptimizationChange
from vela.opt.passes.dce import is_global_var


def _replace_operand_if_constant(op: Any, env: dict[str, Constant]) -> tuple[Any, bool]:
    if isinstance(op, (Variable, Temporary)):
        name = str(op)
        if not is_global_var(name) and name in env:
            return env[name], True
    return op, False


def run_constant_propagation(program: TACProgram) -> tuple[TACProgram, list[OptimizationChange]]:
    """Propagate constant values locally within blocks and globally using reaching definitions."""
    partition = partition_into_blocks(program.instructions)
    cfg = build_cfg(partition)
    reach_res = solve_reaching_definitions(cfg)

    # 1. Map each Definition to its constant value, if it is an ASSIGN of a Constant
    def_to_const: dict[tuple[int, int], Constant] = {}
    for bid, block in cfg.blocks.items():
        for idx, instr in enumerate(block.instructions):
            if instr.opcode == "ASSIGN" and isinstance(instr.arg1, Constant):
                def_to_const[(bid, idx)] = instr.arg1

    new_instructions: list[TACInstruction] = []
    changes: list[OptimizationChange] = []
    global_idx = 0

    for bid in sorted(cfg.blocks.keys()):
        block = cfg.blocks[bid]
        # Local constant environment for this block
        local_env: dict[str, Constant] = {}

        # Global reaching definitions entering this block
        in_defs = reach_res.in_sets.get(bid, set())
        # If all reaching defs for variable v have the exact same constant, pre-seed local_env
        var_defs: dict[str, list[Constant | None]] = {}
        for d in in_defs:
            c = def_to_const.get((d.block_id, d.instr_index), None)
            var_defs.setdefault(d.var_name, []).append(c)

        for v_name, const_list in var_defs.items():
            if not is_global_var(v_name) and const_list and all(c is not None and c == const_list[0] for c in const_list):
                assert const_list[0] is not None
                local_env[v_name] = const_list[0]

        for block_idx, instr in enumerate(block.instructions):
            orig_text = str(instr)
            changed = False

            new_arg1 = instr.arg1
            new_arg2 = instr.arg2

            # Try replacing arg1 and arg2
            if new_arg1 is not None:
                new_arg1, c1 = _replace_operand_if_constant(new_arg1, local_env)
                if c1:
                    changed = True

            if new_arg2 is not None:
                new_arg2, c2 = _replace_operand_if_constant(new_arg2, local_env)
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
                    rule_id="OPT-CONST-PROP",
                )
                new_instructions.append(new_instr)
                changes.append(
                    OptimizationChange(
                        pass_name="Constant Propagation",
                        description=f"Propagated constant into {orig_text}",
                        original=orig_text,
                        transformed=str(new_instr),
                        instr_index=global_idx,
                    )
                )
                curr_instr = new_instr
            else:
                new_instructions.append(instr)
                curr_instr = instr

            # Update local_env with defs from curr_instr
            if curr_instr.opcode == "CALL":
                # Function calls can modify any global variable
                local_env = {k: v for k, v in local_env.items() if "_" in k}
                if isinstance(curr_instr.result, (Variable, Temporary)):
                    local_env.pop(str(curr_instr.result), None)
            elif curr_instr.opcode == "ASSIGN" and isinstance(curr_instr.arg1, Constant):
                if isinstance(curr_instr.result, (Variable, Temporary)):
                    v_name = str(curr_instr.result)
                    if not is_global_var(v_name):
                        local_env[v_name] = curr_instr.arg1
            else:
                # Any other assignment/read invalidates the defined variable
                if isinstance(curr_instr.result, (Variable, Temporary)):
                    local_env.pop(str(curr_instr.result), None)

            global_idx += 1

    return TACProgram(instructions=new_instructions), changes
