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
from vela.opt.pipeline import OptimizationResult, OptimizerPipeline, PassReport, optimize_tac
from vela.opt.validate import TACValidationError, validate_tac_well_formedness, verify_equivalence

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
    "OptimizationResult",
    "OptimizerPipeline",
    "PassReport",
    "TACValidationError",
    "build_cfg",
    "compute_dominators",
    "optimize_tac",
    "partition_into_blocks",
    "solve_available_copies",
    "solve_available_expressions",
    "solve_live_variables",
    "solve_reaching_definitions",
    "validate_tac_well_formedness",
    "verify_equivalence",
]
