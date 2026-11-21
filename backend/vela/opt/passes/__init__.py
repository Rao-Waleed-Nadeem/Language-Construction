"""Optimization Passes Package (Phase 6).

Defined per:
- docs/10_CODE_OPTIMIZATION.md §5
- Master Spec P6-03..P6-09
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class OptimizationChange:
    """Record of a single transformation performed by an optimization pass."""

    pass_name: str
    description: str
    original: str
    transformed: str
    instr_index: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "pass_name": self.pass_name,
            "description": self.description,
            "original": self.original,
            "transformed": self.transformed,
            "instr_index": self.instr_index,
        }


from vela.opt.passes.const_fold import run_constant_folding
from vela.opt.passes.const_prop import run_constant_propagation
from vela.opt.passes.copy_prop import run_copy_propagation
from vela.opt.passes.cse import run_common_subexpression_elimination
from vela.opt.passes.dce import run_dead_code_elimination
from vela.opt.passes.licm import run_loop_invariant_code_motion
from vela.opt.passes.simplify import run_algebraic_simplification
from vela.opt.passes.strength import run_strength_reduction

__all__ = [
    "OptimizationChange",
    "run_algebraic_simplification",
    "run_common_subexpression_elimination",
    "run_constant_folding",
    "run_constant_propagation",
    "run_copy_propagation",
    "run_dead_code_elimination",
    "run_loop_invariant_code_motion",
    "run_strength_reduction",
]
