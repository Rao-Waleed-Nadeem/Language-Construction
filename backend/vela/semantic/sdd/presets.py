"""Pre-configured SDD presets for educational exploration and verification.

Per doc 03 §5.6, doc 08 §3, and agent-prompt.md:
- Preset 1: Desk calculator (S-attributed arithmetic expression evaluator).
- Preset 2: Type declarations (L-attributed inherited type distributor).
- Preset 3: Boolean expression labels (short-circuit jump label generator).
- Preset 4: Vela expression typing (bottom-up operator typing and widening).
"""

from __future__ import annotations

from vela.semantic.sdd.model import SDDProduction, SemanticRule


def preset_desk_calculator() -> list[SDDProduction]:
    """Desk calculator: S-attributed = True, L-attributed = True."""
    return [
        SDDProduction(
            id=1,
            lhs="L",
            rhs=["E"],
            rules=[
                SemanticRule(target_symbol="L", target_attr="val", expr_str="E.val"),
            ],
        ),
        SDDProduction(
            id=2,
            lhs="E",
            rhs=["E", "+", "T"],
            rules=[
                SemanticRule(target_symbol="E", target_attr="val", expr_str="E1.val + T.val"),
            ],
        ),
        SDDProduction(
            id=3,
            lhs="E",
            rhs=["T"],
            rules=[
                SemanticRule(target_symbol="E", target_attr="val", expr_str="T.val"),
            ],
        ),
        SDDProduction(
            id=4,
            lhs="T",
            rhs=["T", "*", "F"],
            rules=[
                SemanticRule(target_symbol="T", target_attr="val", expr_str="T1.val * F.val"),
            ],
        ),
        SDDProduction(
            id=5,
            lhs="T",
            rhs=["F"],
            rules=[
                SemanticRule(target_symbol="T", target_attr="val", expr_str="F.val"),
            ],
        ),
        SDDProduction(
            id=6,
            lhs="F",
            rhs=["(", "E", ")"],
            rules=[
                SemanticRule(target_symbol="F", target_attr="val", expr_str="E.val"),
            ],
        ),
        SDDProduction(
            id=7,
            lhs="F",
            rhs=["digit"],
            rules=[
                SemanticRule(target_symbol="F", target_attr="val", expr_str="int(digit.lexval)"),
            ],
        ),
    ]


def preset_type_declarations() -> list[SDDProduction]:
    """Type declarations: S-attributed = False, L-attributed = True."""
    return [
        SDDProduction(
            id=1,
            lhs="D",
            rhs=["T", "L"],
            rules=[
                SemanticRule(target_symbol="L", target_attr="inh", expr_str="T.type"),
            ],
        ),
        SDDProduction(
            id=2,
            lhs="T",
            rhs=["int"],
            rules=[
                SemanticRule(target_symbol="T", target_attr="type", expr_str="'int'"),
            ],
        ),
        SDDProduction(
            id=3,
            lhs="T",
            rhs=["float"],
            rules=[
                SemanticRule(target_symbol="T", target_attr="type", expr_str="'float'"),
            ],
        ),
        SDDProduction(
            id=4,
            lhs="L",
            rhs=["L", ",", "id"],
            rules=[
                SemanticRule(target_symbol="L1", target_attr="inh", expr_str="L.inh"),
                SemanticRule(target_symbol="id", target_attr="type", expr_str="L.inh"),
            ],
        ),
        SDDProduction(
            id=5,
            lhs="L",
            rhs=["id"],
            rules=[
                SemanticRule(target_symbol="id", target_attr="type", expr_str="L.inh"),
            ],
        ),
    ]


def preset_boolean_labels() -> list[SDDProduction]:
    """Boolean expression short-circuit labels: S-attributed = False, L-attributed = True."""
    return [
        SDDProduction(
            id=1,
            lhs="S",
            rhs=["if", "(", "B", ")", "S1"],
            rules=[
                SemanticRule(target_symbol="B", target_attr="true", expr_str="new_label('L_then')"),
                SemanticRule(target_symbol="B", target_attr="false", expr_str="new_label('L_fall')"),
            ],
        ),
        SDDProduction(
            id=2,
            lhs="B",
            rhs=["B", "or", "M", "B"],
            rules=[
                SemanticRule(target_symbol="B1", target_attr="true", expr_str="B.true"),
                SemanticRule(target_symbol="B1", target_attr="false", expr_str="new_label('L_or')"),
                SemanticRule(target_symbol="B2", target_attr="true", expr_str="B.true"),
                SemanticRule(target_symbol="B2", target_attr="false", expr_str="B.false"),
            ],
        ),
        SDDProduction(
            id=3,
            lhs="B",
            rhs=["id"],
            rules=[
                SemanticRule(
                    target_symbol="B",
                    target_attr="code",
                    expr_str="'if ' + str(id.lexval) + ' goto ' + str(B.true) + ' else goto ' + str(B.false)",
                ),
            ],
        ),
    ]


def preset_vela_expression_typing() -> list[SDDProduction]:
    """Vela expression typing: S-attributed = True, L-attributed = True."""
    return [
        SDDProduction(
            id=1,
            lhs="E",
            rhs=["E", "+", "T"],
            rules=[
                SemanticRule(
                    target_symbol="E",
                    target_attr="type",
                    expr_str="'float' if (E1.type == 'float' or T.type == 'float') else ('string' if (E1.type == 'string' and T.type == 'string') else 'int')",
                ),
            ],
        ),
        SDDProduction(
            id=2,
            lhs="E",
            rhs=["T"],
            rules=[
                SemanticRule(target_symbol="E", target_attr="type", expr_str="T.type"),
            ],
        ),
        SDDProduction(
            id=3,
            lhs="T",
            rhs=["num"],
            rules=[
                SemanticRule(
                    target_symbol="T",
                    target_attr="type",
                    expr_str="'float' if '.' in str(num.lexval) else 'int'",
                ),
            ],
        ),
    ]
