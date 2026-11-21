"""Classifier for S-attributed and L-attributed Syntax-Directed Definitions.

Per doc 03 §5.6, doc 08 §3, and agent-prompt.md:
- S-attributed check: all attributes must be synthesized.
- L-attributed check: inherited attributes may only depend on parent inherited attributes
  or left-sibling attributes.
- Pinpoints the exact violating rule when a grammar is not S- or L-attributed.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from vela.semantic.sdd.evaluator import SafeSDDEvaluator
from vela.semantic.sdd.model import SDDProduction


@dataclass
class ClassificationResult:
    """Result of classifying an SDD."""

    is_s_attributed: bool
    is_l_attributed: bool
    violating_rule: str | None = None
    violating_production: str | None = None
    reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "is_s_attributed": self.is_s_attributed,
            "is_l_attributed": self.is_l_attributed,
            "violating_rule": self.violating_rule,
            "violating_production": self.violating_production,
            "reason": self.reason,
        }


class SDDClassifier:
    """Analyzes attribute dependencies to determine S- and L-attributed membership."""

    @classmethod
    def classify(cls, productions: list[SDDProduction]) -> ClassificationResult:
        is_s_attr = True
        is_l_attr = True
        s_violation_rule: str | None = None
        s_violation_prod: str | None = None
        l_violation_rule: str | None = None
        l_violation_prod: str | None = None
        l_violation_reason = ""

        # First pass: map symbols to their position in each production
        for prod in productions:
            # Normalize rhs symbols with potential subscript names
            # e.g. for E -> E + T, the symbols in rules might be E (LHS), E1 (RHS[0]), T (RHS[2])
            symbol_positions: dict[str, int] = {}
            symbol_positions[prod.lhs] = -1  # -1 represents LHS / parent

            # Map RHS symbols
            counts: dict[str, int] = {}
            for pos, sym in enumerate(prod.rhs):
                counts[sym] = counts.get(sym, 0) + 1
                # Plain name
                if sym not in symbol_positions:
                    symbol_positions[sym] = pos
                # Subscripted name (e.g. E1, E2)
                sub_name = f"{sym}{counts[sym]}"
                symbol_positions[sub_name] = pos

            for rule in prod.rules:
                target_sym = rule.target_symbol
                # Check if target is LHS (synthesized) or RHS (inherited)
                is_synthesized = (target_sym == prod.lhs)

                if not is_synthesized:
                    # Inherited attribute definition
                    if is_s_attr:
                        is_s_attr = False
                        s_violation_rule = str(rule)
                        s_violation_prod = prod.production_str

                    # Check L-attributed condition for this inherited attribute
                    target_pos = symbol_positions.get(target_sym)
                    if target_pos is None:
                        # Unknown symbol
                        continue

                    # Extract dependencies
                    deps = rule.source_refs or SafeSDDEvaluator.extract_dependencies(rule.expr_str)
                    for dep_sym, dep_attr in deps:
                        dep_pos = symbol_positions.get(dep_sym)
                        if dep_pos is None:
                            continue

                        # If dependent on a right sibling (dep_pos > target_pos)
                        if dep_pos > target_pos:
                            is_l_attr = False
                            l_violation_rule = str(rule)
                            l_violation_prod = prod.production_str
                            l_violation_reason = (
                                f"Rule '{rule}' defines inherited attribute on '{target_sym}' "
                                f"at position {target_pos}, but depends on right sibling '{dep_sym}' "
                                f"at position {dep_pos}."
                            )
                            break

                if not is_l_attr:
                    break

            if not is_l_attr:
                break

        if not is_l_attr:
            return ClassificationResult(
                is_s_attributed=False,
                is_l_attributed=False,
                violating_rule=l_violation_rule,
                violating_production=l_violation_prod,
                reason=l_violation_reason,
            )

        if not is_s_attr:
            return ClassificationResult(
                is_s_attributed=False,
                is_l_attributed=True,
                violating_rule=s_violation_rule,
                violating_production=s_violation_prod,
                reason=f"SDD contains inherited attributes (e.g. {s_violation_rule}).",
            )

        return ClassificationResult(
            is_s_attributed=True,
            is_l_attributed=True,
            reason="All attributes are synthesized (S-attributed and therefore L-attributed).",
        )
