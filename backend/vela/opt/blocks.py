"""Basic Block Partitioning and Leader Identification.

Defined per:
- docs/10_CODE_OPTIMIZATION.md §2
- Dragon Book (Aho, Lam, Sethi, Ullman) §8.4 Algorithm 8.5
- Master Spec P6-01
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from vela.ir.tac import Label, TACInstruction


@dataclass
class Leader:
    """An instruction identified as the beginning of a basic block."""

    index: int
    reason: str


@dataclass
class BasicBlock:
    """A maximal sequence of consecutive instructions with single entry and exit."""

    id: int
    instructions: list[TACInstruction] = field(default_factory=list)
    leader_reason: str = ""
    start_index: int = 0
    end_index: int = 0  # inclusive
    label: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "label": self.label,
            "start_index": self.start_index,
            "end_index": self.end_index,
            "leader_reason": self.leader_reason,
            "instruction_count": len(self.instructions),
            "instructions": [instr.to_dict() for instr in self.instructions],
        }


@dataclass
class BlockPartition:
    """Result of partitioning TAC instructions into basic blocks."""

    blocks: list[BasicBlock]
    leaders: list[Leader]
    label_to_block_id: dict[str, int] = field(default_factory=dict)

    def get_block(self, block_id: int) -> BasicBlock | None:
        for b in self.blocks:
            if b.id == block_id:
                return b
        return None

    def to_dict(self) -> dict[str, Any]:
        return {
            "block_count": len(self.blocks),
            "blocks": [b.to_dict() for b in self.blocks],
            "leaders": [{"index": l.index, "reason": l.reason} for l in self.leaders],
        }


def partition_into_blocks(instructions: list[TACInstruction]) -> BlockPartition:
    """Partition TAC instructions into basic blocks following Algorithm 8.5."""
    if not instructions:
        return BlockPartition(blocks=[], leaders=[])

    n = len(instructions)
    # Collect all jump targets
    label_indices: dict[str, int] = {}
    for idx, instr in enumerate(instructions):
        if instr.opcode == "LABEL" and isinstance(instr.result, Label):
            label_indices[instr.result.name] = idx

    # 1. Identify leaders
    leaders_map: dict[int, str] = {}

    # Rule 1: The first instruction is a leader
    leaders_map[0] = "first instruction"

    for idx, instr in enumerate(instructions):
        op = instr.opcode

        # Rule 2: Any instruction that is the target of a jump is a leader
        if op in ("JUMP", "JUMP_IF", "JUMP_IF_FALSE") and isinstance(instr.result, Label):
            target_name = instr.result.name
            if target_name in label_indices:
                t_idx = label_indices[target_name]
                if t_idx not in leaders_map:
                    leaders_map[t_idx] = f"jump target: {target_name}"

        # Rule 3: Any instruction following a jump or return is a leader
        if (
            op in ("JUMP", "JUMP_IF", "JUMP_IF_FALSE", "RETURN")
            and idx + 1 < n
            and instructions[idx + 1].opcode != "FUNC_END"
            and (idx + 1) not in leaders_map
        ):
            leaders_map[idx + 1] = f"follows {op}"

        # Function boundaries also start leaders
        if op == "FUNC_BEGIN" and idx not in leaders_map:
            leaders_map[idx] = f"function entry: {instr.result}"

    sorted_leader_indices = sorted(leaders_map.keys())
    leaders = [Leader(index=i, reason=leaders_map[i]) for i in sorted_leader_indices]

    # 2. Form blocks
    blocks: list[BasicBlock] = []
    label_to_block_id: dict[str, int] = {}

    for b_idx, start in enumerate(sorted_leader_indices):
        end = sorted_leader_indices[b_idx + 1] - 1 if b_idx + 1 < len(sorted_leader_indices) else n - 1
        block_instrs = instructions[start : end + 1]

        # Extract label name if the block starts with LABEL or FUNC_BEGIN
        block_label: str | None = None
        if block_instrs and block_instrs[0].opcode in ("LABEL", "FUNC_BEGIN") and isinstance(block_instrs[0].result, Label):
            block_label = block_instrs[0].result.name

        block_id = b_idx + 1
        if block_label is not None:
            label_to_block_id[block_label] = block_id

        block = BasicBlock(
            id=block_id,
            instructions=block_instrs,
            leader_reason=leaders_map[start],
            start_index=start,
            end_index=end,
            label=block_label,
        )
        blocks.append(block)

    return BlockPartition(
        blocks=blocks,
        leaders=leaders,
        label_to_block_id=label_to_block_id,
    )
