"""Chomsky Hierarchy Classification.

Per doc 01 §13.5 and doc 06 §5:
Classifies grammars into Type 2 (Context-Free) or Type 3 (Regular) with justification.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from vela.grammar.model import Grammar


@dataclass
class ChomskyClassification:
    chomsky_type: int  # 2 or 3
    name: str  # "Type 2: Context-Free" or "Type 3: Regular"
    is_regular: bool
    is_right_linear: bool
    is_left_linear: bool
    justification: str
    non_regular_productions: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "chomsky_type": self.chomsky_type,
            "name": self.name,
            "is_regular": self.is_regular,
            "is_right_linear": self.is_right_linear,
            "is_left_linear": self.is_left_linear,
            "justification": self.justification,
            "non_regular_productions": self.non_regular_productions,
        }


def classify_grammar(grammar: Grammar) -> ChomskyClassification:
    """Classify a context-free grammar as Type 2 or Type 3."""
    is_right_linear = True
    is_left_linear = True
    non_reg_prods: list[str] = []

    for p in grammar.productions:
        rhs = p.normalized_rhs()
        if not rhs:
            # Epsilon production is allowed in both
            continue

        nt_indices = [i for i, sym in enumerate(rhs) if grammar.is_nonterminal(sym)]

        # If more than 1 nonterminal on RHS -> not regular (e.g. A -> B C)
        if len(nt_indices) > 1:
            is_right_linear = False
            is_left_linear = False
            non_reg_prods.append(str(p))
            continue

        if len(nt_indices) == 1:
            idx = nt_indices[0]
            # Right-linear: nonterminal must be at the very end (rhs[-1])
            if idx != len(rhs) - 1:
                is_right_linear = False

            # Left-linear: nonterminal must be at the very beginning (rhs[0])
            if idx != 0:
                is_left_linear = False

            if not (is_right_linear or is_left_linear):
                non_reg_prods.append(str(p))

    is_regular = is_right_linear or is_left_linear

    if is_regular:
        sub_type = "Right-linear" if is_right_linear else "Left-linear"
        justification = (
            f"The grammar is Type 3 (Regular, {sub_type}): all productions contain at most "
            "one nonterminal, strictly placed at the boundary of the right-hand side."
        )
        return ChomskyClassification(
            chomsky_type=3,
            name="Type 3: Regular Grammar",
            is_regular=True,
            is_right_linear=is_right_linear,
            is_left_linear=is_left_linear,
            justification=justification,
            non_regular_productions=[],
        )
    else:
        sample_prods = non_reg_prods[:5]
        justification = (
            "The grammar is Type 2 (Context-Free): every production has a single nonterminal "
            "on the left-hand side, but right-hand sides contain multiple nonterminals or "
            f"nested structures (e.g., {', '.join(sample_prods)})."
        )
        return ChomskyClassification(
            chomsky_type=2,
            name="Type 2: Context-Free Grammar",
            is_regular=False,
            is_right_linear=False,
            is_left_linear=False,
            justification=justification,
            non_regular_productions=non_reg_prods,
        )
