"""Data structures for Syntax-Directed Definitions (SDD) and Translations (SDT).

Per doc 03 §5.6 and doc 08 §3:
- Semantic rules associated with grammar productions.
- Annotated parse tree nodes with attribute maps.
- Attribute dependency graph nodes and edges.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class SemanticRule:
    """A semantic rule defining an attribute computation."""

    target_symbol: str  # e.g. "E", "L1", "id"
    target_attr: str  # e.g. "val", "type", "inh"
    expr_str: str  # e.g. "E1.val + T.val", "T.type"
    source_refs: list[tuple[str, str]] = field(default_factory=list)  # [("E1", "val"), ("T", "val")]

    @property
    def target_key(self) -> str:
        return f"{self.target_symbol}.{self.target_attr}"

    def __str__(self) -> str:
        return f"{self.target_key} = {self.expr_str}"

    def to_dict(self) -> dict[str, Any]:
        return {
            "target_symbol": self.target_symbol,
            "target_attr": self.target_attr,
            "expr_str": self.expr_str,
            "source_refs": [f"{s}.{a}" for s, a in self.source_refs],
        }


@dataclass
class SDDProduction:
    """A grammar production with attached semantic rules."""

    id: int
    lhs: str
    rhs: list[str]
    rules: list[SemanticRule] = field(default_factory=list)

    @property
    def production_str(self) -> str:
        rhs_str = " ".join(self.rhs) if self.rhs else "ε"
        return f"{self.lhs} -> {rhs_str}"

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "lhs": self.lhs,
            "rhs": self.rhs,
            "production": self.production_str,
            "rules": [r.to_dict() for r in self.rules],
        }


@dataclass
class AnnotatedNode:
    """A node in an annotated parse tree with computed attribute values."""

    id: int
    symbol: str
    children: list[AnnotatedNode] = field(default_factory=list)
    attributes: dict[str, Any] = field(default_factory=dict)
    is_terminal: bool = False
    lexval: Any = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "symbol": self.symbol,
            "is_terminal": self.is_terminal,
            "lexval": self.lexval,
            "attributes": dict(self.attributes),
            "children": [c.to_dict() for c in self.children],
        }


@dataclass(frozen=True)
class SDTActionStep:
    """Step in an SDT evaluation trace."""

    step: int
    action_type: str  # "evaluate", "synthesize", "inherit", "error"
    target_node_id: int
    symbol: str
    attribute: str
    value: Any
    rule_str: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "step": self.step,
            "action_type": self.action_type,
            "target_node_id": self.target_node_id,
            "symbol": self.symbol,
            "attribute": self.attribute,
            "value": self.value,
            "rule_str": self.rule_str,
        }
