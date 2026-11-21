"""Panic-mode error recovery utilities for the recursive descent parser.

Per doc 01 §12, §16.2 and doc 05 §4:
Synchronizes token stream on statement, declaration, and block boundaries.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from vela.parser.recursive_descent import RecursiveDescentParser

# Tokens that can legitimately start a statement
STATEMENT_STARTERS: frozenset[str] = frozenset({
    "let",
    "func",
    "if",
    "switch",
    "while",
    "do",
    "for",
    "return",
    "break",
    "continue",
    "show",
    "read",
    "{",
})

# Tokens that can legitimately start a top-level declaration
DECLARATION_STARTERS: frozenset[str] = frozenset({
    "func",
    "let",
})

# Synchronizing punctuation
STATEMENT_SYNCHRONIZERS: frozenset[str] = frozenset({";", "}"})


class PanicModeRecovery:
    """Helper methods for panic-mode token resynchronization."""

    @staticmethod
    def synchronize_statement(parser: RecursiveDescentParser) -> None:
        """Skip tokens until a statement boundary or starter is reached."""
        while not parser.is_eof:
            sym = parser.current.symbol
            if sym == ";":
                parser.advance()  # Consume the semicolon and resume
                return
            if sym == "}" or sym in STATEMENT_STARTERS:
                # Do not consume '}' or starter; caller will handle next statement or block end
                return
            parser.advance()

    @staticmethod
    def synchronize_declaration(parser: RecursiveDescentParser) -> None:
        """Skip tokens until a top-level declaration starter or EOF is reached."""
        while not parser.is_eof:
            sym = parser.current.symbol
            if sym in DECLARATION_STARTERS:
                return
            if sym == ";":
                parser.advance()
                return
            parser.advance()

    @staticmethod
    def skip_matched_braces(parser: RecursiveDescentParser) -> None:
        """If current token is '{', skip the entire balanced block '{ ... }'."""
        if parser.current.symbol != "{":
            return
        depth = 0
        while not parser.is_eof:
            if parser.current.symbol == "{":
                depth += 1
            elif parser.current.symbol == "}":
                depth -= 1
                if depth == 0:
                    parser.advance()  # consume closing brace
                    return
            parser.advance()
