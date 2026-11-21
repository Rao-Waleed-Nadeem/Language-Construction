"""Golden tests for LR family (LR(0), SLR(1), CLR(1), LALR(1)), shift-reduce parser, and operator-precedence parsing.

Per M2-T4 requirements and doc 01 §13.4.
"""

from pathlib import Path

from vela.grammar.loader import BNFLoader
from vela.grammar.lr import LRBuilder
from vela.grammar.op_precedence import OperatorPrecedenceTable
from vela.grammar.shift_reduce import ShiftReduceParser

PRESETS_DIR = Path(__file__).resolve().parents[3] / "docs" / "grammar" / "presets"
GRAMMAR_DIR = Path(__file__).resolve().parents[3] / "docs" / "grammar"


def test_preset_not_slr_but_lalr():
    """Verify not_slr_but_lalr.bnf: SLR has 1 conflict, LALR has 10 states/0, CLR has 14 states/0."""
    g = BNFLoader.load_file(PRESETS_DIR / "not_slr_but_lalr.bnf")
    builder = LRBuilder(g)

    slr = builder.build_slr1()
    assert len(slr.conflicts) == 1, f"Expected 1 SLR conflict, got {len(slr.conflicts)}"

    lalr = builder.build_lalr1()
    assert lalr.states_count == 10, f"Expected 10 LALR states, got {lalr.states_count}"
    assert lalr.is_conflict_free, f"Expected 0 LALR conflicts, got {len(lalr.conflicts)}"

    clr = builder.build_clr1()
    assert clr.states_count == 14, f"Expected 14 CLR states, got {clr.states_count}"
    assert clr.is_conflict_free


def test_preset_not_lalr_but_clr():
    """Verify not_lalr_but_clr.bnf: LALR has 13 states / 2 conflicts, CLR has 14 states / 0 conflicts."""
    g = BNFLoader.load_file(PRESETS_DIR / "not_lalr_but_clr.bnf")
    builder = LRBuilder(g)

    clr = builder.build_clr1()
    assert clr.states_count == 14, f"Expected 14 CLR states, got {clr.states_count}"
    assert clr.is_conflict_free

    lalr = builder.build_lalr1()
    assert lalr.states_count == 13, f"Expected 13 LALR states, got {lalr.states_count}"
    assert len(lalr.conflicts) == 2, f"Expected 2 LALR conflicts, got {len(lalr.conflicts)}"


def test_preset_dangling_else():
    """Verify dangling_else.bnf has 1 shift/reduce conflict on 'e'."""
    g = BNFLoader.load_file(PRESETS_DIR / "dangling_else.bnf")
    builder = LRBuilder(g)

    slr = builder.build_slr1()
    assert len(slr.conflicts) == 1
    assert slr.conflicts[0].symbol == "e"
    assert slr.conflicts[0].conflict_type == "shift/reduce"


def test_preset_dangling_else_unambiguous():
    """Verify dangling_else_unambiguous.bnf has 11 LR(0) states and 0 conflicts."""
    g = BNFLoader.load_file(PRESETS_DIR / "dangling_else_unambiguous.bnf")
    builder = LRBuilder(g)

    lr0 = builder.build_lr0()
    assert lr0.states_count == 11, f"Expected 11 LR(0) states, got {lr0.states_count}"
    slr = builder.build_slr1()
    assert slr.is_conflict_free


def test_preset_expr_ambiguous_with_precedence():
    """Verify expr_ambiguous.bnf has 4 SLR conflicts, resolvable with declared precedence."""
    g = BNFLoader.load_file(PRESETS_DIR / "expr_ambiguous.bnf")

    # Unresolved: has 4 conflicts
    unresolved_builder = LRBuilder(g)
    unresolved_slr = unresolved_builder.build_slr1()
    assert len(unresolved_slr.conflicts) == 4, f"Expected 4 SLR conflicts, got {len(unresolved_slr.conflicts)}"

    # With declared precedence: left + (1), left * (2)
    prec = {"+": ("left", 1), "*": ("left", 2)}
    resolved_builder = LRBuilder(g, precedence=prec)
    resolved_slr = resolved_builder.build_slr1()
    assert resolved_slr.is_conflict_free, f"Expected 0 conflicts after precedence resolution, got {len(resolved_slr.conflicts)}"


