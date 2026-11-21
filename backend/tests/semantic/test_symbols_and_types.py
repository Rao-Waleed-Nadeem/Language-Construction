"""Tests for Types, Symbols, Scopes, and Return-Path Analysis (M4-T1).

Per doc 01 §4–§6, §8, §12 and agent-prompt.md:
- Type compatibility, implicit widening (int -> float), and explicit cast table.
- Lexical scopes, shadowing tracking, and redeclaration detection.
- Symbol table event logging and scope tree hierarchy.
- Structural all-paths-return analysis.
"""

from vela.ast.nodes import (
    Block,
    BreakStmt,
    CaseClause,
    DoWhileStmt,
    ForStmt,
    IfStmt,
    LiteralExpr,
    ReturnStmt,
    SwitchStmt,
    WhileStmt,
)
from vela.common.source import SourceLocation, Span
from vela.semantic.returns import block_returns, statement_returns
from vela.semantic.symbols import ScopeKind, Symbol, SymbolTable
from vela.semantic.types import (
    BOOL,
    CHAR,
    ERROR,
    FLOAT,
    INT,
    STRING,
    VOID,
    ArrayType,
    can_explicit_cast,
    can_implicit_widen,
    get_binary_op_result_type,
    get_type_by_name,
    get_unary_op_result_type,
    is_assignable,
)

DUMMY_SPAN = Span(
    SourceLocation(1, 1, 0),
    SourceLocation(1, 10, 9),
)


def test_types_and_compatibility() -> None:
    # Scalar types
    assert INT.is_scalar and INT.is_numeric
    assert FLOAT.is_scalar and FLOAT.is_numeric
    assert CHAR.is_scalar and not CHAR.is_numeric
    assert STRING.is_scalar and not STRING.is_numeric
    assert BOOL.is_scalar and not BOOL.is_numeric
    assert VOID.is_void and not VOID.is_scalar
    assert ERROR.is_error

    # Array types
    arr_type = ArrayType(INT, 5)
    assert arr_type.is_array
    assert arr_type.element_type == INT
    assert arr_type.size == 5
    assert str(arr_type) == "int[5]"

    # Name lookup
    assert get_type_by_name("int") == INT
    assert get_type_by_name("float") == FLOAT
    assert get_type_by_name("int[10]") == ArrayType(INT, 10)

    # Assignability
    assert is_assignable(INT, INT)
    assert is_assignable(INT, FLOAT)  # Implicit widening
    assert not is_assignable(FLOAT, INT)
    assert not is_assignable(STRING, INT)
    assert not is_assignable(BOOL, INT)

    # Widening
    assert can_implicit_widen(INT, FLOAT)
    assert not can_implicit_widen(FLOAT, INT)
    assert not can_implicit_widen(INT, STRING)


def test_explicit_cast_table() -> None:
    # Row INT
    assert can_explicit_cast(INT, FLOAT)
    assert can_explicit_cast(INT, CHAR)
    assert can_explicit_cast(INT, STRING)
    assert not can_explicit_cast(INT, BOOL)

    # Row FLOAT
    assert can_explicit_cast(FLOAT, INT)
    assert can_explicit_cast(FLOAT, STRING)
    assert not can_explicit_cast(FLOAT, CHAR)
    assert not can_explicit_cast(FLOAT, BOOL)

    # Row CHAR
    assert can_explicit_cast(CHAR, INT)
    assert can_explicit_cast(CHAR, STRING)
    assert not can_explicit_cast(CHAR, FLOAT)
    assert not can_explicit_cast(CHAR, BOOL)

    # Row STRING
    assert not can_explicit_cast(STRING, INT)
    assert not can_explicit_cast(STRING, FLOAT)
    assert not can_explicit_cast(STRING, CHAR)
    assert not can_explicit_cast(STRING, BOOL)

    # Row BOOL
    assert can_explicit_cast(BOOL, INT)
    assert can_explicit_cast(BOOL, STRING)
    assert not can_explicit_cast(BOOL, FLOAT)
    assert not can_explicit_cast(BOOL, CHAR)


