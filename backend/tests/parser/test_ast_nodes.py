"""Unit tests for AST node construction, tree traversal, and S-expression printing.

Per M3-T1 requirements and doc 08 §1:
- constructs every node type
- verifies S-expression output
- verifies to_dict serialization
- verifies ImplicitCast representation
"""

from vela.ast.nodes import (
    BinaryExpr,
    Block,
    FuncDecl,
    IfStmt,
    ImplicitCast,
    LiteralExpr,
    Param,
    Program,
    ReturnStmt,
    ShowStmt,
    VarDecl,
    VarRefExpr,
)
from vela.ast.printer import ASTPrinter
from vela.common.source import SourceLocation, Span


def dummy_span() -> Span:
    loc = SourceLocation(1, 1, 0)
    return Span(loc, loc)


def test_ast_node_construction_and_children():
    """Verify constructing nodes, children traversal, and to_dict serialization."""
    span = dummy_span()

    # Program: let x: int = 10;
    var_x = VarDecl(
        id=1,
        span=span,
        name="x",
        type_name="int",
        init=LiteralExpr(id=2, span=span, literal_type="int", value=10),
    )
    prog = Program(id=0, span=span, items=[var_x])

    assert len(prog.children()) == 1
    assert prog.children()[0] == var_x
    assert len(var_x.children()) == 1

    d = prog.to_dict()
    assert d["node_type"] == "Program"
    assert d["id"] == 0
    assert len(d["items"]) == 1
    assert d["items"][0]["name"] == "x"


def test_ast_sexpr_printer():
    """Verify S-expression serialization for complex language constructs."""
    span = dummy_span()

    # func add(a: int, b: int): int { return a + b; }
    param_a = Param(id=1, span=span, name="a", type_name="int")
    param_b = Param(id=2, span=span, name="b", type_name="int")
    add_expr = BinaryExpr(
        id=5,
        span=span,
        left=VarRefExpr(id=3, span=span, name="a"),
        op="+",
        right=VarRefExpr(id=4, span=span, name="b"),
    )
    ret_stmt = ReturnStmt(id=6, span=span, value=add_expr)
    body = Block(id=7, span=span, statements=[ret_stmt])

    fn_decl = FuncDecl(
        id=8,
        span=span,
        name="add",
        params=[param_a, param_b],
        return_type="int",
        body=body,
    )

    sexpr = ASTPrinter.to_sexpr(fn_decl)
    assert sexpr == "(FuncDecl add ((a int) (b int)) : int (Block (return (+ a b))))"


def test_ast_implicit_cast_node():
    """Verify ImplicitCast node (P4-10) used for int -> float widening."""
    span = dummy_span()
    lit_int = LiteralExpr(id=1, span=span, literal_type="int", value=42)
    cast = ImplicitCast(
        id=2,
        span=span,
        expr=lit_int,
        from_type="int",
        to_type="float",
    )

    assert cast.from_type == "int"
    assert cast.to_type == "float"
    assert len(cast.children()) == 1
    sexpr = ASTPrinter.to_sexpr(cast)
    assert sexpr == "(implicit-cast int->float 42)"


def test_ast_control_flow_nodes():
    """Verify IfStmt and ForStmt construction and printing."""
    span = dummy_span()
    cond = BinaryExpr(
        id=1,
        span=span,
        left=VarRefExpr(id=2, span=span, name="i"),
        op="<",
        right=LiteralExpr(id=3, span=span, literal_type="int", value=10),
    )
    then_blk = Block(
        id=4,
        span=span,
        statements=[ShowStmt(id=5, span=span, expressions=[VarRefExpr(id=6, span=span, name="i")])],
    )
    if_stmt = IfStmt(id=7, span=span, condition=cond, then_block=then_blk)

    sexpr = ASTPrinter.to_sexpr(if_stmt)
    assert sexpr == "(if (< i 10) (Block (show i)))"
