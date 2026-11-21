"""Directed Acyclic Graph (DAG) for Expressions and Basic Blocks.

Implements value numbering for common subexpression elimination (CSE)
and efficient code generation as specified in:
- docs/08_AST_DAG_SDD_SDT_SPECIFICATION.md §4
- Dragon Book (Aho, Lam, Sethi, Ullman) §6.1, §8.4
- Master Spec D-04
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from vela.ast.nodes import (
    ArrayAccessExpr,
    AssignStmt,
    BinaryExpr,
    Block,
    CallExpr,
    CastExpr,
    Expr,
    ImplicitCast,
    LiteralExpr,
    Stmt,
    UnaryExpr,
    VarDecl,
    VarRefExpr,
)

# Binary operators that are commutative (operands can be swapped canonically)
COMMUTATIVE_OPS = frozenset({"+", "*", "==", "!=", "&", "|", "^"})


@dataclass
class DAGNode:
    """Represents a unique computation or value in the DAG."""

    id: int
    kind: str  # "LITERAL", "VAR", "OP", "UNARY", "CAST", "ARRAY_ACCESS", "CALL"
    label: str  # Human-readable label (e.g. "+", "*", "a", "42")
    children: list[int] = field(default_factory=list)
    parents: list[int] = field(default_factory=list)
    value: Any = None
    type_name: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "kind": self.kind,
            "label": self.label,
            "children": list(self.children),
            "parents": list(self.parents),
            "value": self.value,
            "type_name": self.type_name,
        }


@dataclass
class DAGBuildStep:
    """Step in the trace of DAG construction for visualization."""

    step: int
    action: str  # "CREATE_LEAF", "CREATE_OP", "REUSE"
    signature: str
    node_id: int
    reused: bool
    detail: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "step": self.step,
            "action": self.action,
            "signature": self.signature,
            "node_id": self.node_id,
            "reused": self.reused,
            "detail": self.detail,
        }


@dataclass
class DAG:
    """A Directed Acyclic Graph representing shared expressions."""

    nodes: dict[int, DAGNode] = field(default_factory=dict)
    roots: list[int] = field(default_factory=list)
    var_map: dict[str, int] = field(default_factory=dict)
    trace: list[DAGBuildStep] = field(default_factory=list)
    tree_node_count: int = 0

    @property
    def dag_node_count(self) -> int:
        return len(self.nodes)

    @property
    def savings(self) -> int:
        return max(0, self.tree_node_count - self.dag_node_count)

    def get_node(self, node_id: int) -> DAGNode | None:
        return self.nodes.get(node_id)

    def to_dict(self) -> dict[str, Any]:
        return {
            "nodes": {str(nid): n.to_dict() for nid, n in self.nodes.items()},
            "roots": list(self.roots),
            "var_map": dict(self.var_map),
            "tree_node_count": self.tree_node_count,
            "dag_node_count": self.dag_node_count,
            "savings": self.savings,
            "trace": [s.to_dict() for s in self.trace],
        }

    def to_mermaid(self) -> str:
        """Render the DAG in Mermaid format for visual inspection."""
        lines = ["graph TD"]
        for nid, node in self.nodes.items():
            safe_label = str(node.label).replace('"', '\\"')
            lines.append(f'    n{nid}["n{nid}: {safe_label}"]')
            for child_id in node.children:
                lines.append(f"    n{nid} --> n{child_id}")
        return "\n".join(lines)


class DAGBuilder:
    """Constructs a DAG from AST expressions and statements via value numbering."""

    def __init__(self) -> None:
        self.dag = DAG()
        self._next_id = 1
        # Signature -> node_id lookup table
        self._signature_table: dict[tuple[Any, ...], int] = {}
        # Variable name -> current DAG node ID
        self._var_map: dict[str, int] = {}
        self._step_counter = 0

    def _alloc_id(self) -> int:
        nid = self._next_id
        self._next_id += 1
        return nid

    def _record_step(self, action: str, sig_key: tuple[Any, ...], node_id: int, reused: bool, detail: str) -> None:
        self._step_counter += 1
        sig_str = "(" + ", ".join(str(x) for x in sig_key) + ")"
        self.dag.trace.append(
            DAGBuildStep(
                step=self._step_counter,
                action=action,
                signature=sig_str,
                node_id=node_id,
                reused=reused,
                detail=detail,
            )
        )

    def build_expr(self, expr: Expr) -> int:
        """Add an expression to the DAG, returning its root node ID."""
        self.dag.tree_node_count += 1

        if isinstance(expr, LiteralExpr):
            sig = ("LITERAL", expr.literal_type, expr.value)
            if sig in self._signature_table:
                nid = self._signature_table[sig]
                self._record_step("REUSE", sig, nid, True, f"Reused constant literal {expr.value}")
                return nid
            nid = self._alloc_id()
            node = DAGNode(
                id=nid,
                kind="LITERAL",
                label=str(expr.value),
                value=expr.value,
                type_name=expr.literal_type,
            )
            self.dag.nodes[nid] = node
            self._signature_table[sig] = nid
            self._record_step("CREATE_LEAF", sig, nid, False, f"Created constant literal {expr.value}")
            return nid

        if isinstance(expr, VarRefExpr):
            # Check if this variable already has a current value in this block
            if expr.name in self._var_map:
                nid = self._var_map[expr.name]
                sig = ("VAR_LOOKUP", expr.name, nid)
                self._record_step("REUSE", sig, nid, True, f"Referenced variable '{expr.name}' from current block")
                return nid
            # Unbound / initial variable leaf
            sig = ("VAR_LEAF", expr.name)
            if sig in self._signature_table:
                nid = self._signature_table[sig]
                self._record_step("REUSE", sig, nid, True, f"Reused initial variable leaf '{expr.name}'")
                return nid
            nid = self._alloc_id()
            node = DAGNode(id=nid, kind="VAR", label=expr.name)
            self.dag.nodes[nid] = node
            self._signature_table[sig] = nid
            self._var_map[expr.name] = nid
            self._record_step("CREATE_LEAF", sig, nid, False, f"Created initial variable leaf '{expr.name}'")
            return nid

        if isinstance(expr, BinaryExpr):
            left_id = self.build_expr(expr.left)
            right_id = self.build_expr(expr.right)

            # Canonical order for commutative operators
            if expr.op in COMMUTATIVE_OPS:
                child_tuple = (min(left_id, right_id), max(left_id, right_id))
            else:
                child_tuple = (left_id, right_id)

            sig = ("OP", expr.op, child_tuple)
            if sig in self._signature_table:
                nid = self._signature_table[sig]
                self._record_step(
                    "REUSE",
                    sig,
                    nid,
                    True,
                    f"Reused common subexpression '{expr.op}' with operands {child_tuple}",
                )
                return nid

            nid = self._alloc_id()
            node = DAGNode(
                id=nid,
                kind="OP",
                label=expr.op,
                children=[left_id, right_id],
            )
            self.dag.nodes[nid] = node
            self.dag.nodes[left_id].parents.append(nid)
            self.dag.nodes[right_id].parents.append(nid)
            self._signature_table[sig] = nid
            self._record_step(
                "CREATE_OP",
                sig,
                nid,
                False,
                f"Created operator '{expr.op}' node with operands ({left_id}, {right_id})",
            )
            return nid

        if isinstance(expr, UnaryExpr):
            child_id = self.build_expr(expr.operand)
            sig = ("UNARY", expr.op, (child_id,))
            if sig in self._signature_table:
                nid = self._signature_table[sig]
                self._record_step("REUSE", sig, nid, True, f"Reused unary op '{expr.op}' on node {child_id}")
                return nid
            nid = self._alloc_id()
            node = DAGNode(id=nid, kind="UNARY", label=expr.op, children=[child_id])
            self.dag.nodes[nid] = node
            self.dag.nodes[child_id].parents.append(nid)
            self._signature_table[sig] = nid
            self._record_step("CREATE_OP", sig, nid, False, f"Created unary op '{expr.op}' on node {child_id}")
            return nid

        if isinstance(expr, (CastExpr, ImplicitCast)):
            target_type = expr.target_type if isinstance(expr, CastExpr) else expr.to_type
            child_id = self.build_expr(expr.expr)
            sig = ("CAST", target_type, (child_id,))
            if sig in self._signature_table:
                nid = self._signature_table[sig]
                self._record_step("REUSE", sig, nid, True, f"Reused cast to {target_type} on node {child_id}")
                return nid
            nid = self._alloc_id()
            label = f"as {target_type}"
            node = DAGNode(id=nid, kind="CAST", label=label, children=[child_id], type_name=target_type)
            self.dag.nodes[nid] = node
            self.dag.nodes[child_id].parents.append(nid)
            self._signature_table[sig] = nid
            self._record_step("CREATE_OP", sig, nid, False, f"Created cast to {target_type} on node {child_id}")
            return nid

        if isinstance(expr, ArrayAccessExpr):
            idx_id = self.build_expr(expr.index)
            sig = ("ARRAY_ACCESS", expr.name, (idx_id,))
            if sig in self._signature_table:
                nid = self._signature_table[sig]
                self._record_step("REUSE", sig, nid, True, f"Reused array access {expr.name}[node {idx_id}]")
                return nid
            nid = self._alloc_id()
            label = f"{expr.name}[]"
            node = DAGNode(id=nid, kind="ARRAY_ACCESS", label=label, children=[idx_id])
            self.dag.nodes[nid] = node
            self.dag.nodes[idx_id].parents.append(nid)
            self._signature_table[sig] = nid
            self._record_step("CREATE_OP", sig, nid, False, f"Created array access {expr.name}[node {idx_id}]")
            return nid

        if isinstance(expr, CallExpr):
            arg_ids = [self.build_expr(arg) for arg in expr.args]
            # Calls can have side effects, but pure call value-numbering traces args
            sig = ("CALL", expr.callee, tuple(arg_ids))
            if sig in self._signature_table:
                nid = self._signature_table[sig]
                self._record_step("REUSE", sig, nid, True, f"Reused call {expr.callee} with args {arg_ids}")
                return nid
            nid = self._alloc_id()
            label = f"{expr.callee}()"
            node = DAGNode(id=nid, kind="CALL", label=label, children=arg_ids)
            self.dag.nodes[nid] = node
            for aid in arg_ids:
                self.dag.nodes[aid].parents.append(nid)
            self._signature_table[sig] = nid
            self._record_step("CREATE_OP", sig, nid, False, f"Created call {expr.callee}() with args {arg_ids}")
            return nid

        # Fallback for unrecognized expression types
        nid = self._alloc_id()
        node = DAGNode(id=nid, kind="EXPR", label=type(expr).__name__)
        self.dag.nodes[nid] = node
        return nid

    def add_expression(self, expr: Expr) -> int:
        """Add an expression and register it as a root in the DAG."""
        root_id = self.build_expr(expr)
        if root_id not in self.dag.roots:
            self.dag.roots.append(root_id)
        self.dag.var_map = dict(self._var_map)
        return root_id

    def add_assignment(self, var_name: str, expr: Expr) -> int:
        """Process an assignment: evaluate RHS expression and bind variable name to that node."""
        rhs_id = self.build_expr(expr)
        self._var_map[var_name] = rhs_id
        self.dag.var_map[var_name] = rhs_id
        if rhs_id not in self.dag.roots:
            self.dag.roots.append(rhs_id)
        return rhs_id

    def build_statements(self, statements: list[Stmt]) -> DAG:
        """Build DAG for a sequence of basic block statements."""
        for stmt in statements:
            if isinstance(stmt, VarDecl):
                if stmt.init is not None:
                    self.add_assignment(stmt.name, stmt.init)
            elif isinstance(stmt, AssignStmt):
                if isinstance(stmt.target, VarRefExpr):
                    if stmt.op == "=" and stmt.value is not None:
                        self.add_assignment(stmt.target.name, stmt.value)
                    elif stmt.value is not None:
                        # Compound assignment e.g. x += y -> x = x + y
                        arith_op = stmt.op[:-1]  # remove '='
                        expanded = BinaryExpr(
                            id=0,
                            span=stmt.span,
                            left=VarRefExpr(id=0, span=stmt.span, name=stmt.target.name),
                            op=arith_op,
                            right=stmt.value,
                        )
                        self.add_assignment(stmt.target.name, expanded)
            elif hasattr(stmt, "expressions"):  # ShowStmt
                for ex in stmt.expressions:
                    self.add_expression(ex)
            elif hasattr(stmt, "expr"):  # CallStmt
                self.add_expression(stmt.expr)

        self.dag.var_map = dict(self._var_map)
        return self.dag


def build_expression_dag(expressions: list[Expr]) -> DAG:
    """Helper to build a DAG from a list of expressions."""
    builder = DAGBuilder()
    for expr in expressions:
        builder.add_expression(expr)
    return builder.dag


def build_block_dag(block: Block) -> DAG:
    """Helper to build a DAG from a basic block."""
    builder = DAGBuilder()
    return builder.build_statements(block.statements)
