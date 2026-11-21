"""Dominator Tree and Natural Loop Analysis.

Defined per:
- docs/10_CODE_OPTIMIZATION.md §3
- Dragon Book §9.6
- Master Spec P6-02
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from vela.opt.cfg import ControlFlowGraph


@dataclass
class DominatorInfo:
    """Dominator analysis results for a CFG."""

    # block_id -> set of block_ids that dominate it
    dom: dict[int, set[int]] = field(default_factory=dict)
    # block_id -> immediate dominator id (or None for ENTRY)
    idom: dict[int, int | None] = field(default_factory=dict)
    # block_id -> list of block_ids immediately dominated by it
    children: dict[int, list[int]] = field(default_factory=dict)
    # list of (source, target) back edges where target dominates source
    back_edges: list[tuple[int, int]] = field(default_factory=list)
    # (source, target) -> set of block_ids in the natural loop
    natural_loops: dict[tuple[int, int], set[int]] = field(default_factory=dict)

    def dominates(self, a: int, b: int) -> bool:
        """Returns True if block a dominates block b."""
        return a in self.dom.get(b, set())

    def strictly_dominates(self, a: int, b: int) -> bool:
        """Returns True if block a strictly dominates block b (a != b and a dom b)."""
        return a != b and self.dominates(a, b)

    def to_dict(self) -> dict[str, Any]:
        return {
            "dom": {str(k): sorted(v) for k, v in self.dom.items()},
            "idom": {str(k): v for k, v in self.idom.items()},
            "children": {str(k): sorted(v) for k, v in self.children.items()},
            "back_edges": [{"source": src, "target": tgt} for src, tgt in self.back_edges],
            "natural_loops": [
                {"back_edge": {"source": src, "target": tgt}, "blocks": sorted(blocks)}
                for (src, tgt), blocks in self.natural_loops.items()
            ],
        }


def compute_dominators(cfg: ControlFlowGraph) -> DominatorInfo:
    """Compute dominators, immediate dominators, back edges, and natural loops for a CFG."""
    info = DominatorInfo()
    entry = cfg.entry_id
    all_blocks = {entry} | set(cfg.blocks.keys())

    # 1. Iterative dominator computation:
    # DOM(entry) = {entry}
    # DOM(n) = {n} U (intersection of DOM(p) for all predecessors p of n)
    dom: dict[int, set[int]] = {entry: {entry}}
    for b in all_blocks:
        if b != entry:
            dom[b] = set(all_blocks)

    changed = True
    while changed:
        changed = False
        for b in all_blocks:
            if b == entry:
                continue
            preds = [p for p in cfg.get_predecessors(b) if p in all_blocks]
            if not preds:
                new_dom = {b}
            else:
                inter = set(dom[preds[0]])
                for p in preds[1:]:
                    inter &= dom[p]
                new_dom = {b} | inter

            if new_dom != dom[b]:
                dom[b] = new_dom
                changed = True

    info.dom = dom

    # 2. Compute immediate dominator (idom):
    # idom(n) is the unique strict dominator d of n that does not dominate any other strict dominator of n
    idom: dict[int, int | None] = {entry: None}
    for n in all_blocks:
        if n == entry:
            continue
        strict_doms = dom[n] - {n}
        if not strict_doms:
            idom[n] = None
            continue

        # Find d in strict_doms that does not strictly dominate any other element of strict_doms
        candidate: int | None = None
        for d in strict_doms:
            # Check if d is dominated by all other strict dominators
            # That is: no other s in strict_doms dominates d (except d itself)
            # Actually, idom(n) is dominated by all other strict dominators!
            # Let's verify: in a chain 0 -> 1 -> 2, dom(2)={0, 1, 2}. strict={0, 1}.
            # 0 dom 1. So 1 is closest to 2. 1's strict doms are {0}.
            # Thus idom(n) is the element d in strict_doms whose dom set has size len(strict_doms).
            if len(dom[d]) == len(strict_doms):
                candidate = d
                break

        if candidate is None and strict_doms:
            # Fallback by sorting by dom set size descending
            candidate = max(strict_doms, key=lambda d: len(dom[d]))

        idom[n] = candidate

    info.idom = idom

    # Build dominator tree children
    for n, p in idom.items():
        if p is not None:
            info.children.setdefault(p, []).append(n)

    # 3. Identify back edges and natural loops:
    # A back edge is a CFG edge a -> b where b dominates a (b in DOM(a))
    back_edges: list[tuple[int, int]] = []
    for edge in cfg.edges:
        if edge.kind == "call":
            continue
        src, tgt = edge.source, edge.target
        if tgt != cfg.exit_id and src in all_blocks and tgt in all_blocks and info.dominates(tgt, src):
            back_edges.append((src, tgt))

    info.back_edges = back_edges

    # 4. Construct natural loop for each back edge n -> d
    natural_loops: dict[tuple[int, int], set[int]] = {}
    for src, tgt in back_edges:
        loop: set[int] = {tgt, src}
        stack: list[int] = []
        if src != tgt:
            stack.append(src)

        while stack:
            m = stack.pop()
            for p in cfg.get_predecessors(m):
                if p in all_blocks and p not in loop:
                    loop.add(p)
                    stack.append(p)

        natural_loops[(src, tgt)] = loop

    info.natural_loops = natural_loops
    return info
