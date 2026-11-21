"""Vela Optimization Package (Phase 6).

Implements basic block partitioning, control-flow graph construction,
dominator trees, natural loops, data-flow framework, and optimization passes.
"""

from vela.opt.blocks import BasicBlock, BlockPartition, Leader, partition_into_blocks
from vela.opt.cfg import CFGEdge, ControlFlowGraph, build_cfg
from vela.opt.dataflow import (
    CopyItem,
    DataFlowResult,
    Definition,
    Direction,
    ExprItem,
    IterationLog,
    MeetOperator,
    solve_available_copies,
    solve_available_expressions,
    solve_live_variables,
    solve_reaching_definitions,
)
from vela.opt.dominators import DominatorInfo, compute_dominators

__all__ = [
    "BasicBlock",
    "BlockPartition",
    "CFGEdge",
    "ControlFlowGraph",
    "CopyItem",
    "DataFlowResult",
    "Definition",
    "Direction",
    "DominatorInfo",
    "ExprItem",
    "IterationLog",
    "Leader",
    "MeetOperator",
    "build_cfg",
    "compute_dominators",
    "partition_into_blocks",
    "solve_available_copies",
    "solve_available_expressions",
    "solve_live_variables",
    "solve_reaching_definitions",
]
