"""Unit and golden tests for Grammar loader, analysis, and Chomsky classification.

Per M2-T1 requirements and doc 01 §13.4:
- loads every .bnf file (root and presets)
- golden values for vela.bnf and vela_ll1.bnf
- FOLLOW(IfStmt) contains no 'else'
- Chomsky classification
"""

from pathlib import Path

from vela.grammar.analysis import GrammarAnalysis
from vela.grammar.classify import classify_grammar
from vela.grammar.loader import BNFLoader


def test_load_all_bnf_files():
    """Verify that every .bnf file in docs/grammar and presets loads without errors."""
    grammar_dir = Path(__file__).resolve().parents[3] / "docs" / "grammar"
    assert grammar_dir.exists()

    bnf_files = list(grammar_dir.glob("*.bnf")) + list((grammar_dir / "presets").glob("*.bnf"))
    assert len(bnf_files) >= 13, f"Expected at least 13 .bnf files, found {len(bnf_files)}"

    for f in bnf_files:
        g = BNFLoader.load_file(f)
        assert len(g.productions) > 0, f"No productions loaded from {f.name}"
        assert len(g.nonterminals) > 0
        assert g.start_symbol in g.nonterminals


def test_vela_authoritative_grammar_golden_values():
    """Verify golden metrics for vela.bnf per doc 01 §13.4."""
    grammar_file = Path(__file__).resolve().parents[3] / "docs" / "grammar" / "vela.bnf"
    g = BNFLoader.load_file(grammar_file)

    # 121 productions, 47 nonterminals, 59 terminals
    assert len(g.productions) == 121, f"Expected 121 productions in vela.bnf, got {len(g.productions)}"
    assert len(g.nonterminals) == 47, f"Expected 47 nonterminals, got {len(g.nonterminals)}"
    assert len(g.terminals) == 59, f"Expected 59 terminals, got {len(g.terminals)}"


def test_vela_ll1_grammar_golden_values():
    """Verify golden metrics for vela_ll1.bnf per doc 01 §13.4."""
    grammar_file = Path(__file__).resolve().parents[3] / "docs" / "grammar" / "vela_ll1.bnf"
    g = BNFLoader.load_file(grammar_file)

    # 138 productions, 65 nonterminals, 59 terminals
    assert len(g.productions) == 138, f"Expected 138 productions in vela_ll1.bnf, got {len(g.productions)}"
    assert len(g.nonterminals) == 65, f"Expected 65 nonterminals, got {len(g.nonterminals)}"
    assert len(g.terminals) == 59, f"Expected 59 terminals, got {len(g.terminals)}"


def test_follow_if_stmt_has_no_else():
    """Verify that FOLLOW(IfStmt) in vela.bnf contains NO 'else' (doc 01 §13.4).

    Reason: mandatory braces ensure an 'else' always binds to the nearest enclosing 'if'
    by construction, completely eliminating the dangling-else ambiguity.
    """
    grammar_file = Path(__file__).resolve().parents[3] / "docs" / "grammar" / "vela.bnf"
    g = BNFLoader.load_file(grammar_file)
    analysis = GrammarAnalysis(g)

    follow_if = analysis.follow.get("IfStmt", set())
    assert "else" not in follow_if, f"Dangling else violation: 'else' found in FOLLOW(IfStmt): {follow_if}"

    # Expected FOLLOW(IfStmt) symbols per doc 01 §13.4
    expected_subset = {
        "ID",
        "break",
        "case",
        "continue",
        "default",
        "do",
        "for",
        "if",
        "let",
        "read",
        "return",
        "show",
        "switch",
        "while",
        "{",
        "}",
    }
    assert expected_subset.issubset(follow_if), f"Missing expected symbols in FOLLOW(IfStmt): {expected_subset - follow_if}"


def test_chomsky_classification():
    """Verify that vela.bnf is classified as Type 2 Context-Free."""
    grammar_file = Path(__file__).resolve().parents[3] / "docs" / "grammar" / "vela.bnf"
    g = BNFLoader.load_file(grammar_file)
    classification = classify_grammar(g)

    assert classification.chomsky_type == 2
    assert classification.is_regular is False
    assert "Context-Free" in classification.name
