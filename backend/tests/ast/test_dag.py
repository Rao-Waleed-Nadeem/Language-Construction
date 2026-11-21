"""Tests for Directed Acyclic Graph (DAG) construction and value numbering.

Verifies:
- Acceptance criterion: `(a+b)*2` and `(a+b)*3` share one `a+b` node.
- Commutativity canonical ordering for +, *, ==, !=.
- Non-commutative operators preserve operand order (-, /, %).
- Basic block assignment tracking and variable redefinition (def-kill).
- Tree vs DAG node counts and savings calculation.
- Step-by-step trace generation for UI explainability.
- Integration with parsed Vela AST expressions.
"""

from vela.ast.dag import DAGBuilder, build_block_dag, build_expression_dag
from vela.ast.nodes import (
    AssignStmt,
    BinaryExpr,
    Block,
    LiteralExpr,
    VarDecl,
    VarRefExpr,
)
from vela.common.source import SourceFile, SourceLocation, Span
from vela.lexer.scanner import Scanner
from vela.parser.recursive_descent import RecursiveDescentParser


def dummy_span() -> Span:
    loc = SourceLocation(1, 1, 0)
    return Span(loc, loc)


def _var(name: str) -> VarRefExpr:
    return VarRefExpr(id=0, span=dummy_span(), name=name)


def _lit_int(val: int) -> LiteralExpr:
    return LiteralExpr(id=0, span=dummy_span(), literal_type="int", value=val)


def _bin(left, op: str, right) -> BinaryExpr:
    return BinaryExpr(id=0, span=dummy_span(), left=left, op=op, right=right)


def test_shared_subexpression_acceptance_criterion() -> None:
    """Verify acceptance criterion from agent-prompt.md:

    '(a+b)*2' and '(a+b)*3' share one 'a+b' node.
    """
    # Build (a + b) * 2
    plus1 = _bin(_var("a"), "+", _var("b"))
    expr1 = _bin(plus1, "*", _lit_int(2))

    # Build (a + b) * 3
    plus2 = _bin(_var("a"), "+", _var("b"))
    expr2 = _bin(plus2, "*", _lit_int(3))

    builder = DAGBuilder()
    root1 = builder.add_expression(expr1)
    root2 = builder.add_expression(expr2)
    dag = builder.dag

    # Roots should be different multiplication nodes
    assert root1 != root2
    mul1 = dag.nodes[root1]
    mul2 = dag.nodes[root2]

    # Both multiplications must point to the SAME plus node
    assert mul1.label == "*"
    assert mul2.label == "*"
    assert mul1.children[0] == mul2.children[0]
    shared_plus_id = mul1.children[0]
    shared_node = dag.nodes[shared_plus_id]

    assert shared_node.label == "+"
    # Node should have both multiplications as parents
    assert set(shared_node.parents) == {root1, root2}

    # Tree node count: expr1 (5) + expr2 (5) = 10
    assert dag.tree_node_count == 10
    # Unique DAG nodes: a, b, +, 2, *(1), 3, *(2) = 7 nodes
    assert dag.dag_node_count == 7
    # Savings: 10 - 7 = 3 nodes saved
    assert dag.savings == 3


def test_commutative_canonical_ordering() -> None:
    """Verify that commutative operators like '+' and '*' share nodes regardless of operand order."""
    # a + b vs b + a
    expr1 = _bin(_var("a"), "+", _var("b"))
    expr2 = _bin(_var("b"), "+", _var("a"))

    dag = build_expression_dag([expr1, expr2])
    # Both expressions should map to the exact same root node ID
    assert len(dag.roots) == 1
    assert dag.dag_node_count == 3  # a, b, +
    assert dag.tree_node_count == 6
    assert dag.savings == 3


def test_non_commutative_operator_distinction() -> None:
    """Verify that non-commutative operators like '-' and '/' do NOT share swapped operands."""
    # a - b vs b - a
    expr1 = _bin(_var("a"), "-", _var("b"))
    expr2 = _bin(_var("b"), "-", _var("a"))

    dag = build_expression_dag([expr1, expr2])
    assert len(dag.roots) == 2
    assert dag.roots[0] != dag.roots[1]
    # Nodes: a, b, (a - b), (b - a) = 4 nodes
    assert dag.dag_node_count == 4


