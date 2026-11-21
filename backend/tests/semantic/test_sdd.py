"""Tests for the Syntax-Directed Definition (SDD) and Translation (SDT) Engine (M4-T3).

Per doc 03 §5.6, doc 08 §3, and agent-prompt.md:
- Desk calculator = S-attributed yes.
- Type declarations = L-attributed yes / S-attributed no.
- Rule depending on a right sibling reported not L-attributed naming the rule.
- Evaluation results correct for preset inputs.
- Safe evaluator prevents arbitrary code execution without eval/exec.
"""

import pytest

from vela.semantic.sdd.engine import SDDEngine
from vela.semantic.sdd.evaluator import SafeSDDEvaluator
from vela.semantic.sdd.model import AnnotatedNode, SDDProduction, SemanticRule
from vela.semantic.sdd.presets import (
    preset_boolean_labels,
    preset_desk_calculator,
    preset_type_declarations,
    preset_vela_expression_typing,
)


def test_desk_calculator_preset() -> None:
    prods = preset_desk_calculator()
    engine = SDDEngine(prods)
    classification = engine.classify()

    assert classification.is_s_attributed, "Desk calculator must be S-attributed"
    assert classification.is_l_attributed, "S-attributed SDD must also be L-attributed"
    assert classification.violating_rule is None

    # Evaluate parse tree for (3 + 4) * 5 = 35
    # L -> E -> T -> T * F
    # T1 -> F -> ( E ) -> E1 + T -> 3 + 4
    # F -> 5
    d3 = AnnotatedNode(id=1, symbol="digit", is_terminal=True, lexval=3)
    f3 = AnnotatedNode(id=2, symbol="F", children=[d3])
    t3 = AnnotatedNode(id=3, symbol="T", children=[f3])
    e3 = AnnotatedNode(id=4, symbol="E", children=[t3])

    op_plus = AnnotatedNode(id=5, symbol="+", is_terminal=True, lexval="+")

    d4 = AnnotatedNode(id=6, symbol="digit", is_terminal=True, lexval=4)
    f4 = AnnotatedNode(id=7, symbol="F", children=[d4])
    t4 = AnnotatedNode(id=8, symbol="T", children=[f4])

    e_add = AnnotatedNode(id=9, symbol="E", children=[e3, op_plus, t4])

    p_open = AnnotatedNode(id=10, symbol="(", is_terminal=True, lexval="(")
    p_close = AnnotatedNode(id=11, symbol=")", is_terminal=True, lexval=")")
    f_paren = AnnotatedNode(id=12, symbol="F", children=[p_open, e_add, p_close])
    t_mul_left = AnnotatedNode(id=13, symbol="T", children=[f_paren])

    op_mul = AnnotatedNode(id=14, symbol="*", is_terminal=True, lexval="*")
    d5 = AnnotatedNode(id=15, symbol="digit", is_terminal=True, lexval=5)
    f5 = AnnotatedNode(id=16, symbol="F", children=[d5])

    t_mul = AnnotatedNode(id=17, symbol="T", children=[t_mul_left, op_mul, f5])
    e_root = AnnotatedNode(id=18, symbol="E", children=[t_mul])
    l_root = AnnotatedNode(id=19, symbol="L", children=[e_root])

    res = engine.evaluate(l_root)
    assert not res.is_cyclic
    assert l_root.attributes.get("val") == 35
    assert len(res.action_trace) > 0
    assert len(res.evaluation_order) > 0


def test_type_declarations_preset() -> None:
    prods = preset_type_declarations()
    engine = SDDEngine(prods)
    classification = engine.classify()

    assert not classification.is_s_attributed, "Type declarations contains inherited attributes"
    assert classification.is_l_attributed, "Type declarations must be L-attributed"

    # Evaluate parse tree for: float id1 , id2
    # D -> T L
    # T -> float
    # L -> L , id2
    # L -> id1
    tok_float = AnnotatedNode(id=1, symbol="float", is_terminal=True, lexval="float")
    t_node = AnnotatedNode(id=2, symbol="T", children=[tok_float])

    tok_id1 = AnnotatedNode(id=3, symbol="id", is_terminal=True, lexval="a")
    l_inner = AnnotatedNode(id=4, symbol="L", children=[tok_id1])

    tok_comma = AnnotatedNode(id=5, symbol=",", is_terminal=True, lexval=",")
    tok_id2 = AnnotatedNode(id=6, symbol="id", is_terminal=True, lexval="b")
    l_outer = AnnotatedNode(id=7, symbol="L", children=[l_inner, tok_comma, tok_id2])

    d_root = AnnotatedNode(id=8, symbol="D", children=[t_node, l_outer])

    res = engine.evaluate(d_root)
    assert not res.is_cyclic
    assert t_node.attributes.get("type") == "float"
    assert l_outer.attributes.get("inh") == "float"
    assert l_inner.attributes.get("inh") == "float"
    assert tok_id1.attributes.get("type") == "float"
    assert tok_id2.attributes.get("type") == "float"


def test_right_sibling_violation() -> None:
    # Rule where T (at pos 0) depends on right sibling L (at pos 1): T.attr = L.val
    violating_rule = SemanticRule(target_symbol="T", target_attr="attr", expr_str="L.val")
    prods = [
        SDDProduction(
            id=1,
            lhs="D",
            rhs=["T", "L"],
            rules=[violating_rule],
        ),
    ]
    engine = SDDEngine(prods)
    classification = engine.classify()

    assert not classification.is_s_attributed
    assert not classification.is_l_attributed
    assert classification.violating_rule is not None
    assert "T.attr = L.val" in classification.violating_rule
    assert "right sibling" in classification.reason


def test_other_presets_classification() -> None:
    # Boolean labels preset
    engine_bool = SDDEngine(preset_boolean_labels())
    class_bool = engine_bool.classify()
    assert not class_bool.is_s_attributed
    assert class_bool.is_l_attributed

    # Vela expression typing preset
    engine_type = SDDEngine(preset_vela_expression_typing())
    class_type = engine_type.classify()
    assert class_type.is_s_attributed
    assert class_type.is_l_attributed


def test_safe_evaluator_security() -> None:
    env = {"A": {"x": 10, "y": 20}}

    # Safe arithmetic
    assert SafeSDDEvaluator.evaluate("A.x + A.y * 2", env) == 50
    assert SafeSDDEvaluator.evaluate("A.x < A.y", env) is True
    assert SafeSDDEvaluator.evaluate("max(A.x, A.y)", env) == 20
    assert SafeSDDEvaluator.evaluate("'val_' + str(A.x)", env) == "val_10"
    assert SafeSDDEvaluator.evaluate("'yes' if A.x > 5 else 'no'", env) == "yes"

    # Block disallowed operations
    with pytest.raises((ValueError, TypeError)):
        SafeSDDEvaluator.evaluate("__import__('os').system('dir')", env)

    with pytest.raises((ValueError, TypeError)):
        SafeSDDEvaluator.evaluate("eval('1+1')", env)


def test_cyclic_dependency_detection() -> None:
    prods = [
        SDDProduction(
            id=1,
            lhs="A",
            rhs=["B"],
            rules=[
                SemanticRule(target_symbol="A", target_attr="x", expr_str="A.y + 1"),
                SemanticRule(target_symbol="A", target_attr="y", expr_str="A.x + 1"),
            ],
        ),
    ]
    engine = SDDEngine(prods)
    root = AnnotatedNode(id=1, symbol="A", children=[AnnotatedNode(id=2, symbol="B")])
    res = engine.evaluate(root)
    assert res.is_cyclic