def test_preset_slr_expr_shift_reduce_trace():
    """Verify shift-reduce trace of 'id + id * id' on slr_expr.bnf ends in accept."""
    g = BNFLoader.load_file(PRESETS_DIR / "slr_expr.bnf")
    builder = LRBuilder(g)
    slr = builder.build_slr1()
    assert slr.is_conflict_free

    parser = ShiftReduceParser(slr)
    tokens = ["id", "+", "id", "*", "id"]
    res = parser.parse(tokens)

    assert res.accepted, f"Shift-reduce parse failed: {res.error}"
    assert res.parse_tree is not None
    assert res.parse_tree.symbol == "E"
    assert len(res.steps) > 5


def test_preset_vela_expr_operator():
    """Verify vela_expr_operator.bnf: operator precedence without conflicts, parses id + id * id."""
    g = BNFLoader.load_file(PRESETS_DIR / "vela_expr_operator.bnf")
    table = OperatorPrecedenceTable(g)

    assert table.is_eligible, f"Expected eligible operator grammar: {table.eligibility_errors}"
    assert not table.has_conflicts, f"Expected 0 conflicts, got {len(table.conflicts)}"

    res = table.parse(["id", "+", "id", "*", "id"])
    assert res.accepted, f"Operator precedence parse failed: {res.error}"


def test_operator_precedence_conflict_with_shared_minus():
    """Verify operator grammar with shared unary and binary minus reports conflicts."""
    # Modified grammar with shared '-'
    grammar_text = """
    E -> E + E | E - E | - E | id
    """
    g = BNFLoader.load_string(grammar_text, start_symbol="E")
    table = OperatorPrecedenceTable(g)
    assert table.is_eligible
    assert table.has_conflicts, "Expected conflicts on shared minus in operator precedence"


def test_vela_authoritative_grammar_lr_metrics():
    """Verify authoritative vela.bnf golden LR metrics per doc 01 §13.4.

    LR(0): 214 states with conflicts
    SLR(1): 0 conflicts, 214 states
    LALR(1): 214 states, 0 conflicts
    CLR(1): 609 states, 0 conflicts
    """
    g = BNFLoader.load_file(GRAMMAR_DIR / "vela.bnf")
    builder = LRBuilder(g)

    # 1. LR(0): 214 states with conflicts
    lr0 = builder.build_lr0()
    assert lr0.states_count == 214, f"Expected 214 LR(0) states, got {lr0.states_count}"
    assert not lr0.is_conflict_free, "Expected LR(0) conflicts on vela.bnf"

    # 2. SLR(1): 0 conflicts (214 states)
    slr1 = builder.build_slr1()
    assert slr1.states_count == 214, f"Expected 214 SLR(1) states, got {slr1.states_count}"
    assert slr1.is_conflict_free, f"Expected 0 SLR(1) conflicts on vela.bnf, got {len(slr1.conflicts)}: {slr1.conflicts[:3]}"

    # 3. LALR(1): 214 states, 0 conflicts
    lalr1 = builder.build_lalr1()
    assert lalr1.states_count == 214, f"Expected 214 LALR(1) states, got {lalr1.states_count}"
    assert lalr1.is_conflict_free, f"Expected 0 LALR(1) conflicts on vela.bnf, got {len(lalr1.conflicts)}: {lalr1.conflicts[:3]}"

    # 4. CLR(1): 609 states, 0 conflicts
    clr1 = builder.build_clr1()
    assert clr1.states_count == 609, f"Expected 609 CLR(1) states, got {clr1.states_count}"
    assert clr1.is_conflict_free, f"Expected 0 CLR(1) conflicts on vela.bnf, got {len(clr1.conflicts)}"