def test_operator_typing() -> None:
    # Binary arithmetic
    assert get_binary_op_result_type(INT, "+", INT) == INT
    assert get_binary_op_result_type(INT, "+", FLOAT) == FLOAT
    assert get_binary_op_result_type(FLOAT, "*", INT) == FLOAT
    assert get_binary_op_result_type(STRING, "+", STRING) == STRING
    assert get_binary_op_result_type(STRING, "-", STRING) is None
    assert get_binary_op_result_type(INT, "%", INT) == INT
    assert get_binary_op_result_type(FLOAT, "%", FLOAT) is None

    # Relational
    assert get_binary_op_result_type(INT, "<", FLOAT) == BOOL
    assert get_binary_op_result_type(CHAR, ">=", CHAR) == BOOL
    assert get_binary_op_result_type(STRING, "<", STRING) is None  # Strings not ordered

    # Equality
    assert get_binary_op_result_type(STRING, "==", STRING) == BOOL
    assert get_binary_op_result_type(BOOL, "!=", BOOL) == BOOL
    assert get_binary_op_result_type(INT, "==", FLOAT) == BOOL

    # Logical
    assert get_binary_op_result_type(BOOL, "and", BOOL) == BOOL
    assert get_binary_op_result_type(INT, "and", BOOL) is None

    # Unary
    assert get_unary_op_result_type("-", INT) == INT
    assert get_unary_op_result_type("-", FLOAT) == FLOAT
    assert get_unary_op_result_type("-", STRING) is None
    assert get_unary_op_result_type("not", BOOL) == BOOL
    assert get_unary_op_result_type("not", INT) is None


def test_scopes_and_shadowing() -> None:
    st = SymbolTable()
    global_scope = st.current_scope
    assert global_scope.kind == ScopeKind.GLOBAL

    # Define global 'x'
    sym_global_x = Symbol(
        name="x",
        symbol_type=INT,
        kind="var",
        scope_id=global_scope.id,
        decl_span=DUMMY_SPAN,
    )
    ok, err = st.define(sym_global_x)
    assert ok and err is None

    # Enter function scope
    func_scope = st.enter_scope(ScopeKind.FUNCTION, "func_test")
    assert st.current_scope == func_scope

    # Shadow global 'x' with local 'x'
    sym_local_x = Symbol(
        name="x",
        symbol_type=FLOAT,
        kind="var",
        scope_id=func_scope.id,
        decl_span=DUMMY_SPAN,
    )
    ok, err = st.define(sym_local_x)
    assert ok and err is None

    # Lookup 'x' in function scope finds local 'x'
    found = st.lookup("x")
    assert found is not None
    assert found.symbol_type == FLOAT
    assert found.scope_id == func_scope.id

    # Check shadow event was recorded
    shadow_events = [e for e in st.events if e.event_type == "shadow_symbol"]
    assert len(shadow_events) == 1
    assert shadow_events[0].symbol_name == "x"

    # Exit function scope
    st.exit_scope()
    assert st.current_scope == global_scope

    # Lookup 'x' in global scope finds global 'x'
    found_global = st.lookup("x")
    assert found_global is not None
    assert found_global.symbol_type == INT
    assert found_global.scope_id == global_scope.id


def test_redeclaration_in_same_scope() -> None:
    st = SymbolTable()
    st.enter_scope(ScopeKind.BLOCK, "block_1")

    sym1 = Symbol(name="a", symbol_type=INT, kind="var", scope_id=st.current_scope.id, decl_span=DUMMY_SPAN)
    ok1, err1 = st.define(sym1)
    assert ok1 and err1 is None

    # Redeclare 'a' in same block
    sym2 = Symbol(name="a", symbol_type=FLOAT, kind="var", scope_id=st.current_scope.id, decl_span=DUMMY_SPAN)
    ok2, err2 = st.define(sym2)
    assert not ok2
    assert err2 == sym1


