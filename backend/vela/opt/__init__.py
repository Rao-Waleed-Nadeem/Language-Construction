"""Vela Optimization Package (Phase 6).

Implements basic block partitioning, control-flow graph construction,
dominator trees, natural loops, data-flow framework, and optimization passes.
"""

from vela.opt.blocks import BasicBlock, BlockPartition, Leader, partition_into_blocks
from vela.opt.cfg import CFGEdge, ControlFlowGraph, build_cfg
from vela.opt.dominators import DominatorInfo, compute_dominators

__all__ = [
    "BasicBlock",
    "BlockPartition",
    "CFGEdge",
    "ControlFlowGraph",
    "DominatorInfo",
    "Leader",
    "build_cfg",
    "compute_dominators",
    "partition_into_blocks",
]
