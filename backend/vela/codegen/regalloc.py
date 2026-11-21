"""Register Allocation using Dragon Book Algorithm 8.7 (getReg).

Defined per:
- docs/11_TARGET_CODE_AND_VM_SPECIFICATION.md §3
- Master Spec P7-04, P7-05
- Acceptance criteria:
  - AC-C3: Register snapshots never show two live variables in one register.
  - AC-C4: Functions with > 8 simultaneously live values show spills.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from vela.codegen.cost import get_instruction_cost
from vela.codegen.isa import (
    ALLOCATABLE_REGS,
    FP,
    MemoryRef,
    Register,
    TargetInstruction,
    TargetProgram,
)


@dataclass
class RegisterSnapshot:
    """Snapshot of register and address descriptors at a single step."""

    step: int
    instruction_text: str
    register_descriptors: dict[str, list[str]]
    address_descriptors: dict[str, list[str]]
    spill_events: list[str] = field(default_factory=list)
    load_events: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "step": self.step,
            "instruction_text": self.instruction_text,
            "register_descriptors": self.register_descriptors,
            "address_descriptors": self.address_descriptors,
            "spill_events": self.spill_events,
            "load_events": self.load_events,
        }


@dataclass
class AllocationResult:
    """Result of register allocation over a target program."""

    program: TargetProgram
    spills_count: int
    max_registers_used: int
    temp_to_location: dict[str, str]
    snapshots: list[RegisterSnapshot] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "spills_count": self.spills_count,
            "max_registers_used": self.max_registers_used,
            "temp_to_location": self.temp_to_location,
            "snapshots_count": len(self.snapshots),
            "instruction_count": len(self.program.instructions),
            "total_cost": self.program.total_cost(),
            "snapshots": [s.to_dict() for s in self.snapshots],
            "text": self.program.to_text(),
        }


BRANCH_OR_CALL_OPS = {"JMP", "JE", "JNE", "JL", "JLE", "JG", "JGE", "CALL", "LABEL"}


def _is_var(operand: Any, labels: set[str] | None = None) -> bool:
    if not isinstance(operand, str):
        return False
    if operand.startswith(("L_", "L")) or operand in ("true", "false"):
        return False
    return not (labels is not None and operand in labels)


class RegisterAllocator:
    """Allocates physical registers R0-R7 to symbolic variables using Algorithm 8.7."""

    def __init__(self, registers: list[Register] | None = None) -> None:
        self.registers = registers or list(ALLOCATABLE_REGS)
        self.reg_desc: dict[str, set[str]] = {r.name: set() for r in self.registers}
        self.addr_desc: dict[str, set[str]] = {}
        self.stack_offsets: dict[str, int] = {}
        self.next_stack_offset = 4
        self.spills_count = 0
        self.max_regs_used = 0
        self.snapshots: list[RegisterSnapshot] = []
        self.temp_to_location: dict[str, str] = {}
        self.var_to_reg: dict[str, Register] = {}

    def _get_stack_ref(self, var: str) -> MemoryRef:
        if var not in self.stack_offsets:
            self.stack_offsets[var] = self.next_stack_offset
            self.next_stack_offset += 4
        return MemoryRef(base=FP, offset=-self.stack_offsets[var])

    def _spill_reg(self, reg_name: str, instrs: list[TargetInstruction], tac_idx: int) -> None:
        vars_in_reg = list(self.reg_desc[reg_name])
        for v in vars_in_reg:
            # If variable has no other copy (in memory or another reg), spill to stack
            locs = self.addr_desc.get(v, set())
            has_mem = any(loc.startswith("[") for loc in locs)
            if not has_mem:
                mem_ref = self._get_stack_ref(v)
                instr = TargetInstruction(
                    opcode="STORE",
                    dst=mem_ref,
                    src1=Register(reg_name),
                    cost=get_instruction_cost("STORE", mem_ref, Register(reg_name)),
                    tac_index=tac_idx,
                    rule_name="REG-SPILL",
                    comment=f"spill {v}",
                )
                instrs.append(instr)
                self.spills_count += 1
                locs.add(str(mem_ref))
                self.temp_to_location[v] = str(mem_ref)
            locs.discard(reg_name)
        self.reg_desc[reg_name].clear()

    def _load_var_to_reg(
        self,
        v: str,
        idx: int,
        tac_idx: int,
        next_uses: list[dict[str, int]],
        allocated_instructions: list[TargetInstruction],
        spill_events: list[str],
        load_events: list[str],
        exclude_regs: set[str] | None = None,
    ) -> Register:
        exclude = exclude_regs or set()
        available_regs = [r for r in self.registers if r.name not in exclude]

        # 1. If variable already assigned a register, reuse that register
        if v in self.var_to_reg and self.var_to_reg[v].name not in exclude:
            chosen = self.var_to_reg[v]
            if v not in self.reg_desc[chosen.name]:
                # Emit LOAD if variable was spilled or not loaded yet
                mem_ref = self._get_stack_ref(v)
                load_instr = TargetInstruction(
                    opcode="LOAD",
                    dst=chosen,
                    src1=mem_ref,
                    cost=get_instruction_cost("LOAD", chosen, mem_ref),
                    tac_index=tac_idx,
                    rule_name="REG-LOAD",
                    comment=f"load {v}",
                )
                allocated_instructions.append(load_instr)
                load_events.append(f"Loaded {v} into {chosen.name}")
                self.reg_desc[chosen.name].clear()
                self.reg_desc[chosen.name].add(v)
            return chosen

        for r in available_regs:
            if v in self.reg_desc[r.name]:
                return r

        # 2. Pick an empty register
        empty_regs = [r for r in available_regs if not self.reg_desc[r.name]]
        if empty_regs:
            chosen = empty_regs[0]
        else:
            # 3. Spill register with farthest next use (from available_regs!)
            current_nu = next_uses[idx] if idx < len(next_uses) else {}
            chosen = max(
                available_regs,
                key=lambda r: max([current_nu.get(var, 999999) for var in self.reg_desc[r.name]] or [999999]),
            )
            spill_events.append(f"Spilled {chosen.name} holding {list(self.reg_desc[chosen.name])}")
            self._spill_reg(chosen.name, allocated_instructions, tac_idx)

        # Emit LOAD if variable has memory address
        mem_ref = self._get_stack_ref(v)
        load_instr = TargetInstruction(
            opcode="LOAD",
            dst=chosen,
            src1=mem_ref,
            cost=get_instruction_cost("LOAD", chosen, mem_ref),
            tac_index=tac_idx,
            rule_name="REG-LOAD",
            comment=f"load {v}",
        )
        allocated_instructions.append(load_instr)
        load_events.append(f"Loaded {v} into {chosen.name}")
        self.reg_desc[chosen.name].add(v)
        self.addr_desc.setdefault(v, set()).add(chosen.name)
        if not (v.startswith("t") and v[1:].isdigit()):
            self.var_to_reg[v] = chosen
        return chosen

    def allocate(self, unallocated: TargetProgram) -> AllocationResult:
        """Run register allocation across all instructions."""
        self.reg_desc = {r.name: set() for r in self.registers}
        self.addr_desc = {}
        self.stack_offsets = {}
        self.next_stack_offset = 4
        self.spills_count = 0
        self.max_regs_used = 0
        self.snapshots = []
        self.temp_to_location = {}
        self.var_to_reg = {}

        allocated_instructions: list[TargetInstruction] = []
        step = 0
        known_labels = set(unallocated.labels.keys())

        # Collect label positions
        label_positions: dict[str, int] = {}
        for idx, instr in enumerate(unallocated.instructions):
            if instr.opcode == "LABEL":
                label_positions[str(instr.dst)] = idx

        # Multi-pass next-use calculation with jump propagation and def-kill
        next_uses: list[dict[str, int]] = [{} for _ in unallocated.instructions]
        for _ in range(5):
            future_use_map: dict[str, int] = {}
            for idx in range(len(unallocated.instructions) - 1, -1, -1):
                instr = unallocated.instructions[idx]
                op = instr.opcode
                if op in ("JMP", "JE", "JNE", "JL", "JLE", "JG", "JGE"):
                    target = str(instr.dst)
                    if target in label_positions:
                        target_idx = label_positions[target]
                        if target_idx < len(next_uses):
                            for var, next_idx in next_uses[target_idx].items():
                                if var not in future_use_map or next_idx < future_use_map[var]:
                                    future_use_map[var] = next_idx

                next_uses[idx] = dict(future_use_map)

                if op in BRANCH_OR_CALL_OPS:
                    continue

                # Def kills live variable in backward scan
                if op != "STORE" and _is_var(instr.dst, known_labels):
                    future_use_map.pop(str(instr.dst), None)

                # Used variables generated in backward scan
                src_list = (instr.dst, instr.src1, instr.src2) if op == "STORE" else (instr.src1, instr.src2)
                for oper in src_list:
                    if _is_var(oper, known_labels):
                        future_use_map[str(oper)] = idx

        for idx, instr in enumerate(unallocated.instructions):
            step += 1
            spill_events: list[str] = []
            load_events: list[str] = []
            op = instr.opcode
            tac_idx = instr.tac_index

            # Labels and control flow reset or pass through
            if op == "LABEL":
                allocated_instructions.append(instr)
                continue

            if op in BRANCH_OR_CALL_OPS:
                allocated_instructions.append(instr)
                continue

            if op == "STORE":
                # STORE can be array store (dst=arr, src1=idx, src2=val) or memory store (dst=MemoryRef, src1=val)
                if instr.src2 is not None:
                    var_arr = str(instr.dst) if _is_var(instr.dst, known_labels) else None
                    var_idx = str(instr.src1) if _is_var(instr.src1, known_labels) else None
                    var_val = str(instr.src2) if _is_var(instr.src2, known_labels) else None

                    reg_arr = self._load_var_to_reg(var_arr, idx, tac_idx, next_uses, allocated_instructions, spill_events, load_events) if var_arr else instr.dst
                    ex1 = {reg_arr.name} if isinstance(reg_arr, Register) else set()
                    reg_idx = self._load_var_to_reg(var_idx, idx, tac_idx, next_uses, allocated_instructions, spill_events, load_events, exclude_regs=ex1) if var_idx else instr.src1
                    ex2 = ex1 | ({reg_idx.name} if isinstance(reg_idx, Register) else set())
                    reg_val = self._load_var_to_reg(var_val, idx, tac_idx, next_uses, allocated_instructions, spill_events, load_events, exclude_regs=ex2) if var_val else instr.src2

                    reg_dst = reg_arr
                    reg_src1 = reg_idx
                    reg_src2 = reg_val
                else:
                    var_src1 = str(instr.src1) if _is_var(instr.src1, known_labels) else None
                    reg_src1 = self._load_var_to_reg(var_src1, idx, tac_idx, next_uses, allocated_instructions, spill_events, load_events) if var_src1 else instr.src1
                    reg_dst = instr.dst
                    reg_src2 = None

            else:
                # Identify variable operands
                var_dst = str(instr.dst) if _is_var(instr.dst, known_labels) else None
                var_src1 = str(instr.src1) if _is_var(instr.src1, known_labels) else None
                var_src2 = str(instr.src2) if _is_var(instr.src2, known_labels) else None

                # Load src1 and src2 if variables
                reg_src1 = (
                    self._load_var_to_reg(
                        var_src1, idx, tac_idx, next_uses, allocated_instructions, spill_events, load_events
                    )
                    if var_src1
                    else instr.src1
                )
                ex1 = {reg_src1.name} if (isinstance(reg_src1, Register) and var_src1 != var_src2) else set()
                reg_src2 = (
                    self._load_var_to_reg(
                        var_src2, idx, tac_idx, next_uses, allocated_instructions, spill_events, load_events, exclude_regs=ex1
                    )
                    if var_src2
                    else instr.src2
                )

                # Allocate dst if variable
                reg_dst = instr.dst
                if var_dst:
                    # 1. If var_dst has an assigned register in var_to_reg, reuse it
                    if var_dst in self.var_to_reg:
                        reg_dst = self.var_to_reg[var_dst]
                    else:
                        existing_reg = None
                        for r in self.registers:
                            if var_dst in self.reg_desc[r.name]:
                                existing_reg = r
                                break

                        if existing_reg is not None:
                            reg_dst = existing_reg
                        else:
                            # 2. If var_src1 is no longer needed after this instruction, we can reuse its register
                            can_reuse = False
                            nu = next_uses[idx].get(var_src1) if var_src1 and idx < len(next_uses) else None
                            if (
                                var_src1
                                and isinstance(reg_src1, Register)
                                and nu is None
                                and self.reg_desc[reg_src1.name] == {var_src1}
                            ):
                                can_reuse = True
                                reg_dst = reg_src1

                            if not can_reuse:
                                empty_regs = [r for r in self.registers if not self.reg_desc[r.name]]
                                if empty_regs:
                                    reg_dst = empty_regs[0]
                                else:
                                    current_nu = next_uses[idx] if idx < len(next_uses) else {}
                                    cand_regs = list(self.registers)
                                    chosen = max(
                                        cand_regs,
                                        key=lambda r: max([current_nu.get(v, 999999) for v in self.reg_desc[r.name]] or [999999]),
                                    )
                                    spill_events.append(f"Spilled {chosen.name} holding {list(self.reg_desc[chosen.name])}")
                                    self._spill_reg(chosen.name, allocated_instructions, tac_idx)
                                    reg_dst = chosen

                    # Update descriptors for var_dst
                    assert isinstance(reg_dst, Register)
                    if not (var_dst.startswith("t") and var_dst[1:].isdigit()):
                        self.var_to_reg[var_dst] = reg_dst

                    # Spill previous occupant of reg_dst if it's a different live variable
                    prev_occupants = [v for v in self.reg_desc[reg_dst.name] if v != var_dst]
                    if prev_occupants:
                        current_nu = next_uses[idx] if idx < len(next_uses) else {}
                        for prev_v in prev_occupants:
                            if current_nu.get(prev_v) is not None:
                                self._spill_reg(reg_dst.name, allocated_instructions, tac_idx)
                                spill_events.append(f"Spilled {reg_dst.name} holding {list(prev_occupants)}")
                                break

                    # Any old locations of var_dst are overwritten
                    for r in self.registers:
                        self.reg_desc[r.name].discard(var_dst)
                    # Clear previous occupant of reg_dst to ensure at most 1 variable per register (AC-C3)
                    self.reg_desc[reg_dst.name].clear()
                    self.reg_desc[reg_dst.name].add(var_dst)
                    self.addr_desc[var_dst] = {reg_dst.name}
                    self.temp_to_location[var_dst] = reg_dst.name

            # Emit allocated instruction
            alloc_instr = TargetInstruction(
                opcode=instr.opcode,
                dst=reg_dst,
                src1=reg_src1,
                src2=reg_src2,
                cost=get_instruction_cost(instr.opcode, reg_dst, reg_src1, reg_src2),
                tac_index=tac_idx,
                rule_name=instr.rule_name,
                comment=instr.comment,
            )
            allocated_instructions.append(alloc_instr)

            # Track max registers used
            used_now = sum(1 for r in self.registers if len(self.reg_desc[r.name]) > 0)
            self.max_regs_used = max(self.max_regs_used, used_now)

            # Discard dead temporaries that have no future next-use
            current_nu = next_uses[idx] if idx < len(next_uses) else {}
            for r in self.registers:
                for v in list(self.reg_desc[r.name]):
                    if (v.startswith("t") and v[1:].isdigit()) and current_nu.get(v) is None:
                        self.reg_desc[r.name].discard(v)

            # Record snapshot
            self.snapshots.append(
                RegisterSnapshot(
                    step=step,
                    instruction_text=str(alloc_instr).strip(),
                    register_descriptors={r.name: sorted(self.reg_desc[r.name]) for r in self.registers},
                    address_descriptors={k: sorted(v) for k, v in self.addr_desc.items()},
                    spill_events=spill_events,
                    load_events=load_events,
                )
            )

        # Rebuild labels map based on allocated instruction offsets
        allocated_labels: dict[str, int] = {}
        for idx, ins in enumerate(allocated_instructions):
            if ins.opcode == "LABEL" and ins.dst is not None:
                allocated_labels[str(ins.dst)] = idx

        return AllocationResult(
            program=TargetProgram(instructions=allocated_instructions, labels=allocated_labels),
            spills_count=self.spills_count,
            max_registers_used=self.max_regs_used,
            temp_to_location=self.temp_to_location,
            snapshots=self.snapshots,
        )
