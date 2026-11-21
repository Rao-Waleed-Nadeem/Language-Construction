"""Unit tests for grammar transformations: left-recursion elimination and left factoring.

Per M2-T2 requirements:
- preset left_recursion_indirect eliminates indirect left recursion
- preset left_factoring extracts common prefixes
- transforms produce valid, equivalent grammars with transformation step logs
"""

from pathlib import Path

from vela.grammar.analysis import GrammarAnalysis
from vela.grammar.loader import BNFLoader
from vela.grammar.transform import eliminate_left_recursion, left_factor


def test_preset_left_recursion_indirect():
    """Verify indirect left recursion elimination on left_recursion_indirect.bnf."""
    preset_file = (
        Path(__file__).resolve().parents[3]
        / "docs"
        / "grammar"
        / "presets"
        / "left_recursion_indirect.bnf"
    )
    g = BNFLoader.load_file(preset_file)

    # Before: S -> A a | b, A -> A c | S d | ε
    # There is an indirect cycle A => S d => A a d
    transformed, steps = eliminate_left_recursion(g)

    assert len(steps) >= 1
    # Check that in transformed grammar, no production has immediate left recursion
    for p in transformed.productions:
        rhs = p.normalized_rhs()
        if rhs:
            assert rhs[0] != p.lhs, f"Immediate left recursion remaining in {p}"

    # Verify that FIRST and FOLLOW compute without infinite recursion
    analysis = GrammarAnalysis(transformed)
    assert len(analysis.first) > 0
    assert len(analysis.follow) > 0


def test_preset_left_factoring():
    """Verify left factoring on left_factoring.bnf."""
    preset_file = (
        Path(__file__).resolve().parents[3]
        / "docs"
        / "grammar"
        / "presets"
        / "left_factoring.bnf"
    )
    g = BNFLoader.load_file(preset_file)

    # Before: S -> i E t S | i E t S e S | a
    transformed, steps = left_factor(g)

    assert len(steps) >= 1
    # Verify that in transformed grammar, for every NT, no two alternatives share a common prefix
    for nt in transformed.nonterminals:
        prods = transformed.productions_for(nt)
        rhss = [p.normalized_rhs() for p in prods]
        for i in range(len(rhss)):
            for j in range(i + 1, len(rhss)):
                if rhss[i] and rhss[j]:
                    assert rhss[i][0] != rhss[j][0], (
                        f"Nonterminal {nt} still shares leading symbol '{rhss[i][0]}': {rhss[i]} vs {rhss[j]}"
                    )


def test_step_log_structure():
    """Verify transformation step logs contain required fields for UI visualization."""
    preset_file = (
        Path(__file__).resolve().parents[3]
        / "docs"
        / "grammar"
        / "presets"
        / "left_recursion_indirect.bnf"
    )
    g = BNFLoader.load_file(preset_file)
    _, steps = eliminate_left_recursion(g)

    for step in steps:
        step_dict = step.to_dict()
        assert "step_number" in step_dict
        assert "transformation" in step_dict
        assert "nonterminal" in step_dict
        assert "before_productions" in step_dict
        assert "after_productions" in step_dict
        assert "explanation" in step_dict
        assert len(step.explanation) > 0
