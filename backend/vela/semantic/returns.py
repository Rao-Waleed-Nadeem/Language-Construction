"""Structural all-paths-return analysis for Vela functions.

Per doc 01 §8 and doc 07 §4:
- A block returns iff its reachable statements guarantee a return.
- An if/else statement returns iff both the then-block and the else-statement return.
- An if without else never guarantees a return.
- A switch statement returns iff:
    1. It has a default clause.
    2. Every case clause and the default clause guarantee a return.
    3. No break statement directly targets the switch.
- Loops (while, for, do-while) never count as guaranteeing a return.
"""

from __future__ import annotations

from vela.ast.nodes import (
    Block,
    BreakStmt,
    DoWhileStmt,
    ForStmt,
    IfStmt,
    ReturnStmt,
    Stmt,
    SwitchStmt,
    WhileStmt,
)


def statement_returns(stmt: Stmt | None) -> bool:
    """Determine if a single statement unconditionally returns."""
    if stmt is None:
        return False

    if isinstance(stmt, ReturnStmt):
        return True

    if isinstance(stmt, Block):
        return block_returns(stmt)

    if isinstance(stmt, IfStmt):
        if stmt.else_stmt is None:
            return False
        then_ret = block_returns(stmt.then_block)
        if isinstance(stmt.else_stmt, IfStmt):
            else_ret = statement_returns(stmt.else_stmt)
        elif isinstance(stmt.else_stmt, Block):
            else_ret = block_returns(stmt.else_stmt)
        else:
            else_ret = False
        return then_ret and else_ret

    if isinstance(stmt, SwitchStmt):
        return switch_returns(stmt)

    if isinstance(stmt, (WhileStmt, DoWhileStmt, ForStmt)):
        # doc 01 §8: loops never count as returning
        return False

    return False


def block_returns(block: Block | None) -> bool:
    """Determine if a block unconditionally returns."""
    if block is None or not block.statements:
        return False

    for stmt in block.statements:
        if statement_returns(stmt):
            return True

    return False


def switch_returns(switch_stmt: SwitchStmt) -> bool:
    """Determine if a switch statement guarantees a return.

    Requires:
    1. A default case is present.
    2. Every case clause returns.
    3. The default case returns.
    4. No break statement targets the switch in any case.
    """
    if switch_stmt.default_case is None:
        return False

    # Check that default case returns and has no breaks
    if not clause_returns(switch_stmt.default_case):
        return False

    # Check each case clause
    for case_clause in switch_stmt.cases:
        if not clause_returns(case_clause.body):
            return False

    return True


def clause_returns(statements: list[Stmt]) -> bool:
    """Check if a switch case body returns without any breaking out."""
    has_return = False
    for stmt in statements:
        if contains_direct_break(stmt):
            return False
        if statement_returns(stmt):
            has_return = True
            break
    return has_return


def contains_direct_break(stmt: Stmt) -> bool:
    """Check if a statement contains a 'break' statement not enclosed in an inner loop/switch."""
    if isinstance(stmt, BreakStmt):
        return True

    if isinstance(stmt, Block):
        return any(contains_direct_break(s) for s in stmt.statements)

    if isinstance(stmt, IfStmt):
        if contains_direct_break(stmt.then_block):
            return True
        if stmt.else_stmt:
            return contains_direct_break(stmt.else_stmt)
        return False

    # Inner loops or inner switches consume their own breaks
    if isinstance(stmt, (WhileStmt, DoWhileStmt, ForStmt, SwitchStmt)):
        return False

    return False
