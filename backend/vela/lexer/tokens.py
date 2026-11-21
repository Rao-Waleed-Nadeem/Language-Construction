"""Token data structures and LexResult container.

Per doc 01 §2.7 and doc 04 §3:
Every token carries category, symbol, lexeme, value, span.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from vela.common.diagnostics import Diagnostic
from vela.common.source import Span
from vela.language.spec import TokenCategory


@dataclass(frozen=True)
class Token:
    """A lexical token."""

    category: TokenCategory
    symbol: str  # Grammar terminal ('let', '<=', ';', 'ID', 'INT_LIT', '$')
    lexeme: str  # Exact text from source
    value: Any  # Evaluated literal value (int, float, str, bool) or None
    span: Span  # Start and end source coordinate

    def __str__(self) -> str:
        val_str = f"({self.value})" if self.value is not None else ""
        return f"Token({self.symbol}, '{self.lexeme}'{val_str}, {self.span.start})"

    def to_dict(self) -> dict[str, Any]:
        return {
            "category": self.category.value,
            "symbol": self.symbol,
            "lexeme": self.lexeme,
            "value": self.value,
            "span": self.span.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Token:
        return cls(
            category=TokenCategory(data["category"]),
            symbol=data["symbol"],
            lexeme=data["lexeme"],
            value=data.get("value"),
            span=Span.from_dict(data["span"]),
        )


@dataclass
class LexResult:
    """Result of lexical analysis."""

    tokens: list[Token] = field(default_factory=list)
    diagnostics: list[Diagnostic] = field(default_factory=list)
    dfa_trace: list[dict[str, Any]] = field(default_factory=list)
    buffer_trace: list[dict[str, Any]] = field(default_factory=list)

    @property
    def has_errors(self) -> bool:
        return any(d.severity == "error" for d in self.diagnostics)

    def to_dict(self) -> dict[str, Any]:
        return {
            "tokens": [t.to_dict() for t in self.tokens],
            "diagnostics": [d.to_dict() for d in self.diagnostics],
            "dfa_trace": self.dfa_trace,
            "buffer_trace": self.buffer_trace,
        }
