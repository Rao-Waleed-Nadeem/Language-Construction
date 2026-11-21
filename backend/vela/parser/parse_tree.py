"""Concrete Parse Tree (CST) representation for the Vela parser.

Per doc 01 §13, doc 02 §7, doc 05 §3:
Represents the concrete parse tree following the LL(1) grammar G'.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from vela.common.source import Span
from vela.lexer.tokens import Token


@dataclass
class ParseTreeNode:
    """A node in the concrete syntax parse tree."""

    name: str  # Grammar symbol (e.g. 'Program', 'Stmt', 'func', ';', 'ID')
    is_terminal: bool
    token: Token | None = None
    children: list[ParseTreeNode] = field(default_factory=list)
    span: Span | None = None

    def add_child(self, child: ParseTreeNode) -> None:
        self.children.append(child)
        if child.span is not None:
            if self.span is None:
                self.span = child.span
            else:
                self.span = Span(
                    min(self.span.start, child.span.start),
                    max(self.span.end, child.span.end),
                )

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "is_terminal": self.is_terminal,
            "token": self.token.to_dict() if self.token else None,
            "span": self.span.to_dict() if self.span else None,
            "children": [c.to_dict() for c in self.children],
        }

    def pretty_print(self, indent: int = 0) -> str:
        pad = "  " * indent
        term_info = f" ('{self.token.lexeme}')" if self.token and self.token.lexeme else ""
        lines = [f"{pad}{self.name}{term_info}"]
        for child in self.children:
            lines.append(child.pretty_print(indent + 1))
        return "\n".join(lines)


@dataclass
class ParseTree:
    """Container for the full concrete parse tree."""

    root: ParseTreeNode | None = None

    def to_dict(self) -> dict[str, Any]:
        return {"root": self.root.to_dict() if self.root else None}