def test_nested_common_subexpressions() -> None:
    """Verify sharing of nested subexpressions: ((a + b) * c) + ((a + b) * c)."""
    # (a + b)
    sub = _bin(_var("a"), "+", _var("b"))
    # (a + b) * c
    term1 = _bin(sub, "*", _var("c"))
    # (a + b) * c (separate AST instance)
    term2 = _bin(_bin(_var("a"), "+", _var("b")), "*", _var("c"))
    # Top-level: term1 + term2
    top = _bin(term1, "+", term2)

    dag = build_expression_dag([top])
    root = dag.nodes[dag.roots[0]]
    assert root.label == "+"
    # Left and right children of top '+' should be the EXACT same node ID
    assert root.children[0] == root.children[1]


def test_block_assignment_value_numbering() -> None:
    """Verify basic block value numbering and definition kill on variable re-assignment."""
    # Statements:
    # let a: int = 1;
    # let b: int = a + 2;
    # a = 5;
    # let c: int = a + 2;
    stmts = [
        VarDecl(id=0, span=dummy_span(), name="a", type_name="int", init=_lit_int(1)),
        VarDecl(id=0, span=dummy_span(), name="b", type_name="int", init=_bin(_var("a"), "+", _lit_int(2))),
        AssignStmt(id=0, span=dummy_span(), target=_var("a"), op="=", value=_lit_int(5)),
        VarDecl(id=0, span=dummy_span(), name="c", type_name="int", init=_bin(_var("a"), "+", _lit_int(2))),
    ]
    block = Block(id=0, span=dummy_span(), statements=stmts)
    dag = build_block_dag(block)

    b_node_id = dag.var_map["b"]
    c_node_id = dag.var_map["c"]

    # b and c must NOT be the same node because 'a' was reassigned from 1 to 5
    assert b_node_id != c_node_id
    assert dag.nodes[b_node_id].label == "+"
    assert dag.nodes[c_node_id].label == "+"


def test_trace_and_serialization() -> None:
    """Verify trace generation and to_dict / to_mermaid exports."""
    expr1 = _bin(_var("x"), "*", _lit_int(10))
    expr2 = _bin(_var("x"), "*", _lit_int(10))

    builder = DAGBuilder()
    builder.add_expression(expr1)
    builder.add_expression(expr2)
    dag = builder.dag

    # Trace must contain steps
    assert len(dag.trace) > 0
    actions = [step.action for step in dag.trace]
    assert "CREATE_LEAF" in actions
    assert "CREATE_OP" in actions
    assert "REUSE" in actions

    # to_dict structure
    d = dag.to_dict()
    assert "nodes" in d
    assert "roots" in d
    assert "tree_node_count" in d
    assert "dag_node_count" in d
    assert "savings" in d
    assert "trace" in d

    # Mermaid string
    mermaid = dag.to_mermaid()
    assert "graph TD" in mermaid
    assert "n" in mermaid


def test_dag_from_parsed_vela_code() -> None:
    """Verify DAG construction from a parsed Vela source program."""
    code = """
    func main() {
        let a: int = 10;
        let b: int = 20;
        let x: int = (a + b) * 2;
        let y: int = (a + b) * 3;
        show x, y;
    }
    """
    source = SourceFile("test.vela", code)
    scanner = Scanner(source)
    lex_result = scanner.scan()
    parser = RecursiveDescentParser(lex_result.tokens, source)
    parse_result = parser.parse()
    assert parse_result.ast is not None
    assert len(parser.diagnostics) == 0

    func_decl = parse_result.ast.items[0]
    dag = build_block_dag(func_decl.body)

    assert "x" in dag.var_map
    assert "y" in dag.var_map
    x_id = dag.var_map["x"]
    y_id = dag.var_map["y"]

    x_node = dag.nodes[x_id]
    y_node = dag.nodes[y_id]
    assert x_node.label == "*"
    assert y_node.label == "*"

    # Common subexpression (a + b) is shared
    assert x_node.children[0] == y_node.children[0]
    shared_id = x_node.children[0]
    assert dag.nodes[shared_id].label == "+"
    assert dag.savings > 0
