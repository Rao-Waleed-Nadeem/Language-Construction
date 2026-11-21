"""Unit and golden tests for LL(1) table, conflict detection, predictive parser, and pseudocode generator.

Per M2-T3 requirements and doc 01 §13.4:
- vela_ll1.bnf has 0 conflicts (138 productions, 65 nonterminals)
- vela.bnf has conflicts (19 nonterminals)
- preset dangling_else and left_factoring conflicts reported
- ll1_expr parses 'id + id * id'
- rdgen produces valid pseudocode
"""

from pathlib import Path

from vela.grammar.ll1 import LL1Table
from vela.grammar.loader import BNFLoader
from vela.grammar.rdgen import RecursiveDescentGenerator


def test_vela_ll1_has_zero_conflicts():
    """Verify vela_ll1.bnf is completely conflict-free in LL(1) per doc 01 §13.4."""
    grammar_file = Path(__file__).resolve().parents[3] / "docs" / "grammar" / "vela_ll1.bnf"
    g = BNFLoader.load_file(grammar_file)

    table = LL1Table(g)
    assert len(g.productions) == 138
    assert len(g.nonterminals) == 65
    assert table.is_ll1, f"Expected 0 conflicts in vela_ll1.bnf, found {len(table.conflicts)} conflicts: {table.conflicts[:5]}"
    assert len(table.conflicts) == 0


def test_vela_natural_has_19_conflicted_nonterminals():
    """Verify vela.bnf has LL(1) conflicts on exactly 19 nonterminals per doc 01 §13.4."""
    grammar_file = Path(__file__).resolve().parents[3] / "docs" / "grammar" / "vela.bnf"
    g = BNFLoader.load_file(grammar_file)

    table = LL1Table(g)
    assert not table.is_ll1
    conflicted_nts = table.conflicted_nonterminals
    assert len(conflicted_nts) == 19, (
        f"Expected 19 conflicted nonterminals in vela.bnf, got {len(conflicted_nts)}: {conflicted_nts}"
    )


def test_preset_dangling_else_has_conflicts():
    """Verify preset dangling_else.bnf reports LL(1) conflict on 'i' (common prefix)."""
    preset_file = (
        Path(__file__).resolve().parents[3]
        / "docs"
        / "grammar"
        / "presets"
        / "dangling_else.bnf"
    )
    g = BNFLoader.load_file(preset_file)
    table = LL1Table(g)

    assert not table.is_ll1
    assert len(table.conflicts) >= 1
    # LL(1) FIRST/FIRST conflict on 'i' between S -> i S and S -> i S e S
    conflict_symbols = {c.terminal for c in table.conflicts}
    assert "i" in conflict_symbols


def test_preset_left_factoring_has_conflicts():
    """Verify unfactored preset left_factoring.bnf reports LL(1) conflict on 'i'."""
    preset_file = (
        Path(__file__).resolve().parents[3]
        / "docs"
        / "grammar"
        / "presets"
        / "left_factoring.bnf"
    )
    g = BNFLoader.load_file(preset_file)
    table = LL1Table(g)

    assert not table.is_ll1
    conflict_terms = {c.terminal for c in table.conflicts}
    assert "i" in conflict_terms


def test_ll1_expr_parses_tokens():
    """Verify ll1_expr.bnf parses 'id + id * id' with predictive table."""
    preset_file = (
        Path(__file__).resolve().parents[3]
        / "docs"
        / "grammar"
        / "presets"
        / "ll1_expr.bnf"
    )
    g = BNFLoader.load_file(preset_file)
    table = LL1Table(g)
    assert table.is_ll1

    tokens = ["id", "+", "id", "*", "id"]
    res = table.parse(tokens)
    assert res.accepted, f"Parse failed: {res.error}"
    assert len(res.steps) > 5

    # Negative test: invalid sentence 'id + * id'
    bad_tokens = ["id", "+", "*", "id"]
    bad_res = table.parse(bad_tokens)
    assert not bad_res.accepted


def test_recursive_descent_pseudocode_generation():
    """Verify rdgen produces valid pseudocode containing function per nonterminal."""
    preset_file = (
        Path(__file__).resolve().parents[3]
        / "docs"
        / "grammar"
        / "presets"
        / "ll1_expr.bnf"
    )
    g = BNFLoader.load_file(preset_file)
    code = RecursiveDescentGenerator(g).generate()

    assert "def parse_E():" in code
    assert "def parse_T():" in code
    assert "def parse_F():" in code
    assert "match('id')" in code or "match('(')" in code