def test_symbol_use_tracking() -> None:
    st = SymbolTable()
    sym = Symbol(name="total", symbol_type=INT, kind="var", scope_id=st.current_scope.id, decl_span=DUMMY_SPAN)
    st.define(sym)

    span1 = Span(SourceLocation(3, 5, 20), SourceLocation(3, 10, 25))
    span2 = Span(SourceLocation(5, 5, 40), SourceLocation(5, 10, 45))

    st.record_use("total", span1)
    st.record_use("total", span2)

    found = st.lookup("total")
    assert found is not None
    assert len(found.uses) == 2
    assert found.to_dict()["use_count"] == 2

    # Scope tree export
    tree = st.get_scope_tree()
    assert tree["name"] == "global"
    assert "total" in tree["symbols"]


def test_return_path_analysis() -> None:
    ret_stmt = ReturnStmt(id=1, span=DUMMY_SPAN, value=LiteralExpr(2, DUMMY_SPAN, "int", 1))
    break_stmt = BreakStmt(id=3, span=DUMMY_SPAN)

    # Simple return
    assert statement_returns(ret_stmt)

    # Block with return
    blk_with_ret = Block(id=4, span=DUMMY_SPAN, statements=[ret_stmt])
    assert block_returns(blk_with_ret)

    # Block without return
    blk_no_ret = Block(id=5, span=DUMMY_SPAN, statements=[])
    assert not block_returns(blk_no_ret)

    # If-else where both return
    if_both = IfStmt(
        id=6,
        span=DUMMY_SPAN,
        condition=LiteralExpr(7, DUMMY_SPAN, "bool", True),
        then_block=blk_with_ret,
        else_stmt=blk_with_ret,
    )
    assert statement_returns(if_both)

    # If without else
    if_no_else = IfStmt(
        id=8,
        span=DUMMY_SPAN,
        condition=LiteralExpr(9, DUMMY_SPAN, "bool", True),
        then_block=blk_with_ret,
        else_stmt=None,
    )
    assert not statement_returns(if_no_else)

    # If with else-if where last branch missing
    if_else_if_no_ret = IfStmt(
        id=10,
        span=DUMMY_SPAN,
        condition=LiteralExpr(11, DUMMY_SPAN, "bool", True),
        then_block=blk_with_ret,
        else_stmt=if_no_else,
    )
    assert not statement_returns(if_else_if_no_ret)

    # Loops never guarantee return
    while_stmt = WhileStmt(
        id=12,
        span=DUMMY_SPAN,
        condition=LiteralExpr(13, DUMMY_SPAN, "bool", True),
        body=blk_with_ret,
    )
    assert not statement_returns(while_stmt)

    for_stmt = ForStmt(
        id=14,
        span=DUMMY_SPAN,
        body=blk_with_ret,
    )
    assert not statement_returns(for_stmt)

    do_while = DoWhileStmt(
        id=15,
        span=DUMMY_SPAN,
        body=blk_with_ret,
        condition=LiteralExpr(16, DUMMY_SPAN, "bool", True),
    )
    assert not statement_returns(do_while)

    # Switch: all return + default -> True
    switch_ok = SwitchStmt(
        id=17,
        span=DUMMY_SPAN,
        expr=LiteralExpr(18, DUMMY_SPAN, "int", 1),
        cases=[CaseClause(id=19, span=DUMMY_SPAN, labels=[1], body=[ret_stmt])],
        default_case=[ret_stmt],
    )
    assert statement_returns(switch_ok)

    # Switch: missing default -> False
    switch_no_def = SwitchStmt(
        id=20,
        span=DUMMY_SPAN,
        expr=LiteralExpr(21, DUMMY_SPAN, "int", 1),
        cases=[CaseClause(id=22, span=DUMMY_SPAN, labels=[1], body=[ret_stmt])],
        default_case=None,
    )
    assert not statement_returns(switch_no_def)

    # Switch: case contains break -> False
    switch_with_break = SwitchStmt(
        id=23,
        span=DUMMY_SPAN,
        expr=LiteralExpr(24, DUMMY_SPAN, "int", 1),
        cases=[CaseClause(id=25, span=DUMMY_SPAN, labels=[1], body=[break_stmt])],
        default_case=[ret_stmt],
    )
    assert not statement_returns(switch_with_break)
