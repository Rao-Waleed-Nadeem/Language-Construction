"""Control-Flow Graph (CFG) Construction and Representation.

Defined per:
- docs/10_CODE_OPTIMIZATION.md §2
- Dragon Book §8.4
- Master Spec P6-02
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from vela.ir.tac import Label
from vela.opt.blocks import BasicBlock, BlockPartition


@dataclass(frozen=True)
class CFGEdge:
    """Directed edge in the Control-Flow Graph."""

    source: int
    target: int
    kind: str  # "entry", "fall_through", "jump", "branch", "return"


@dataclass
class ControlFlowGraph:
    """Control-Flow Graph of basic blocks."""

    blocks: dict[int, BasicBlock]
    entry_id: int = 0
    exit_id: int = -1
    edges: list[CFGEdge] = field(default_factory=list)
    successors: dict[int, list[int]] = field(default_factory=dict)
    predecessors: dict[int, list[int]] = field(default_factory=dict)

    def add_edge(self, source: int, target: int, kind: str = "edge") -> None:
        edge = CFGEdge(source=source, target=target, kind=kind)
        if edge not in self.edges:
            self.edges.append(edge)
            self.successors.setdefault(source, [])
            if target not in self.successors[source]:
                self.successors[source].append(target)
            self.predecessors.setdefault(target, [])
            if source not in self.predecessors[target]:
                self.predecessors[target].append(source)

    def get_successors(self, block_id: int) -> list[int]:
        return self.successors.get(block_id, [])

    def get_predecessors(self, block_id: int) -> list[int]:
        return self.predecessors.get(block_id, [])

    def to_dict(self) -> dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "exit_id": self.exit_id,
            "block_count": len(self.blocks),
            "edge_count": len(self.edges),
            "blocks": {str(bid): b.to_dict() for bid, b in self.blocks.items()},
            "edges": [{"source": e.source, "target": e.target, "kind": e.kind} for e in self.edges],
            "successors": {str(bid): list(succs) for bid, succs in self.successors.items()},
            "predecessors": {str(bid): list(preds) for bid, preds in self.predecessors.items()},
        }

    def to_mermaid(self) -> str:
        """Render CFG in Mermaid flowchart format."""
        lines = ["flowchart TD"]
        lines.append('    B0["[ENTRY]"]')
        lines.append('    B_EXIT["[EXIT]"]')

        for bid, block in self.blocks.items():
            label = block.label or f"Block_{bid}"
            instr_lines = "\\n".join(str(i) for i in block.instructions[:4])
            if len(block.instructions) > 4:
                instr_lines += f"\\n... (+{len(block.instructions) - 4} more)"
            safe_text = f"B{bid}: {label}\\n{instr_lines}".replace('"', "'")
            lines.append(f'    B{bid}["{safe_text}"]')

        for edge in self.edges:
            src = "B0" if edge.source == self.entry_id else f"B{edge.source}"
            tgt = "B_EXIT" if edge.target == self.exit_id else f"B{edge.target}"
            label_text = f"|{edge.kind}|" if edge.kind not in ("fall_through", "jump") else ""
            lines.append(f"    {src} -->{label_text} {tgt}")

        return "\n".join(lines)


def build_cfg(partition: BlockPartition) -> ControlFlowGraph:
    """Build directed CFG from basic blocks."""
    blocks_dict: dict[int, BasicBlock] = {b.id: b for b in partition.blocks}
    cfg = ControlFlowGraph(blocks=blocks_dict)

    if not partition.blocks:
        return cfg

    # 1. Edge from ENTRY to first block
    first_block_id = partition.blocks[0].id
    cfg.add_edge(cfg.entry_id, first_block_id, kind="entry")

    # 2. Add edges between blocks
    for i, block in enumerate(partition.blocks):
        bid = block.id
        next_block_id = partition.blocks[i + 1].id if i + 1 < len(partition.blocks) else None

        if not block.instructions:
            if next_block_id is not None:
                cfg.add_edge(bid, next_block_id, kind="fall_through")
            continue

        # Check for function calls in block
        for instr in block.instructions:
            if instr.opcode == "CALL":
                target = instr.arg1
                target_name = target.name if isinstance(target, Label) else str(target) if target is not None else None
                if target_name and target_name in partition.label_to_block_id:
                    cfg.add_edge(bid, partition.label_to_block_id[target_name], kind="call")

        # Determine block exit control transfers
        has_return = any(i.opcode in ("RETURN", "FUNC_END") for i in block.instructions)
        last_instr = block.instructions[-1]
        op = last_instr.opcode

        if op == "JUMP":
            if isinstance(last_instr.result, Label) and last_instr.result.name in partition.label_to_block_id:
                target_bid = partition.label_to_block_id[last_instr.result.name]
                cfg.add_edge(bid, target_bid, kind="jump")
            # Unconditional jump has no fall-through

        elif op in ("JUMP_IF", "JUMP_IF_FALSE"):
            # Target branch
            if isinstance(last_instr.result, Label) and last_instr.result.name in partition.label_to_block_id:
                target_bid = partition.label_to_block_id[last_instr.result.name]
                cfg.add_edge(bid, target_bid, kind="branch")
            # Fall-through to next block
            if next_block_id is not None:
                cfg.add_edge(bid, next_block_id, kind="fall_through")

        elif has_return:
            cfg.add_edge(bid, cfg.exit_id, kind="return")

        else:
            # Fall-through to next block
            if next_block_id is not None:
                cfg.add_edge(bid, next_block_id, kind="fall_through")
            else:
                cfg.add_edge(bid, cfg.exit_id, kind="return")

    return cfg
