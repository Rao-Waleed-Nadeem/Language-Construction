"""Optimization Pipeline and Iterative Runner.

Defined per:
- docs/10_CODE_OPTIMIZATION.md §5, §6
- Master Spec P6-12, P6-13
- Runs passes to fixed-point, logging before/after diffs, change records, and metrics.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, ClassVar

from vela.ir.tac import TACProgram
from vela.opt.passes import (
    OptimizationChange,
    run_algebraic_simplification,
    run_common_subexpression_elimination,
    run_constant_folding,
    run_constant_propagation,
    run_copy_propagation,
    run_dead_code_elimination,
    run_loop_invariant_code_motion,
    run_strength_reduction,
)
from vela.opt.validate import validate_tac_well_formedness

PassFunction = Callable[[TACProgram], tuple[TACProgram, list[OptimizationChange]]]


@dataclass
class PassReport:
    """Report on execution of one optimization pass."""

    name: str
    change_count: int
    changes: list[OptimizationChange]
    before_instruction_count: int
    after_instruction_count: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "change_count": self.change_count,
            "changes": [c.to_dict() for c in self.changes],
            "before_instruction_count": self.before_instruction_count,
            "after_instruction_count": self.after_instruction_count,
        }


@dataclass
class OptimizationResult:
    """Complete result of the optimization pipeline."""

    original_program: TACProgram
    optimized_program: TACProgram
    passes: list[PassReport] = field(default_factory=list)
    all_changes: list[OptimizationChange] = field(default_factory=list)
    iterations_run: int = 0
    instruction_count_before: int = 0
    instruction_count_after: int = 0
    reduction_percentage: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "instruction_count_before": self.instruction_count_before,
            "instruction_count_after": self.instruction_count_after,
            "reduction_percentage": round(self.reduction_percentage, 2),
            "iterations_run": self.iterations_run,
            "total_changes_count": len(self.all_changes),
            "passes": [p.to_dict() for p in self.passes],
            "all_changes": [c.to_dict() for c in self.all_changes],
            "original_text": self.original_program.to_text(),
            "optimized_text": self.optimized_program.to_text(),
        }


class OptimizerPipeline:
    """Fixed-point optimization pipeline running configured passes."""

    DEFAULT_PASSES: ClassVar[list[tuple[str, PassFunction]]] = [
        ("Constant Folding", run_constant_folding),
        ("Algebraic Simplification", run_algebraic_simplification),
        ("Constant Propagation", run_constant_propagation),
        ("Copy Propagation", run_copy_propagation),
        ("Common Subexpression Elimination", run_common_subexpression_elimination),
        ("Strength Reduction", run_strength_reduction),
        ("Loop-Invariant Code Motion", run_loop_invariant_code_motion),
        ("Dead-Code Elimination", run_dead_code_elimination),
    ]

    def __init__(
        self,
        passes: list[tuple[str, PassFunction]] | None = None,
        max_iterations: int = 5,
    ) -> None:
        self.passes = passes or self.DEFAULT_PASSES
        self.max_iterations = max_iterations

    def optimize(self, program: TACProgram) -> OptimizationResult:
        """Run all passes in sequence iteratively until fixed-point or max iterations reached."""
        current_program = program
        before_count = len(program.instructions)

        pass_reports: list[PassReport] = []
        all_changes: list[OptimizationChange] = []
        iterations_run = 0

        for it in range(self.max_iterations):
            iterations_run = it + 1
            iteration_changed = False

            for pass_name, pass_fn in self.passes:
                count_before = len(current_program.instructions)
                next_program, changes = pass_fn(current_program)
                count_after = len(next_program.instructions)

                if changes:
                    iteration_changed = True
                    all_changes.extend(changes)

                pass_reports.append(
                    PassReport(
                        name=pass_name,
                        change_count=len(changes),
                        changes=changes,
                        before_instruction_count=count_before,
                        after_instruction_count=count_after,
                    )
                )
                current_program = next_program

            # If no pass produced any changes this iteration, we reached fixed-point
            if not iteration_changed:
                break

        # Validate well-formedness of final program
        validate_tac_well_formedness(current_program)

        after_count = len(current_program.instructions)
        reduction = ((before_count - after_count) / before_count * 100.0) if before_count > 0 else 0.0

        return OptimizationResult(
            original_program=program,
            optimized_program=current_program,
            passes=pass_reports,
            all_changes=all_changes,
            iterations_run=iterations_run,
            instruction_count_before=before_count,
            instruction_count_after=after_count,
            reduction_percentage=reduction,
        )


def optimize_tac(program: TACProgram, max_iterations: int = 5) -> OptimizationResult:
    """Convenience helper to optimize a TACProgram with standard pipeline."""
    return OptimizerPipeline(max_iterations=max_iterations).optimize(program)
