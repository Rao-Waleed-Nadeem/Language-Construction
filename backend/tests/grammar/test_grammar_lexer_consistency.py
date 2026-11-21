"""Consistency test between Grammar terminals and Lexer terminals.

Enforces Architectural Principle AP-5 (doc 02 §1, doc 00 PR-04):
Terminals of authoritative grammar docs/grammar/vela.bnf must match the lexer's terminal symbols.
"""

from pathlib import Path

from vela.grammar.loader import BNFLoader
from vela.language.spec import (
    DELIMITERS,
    KEYWORDS,
    SYMBOLIC_OPERATORS,
)


def test_grammar_lexer_consistency():
    """Verify that grammar G terminals equal the lexer's recognized terminals."""
    grammar_file = Path(__file__).resolve().parents[3] / "docs" / "grammar" / "vela.bnf"
    assert grammar_file.exists(), f"vela.bnf not found at {grammar_file}"

    g = BNFLoader.load_file(grammar_file)

    # Lexer terminal symbols:
    # 26 keywords + 5 token classes + 9 delimiters + 19 symbolic operators = 59 terminals
    token_classes = {"ID", "INT_LIT", "FLOAT_LIT", "CHAR_LIT", "STRING_LIT"}
    lexer_terminals = set(KEYWORDS) | token_classes | set(DELIMITERS) | set(SYMBOLIC_OPERATORS)

    assert len(lexer_terminals) == 59, f"Expected 59 lexer terminals, got {len(lexer_terminals)}"
    assert len(g.terminals) == 59, f"Expected 59 grammar terminals, got {len(g.terminals)}"

    diff = set(g.terminals) ^ lexer_terminals
    assert not diff, f"Discrepancy between grammar terminals and lexer terminals: {diff}"
