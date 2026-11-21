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


def _is_var(operand: Any) -> bool:
    return isinstance(operand, str) and not operand.startswith("L_") and not operand.startswith("L") and operand not in ("true", "false")


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
    ) -> Register:
        # 1. If already in a register, reuse it
        for r in self.registers:
            if v in self.reg_desc[r.name]:
                return r
        # 2. Pick an empty register
        empty_regs = [r for r in self.registers if not self.reg_desc[r.name]]
        if empty_regs:
            chosen = empty_regs[0]
        else:
            # 3. Spill register with farthest next use
            current_nu = next_uses[idx] if idx < len(next_uses) else {}
            chosen = max(
                self.registers,
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

        allocated_instructions: list[TargetInstruction] = []
        step = 0

        # Precompute next uses for each variable at each instruction index
        next_uses: list[dict[str, int]] = []
        future_use_map: dict[str, int] = {}
        for idx in range(len(unallocated.instructions) - 1, -1, -1):
            instr = unallocated.instructions[idx]
            current_next_uses = dict(future_use_map)
            next_uses.insert(0, current_next_uses)
            for oper in (instr.dst, instr.src1, instr.src2):
                if _is_var(oper):
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

            # Identify variable operands
            var_dst = str(instr.dst) if _is_var(instr.dst) else None
            var_src1 = str(instr.src1) if _is_var(instr.src1) else None
            var_src2 = str(instr.src2) if _is_var(instr.src2) else None

            # Load src1 and src2 if variables
            reg_src1 = (
                self._load_var_to_reg(
                    var_src1, idx, tac_idx, next_uses, allocated_instructions, spill_events, load_events
                )
                if var_src1
                else instr.src1
            )
            reg_src2 = (
                self._load_var_to_reg(
                    var_src2, idx, tac_idx, next_uses, allocated_instructions, spill_events, load_events
                )
                if var_src2
                else instr.src2
            )

            # Allocate dst if variable
            reg_dst: Any = instr.dst
            if var_dst:
                # If var_src1 is no longer needed after this instruction, we can reuse its register
                can_reuse = False
                nu = next_uses[idx].get(var_src1) if var_src1 and idx < len(next_uses) else None
                if (
                    var_src1
                    and isinstance(reg_src1, Register)
                    and (nu is None or nu > idx)
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
                        chosen = max(
                            self.registers,
                            key=lambda r: max([current_nu.get(v, 999999) for v in self.reg_desc[r.name]] or [999999]),
                        )
                        spill_events.append(f"Spilled {chosen.name} holding {list(self.reg_desc[chosen.name])}")
                        self._spill_reg(chosen.name, allocated_instructions, tac_idx)
                        reg_dst = chosen

                # Update descriptors for var_dst
                assert isinstance(reg_dst, Register)
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

        return AllocationResult(
            program=TargetProgram(instructions=allocated_instructions, labels=unallocated.labels),
            spills_count=self.spills_count,
            max_registers_used=self.max_regs_used,
            temp_to_location=self.temp_to_location,
            snapshots=self.snapshots,
        )
