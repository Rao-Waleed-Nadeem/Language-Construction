"""Constant Folding Optimization Pass.

Defined per:
- docs/10_CODE_OPTIMIZATION.md §5.1
- Master Spec P6-04
- Safety rule: NEVER fold division or modulo by zero (preserves VL-RUN-001).
- Arithmetic rule: Obey 32-bit two's-complement integer wrap-around.
"""

from __future__ import annotations

from vela.common.limits import wrap32
from vela.ir.tac import Constant, TACInstruction, TACProgram
from vela.opt.passes import OptimizationChange


def _compute_binary_op(op: str, v1: float | str | bool, v2: float | str | bool) -> Constant | None:
    # Division / modulo safety: NEVER fold division or modulo by zero!
    if op in ("DIV", "MOD") and v2 == 0:
        return None

    if op == "ADD":
        if isinstance(v1, str) or isinstance(v2, str):
            return Constant(f"{v1}{v2}", "string")
        if isinstance(v1, float) or isinstance(v2, float):
            return Constant(float(v1) + float(v2), "float")
        return Constant(wrap32(int(v1) + int(v2)), "int")

    if op == "SUB":
        if isinstance(v1, float) or isinstance(v2, float):
            return Constant(float(v1) - float(v2), "float")
        return Constant(wrap32(int(v1) - int(v2)), "int")

    if op == "MUL":
        if isinstance(v1, float) or isinstance(v2, float):
            return Constant(float(v1) * float(v2), "float")
        return Constant(wrap32(int(v1) * int(v2)), "int")

    if op == "DIV":
        if isinstance(v1, float) or isinstance(v2, float):
            return Constant(float(v1) / float(v2), "float")
        # Integer division truncating toward zero
        return Constant(int(int(v1) / int(v2)), "int")

    if op == "MOD":
        # Vela modulo: sign matches dividend
        div = int(int(v1) / int(v2))
        return Constant(int(v1) - div * int(v2), "int")

    # Relational operators
    if op == "LT":
        return Constant(v1 < v2, "bool")
    if op == "LE":
        return Constant(v1 <= v2, "bool")
    if op == "GT":
        return Constant(v1 > v2, "bool")
    if op == "GE":
        return Constant(v1 >= v2, "bool")
    if op == "EQ":
        return Constant(v1 == v2, "bool")
    if op == "NE":
        return Constant(v1 != v2, "bool")

    return None


def _compute_unary_op(op: str, v: float | bool) -> Constant | None:
    if op == "NEG":
        if isinstance(v, float):
            return Constant(-v, "float")
        return Constant(wrap32(-int(v)), "int")
    if op == "NOT":
        return Constant(not bool(v), "bool")
    return None


def run_constant_folding(program: TACProgram) -> tuple[TACProgram, list[OptimizationChange]]:
    """Scan TAC instructions and fold statically computable constant expressions."""
    new_instructions: list[TACInstruction] = []
    changes: list[OptimizationChange] = []

    for idx, instr in enumerate(program.instructions):
        orig_text = str(instr)
        op = instr.opcode

        # Binary ops on two constants
        if isinstance(instr.arg1, Constant) and isinstance(instr.arg2, Constant):
            folded_const = _compute_binary_op(op, instr.arg1.value, instr.arg2.value)
            if folded_const is not None:
                new_instr = TACInstruction(
                    opcode="ASSIGN",
                    arg1=folded_const,
                    arg2=None,
                    result=instr.result,
                    src_span=instr.src_span,
                    ast_id=instr.ast_id,
                    rule_id="OPT-CONST-FOLD",
                )
                new_instructions.append(new_instr)
                changes.append(
                    OptimizationChange(
                        pass_name="Constant Folding",
                        description=f"Folded {instr.arg1} {op} {instr.arg2} into {folded_const}",
                        original=orig_text,
                        transformed=str(new_instr),
                        instr_index=idx,
                    )
                )
                continue

        # Unary ops on single constant
        elif isinstance(instr.arg1, Constant) and instr.arg2 is None and op in ("NEG", "NOT"):
            folded_const = _compute_unary_op(op, instr.arg1.value)
            if folded_const is not None:
                new_instr = TACInstruction(
                    opcode="ASSIGN",
                    arg1=folded_const,
                    arg2=None,
                    result=instr.result,
                    src_span=instr.src_span,
                    ast_id=instr.ast_id,
                    rule_id="OPT-CONST-FOLD",
                )
                new_instructions.append(new_instr)
                changes.append(
                    OptimizationChange(
                        pass_name="Constant Folding",
                        description=f"Folded {op} {instr.arg1} into {folded_const}",
                        original=orig_text,
                        transformed=str(new_instr),
                        instr_index=idx,
                    )
                )
                continue

        # CAST on constant
        elif op == "CAST" and isinstance(instr.arg1, Constant) and isinstance(instr.arg2, Constant):
            target_type = str(instr.arg2.value)
            val = instr.arg1.value
            cast_res: Constant | None = None
            if target_type == "int":
                cast_res = Constant(int(val), "int")
            elif target_type == "float":
                cast_res = Constant(float(val), "float")
            elif target_type == "string":
                cast_res = Constant(str(val), "string")

            if cast_res is not None:
                new_instr = TACInstruction(
                    opcode="ASSIGN",
                    arg1=cast_res,
                    arg2=None,
                    result=instr.result,
                    src_span=instr.src_span,
                    ast_id=instr.ast_id,
                    rule_id="OPT-CONST-FOLD",
                )
                new_instructions.append(new_instr)
                changes.append(
                    OptimizationChange(
                        pass_name="Constant Folding",
                        description=f"Folded cast({instr.arg1}, {target_type}) into {cast_res}",
                        original=orig_text,
                        transformed=str(new_instr),
                        instr_index=idx,
                    )
                )
                continue

        new_instructions.append(instr)

    return TACProgram(instructions=new_instructions), changes
