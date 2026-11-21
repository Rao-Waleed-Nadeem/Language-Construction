"""Target Instruction Selection (Phase 7).

Defined per:
- docs/11_TARGET_CODE_AND_VM_SPECIFICATION.md §2
- Master Spec P7-02
- Maps TAC quadruples to target machine instructions with rule provenance and cost.
"""

from __future__ import annotations

from typing import Any

from vela.codegen.cost import get_instruction_cost
from vela.codegen.isa import (
    Immediate,
    MemoryRef,
    Register,
    TargetInstruction,
    TargetProgram,
)
from vela.ir.tac import Constant, Label, TACInstruction, TACProgram, Temporary, Variable
from vela.opt.passes.dce import is_global_var


def _convert_operand(op: Any) -> Any:
    if op is None:
        return None
    if isinstance(op, Constant):
        return Immediate(op.value)
    if isinstance(op, Label):
        return op.name
    if isinstance(op, Variable):
        if is_global_var(op.name):
            return MemoryRef(symbol=op.name)
        return op.name
    if isinstance(op, Temporary):
        return str(op)
    return str(op)


class InstructionSelector:
    """Translates TAC instructions into target ISA instructions."""

    def __init__(self) -> None:
        self.instructions: list[TargetInstruction] = []
        self.labels: dict[str, int] = {}

    def _emit(
        self,
        opcode: str,
        dst: Any = None,
        src1: Any = None,
        src2: Any = None,
        tac_index: int = 0,
        rule_name: str = "DEFAULT",
        comment: str = "",
    ) -> TargetInstruction:
        cost = get_instruction_cost(opcode, dst, src1, src2)
        instr = TargetInstruction(
            opcode=opcode,
            dst=dst,
            src1=src1,
            src2=src2,
            cost=cost,
            tac_index=tac_index,
            rule_name=rule_name,
            comment=comment,
        )
        if opcode == "LABEL" and dst is not None:
            self.labels[str(dst)] = len(self.instructions)
        self.instructions.append(instr)
        return instr

    def select(self, tac_program: TACProgram) -> TargetProgram:
        """Translate all TAC instructions into target machine instructions."""
        self.instructions = []
        self.labels = {}

        for idx, instr in enumerate(tac_program.instructions):
            self._select_instruction(instr, idx)

        return TargetProgram(instructions=self.instructions, labels=self.labels)

    def _select_instruction(self, instr: TACInstruction, tac_idx: int) -> None:
        op = instr.opcode
        dst = _convert_operand(instr.result)
        a1 = _convert_operand(instr.arg1)
        a2 = _convert_operand(instr.arg2)

        if op == "LABEL":
            self._emit("LABEL", dst=dst, tac_index=tac_idx, rule_name="SEL-LABEL")

        elif op == "FUNC_BEGIN":
            self._emit("LABEL", dst=dst, tac_index=tac_idx, rule_name="SEL-FUNC-ENTRY", comment=f"func {dst}")

        elif op == "FUNC_END":
            self._emit("LABEL", dst=f"L_end_{dst}", tac_index=tac_idx, rule_name="SEL-FUNC-EXIT", comment=f"endfunc {dst}")

        elif op == "ASSIGN":
            rule = "SEL-ASSIGN-IMM" if isinstance(a1, Immediate) else "SEL-ASSIGN-MOV"
            self._emit("MOV", dst=dst, src1=a1, tac_index=tac_idx, rule_name=rule)

        elif op in ("ADD", "SUB", "MUL", "DIV", "MOD"):
            rule = f"SEL-{op}"
            self._emit(op, dst=dst, src1=a1, src2=a2, tac_index=tac_idx, rule_name=rule)

        elif op in ("LT", "LE", "GT", "GE", "EQ", "NE"):
            # Compare and evaluate condition
            self._emit("CMP", dst=None, src1=a1, src2=a2, tac_index=tac_idx, rule_name=f"SEL-CMP-{op}")
            # Map condition to flag extraction
            cond_map = {"LT": "JL", "LE": "JLE", "GT": "JG", "GE": "JGE", "EQ": "JE", "NE": "JNE"}
            jmp_op = cond_map[op]
            true_label = f"L_cmp_true_{tac_idx}"
            join_label = f"L_cmp_join_{tac_idx}"
            self._emit(jmp_op, dst=true_label, tac_index=tac_idx, rule_name=f"SEL-SET-{op}")
            self._emit("MOV", dst=dst, src1=Immediate(False), tac_index=tac_idx, rule_name="SEL-SET-FALSE")
            self._emit("JMP", dst=join_label, tac_index=tac_idx, rule_name="SEL-CMP-JMP")
            self._emit("LABEL", dst=true_label, tac_index=tac_idx, rule_name="SEL-CMP-LABEL")
            self._emit("MOV", dst=dst, src1=Immediate(True), tac_index=tac_idx, rule_name="SEL-SET-TRUE")
            self._emit("LABEL", dst=join_label, tac_index=tac_idx, rule_name="SEL-CMP-LABEL")

        elif op == "NEG":
            self._emit("NEG", dst=dst, src1=a1, tac_index=tac_idx, rule_name="SEL-NEG")

        elif op == "NOT":
            self._emit("NOT", dst=dst, src1=a1, tac_index=tac_idx, rule_name="SEL-NOT")

        elif op == "JUMP":
            self._emit("JMP", dst=dst, tac_index=tac_idx, rule_name="SEL-JMP")

        elif op == "JUMP_IF":
            self._emit("CMP", dst=None, src1=a1, src2=Immediate(True), tac_index=tac_idx, rule_name="SEL-TEST-TRUE")
            self._emit("JE", dst=dst, tac_index=tac_idx, rule_name="SEL-BRANCH-IF")

        elif op == "JUMP_IF_FALSE":
            self._emit("CMP", dst=None, src1=a1, src2=Immediate(True), tac_index=tac_idx, rule_name="SEL-TEST-FALSE")
            self._emit("JNE", dst=dst, tac_index=tac_idx, rule_name="SEL-BRANCH-IF-FALSE")

        elif op == "PARAM":
            self._emit("PUSH", dst=None, src1=a1, tac_index=tac_idx, rule_name="SEL-PARAM-PUSH")

        elif op == "CALL":
            self._emit("CALL", dst=a1, src1=a2, tac_index=tac_idx, rule_name="SEL-CALL")
            if dst is not None:
                # Result convention: callee leaves return value in R0
                self._emit("MOV", dst=dst, src1=Register("R0"), tac_index=tac_idx, rule_name="SEL-CALL-RETVAL")

        elif op == "RETURN":
            if a1 is not None:
                self._emit("MOV", dst=Register("R0"), src1=a1, tac_index=tac_idx, rule_name="SEL-RETVAL")
            self._emit("RET", tac_index=tac_idx, rule_name="SEL-RET")

        elif op == "RECEIVE":
            self._emit("POP", dst=dst, tac_index=tac_idx, rule_name="SEL-RECEIVE-POP")

        elif op == "SHOW":
            self._emit("SYS_SHOW", dst=None, src1=a1, tac_index=tac_idx, rule_name="SEL-SYS-SHOW")

        elif op == "SHOW_NL":
            self._emit("SYS_SHOW_NL", tac_index=tac_idx, rule_name="SEL-SYS-SHOW-NL")

        elif op == "READ":
            self._emit("SYS_READ", dst=dst, tac_index=tac_idx, rule_name="SEL-SYS-READ")

        elif op == "ALLOC_ARRAY":
            self._emit("SYS_ALLOC", dst=dst, src1=a1, src2=a2, tac_index=tac_idx, rule_name="SEL-SYS-ALLOC")

        elif op == "ARRAY_GET":
            # Load from array element: dst = array[index]
            self._emit("LOAD", dst=dst, src1=a1, src2=a2, tac_index=tac_idx, rule_name="SEL-ARRAY-GET")

        elif op == "ARRAY_SET":
            # Store into array element: array[index] = val
            self._emit("STORE", dst=a1, src1=a2, src2=dst, tac_index=tac_idx, rule_name="SEL-ARRAY-SET")

        elif op == "CAST":
            target_t = a2.value if hasattr(a2, "value") else str(a2)
            self._emit("CAST", dst=dst, src1=a1, src2=Immediate(target_t), tac_index=tac_idx, rule_name="SEL-CAST")

        else:
            self._emit(op, dst=dst, src1=a1, src2=a2, tac_index=tac_idx, rule_name="SEL-RAW")
