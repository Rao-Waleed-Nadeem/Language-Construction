"""Grammar data models.

Per doc 01 §13, doc 02 §3, doc 06 §3:
Production and Grammar representations for arbitrary context-free grammars.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

EPSILON = "ε"


@dataclass(frozen=True)
class Production:
    """A single context-free grammar production A -> alpha."""

    id: int
    lhs: str
    rhs: tuple[str, ...]  # Empty tuple () represents epsilon

    @property
    def is_epsilon(self) -> bool:
        return len(self.rhs) == 0 or (len(self.rhs) == 1 and self.rhs[0] == EPSILON)

    def normalized_rhs(self) -> tuple[str, ...]:
        """Return empty tuple if production is epsilon."""
        if self.is_epsilon:
            return ()
        return self.rhs

    def __str__(self) -> str:
        rhs_str = " ".join(self.rhs) if self.rhs else EPSILON
        return f"{self.lhs} -> {rhs_str}"

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "lhs": self.lhs,
            "rhs": list(self.rhs) if self.rhs else [EPSILON],
            "is_epsilon": self.is_epsilon,
            "text": str(self),
        }


@dataclass
class Grammar:
    """A context-free grammar G = (V, Sigma, R, S)."""

    start_symbol: str
    productions: list[Production] = field(default_factory=list)
    nonterminals: list[str] = field(default_factory=list)
    terminals: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.nonterminals or not self.terminals:
            self._recalculate_symbols()

    def _recalculate_symbols(self) -> None:
        """Derive ordered nonterminals and terminals from productions."""
        nts: list[str] = []
        for p in self.productions:
            if p.lhs not in nts:
                nts.append(p.lhs)
        self.nonterminals = nts

        nt_set = set(nts)
        terms: list[str] = []
        for p in self.productions:
            for sym in p.rhs:
                if sym != EPSILON and sym not in nt_set and sym not in terms:
                    terms.append(sym)
        self.terminals = terms

    def productions_for(self, nonterminal: str) -> list[Production]:
        """Return all productions with the given LHS."""
        return [p for p in self.productions if p.lhs == nonterminal]

    def is_nonterminal(self, symbol: str) -> bool:
        return symbol in self.nonterminals

    def is_terminal(self, symbol: str) -> bool:
        return symbol in self.terminals

    def to_dict(self) -> dict[str, Any]:
        return {
            "start_symbol": self.start_symbol,
            "nonterminals": self.nonterminals,
            "terminals": self.terminals,
            "production_count": len(self.productions),
            "productions": [p.to_dict() for p in self.productions],
        }
