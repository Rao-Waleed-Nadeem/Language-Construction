"""AST Pretty Printer and S-expression Generator.

Per doc 01 §6–§9, doc 02 §5, doc 08 §2:
Produces S-expression and indented structural representations of Vela ASTs.
"""

from __future__ import annotations

from typing import Any

from vela.ast.nodes import (
    ArrayAccessExpr,
    AssignStmt,
    ASTNode,
    BinaryExpr,
    Block,
    BreakStmt,
    CallExpr,
    CallStmt,
    CaseClause,
    CastExpr,
    ContinueStmt,
    DoWhileStmt,
    ForStmt,
    FuncDecl,
    IfStmt,
    ImplicitCast,
    LiteralExpr,
    Program,
    ReadStmt,
    ReturnStmt,
    ShowStmt,
    SwitchStmt,
    UnaryExpr,
    VarDecl,
    VarRefExpr,
    WhileStmt,
)


class ASTPrinter:
    """Formats AST nodes into S-expressions or JSON-ready structures."""

    @classmethod
    def to_sexpr(cls, node: ASTNode | None) -> str:
        """Convert an AST node into an S-expression string."""
        if node is None:
            return "nil"

        if isinstance(node, Program):
            items_str = " ".join(cls.to_sexpr(item) for item in node.items)
            return f"(Program {items_str})" if items_str else "(Program)"

        if isinstance(node, VarDecl):
            arr_str = f"[{node.array_size}]" if node.is_array else ""
            init_str = f" {cls.to_sexpr(node.init)}" if node.init else ""
            arr_inits_str = (
                f" (inits {' '.join(cls.to_sexpr(e) for e in node.array_inits)})"
                if node.array_inits
                else ""
            )
            return f"(VarDecl {node.name} {node.type_name}{arr_str}{init_str}{arr_inits_str})"

        if isinstance(node, FuncDecl):
            params_str = " ".join(
                f"({p.name} {p.type_name}{'[]' if p.is_array else ''})" for p in node.params
            )
            ret_str = f" : {node.return_type}" if node.return_type else ""
            return f"(FuncDecl {node.name} ({params_str}){ret_str} {cls.to_sexpr(node.body)})"

        if isinstance(node, Block):
            stmts_str = " ".join(cls.to_sexpr(s) for s in node.statements)
            return f"(Block {stmts_str})" if stmts_str else "(Block)"

        if isinstance(node, AssignStmt):
            val_str = f" {cls.to_sexpr(node.value)}" if node.value else ""
            return f"({node.op} {cls.to_sexpr(node.target)}{val_str})"

        if isinstance(node, CallStmt):
            return cls.to_sexpr(node.expr)

        if isinstance(node, IfStmt):
            else_str = f" {cls.to_sexpr(node.else_stmt)}" if node.else_stmt else ""
            return f"(if {cls.to_sexpr(node.condition)} {cls.to_sexpr(node.then_block)}{else_str})"

        if isinstance(node, WhileStmt):
            return f"(while {cls.to_sexpr(node.condition)} {cls.to_sexpr(node.body)})"

        if isinstance(node, DoWhileStmt):
            return f"(do-while {cls.to_sexpr(node.body)} {cls.to_sexpr(node.condition)})"

        if isinstance(node, ForStmt):
            init_str = cls.to_sexpr(node.init)
            cond_str = cls.to_sexpr(node.condition)
            upd_str = cls.to_sexpr(node.update)
            return f"(for ({init_str}; {cond_str}; {upd_str}) {cls.to_sexpr(node.body)})"

        if isinstance(node, SwitchStmt):
            cases_str = " ".join(cls.to_sexpr(c) for c in node.cases)
            def_str = (
                f" (default {' '.join(cls.to_sexpr(s) for s in node.default_case)})"
                if node.default_case is not None
                else ""
            )
            return f"(switch {cls.to_sexpr(node.expr)} {cases_str}{def_str})"

        if isinstance(node, CaseClause):
            labels_str = " ".join(str(lbl) for lbl in node.labels)
            stmts_str = " ".join(cls.to_sexpr(s) for s in node.body)
            return f"(case ({labels_str}) {stmts_str})"

        if isinstance(node, ReturnStmt):
            val_str = f" {cls.to_sexpr(node.value)}" if node.value else ""
            return f"(return{val_str})"

        if isinstance(node, BreakStmt):
            return "(break)"

        if isinstance(node, ContinueStmt):
            return "(continue)"

        if isinstance(node, ShowStmt):
            exprs_str = " ".join(cls.to_sexpr(e) for e in node.expressions)
            return f"(show {exprs_str})"

        if isinstance(node, ReadStmt):
            return f"(read {cls.to_sexpr(node.target)})"

        if isinstance(node, BinaryExpr):
            return f"({node.op} {cls.to_sexpr(node.left)} {cls.to_sexpr(node.right)})"

        if isinstance(node, UnaryExpr):
            return f"({node.op} {cls.to_sexpr(node.operand)})"

        if isinstance(node, CastExpr):
            return f"(as {cls.to_sexpr(node.expr)} {node.target_type})"

        if isinstance(node, ImplicitCast):
            return f"(implicit-cast {node.from_type}->{node.to_type} {cls.to_sexpr(node.expr)})"

        if isinstance(node, LiteralExpr):
            if node.literal_type == "string":
                return f'"{node.value}"'
            if node.literal_type == "char":
                return f"'{node.value}'"
            return str(node.value)

        if isinstance(node, VarRefExpr):
            return node.name

        if isinstance(node, ArrayAccessExpr):
            return f"(index {node.name} {cls.to_sexpr(node.index)})"

        if isinstance(node, CallExpr):
            args_str = " ".join(cls.to_sexpr(a) for a in node.args)
            return f"(call {node.callee} {args_str})" if args_str else f"(call {node.callee})"

        return f"({node.__class__.__name__})"

    @classmethod
    def to_dict(cls, node: ASTNode | None) -> dict[str, Any] | None:
        """Serialize node to dictionary."""
        return node.to_dict() if node else None
