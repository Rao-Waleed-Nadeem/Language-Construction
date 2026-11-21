"""Vela Semantic Checker and Type Validator.

Per doc 01 §4–§9, §12, §16.3 and doc 07:
- Two-pass validation: declaration hoisting followed by statement & expression validation.
- Type checking, operator typing, implicit widening (inserting ImplicitCast nodes).
- All-paths-return structural verification.
- Enforces array bounds on literal indices (VL-SEM-022) and array limits (VL-SEM-016, VL-SEM-017).
- Enforces switch rules (VL-SEM-012, VL-SEM-013), loop control (VL-SEM-011), void function restrictions (VL-SEM-023).
- Generates UI tables (checks_table, conversion_table, overload_table).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from vela.ast.nodes import (
    ArrayAccessExpr,
    AssignStmt,
    BinaryExpr,
    Block,
    BreakStmt,
    CallExpr,
    CallStmt,
    CastExpr,
    ContinueStmt,
    DoWhileStmt,
    Expr,
    ForStmt,
    FuncDecl,
    IfStmt,
    ImplicitCast,
    LiteralExpr,
    Program,
    ReadStmt,
    ReturnStmt,
    ShowStmt,
    Stmt,
    SwitchStmt,
    UnaryExpr,
    VarDecl,
    VarRefExpr,
    WhileStmt,
)
from vela.common.diagnostics import Diagnostic
from vela.common.source import Span
from vela.semantic.returns import block_returns
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
    VelaType,
    can_explicit_cast,
    can_implicit_widen,
    get_binary_op_result_type,
    get_type_by_name,
    get_unary_op_result_type,
    is_assignable,
)


@dataclass
class CheckResult:
    """Outcome of semantic analysis."""

    ast: Program
    symbol_table: SymbolTable
    diagnostics: list[Diagnostic] = field(default_factory=list)
    checks_table: list[dict[str, Any]] = field(default_factory=list)
    conversion_table: list[dict[str, Any]] = field(default_factory=list)
    overload_table: list[dict[str, Any]] = field(default_factory=list)

    @property
    def success(self) -> bool:
        return not any(d.severity == "error" for d in self.diagnostics)

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "diagnostics": [d.to_dict() for d in self.diagnostics],
            "scope_tree": self.symbol_table.get_scope_tree(),
            "events": [e.to_dict() for e in self.symbol_table.events],
            "checks_table": self.checks_table,
            "conversion_table": self.conversion_table,
            "overload_table": self.overload_table,
        }


class SemanticChecker:
    """Production semantic analysis engine."""

    def __init__(self, program: Program) -> None:
        self.program: Program = program
        self.symbol_table: SymbolTable = SymbolTable()
        self.diagnostics: list[Diagnostic] = []
        self.loop_depth: int = 0
        self.switch_depth: int = 0
        self.current_function: FuncDecl | None = None
        self._next_ast_id_counter: int = 100000

    def _next_ast_id(self) -> int:
        self._next_ast_id_counter += 1
        return self._next_ast_id_counter

    def _callee_span(self, expr: Expr) -> Span | None:
        if isinstance(expr, CallExpr):
            return expr.callee_span or Span.point(expr.span.start)
        if isinstance(expr, (ImplicitCast, CastExpr)):
            return self._callee_span(expr.expr)
        if isinstance(expr, UnaryExpr):
            return self._callee_span(expr.operand)
        return None

    def check(self) -> CheckResult:
        """Execute full semantic analysis and return CheckResult."""
        # Pass 1: Collect top-level declarations (functions and global variables)
        self._pass1_collect_declarations()

        # Pass 2: Check global initializers and verify 'main' function
        self._pass2_check_globals_and_main()

        # Pass 3: Validate function bodies
        for item in self.program.items:
            if isinstance(item, FuncDecl):
                self._check_function(item)

        # Pass 4: Unused local variable analysis
        self._check_unused_variables()

        return CheckResult(
            ast=self.program,
            symbol_table=self.symbol_table,
            diagnostics=self.diagnostics,
            checks_table=self._build_checks_table(),
            conversion_table=self._build_conversion_table(),
            overload_table=self._build_overload_table(),
        )

    # ---- Pass 1: Declaration Collection ----

    def _pass1_collect_declarations(self) -> None:
        for item in self.program.items:
            if isinstance(item, FuncDecl):
                name = item.name
                param_types: list[VelaType] = []
                for p in item.params:
                    inner = get_type_by_name(p.type_name)
                    ptype = ArrayType(inner) if p.is_array else inner
                    param_types.append(ptype)
                ret_type = get_type_by_name(item.return_type) if item.return_type else None

                sym = Symbol(
                    name=name,
                    symbol_type=ret_type or VOID,
                    kind="func",
                    scope_id=self.symbol_table.root_scope.id,
                    decl_span=item.name_span or item.span,
                    param_types=param_types,
                    return_type=ret_type,
                )
                ok, existing = self.symbol_table.define(sym)
                if not ok and existing:
                    self.diagnostics.append(
                        Diagnostic.create(
                            "VL-SEM-002",
                            item.name_span or item.span,
                            f"redeclaration of function '{name}' in the same scope",
                        )
                    )

            elif isinstance(item, VarDecl):
                name = item.name
                btype = get_type_by_name(item.type_name)
                var_type = ArrayType(btype, item.array_size) if item.is_array else btype

                sym = Symbol(
                    name=name,
                    symbol_type=var_type,
                    kind="var",
                    scope_id=self.symbol_table.root_scope.id,
                    decl_span=item.name_span or item.span,
                    is_array=item.is_array,
                    array_size=item.array_size,
                )
                ok, existing = self.symbol_table.define(sym)
                if not ok and existing:
                    self.diagnostics.append(
                        Diagnostic.create(
                            "VL-SEM-002",
                            item.name_span or item.span,
                            f"redeclaration of global variable '{name}' in the same scope",
                        )
                    )

    # ---- Pass 2: Globals & Main Check ----

    def _pass2_check_globals_and_main(self) -> None:
        # 1. Check global initializers (doc 01 §5.1, §12: must be literals)
        for item in self.program.items:
            if isinstance(item, VarDecl):
                btype = get_type_by_name(item.type_name)
                if item.is_array:
                    # Array size limit: 1..10 000 (VL-SEM-017)
                    if item.array_size is not None and not (1 <= item.array_size <= 10000):
                        self.diagnostics.append(
                            Diagnostic.create(
                                "VL-SEM-017",
                                item.span,
                                f"invalid array size {item.array_size} (must be 1..10 000)",
                            )
                        )
                    # Initializer count <= size (VL-SEM-016)
                    if item.array_size is not None and len(item.array_inits) > item.array_size:
                        extra_init = item.array_inits[item.array_size]
                        self.diagnostics.append(
                            Diagnostic.create(
                                "VL-SEM-016",
                                extra_init.span,
                                f"too many array initializers: declared size {item.array_size}, got {len(item.array_inits)}",
                            )
                        )
                    # Check each initializer is a literal and matches element type
                    for idx, init_expr in enumerate(item.array_inits):
                        if not self._is_constant_literal(init_expr):
                            self.diagnostics.append(
                                Diagnostic.create(
                                    "VL-SEM-020",
                                    init_expr.span,
                                    "global array initializer element must be a literal",
                                )
                            )
                        init_t = self._check_expr(init_expr)
                        if not is_assignable(init_t, btype):
                            self.diagnostics.append(
                                Diagnostic.create(
                                    "VL-SEM-003",
                                    init_expr.span,
                                    f"type mismatch in array initializer: cannot assign {init_t.name} to {btype.name}",
                                )
                            )
                        elif can_implicit_widen(init_t, btype):
                            item.array_inits[idx] = ImplicitCast(
                                id=self._next_ast_id(),
                                span=init_expr.span,
                                expr=init_expr,
                                from_type="int",
                                to_type="float",
                            )
                else:
                    if item.init is not None:
                        # INV-SEM-18: global initializer must be a literal
                        if not self._is_constant_literal(item.init):
                            self.diagnostics.append(
                                Diagnostic.create(
                                    "VL-SEM-020",
                                    item.init.span,
                                    "global initializer must be a literal",
                                )
                            )
                        init_t = self._check_expr(item.init)
                        if not is_assignable(init_t, btype):
                            self.diagnostics.append(
                                Diagnostic.create(
                                    "VL-SEM-003",
                                    item.init.span,
                                    f"type mismatch in initialization: cannot assign {init_t.name} to {btype.name}",
                                )
                            )
                        elif can_implicit_widen(init_t, btype):
                            item.init = ImplicitCast(
                                id=self._next_ast_id(),
                                span=item.init.span,
                                expr=item.init,
                                from_type="int",
                                to_type="float",
                            )

        # 2. Check main function (INV-SEM-14)
        main_funcs = [
            it for it in self.program.items if isinstance(it, FuncDecl) and it.name == "main"
        ]
        if len(main_funcs) != 1:
            self.diagnostics.append(
                Diagnostic.create(
                    "VL-SEM-018",
                    Span.point(self.program.span.start),
                    "missing or ill-formed 'main' function; exactly one 'func main()' with no parameters and no return type is required",
                )
            )
        else:
            main_f = main_funcs[0]
            if len(main_f.params) > 0 or main_f.return_type is not None:
                self.diagnostics.append(
                    Diagnostic.create(
                        "VL-SEM-018",
                        main_f.name_span or main_f.span,
                        "'main' function must have no parameters and no return type",
                    )
                )

    def _is_constant_literal(self, expr: Expr) -> bool:
        """Check if an expression is a literal, optionally preceded by unary minus."""
        if isinstance(expr, LiteralExpr):
            return True
        return bool(isinstance(expr, UnaryExpr) and expr.op == "-" and isinstance(expr.operand, LiteralExpr))

    # ---- Function & Statement Checking ----

    def _check_function(self, func: FuncDecl) -> None:
        self.current_function = func
        func_scope = self.symbol_table.enter_scope(ScopeKind.FUNCTION, f"func_{func.name}")

        # Define parameters in the function scope
        for p in func.params:
            inner = get_type_by_name(p.type_name)
            ptype = ArrayType(inner) if p.is_array else inner
            sym = Symbol(
                name=p.name,
                symbol_type=ptype,
                kind="param",
                scope_id=func_scope.id,
                decl_span=p.span,
                is_array=p.is_array,
            )
            ok, existing = self.symbol_table.define(sym)
            if not ok and existing:
                self.diagnostics.append(
                    Diagnostic.create(
                        "VL-SEM-002",
                        p.span,
                        f"redeclaration of parameter '{p.name}' in the same scope",
                    )
                )

        # Check all-paths-return (INV-SEM-08)
        if func.return_type is not None and not block_returns(func.body):
            self.diagnostics.append(
                Diagnostic.create(
                    "VL-SEM-010",
                    func.name_span or func.span,
                    f"missing return on some path in function '{func.name}'",
                )
            )

        # Check statements in body
        for stmt in func.body.statements:
            self._check_stmt(stmt)

        self.symbol_table.exit_scope()
        self.current_function = None

    def _check_stmt(self, stmt: Stmt) -> None:
        if isinstance(stmt, VarDecl):
            self._check_local_var_decl(stmt)
        elif isinstance(stmt, AssignStmt):
            self._check_assign_stmt(stmt)
        elif isinstance(stmt, CallStmt):
            self._check_expr(stmt.expr)
        elif isinstance(stmt, IfStmt):
            self._check_if_stmt(stmt)
        elif isinstance(stmt, SwitchStmt):
            self._check_switch_stmt(stmt)
        elif isinstance(stmt, WhileStmt):
            self._check_while_stmt(stmt)
        elif isinstance(stmt, DoWhileStmt):
            self._check_do_while_stmt(stmt)
        elif isinstance(stmt, ForStmt):
            self._check_for_stmt(stmt)
        elif isinstance(stmt, ReturnStmt):
            self._check_return_stmt(stmt)
        elif isinstance(stmt, BreakStmt):
            self._check_break_stmt(stmt)
        elif isinstance(stmt, ContinueStmt):
            self._check_continue_stmt(stmt)
        elif isinstance(stmt, ShowStmt):
            self._check_show_stmt(stmt)
        elif isinstance(stmt, ReadStmt):
            self._check_read_stmt(stmt)
        elif isinstance(stmt, Block):
            self._check_block(stmt)

    def _check_local_var_decl(self, stmt: VarDecl) -> None:
        btype = get_type_by_name(stmt.type_name)
        var_type = ArrayType(btype, stmt.array_size) if stmt.is_array else btype

        sym = Symbol(
            name=stmt.name,
            symbol_type=var_type,
            kind="var",
            scope_id=self.symbol_table.current_scope.id,
            decl_span=stmt.name_span or stmt.span,
            is_array=stmt.is_array,
            array_size=stmt.array_size,
        )
        ok, existing = self.symbol_table.define(sym)
        if not ok and existing:
            self.diagnostics.append(
                Diagnostic.create(
                    "VL-SEM-002",
                    stmt.name_span or stmt.span,
                    f"redeclaration of variable '{stmt.name}' in the same scope",
                )
            )

        if stmt.is_array:
            if stmt.array_size is not None and not (1 <= stmt.array_size <= 10000):
                self.diagnostics.append(
                    Diagnostic.create(
                        "VL-SEM-017",
                        stmt.span,
                        f"invalid array size {stmt.array_size} (must be 1..10 000)",
                    )
                )
            # Initializers
            if stmt.array_size is not None and len(stmt.array_inits) > stmt.array_size:
                extra_init = stmt.array_inits[stmt.array_size]
                self.diagnostics.append(
                    Diagnostic.create(
                        "VL-SEM-016",
                        extra_init.span,
                        f"too many array initializers: expected at most {stmt.array_size}, found {len(stmt.array_inits)}",
                    )
                )
            for idx, init_expr in enumerate(stmt.array_inits):
                init_t = self._check_expr(init_expr)
                if not is_assignable(init_t, btype):
                    self.diagnostics.append(
                        Diagnostic.create(
                            "VL-SEM-003",
                            init_expr.span,
                            f"type mismatch in array initializer: cannot assign {init_t.name} to {btype.name}",
                        )
                    )
                elif can_implicit_widen(init_t, btype):
                    stmt.array_inits[idx] = ImplicitCast(
                        id=self._next_ast_id(),
                        span=init_expr.span,
                        expr=init_expr,
                        from_type="int",
                        to_type="float",
                    )
        else:
            if stmt.init is not None:
                init_t = self._check_expr(stmt.init)
                if init_t.is_void:
                    callee_sp = self._callee_span(stmt.init) or stmt.init.span
                    self.diagnostics.append(
                        Diagnostic.create(
                            "VL-SEM-023",
                            callee_sp,
                            "void function used as a value",
                        )
                    )
                elif init_t.is_array:
                    self.diagnostics.append(
                        Diagnostic.create(
                            "VL-SEM-021",
                            stmt.init.span,
                            "whole array cannot be used as a value",
                        )
                    )
                elif not is_assignable(init_t, btype):
                    self.diagnostics.append(
                        Diagnostic.create(
                            "VL-SEM-003",
                            stmt.init.span,
                            f"type mismatch in initialization: cannot assign {init_t.name} to {btype.name}",
                        )
                    )
                elif can_implicit_widen(init_t, btype):
                    stmt.init = ImplicitCast(
                        id=self._next_ast_id(),
                        span=stmt.init.span,
                        expr=stmt.init,
                        from_type="int",
                        to_type="float",
                    )

    def _check_assign_stmt(self, stmt: AssignStmt) -> None:
        target_type = ERROR
        if isinstance(stmt.target, VarRefExpr):
            sym = self.symbol_table.lookup(stmt.target.name)
            if sym is None:
                self.diagnostics.append(
                    Diagnostic.create(
                        "VL-SEM-001",
                        stmt.target.span,
                        f"undeclared variable '{stmt.target.name}'",
                    )
                )
            else:
                self.symbol_table.record_use(stmt.target.name, stmt.target.span)
                if sym.is_array:
                    self.diagnostics.append(
                        Diagnostic.create(
                            "VL-SEM-021",
                            stmt.target.span,
                            "whole array cannot be assigned as a value",
                        )
                    )
                target_type = sym.symbol_type

        elif isinstance(stmt.target, ArrayAccessExpr):
            sym = self.symbol_table.lookup(stmt.target.name)
            if sym is None:
                self.diagnostics.append(
                    Diagnostic.create(
                        "VL-SEM-001",
                        Span.point(stmt.target.span.start),
                        f"undeclared variable '{stmt.target.name}'",
                    )
                )
            elif not sym.is_array:
                self.diagnostics.append(
                    Diagnostic.create(
                        "VL-SEM-015",
                        Span.point(stmt.target.span.start),
                        f"indexing a non-array variable '{stmt.target.name}'",
                    )
                )
            else:
                self.symbol_table.record_use(stmt.target.name, stmt.target.span)
                idx_t = self._check_expr(stmt.target.index)
                if idx_t != INT and not idx_t.is_error:
                    self.diagnostics.append(
                        Diagnostic.create(
                            "VL-SEM-014",
                            stmt.target.index.span,
                            f"array index must be int, found {idx_t.name}",
                        )
                    )
                if isinstance(stmt.target.index, LiteralExpr) and stmt.target.index.literal_type == "int":
                    idx_val = int(stmt.target.index.value)
                    if sym.array_size is not None and not (0 <= idx_val < sym.array_size):
                        self.diagnostics.append(
                            Diagnostic.create(
                                "VL-SEM-022",
                                stmt.target.index.span,
                                f"constant index {idx_val} out of range [0..{sym.array_size - 1}]",
                            )
                        )
                target_type = sym.symbol_type.element_type

        # Check operation
        if stmt.op in ("++", "--"):
            if not target_type.is_numeric and not target_type.is_error:
                self.diagnostics.append(
                    Diagnostic.create(
                        "VL-SEM-004",
                        stmt.span,
                        f"operand of increment/decrement must be int or float, found {target_type.name}",
                    )
                )
        elif stmt.op == "=" and stmt.value is not None:
            val_t = self._check_expr(stmt.value)
            if val_t.is_void:
                callee_sp = self._callee_span(stmt.value) or stmt.value.span
                self.diagnostics.append(
                    Diagnostic.create(
                        "VL-SEM-023",
                        callee_sp,
                        "void function used as a value",
                    )
                )
            elif val_t.is_array:
                self.diagnostics.append(
                    Diagnostic.create(
                        "VL-SEM-021",
                        stmt.value.span,
                        "whole array cannot be assigned as a value",
                    )
                )
            elif not is_assignable(val_t, target_type):
                self.diagnostics.append(
                    Diagnostic.create(
                        "VL-SEM-003",
                        stmt.value.span,
                        f"type mismatch in assignment: cannot assign {val_t.name} to {target_type.name}",
                    )
                )
            elif can_implicit_widen(val_t, target_type):
                stmt.value = ImplicitCast(
                    id=self._next_ast_id(),
                    span=stmt.value.span,
                    expr=stmt.value,
                    from_type="int",
                    to_type="float",
                )
        elif stmt.op in ("+=", "-=", "*=", "/=", "%=") and stmt.value is not None:
            base_op = stmt.op[0]
            val_t = self._check_expr(stmt.value)
            res_t = get_binary_op_result_type(target_type, base_op, val_t)
            if res_t is None or res_t != target_type:
                self.diagnostics.append(
                    Diagnostic.create(
                        "VL-SEM-004",
                        stmt.span,
                        f"invalid operand types for compound assignment {stmt.op}: {target_type.name} and {val_t.name}",
                    )
                )

    def _check_if_stmt(self, stmt: IfStmt) -> None:
        cond_t = self._check_expr(stmt.condition)
        if cond_t != BOOL and not cond_t.is_error:
            self.diagnostics.append(
                Diagnostic.create(
                    "VL-SEM-005",
                    stmt.condition.span,
                    f"condition must be bool, found {cond_t.name}",
                )
            )

        self._check_block(stmt.then_block)
        if stmt.else_stmt is not None:
            if isinstance(stmt.else_stmt, Block):
                self._check_block(stmt.else_stmt)
            elif isinstance(stmt.else_stmt, IfStmt):
                self._check_stmt(stmt.else_stmt)

    def _check_switch_stmt(self, stmt: SwitchStmt) -> None:
        expr_t = self._check_expr(stmt.expr)
        if expr_t not in (INT, CHAR) and not expr_t.is_error:
            self.diagnostics.append(
                Diagnostic.create(
                    "VL-SEM-013",
                    stmt.expr.span,
                    f"switch expression must be int or char, found {expr_t.name}",
                )
            )

        self.switch_depth += 1
        seen_labels: set[int | str] = set()

        for clause in stmt.cases:
            for idx, label in enumerate(clause.labels):
                label_sp = (
                    clause.label_spans[idx]
                    if idx < len(clause.label_spans)
                    else clause.span
                )
                label_t = INT if isinstance(label, int) else CHAR
                if label_t != expr_t and not expr_t.is_error:
                    self.diagnostics.append(
                        Diagnostic.create(
                            "VL-SEM-013",
                            label_sp,
                            f"switch label type {label_t.name} does not match switch expression {expr_t.name}",
                        )
                    )
                if label in seen_labels:
                    self.diagnostics.append(
                        Diagnostic.create(
                            "VL-SEM-012",
                            label_sp,
                            f"duplicate case label '{label}'",
                        )
                    )
                seen_labels.add(label)

            self.symbol_table.enter_scope(ScopeKind.CASE)
            for s in clause.body:
                self._check_stmt(s)
            self.symbol_table.exit_scope()

        if stmt.default_case is not None:
            self.symbol_table.enter_scope(ScopeKind.CASE)
            for s in stmt.default_case:
                self._check_stmt(s)
            self.symbol_table.exit_scope()

        self.switch_depth -= 1

    def _check_while_stmt(self, stmt: WhileStmt) -> None:
        self.loop_depth += 1
        cond_t = self._check_expr(stmt.condition)
        if cond_t != BOOL and not cond_t.is_error:
            self.diagnostics.append(
                Diagnostic.create(
                    "VL-SEM-005",
                    stmt.condition.span,
                    f"condition must be bool, found {cond_t.name}",
                )
            )
        self._check_block(stmt.body)
        self.loop_depth -= 1

    def _check_do_while_stmt(self, stmt: DoWhileStmt) -> None:
        self.loop_depth += 1
        self._check_block(stmt.body)
        cond_t = self._check_expr(stmt.condition)
        if cond_t != BOOL and not cond_t.is_error:
            self.diagnostics.append(
                Diagnostic.create(
                    "VL-SEM-005",
                    stmt.condition.span,
                    f"condition must be bool, found {cond_t.name}",
                )
            )
        self.loop_depth -= 1

    def _check_for_stmt(self, stmt: ForStmt) -> None:
        self.loop_depth += 1
        self.symbol_table.enter_scope(ScopeKind.FOR_HEADER)
        if stmt.init is not None:
            self._check_stmt(stmt.init)
        if stmt.condition is not None:
            cond_t = self._check_expr(stmt.condition)
            if cond_t != BOOL and not cond_t.is_error:
                self.diagnostics.append(
                    Diagnostic.create(
                        "VL-SEM-005",
                        stmt.condition.span,
                        f"condition must be bool, found {cond_t.name}",
                    )
                )
        if stmt.update is not None:
            self._check_stmt(stmt.update)

        self._check_block(stmt.body)
        self.symbol_table.exit_scope()  # exit FOR_HEADER
        self.loop_depth -= 1

    def _check_return_stmt(self, stmt: ReturnStmt) -> None:
        if self.current_function is None:
            return

        expected_ret = (
            get_type_by_name(self.current_function.return_type)
            if self.current_function.return_type
            else None
        )

        if expected_ret is None:
            if stmt.value is not None:
                self.diagnostics.append(
                    Diagnostic.create(
                        "VL-SEM-009",
                        stmt.value.span,
                        "value returned from function with no return type",
                    )
                )
        else:
            if stmt.value is None:
                self.diagnostics.append(
                    Diagnostic.create(
                        "VL-SEM-009",
                        stmt.span,
                        f"missing return value in function returning {expected_ret.name}",
                    )
                )
            else:
                val_t = self._check_expr(stmt.value)
                if not is_assignable(val_t, expected_ret):
                    self.diagnostics.append(
                        Diagnostic.create(
                            "VL-SEM-009",
                            stmt.value.span,
                            f"return type mismatch: cannot return {val_t.name} from function returning {expected_ret.name}",
                        )
                    )
                elif can_implicit_widen(val_t, expected_ret):
                    stmt.value = ImplicitCast(
                        id=self._next_ast_id(),
                        span=stmt.value.span,
                        expr=stmt.value,
                        from_type="int",
                        to_type="float",
                    )

    def _check_break_stmt(self, stmt: BreakStmt) -> None:
        if self.loop_depth == 0 and self.switch_depth == 0:
            self.diagnostics.append(
                Diagnostic.create(
                    "VL-SEM-011",
                    stmt.keyword_span or stmt.span,
                    "'break' outside loop or switch",
                )
            )

    def _check_continue_stmt(self, stmt: ContinueStmt) -> None:
        if self.loop_depth == 0:
            self.diagnostics.append(
                Diagnostic.create(
                    "VL-SEM-011",
                    stmt.keyword_span or stmt.span,
                    "'continue' outside loop",
                )
            )

    def _check_show_stmt(self, stmt: ShowStmt) -> None:
        for expr in stmt.expressions:
            t = self._check_expr(expr)
            if t.is_void:
                callee_sp = self._callee_span(expr) or expr.span
                self.diagnostics.append(
                    Diagnostic.create(
                        "VL-SEM-023",
                        callee_sp,
                        "void function used as a value",
                    )
                )
            elif t.is_array:
                self.diagnostics.append(
                    Diagnostic.create(
                        "VL-SEM-021",
                        expr.span,
                        "whole array cannot be used as a value",
                    )
                )

    def _check_read_stmt(self, stmt: ReadStmt) -> None:
        if isinstance(stmt.target, VarRefExpr):
            sym = self.symbol_table.lookup(stmt.target.name)
            if sym is None:
                self.diagnostics.append(
                    Diagnostic.create(
                        "VL-SEM-001",
                        stmt.target.span,
                        f"undeclared variable '{stmt.target.name}'",
                    )
                )
            else:
                self.symbol_table.record_use(stmt.target.name, stmt.target.span)
                if sym.is_array:
                    self.diagnostics.append(
                        Diagnostic.create(
                            "VL-SEM-021",
                            stmt.target.span,
                            "whole array cannot be read into",
                        )
                    )
        elif isinstance(stmt.target, ArrayAccessExpr):
            sym = self.symbol_table.lookup(stmt.target.name)
            if sym is None:
                self.diagnostics.append(
                    Diagnostic.create(
                        "VL-SEM-001",
                        Span.point(stmt.target.span.start),
                        f"undeclared variable '{stmt.target.name}'",
                    )
                )
            elif not sym.is_array:
                self.diagnostics.append(
                    Diagnostic.create(
                        "VL-SEM-015",
                        Span.point(stmt.target.span.start),
                        f"indexing a non-array variable '{stmt.target.name}'",
                    )
                )
            else:
                self.symbol_table.record_use(stmt.target.name, stmt.target.span)
                idx_t = self._check_expr(stmt.target.index)
                if idx_t != INT and not idx_t.is_error:
                    self.diagnostics.append(
                        Diagnostic.create(
                            "VL-SEM-014",
                            stmt.target.index.span,
                            f"array index must be int, found {idx_t.name}",
                        )
                    )

    def _check_block(self, block: Block) -> None:
        self.symbol_table.enter_scope(ScopeKind.BLOCK)
        for s in block.statements:
            self._check_stmt(s)
        self.symbol_table.exit_scope()

    # ---- Expression Checking ----

    def _check_expr(self, expr: Expr) -> VelaType:
        if isinstance(expr, LiteralExpr):
            t = get_type_by_name(expr.literal_type)
            expr.inferred_type = t.name
            return t

        if isinstance(expr, VarRefExpr):
            sym = self.symbol_table.lookup(expr.name)
            if sym is None:
                self.diagnostics.append(
                    Diagnostic.create(
                        "VL-SEM-001",
                        expr.span,
                        f"undeclared variable '{expr.name}'",
                    )
                )
                expr.inferred_type = "error"
                return ERROR
            self.symbol_table.record_use(expr.name, expr.span)
            expr.inferred_type = sym.symbol_type.name
            return sym.symbol_type

        if isinstance(expr, ArrayAccessExpr):
            sym = self.symbol_table.lookup(expr.name)
            if sym is None:
                self.diagnostics.append(
                    Diagnostic.create(
                        "VL-SEM-001",
                        Span.point(expr.span.start),
                        f"undeclared variable '{expr.name}'",
                    )
                )
                expr.inferred_type = "error"
                return ERROR
            if not sym.is_array:
                self.diagnostics.append(
                    Diagnostic.create(
                        "VL-SEM-015",
                        Span.point(expr.span.start),
                        f"indexing a non-array variable '{expr.name}'",
                    )
                )
                expr.inferred_type = "error"
                return ERROR
            self.symbol_table.record_use(expr.name, expr.span)
            idx_t = self._check_expr(expr.index)
            if idx_t != INT and not idx_t.is_error:
                self.diagnostics.append(
                    Diagnostic.create(
                        "VL-SEM-014",
                        expr.index.span,
                        f"array index must be int, found {idx_t.name}",
                    )
                )
            if isinstance(expr.index, LiteralExpr) and expr.index.literal_type == "int":
                idx_val = int(expr.index.value)
                if sym.array_size is not None and not (0 <= idx_val < sym.array_size):
                    self.diagnostics.append(
                        Diagnostic.create(
                            "VL-SEM-022",
                            expr.index.span,
                            f"constant index {idx_val} out of range [0..{sym.array_size - 1}]",
                        )
                    )
            elem_t = sym.symbol_type.element_type
            expr.inferred_type = elem_t.name
            return elem_t

        if isinstance(expr, CallExpr):
            sym = self.symbol_table.lookup(expr.callee)
            callee_sp = expr.callee_span or Span.point(expr.span.start)
            if sym is None or sym.kind != "func":
                self.diagnostics.append(
                    Diagnostic.create(
                        "VL-SEM-006",
                        callee_sp,
                        f"call to undeclared function '{expr.callee}'",
                    )
                )
                expr.inferred_type = "error"
                return ERROR

            self.symbol_table.record_use(expr.callee, callee_sp)
            if len(expr.args) != len(sym.param_types):
                self.diagnostics.append(
                    Diagnostic.create(
                        "VL-SEM-007",
                        callee_sp,
                        f"wrong number of arguments for '{expr.callee}': expected {len(sym.param_types)}, found {len(expr.args)}",
                    )
                )

            for idx, (arg, param_t) in enumerate(zip(expr.args, sym.param_types)):
                arg_t = self._check_expr(arg)
                if param_t.is_array:
                    if not isinstance(arg, VarRefExpr):
                        self.diagnostics.append(
                            Diagnostic.create(
                                "VL-SEM-008",
                                arg.span,
                                f"argument {idx + 1} must be an array variable reference",
                            )
                        )
                    else:
                        arg_sym = self.symbol_table.lookup(arg.name)
                        if (
                            arg_sym is None
                            or not arg_sym.is_array
                            or arg_sym.symbol_type.element_type != param_t.element_type
                        ):
                            self.diagnostics.append(
                                Diagnostic.create(
                                    "VL-SEM-008",
                                    arg.span,
                                    f"argument {idx + 1} type mismatch: expected {param_t.name}, found {arg_t.name}",
                                )
                            )
                else:
                    if arg_t.is_void:
                        c_sp = self._callee_span(arg) or arg.span
                        self.diagnostics.append(
                            Diagnostic.create(
                                "VL-SEM-023",
                                c_sp,
                                "void function used as a value",
                            )
                        )
                    elif arg_t.is_array:
                        self.diagnostics.append(
                            Diagnostic.create(
                                "VL-SEM-021",
                                arg.span,
                                "whole array cannot be passed as scalar argument",
                            )
                        )
                    elif not is_assignable(arg_t, param_t):
                        self.diagnostics.append(
                            Diagnostic.create(
                                "VL-SEM-008",
                                arg.span,
                                f"argument {idx + 1} type mismatch: expected {param_t.name}, found {arg_t.name}",
                            )
                        )
                    elif can_implicit_widen(arg_t, param_t):
                        expr.args[idx] = ImplicitCast(
                            id=self._next_ast_id(),
                            span=arg.span,
                            expr=arg,
                            from_type="int",
                            to_type="float",
                        )

            ret_t = sym.return_type if sym.return_type else VOID
            expr.inferred_type = ret_t.name
            return ret_t

        if isinstance(expr, BinaryExpr):
            lt = self._check_expr(expr.left)
            rt = self._check_expr(expr.right)
            if lt.is_void:
                c_sp = self._callee_span(expr.left) or expr.left.span
                self.diagnostics.append(
                    Diagnostic.create("VL-SEM-023", c_sp, "void function used as a value")
                )
            if rt.is_void:
                c_sp = self._callee_span(expr.right) or expr.right.span
                self.diagnostics.append(
                    Diagnostic.create("VL-SEM-023", c_sp, "void function used as a value")
                )

            res_t = get_binary_op_result_type(lt, expr.op, rt)
            if res_t is None:
                op_sp = expr.op_span or expr.span
                self.diagnostics.append(
                    Diagnostic.create(
                        "VL-SEM-004",
                        op_sp,
                        f"invalid operand types for operator '{expr.op}': {lt.name} and {rt.name}",
                    )
                )
                expr.inferred_type = "error"
                return ERROR

            # Implicit widening
            if lt == INT and rt == FLOAT:
                expr.left = ImplicitCast(
                    id=self._next_ast_id(),
                    span=expr.left.span,
                    expr=expr.left,
                    from_type="int",
                    to_type="float",
                )
            elif lt == FLOAT and rt == INT:
                expr.right = ImplicitCast(
                    id=self._next_ast_id(),
                    span=expr.right.span,
                    expr=expr.right,
                    from_type="int",
                    to_type="float",
                )

            expr.inferred_type = res_t.name
            return res_t

        if isinstance(expr, UnaryExpr):
            ot = self._check_expr(expr.operand)
            if ot.is_void:
                c_sp = self._callee_span(expr.operand) or expr.operand.span
                self.diagnostics.append(
                    Diagnostic.create("VL-SEM-023", c_sp, "void function used as a value")
                )
            res_t = get_unary_op_result_type(expr.op, ot)
            if res_t is None:
                self.diagnostics.append(
                    Diagnostic.create(
                        "VL-SEM-004",
                        expr.span,
                        f"invalid operand type for unary '{expr.op}': {ot.name}",
                    )
                )
                expr.inferred_type = "error"
                return ERROR
            expr.inferred_type = res_t.name
            return res_t

        if isinstance(expr, CastExpr):
            from_t = self._check_expr(expr.expr)
            to_t = get_type_by_name(expr.target_type)
            if not can_explicit_cast(from_t, to_t):
                as_sp = expr.as_span or expr.span
                self.diagnostics.append(
                    Diagnostic.create(
                        "VL-SEM-019",
                        as_sp,
                        f"invalid 'as' conversion from {from_t.name} to {to_t.name}",
                    )
                )
                expr.inferred_type = "error"
                return ERROR
            expr.inferred_type = to_t.name
            return to_t

        if isinstance(expr, ImplicitCast):
            expr.inferred_type = expr.to_type
            return get_type_by_name(expr.to_type)

        return ERROR

    # ---- Pass 4: Unused Variables Check ----

    def _check_unused_variables(self) -> None:
        for scope in self.symbol_table.all_scopes:
            if scope.kind != ScopeKind.GLOBAL:
                for sym in scope.symbols.values():
                    if sym.kind == "var" and len(sym.uses) == 0:
                        self.diagnostics.append(
                            Diagnostic.create(
                                "VL-WRN-001",
                                sym.decl_span,
                                f"unused local variable '{sym.name}'",
                                severity="warning",
                            )
                        )

    # ---- UI Metadata Tables ----

    def _build_checks_table(self) -> list[dict[str, Any]]:
        return [
            {"id": "CHK-01", "name": "Variable declarations", "status": "active"},
            {"id": "CHK-02", "name": "Type compatibility & implicit cast", "status": "active"},
            {"id": "CHK-03", "name": "Operator typing and overloading", "status": "active"},
            {"id": "CHK-04", "name": "Function call arity and types", "status": "active"},
            {"id": "CHK-05", "name": "All-paths-return structural check", "status": "active"},
            {"id": "CHK-06", "name": "Array bounds and initializers", "status": "active"},
            {"id": "CHK-07", "name": "Switch-case uniqueness and typing", "status": "active"},
            {"id": "CHK-08", "name": "Break/continue loop nesting", "status": "active"},
            {"id": "CHK-09", "name": "Global initializer literal rule", "status": "active"},
            {"id": "CHK-10", "name": "Main function signature", "status": "active"},
        ]

    def _build_conversion_table(self) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        scalars = [INT, FLOAT, CHAR, STRING, BOOL]
        for src in scalars:
            for tgt in scalars:
                rows.append({
                    "from": src.name,
                    "to": tgt.name,
                    "implicit": can_implicit_widen(src, tgt),
                    "explicit": can_explicit_cast(src, tgt),
                })
        return rows

    def _build_overload_table(self) -> list[dict[str, Any]]:
        return [
            {"operator": "+", "operands": "int, int", "result": "int", "kind": "arithmetic addition"},
            {"operator": "+", "operands": "float, float", "result": "float", "kind": "arithmetic addition"},
            {"operator": "+", "operands": "int, float", "result": "float", "kind": "widened arithmetic addition"},
            {"operator": "+", "operands": "float, int", "result": "float", "kind": "widened arithmetic addition"},
            {"operator": "+", "operands": "string, string", "result": "string", "kind": "string concatenation"},
        ]


def check_source(source_text: str, filename: str = "input.vela") -> CheckResult:
    """Helper to parse and semantically check source code."""
    from vela.parser.recursive_descent import parse_source

    parse_res = parse_source(source_text, filename)
    if not parse_res.success or parse_res.ast is None:
        return CheckResult(
            ast=parse_res.ast or Program(0, Span.point(None), []),  # type: ignore
            symbol_table=SymbolTable(),
            diagnostics=parse_res.diagnostics,
        )

    checker = SemanticChecker(parse_res.ast)
    res = checker.check()
    # Prepend any lexer/parser diagnostics if any
    res.diagnostics = parse_res.diagnostics + res.diagnostics
    return res
