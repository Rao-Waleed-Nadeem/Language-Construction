"""Machine-Dependent Peephole Optimization.

Defined per:
- docs/11_TARGET_CODE_AND_VM_SPECIFICATION.md §1
- Master Spec P6-11
- Applies sliding-window transformations over target instructions to eliminate redundant operations.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from vela.codegen.isa import Immediate, TargetInstruction, TargetProgram


@dataclass
class PeepholeChange:
    """Record of a transformation performed by the peephole optimizer."""

    pattern_name: str
    description: str
    original: list[str]
    transformed: list[str]
    cost_saved: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "pattern_name": self.pattern_name,
            "description": self.description,
            "original": self.original,
            "transformed": self.transformed,
            "cost_saved": self.cost_saved,
        }


@dataclass
class PeepholeResult:
    """Result of running peephole optimization on a target program."""

    program: TargetProgram
    changes: list[PeepholeChange] = field(default_factory=list)
    cost_before: int = 0
    cost_after: int = 0
    cost_saved: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "cost_before": self.cost_before,
            "cost_after": self.cost_after,
            "cost_saved": self.cost_saved,
            "changes_count": len(self.changes),
            "changes": [c.to_dict() for c in self.changes],
            "text": self.program.to_text(),
        }


def optimize_peephole(program: TargetProgram) -> PeepholeResult:
    """Run window-based peephole optimizations on target instructions."""
    cost_before = program.total_cost()
    changes: list[PeepholeChange] = []
    instrs = list(program.instructions)

    changed = True
    while changed:
        changed = False
        new_instrs: list[TargetInstruction] = []
        i = 0
        n = len(instrs)

        while i < n:
            curr = instrs[i]
            nxt = instrs[i + 1] if i + 1 < n else None

            # Pattern 1: Redundant self-move MOV R, R -> eliminate
            if curr.opcode == "MOV" and curr.dst is not None and str(curr.dst) == str(curr.src1):
                changes.append(
                    PeepholeChange(
                        pattern_name="Redundant Move Elimination",
                        description=f"Eliminated self-move {curr}",
                        original=[str(curr)],
                        transformed=[],
                        cost_saved=curr.cost,
                    )
                )
                changed = True
                i += 1
                continue

            # Pattern 2: Algebraic identity ADD R, R, #0 or SUB R, R, #0 -> eliminate
            if (
                curr.opcode in ("ADD", "SUB")
                and curr.src2 is not None
                and isinstance(curr.src2, Immediate)
                and curr.src2.value == 0
                and str(curr.dst) == str(curr.src1)
            ):
                changes.append(
                    PeepholeChange(
                        pattern_name="Algebraic Identity",
                        description=f"Eliminated identity operation {curr}",
                        original=[str(curr)],
                        transformed=[],
                        cost_saved=curr.cost,
                    )
                )
                changed = True
                i += 1
                continue

            # Pattern 3: Redundant jump to immediately following label
            # JMP L; LABEL L: -> LABEL L:
            if nxt is not None and curr.opcode == "JMP" and nxt.opcode == "LABEL" and str(curr.dst) == str(nxt.dst):
                changes.append(
                    PeepholeChange(
                        pattern_name="Redundant Jump Elimination",
                        description=f"Eliminated jump to next label: {curr}",
                        original=[str(curr), str(nxt)],
                        transformed=[str(nxt)],
                        cost_saved=curr.cost,
                    )
                )
                new_instrs.append(nxt)
                changed = True
                i += 2
                continue

            # Pattern 4: Redundant load following store
            # STORE [addr], R; LOAD R, [addr] -> STORE [addr], R
            if (
                nxt is not None
                and curr.opcode == "STORE"
                and nxt.opcode == "LOAD"
                and str(curr.dst) == str(nxt.src1)
                and str(curr.src1) == str(nxt.dst)
            ):
                changes.append(
                    PeepholeChange(
                        pattern_name="Redundant Load Elimination",
                        description=f"Eliminated redundant load after store: {nxt}",
                        original=[str(curr), str(nxt)],
                        transformed=[str(curr)],
                        cost_saved=nxt.cost,
                    )
                )
                new_instrs.append(curr)
                changed = True
                i += 2
                continue

            # Pattern 5: Consecutive inverse moves
            # MOV R1, R2; MOV R2, R1 -> MOV R1, R2
            if (
                nxt is not None
                and curr.opcode == "MOV"
                and nxt.opcode == "MOV"
                and str(curr.dst) == str(nxt.src1)
                and str(curr.src1) == str(nxt.dst)
            ):
                changes.append(
                    PeepholeChange(
                        pattern_name="Inverse Move Elimination",
                        description=f"Eliminated inverse move: {nxt}",
                        original=[str(curr), str(nxt)],
                        transformed=[str(curr)],
                        cost_saved=nxt.cost,
                    )
                )
                new_instrs.append(curr)
                changed = True
                i += 2
                continue

            new_instrs.append(curr)
            i += 1

        instrs = new_instrs

    # Rebuild labels map
    new_labels: dict[str, int] = {}
    for idx, ins in enumerate(instrs):
        if ins.opcode == "LABEL" and ins.dst is not None:
            new_labels[str(ins.dst)] = idx

    cost_after = sum(ins.cost for ins in instrs)
    return PeepholeResult(
        program=TargetProgram(instructions=instrs, labels=new_labels),
        changes=changes,
        cost_before=cost_before,
        cost_after=cost_after,
        cost_saved=cost_before - cost_after,
    )
