"""Abstract Syntax Tree (AST) node definitions for Vela.

Per doc 01 §6–§9, doc 02 §5, doc 08 §1:
Every node carries integer `id` and `span: Span`.
All language constructs are represented, including `ImplicitCast`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from vela.common.source import Span


@dataclass
class ASTNode:
    """Base class for all AST nodes."""

    id: int
    span: Span

    def children(self) -> list[ASTNode]:
        """Return direct child AST nodes for traversal."""
        return []

    def to_dict(self) -> dict[str, Any]:
        """Serialize node to a JSON-ready dictionary."""
        d = {"node_type": self.__class__.__name__, "id": self.id, "span": self.span.to_dict()}
        return d


# ---- Program & Declarations ----


@dataclass
class Program(ASTNode):
    items: list[VarDecl | FuncDecl] = field(default_factory=list)

    def children(self) -> list[ASTNode]:
        return list(self.items)

    def to_dict(self) -> dict[str, Any]:
        d = super().to_dict()
        d["items"] = [item.to_dict() for item in self.items]
        return d


@dataclass
class Param(ASTNode):
    name: str = ""
    type_name: str = ""
    is_array: bool = False

    def to_dict(self) -> dict[str, Any]:
        d = super().to_dict()
        d["name"] = self.name
        d["type_name"] = self.type_name
        d["is_array"] = self.is_array
        return d


@dataclass
class VarDecl(ASTNode):
    name: str = ""
    type_name: str = ""
    array_size: int | None = None
    init: Expr | None = None
    array_inits: list[Expr] = field(default_factory=list)
    name_span: Span | None = None

    @property
    def is_array(self) -> bool:
        return self.array_size is not None

    def children(self) -> list[ASTNode]:
        ch: list[ASTNode] = []
        if self.init:
            ch.append(self.init)
        ch.extend(self.array_inits)
        return ch

    def to_dict(self) -> dict[str, Any]:
        d = super().to_dict()
        d["name"] = self.name
        d["type_name"] = self.type_name
        d["is_array"] = self.is_array
        d["array_size"] = self.array_size
        d["init"] = self.init.to_dict() if self.init else None
        d["array_inits"] = [e.to_dict() for e in self.array_inits]
        return d


@dataclass
class Block(ASTNode):
    statements: list[Stmt] = field(default_factory=list)

    def children(self) -> list[ASTNode]:
        return list(self.statements)

    def to_dict(self) -> dict[str, Any]:
        d = super().to_dict()
        d["statements"] = [s.to_dict() for s in self.statements]
        return d


@dataclass
class FuncDecl(ASTNode):
    name: str = ""
    params: list[Param] = field(default_factory=list)
    return_type: str | None = None
    body: Block = field(default_factory=lambda: Block(id=0, span=Span.point(None)))  # type: ignore
    name_span: Span | None = None

    def children(self) -> list[ASTNode]:
        return list(self.params) + [self.body]

    def to_dict(self) -> dict[str, Any]:
        d = super().to_dict()
        d["name"] = self.name
        d["params"] = [p.to_dict() for p in self.params]
        d["return_type"] = self.return_type
        d["body"] = self.body.to_dict()
        return d


# ---- Statements ----


class Stmt(ASTNode):
    """Base class for statements."""


@dataclass
class AssignStmt(Stmt):
    target: VarRefExpr | ArrayAccessExpr = field(default_factory=lambda: VarRefExpr(0, None, ""))  # type: ignore
    op: str = "="  # =, +=, -=, *=, /=, %=, ++, --
    value: Expr | None = None  # None for ++, --

    def children(self) -> list[ASTNode]:
        ch: list[ASTNode] = [self.target]
        if self.value:
            ch.append(self.value)
        return ch

    def to_dict(self) -> dict[str, Any]:
        d = super().to_dict()
        d["target"] = self.target.to_dict()
        d["op"] = self.op
        d["value"] = self.value.to_dict() if self.value else None
        return d


@dataclass
class CallStmt(Stmt):
    expr: CallExpr = field(default_factory=lambda: CallExpr(0, None, "", []))  # type: ignore

    def children(self) -> list[ASTNode]:
        return [self.expr]

    def to_dict(self) -> dict[str, Any]:
        d = super().to_dict()
        d["expr"] = self.expr.to_dict()
        return d


@dataclass
class IfStmt(Stmt):
    condition: Expr = field(default_factory=lambda: LiteralExpr(0, None, "bool", False))  # type: ignore
    then_block: Block = field(default_factory=lambda: Block(0, None, []))  # type: ignore
    else_stmt: Block | IfStmt | None = None

    def children(self) -> list[ASTNode]:
        ch: list[ASTNode] = [self.condition, self.then_block]
        if self.else_stmt:
            ch.append(self.else_stmt)
        return ch

    def to_dict(self) -> dict[str, Any]:
        d = super().to_dict()
        d["condition"] = self.condition.to_dict()
        d["then_block"] = self.then_block.to_dict()
        d["else_stmt"] = self.else_stmt.to_dict() if self.else_stmt else None
        return d


@dataclass
class CaseClause(ASTNode):
    labels: list[int | str] = field(default_factory=list)  # int literals or char literals
    body: list[Stmt] = field(default_factory=list)
    label_spans: list[Span] = field(default_factory=list)

    def children(self) -> list[ASTNode]:
        return list(self.body)

    def to_dict(self) -> dict[str, Any]:
        d = super().to_dict()
        d["labels"] = self.labels
        d["body"] = [s.to_dict() for s in self.body]
        return d


@dataclass
class SwitchStmt(Stmt):
    expr: Expr = field(default_factory=lambda: LiteralExpr(0, None, "int", 0))  # type: ignore
    cases: list[CaseClause] = field(default_factory=list)
    default_case: list[Stmt] | None = None

    def children(self) -> list[ASTNode]:
        ch: list[ASTNode] = [self.expr]
        ch.extend(self.cases)
        if self.default_case:
            ch.extend(self.default_case)
        return ch

    def to_dict(self) -> dict[str, Any]:
        d = super().to_dict()
        d["expr"] = self.expr.to_dict()
        d["cases"] = [c.to_dict() for c in self.cases]
        d["default_case"] = (
            [s.to_dict() for s in self.default_case] if self.default_case is not None else None
        )
        return d


@dataclass
class WhileStmt(Stmt):
    condition: Expr = field(default_factory=lambda: LiteralExpr(0, None, "bool", False))  # type: ignore
    body: Block = field(default_factory=lambda: Block(0, None, []))  # type: ignore

    def children(self) -> list[ASTNode]:
        return [self.condition, self.body]

    def to_dict(self) -> dict[str, Any]:
        d = super().to_dict()
        d["condition"] = self.condition.to_dict()
        d["body"] = self.body.to_dict()
        return d


@dataclass
class DoWhileStmt(Stmt):
    body: Block = field(default_factory=lambda: Block(0, None, []))  # type: ignore
    condition: Expr = field(default_factory=lambda: LiteralExpr(0, None, "bool", False))  # type: ignore

    def children(self) -> list[ASTNode]:
        return [self.body, self.condition]

    def to_dict(self) -> dict[str, Any]:
        d = super().to_dict()
        d["body"] = self.body.to_dict()
        d["condition"] = self.condition.to_dict()
        return d


@dataclass
class ForStmt(Stmt):
    init: VarDecl | AssignStmt | None = None
    condition: Expr | None = None
    update: AssignStmt | None = None
    body: Block = field(default_factory=lambda: Block(0, None, []))  # type: ignore

    def children(self) -> list[ASTNode]:
        ch: list[ASTNode] = []
        if self.init:
            ch.append(self.init)
        if self.condition:
            ch.append(self.condition)
        if self.update:
            ch.append(self.update)
        ch.append(self.body)
        return ch

    def to_dict(self) -> dict[str, Any]:
        d = super().to_dict()
        d["init"] = self.init.to_dict() if self.init else None
        d["condition"] = self.condition.to_dict() if self.condition else None
        d["update"] = self.update.to_dict() if self.update else None
        d["body"] = self.body.to_dict()
        return d


@dataclass
class ReturnStmt(Stmt):
    value: Expr | None = None

    def children(self) -> list[ASTNode]:
        return [self.value] if self.value else []

    def to_dict(self) -> dict[str, Any]:
        d = super().to_dict()
        d["value"] = self.value.to_dict() if self.value else None
        return d


@dataclass
class BreakStmt(Stmt):
    keyword_span: Span | None = None


@dataclass
class ContinueStmt(Stmt):
    keyword_span: Span | None = None


@dataclass
class ShowStmt(Stmt):
    expressions: list[Expr] = field(default_factory=list)

    def children(self) -> list[ASTNode]:
        return list(self.expressions)

    def to_dict(self) -> dict[str, Any]:
        d = super().to_dict()
        d["expressions"] = [e.to_dict() for e in self.expressions]
        return d


@dataclass
class ReadStmt(Stmt):
    target: VarRefExpr | ArrayAccessExpr = field(default_factory=lambda: VarRefExpr(0, None, ""))  # type: ignore

    def children(self) -> list[ASTNode]:
        return [self.target]

    def to_dict(self) -> dict[str, Any]:
        d = super().to_dict()
        d["target"] = self.target.to_dict()
        return d


# ---- Expressions ----


class Expr(ASTNode):
    """Base class for expression nodes."""
    inferred_type: str | None = None  # Populated during semantic analysis


@dataclass
class LiteralExpr(Expr):
    literal_type: str = "int"  # int, float, char, string, bool
    value: Any = 0

    def to_dict(self) -> dict[str, Any]:
        d = super().to_dict()
        d["literal_type"] = self.literal_type
        d["value"] = self.value
        d["inferred_type"] = self.inferred_type or self.literal_type
        return d


@dataclass
class VarRefExpr(Expr):
    name: str = ""

    def to_dict(self) -> dict[str, Any]:
        d = super().to_dict()
        d["name"] = self.name
        d["inferred_type"] = self.inferred_type
        return d


@dataclass
class ArrayAccessExpr(Expr):
    name: str = ""
    index: Expr = field(default_factory=lambda: LiteralExpr(0, None, "int", 0))  # type: ignore

    def children(self) -> list[ASTNode]:
        return [self.index]

    def to_dict(self) -> dict[str, Any]:
        d = super().to_dict()
        d["name"] = self.name
        d["index"] = self.index.to_dict()
        d["inferred_type"] = self.inferred_type
        return d


@dataclass
class BinaryExpr(Expr):
    left: Expr = field(default_factory=lambda: LiteralExpr(0, None, "int", 0))  # type: ignore
    op: str = "+"
    right: Expr = field(default_factory=lambda: LiteralExpr(0, None, "int", 0))  # type: ignore
    op_span: Span | None = None

    def children(self) -> list[ASTNode]:
        return [self.left, self.right]

    def to_dict(self) -> dict[str, Any]:
        d = super().to_dict()
        d["left"] = self.left.to_dict()
        d["op"] = self.op
        d["right"] = self.right.to_dict()
        d["inferred_type"] = self.inferred_type
        return d


@dataclass
class UnaryExpr(Expr):
    op: str = "-"  # -, not
    operand: Expr = field(default_factory=lambda: LiteralExpr(0, None, "int", 0))  # type: ignore

    def children(self) -> list[ASTNode]:
        return [self.operand]

    def to_dict(self) -> dict[str, Any]:
        d = super().to_dict()
        d["op"] = self.op
        d["operand"] = self.operand.to_dict()
        d["inferred_type"] = self.inferred_type
        return d


@dataclass
class CastExpr(Expr):
    expr: Expr = field(default_factory=lambda: LiteralExpr(0, None, "int", 0))  # type: ignore
    target_type: str = "float"
    as_span: Span | None = None

    def children(self) -> list[ASTNode]:
        return [self.expr]

    def to_dict(self) -> dict[str, Any]:
        d = super().to_dict()
        d["expr"] = self.expr.to_dict()
        d["target_type"] = self.target_type
        d["inferred_type"] = self.inferred_type or self.target_type
        return d


@dataclass
class ImplicitCast(Expr):
    """Inserted during semantic analysis for automatic int -> float widening."""

    expr: Expr = field(default_factory=lambda: LiteralExpr(0, None, "int", 0))  # type: ignore
    from_type: str = "int"
    to_type: str = "float"

    def children(self) -> list[ASTNode]:
        return [self.expr]

    def to_dict(self) -> dict[str, Any]:
        d = super().to_dict()
        d["expr"] = self.expr.to_dict()
        d["from_type"] = self.from_type
        d["to_type"] = self.to_type
        d["inferred_type"] = self.to_type
        return d


@dataclass
class CallExpr(Expr):
    callee: str = ""
    args: list[Expr] = field(default_factory=list)
    callee_span: Span | None = None

    def children(self) -> list[ASTNode]:
        return list(self.args)

    def to_dict(self) -> dict[str, Any]:
        d = super().to_dict()
        d["callee"] = self.callee
        d["args"] = [a.to_dict() for a in self.args]
        d["inferred_type"] = self.inferred_type
        return d
