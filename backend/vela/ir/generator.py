"""Three-Address Code (TAC) generator.

Lowers validated Vela ASTs into machine-independent Three-Address Code.
Defined per:
- docs/09_TAC_SPECIFICATION.md
- Master Spec P5-01..P5-11
"""

from __future__ import annotations

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
from vela.common.source import Span
from vela.ir.tac import (
    Constant,
    Label,
    TACInstruction,
    TACOperand,
    TACProgram,
    Temporary,
    Variable,
)

OP_MAP = {
    "+": "ADD",
    "-": "SUB",
    "*": "MUL",
    "/": "DIV",
    "%": "MOD",
    "<": "LT",
    "<=": "LE",
    ">": "GT",
    ">=": "GE",
    "==": "EQ",
    "!=": "NE",
}


class TACGenerator:
    """Lowers AST Program into linear Three-Address Code."""

    def __init__(self) -> None:
        self._temp_counter = 0
        self._label_counter = 0
        self._instructions: list[TACInstruction] = []
        # Stack of (break_target, continue_target) for loops
        self._loop_stack: list[tuple[Label, Label]] = []
        # General break target stack for loops and switches
        self._break_stack: list[Label] = []

    def new_temp(self, type_name: str = "any") -> Temporary:
        self._temp_counter += 1
        return Temporary(id=self._temp_counter, type_name=type_name)

    def new_label(self, prefix: str = "L") -> Label:
        self._label_counter += 1
        return Label(name=f"{prefix}_{self._label_counter}")

    def emit(
        self,
        opcode: str,
        arg1: TACOperand | None = None,
        arg2: TACOperand | None = None,
        result: TACOperand | None = None,
        span: Span | None = None,
        ast_id: int = 0,
        rule_id: str = "TAC-RAW",
    ) -> TACInstruction:
        instr = TACInstruction(
            opcode=opcode,
            arg1=arg1,
            arg2=arg2,
            result=result,
            src_span=span or Span.zero(),
            ast_id=ast_id,
            rule_id=rule_id,
        )
        self._instructions.append(instr)
        return instr

    def generate(self, program: Program) -> TACProgram:
        """Lower complete AST program to TAC."""
        self._instructions.clear()
        self._temp_counter = 0
        self._label_counter = 0
        self._loop_stack.clear()
        self._break_stack.clear()

        global_vars = [item for item in program.items if isinstance(item, VarDecl)]
        func_decls = [item for item in program.items if isinstance(item, FuncDecl)]

        # 1. Startup prologue: initialize global variables in order, then call main()
        start_label = Label("L_start")
        self.emit("LABEL", None, None, start_label, rule_id="TAC-STARTUP")
        for g_var in global_vars:
            self._lower_var_decl(g_var, is_global=True)

        # Call main if present
        has_main = any(f.name == "main" for f in func_decls)
        if has_main:
            self.emit(
                "CALL",
                Label("main"),
                Constant(0, "int"),
                None,
                rule_id="TAC-MAIN-CALL",
            )
        self.emit("RETURN", None, None, None, rule_id="TAC-STARTUP-HALT")

        # 2. Lower each function
        for func in func_decls:
            self._lower_func(func)

        return TACProgram(instructions=list(self._instructions))

    def _lower_func(self, func: FuncDecl) -> None:
        span = func.span
        self.emit(
            "FUNC_BEGIN",
            None,
            None,
            Label(func.name),
            span=span,
            ast_id=func.id,
            rule_id="TAC-FUNC-BEGIN",
        )

        for stmt in func.body.statements:
            self._lower_stmt(stmt)

        # Ensure return at end of function
        if not self._instructions or self._instructions[-1].opcode != "RETURN":
            self.emit(
                "RETURN",
                None,
                None,
                None,
                span=span,
                ast_id=func.id,
                rule_id="TAC-IMPLICIT-RET",
            )

        self.emit(
            "FUNC_END",
            None,
            None,
            Label(func.name),
            span=span,
            ast_id=func.id,
            rule_id="TAC-FUNC-END",
        )

    def _lower_stmt(self, stmt: Stmt) -> None:
        span = stmt.span
        ast_id = stmt.id

        if isinstance(stmt, VarDecl):
            self._lower_var_decl(stmt, is_global=False)

        elif isinstance(stmt, AssignStmt):
            self._lower_assign_stmt(stmt)

        elif isinstance(stmt, IfStmt):
            self._lower_if_stmt(stmt)

        elif isinstance(stmt, SwitchStmt):
            self._lower_switch_stmt(stmt)

        elif isinstance(stmt, WhileStmt):
            self._lower_while_stmt(stmt)

        elif isinstance(stmt, DoWhileStmt):
            self._lower_dowhile_stmt(stmt)

        elif isinstance(stmt, ForStmt):
            self._lower_for_stmt(stmt)

        elif isinstance(stmt, BreakStmt):
            if self._break_stack:
                self.emit("JUMP", None, None, self._break_stack[-1], span=span, ast_id=ast_id, rule_id="TAC-BREAK")

        elif isinstance(stmt, ContinueStmt):
            if self._loop_stack:
                self.emit(
                    "JUMP",
                    None,
                    None,
                    self._loop_stack[-1][1],
                    span=span,
                    ast_id=ast_id,
                    rule_id="TAC-CONTINUE",
                )

        elif isinstance(stmt, ReturnStmt):
            val = self._lower_expr(stmt.value) if stmt.value is not None else None
            self.emit("RETURN", val, None, None, span=span, ast_id=ast_id, rule_id="TAC-RETURN")

        elif isinstance(stmt, ShowStmt):
            for ex in stmt.expressions:
                val = self._lower_expr(ex)
                self.emit("SHOW", val, None, None, span=ex.span, ast_id=ex.id, rule_id="TAC-SHOW")
            self.emit("SHOW_NL", None, None, None, span=span, ast_id=ast_id, rule_id="TAC-SHOW-NL")

        elif isinstance(stmt, ReadStmt):
            if isinstance(stmt.target, VarRefExpr):
                self.emit(
                    "READ",
                    None,
                    None,
                    Variable(stmt.target.name),
                    span=span,
                    ast_id=ast_id,
                    rule_id="TAC-READ",
                )
            elif isinstance(stmt.target, ArrayAccessExpr):
                idx = self._lower_expr(stmt.target.index)
                t_read = self.new_temp()
                self.emit("READ", None, None, t_read, span=span, ast_id=ast_id, rule_id="TAC-READ")
                self.emit(
                    "ARRAY_SET",
                    t_read,
                    idx,
                    Variable(stmt.target.name),
                    span=span,
                    ast_id=ast_id,
                    rule_id="TAC-READ-ARRAY",
                )

        elif isinstance(stmt, CallStmt):
            self._lower_expr(stmt.expr)

    def _lower_var_decl(self, decl: VarDecl, is_global: bool) -> None:
        span = decl.span
        ast_id = decl.id
        rule_id = "TAC-GLOBAL-DECL" if is_global else "TAC-LOCAL-DECL"

        if decl.init is not None:
            init_val = self._lower_expr(decl.init)
            self.emit("ASSIGN", init_val, None, Variable(decl.name), span=span, ast_id=ast_id, rule_id=rule_id)
        elif decl.array_size is not None and decl.array_inits:
            for i, init_elem in enumerate(decl.array_inits):
                elem_val = self._lower_expr(init_elem)
                self.emit(
                    "ARRAY_SET",
                    elem_val,
                    Constant(i, "int"),
                    Variable(decl.name),
                    span=span,
                    ast_id=ast_id,
                    rule_id=rule_id,
                )

    def _lower_assign_stmt(self, stmt: AssignStmt) -> None:
        span = stmt.span
        ast_id = stmt.id

        if isinstance(stmt.target, VarRefExpr):
            var_op = Variable(stmt.target.name)
            if stmt.op == "=" and stmt.value is not None:
                val = self._lower_expr(stmt.value)
                self.emit("ASSIGN", val, None, var_op, span=span, ast_id=ast_id, rule_id="TAC-ASSIGN")
            elif stmt.value is not None:
                # Compound assignment: +=, -=, *=, /=, %=
                val = self._lower_expr(stmt.value)
                op_char = stmt.op[:-1]
                op_name = OP_MAP[op_char]
                t = self.new_temp()
                self.emit(op_name, var_op, val, t, span=span, ast_id=ast_id, rule_id="TAC-COMPOUND-ASSIGN")
                self.emit("ASSIGN", t, None, var_op, span=span, ast_id=ast_id, rule_id="TAC-ASSIGN")

        elif isinstance(stmt.target, ArrayAccessExpr):
            arr_var = Variable(stmt.target.name)
            idx = self._lower_expr(stmt.target.index)
            if stmt.op == "=" and stmt.value is not None:
                val = self._lower_expr(stmt.value)
                self.emit("ARRAY_SET", val, idx, arr_var, span=span, ast_id=ast_id, rule_id="TAC-ARRAY-SET")
            elif stmt.value is not None:
                cur = self.new_temp()
                self.emit("ARRAY_GET", arr_var, idx, cur, span=span, ast_id=ast_id, rule_id="TAC-ARRAY-GET")
                val = self._lower_expr(stmt.value)
                op_char = stmt.op[:-1]
                op_name = OP_MAP[op_char]
                res = self.new_temp()
                self.emit(op_name, cur, val, res, span=span, ast_id=ast_id, rule_id="TAC-COMPOUND-ARRAY-SET")
                self.emit("ARRAY_SET", res, idx, arr_var, span=span, ast_id=ast_id, rule_id="TAC-ARRAY-SET")

    def _lower_if_stmt(self, stmt: IfStmt) -> None:
        cond_val = self._lower_expr(stmt.condition)
        l_else = self.new_label("L_else")
        l_exit = self.new_label("L_if_exit")

        if stmt.else_stmt is None:
            self.emit("JUMP_IF_FALSE", cond_val, None, l_exit, span=stmt.span, ast_id=stmt.id, rule_id="TAC-IF-THEN")
            for s in stmt.then_block.statements:
                self._lower_stmt(s)
            self.emit("LABEL", None, None, l_exit, rule_id="TAC-LABEL")
        else:
            self.emit("JUMP_IF_FALSE", cond_val, None, l_else, span=stmt.span, ast_id=stmt.id, rule_id="TAC-IF-ELSE")
            for s in stmt.then_block.statements:
                self._lower_stmt(s)
            self.emit("JUMP", None, None, l_exit, rule_id="TAC-JUMP")
            self.emit("LABEL", None, None, l_else, rule_id="TAC-LABEL")
            if isinstance(stmt.else_stmt, Block):
                for s in stmt.else_stmt.statements:
                    self._lower_stmt(s)
            elif isinstance(stmt.else_stmt, IfStmt):
                self._lower_if_stmt(stmt.else_stmt)
            self.emit("LABEL", None, None, l_exit, rule_id="TAC-LABEL")

    def _lower_switch_stmt(self, stmt: SwitchStmt) -> None:
        expr_val = self._lower_expr(stmt.expr)
        l_exit = self.new_label("L_switch_exit")
        self._break_stack.append(l_exit)

        for clause in stmt.cases:
            l_case_body = self.new_label("L_case")
            l_next_case = self.new_label("L_case_next")

            for lbl in clause.labels:
                t_cmp = self.new_temp("bool")
                lbl_type = "int" if isinstance(lbl, int) else ("char" if len(lbl) == 1 else "string")
                lbl_const = Constant(lbl, lbl_type)
                self.emit("EQ", expr_val, lbl_const, t_cmp, span=stmt.span, ast_id=stmt.id, rule_id="TAC-SWITCH-EQ")
                self.emit("JUMP_IF", t_cmp, None, l_case_body, rule_id="TAC-SWITCH-JUMP")

            # Did not match this clause's labels -> skip to next clause check
            self.emit("JUMP", None, None, l_next_case, rule_id="TAC-JUMP")
            self.emit("LABEL", None, None, l_case_body, rule_id="TAC-LABEL")
            for s in clause.body:
                self._lower_stmt(s)
            # No fall-through: jump to exit
            self.emit("JUMP", None, None, l_exit, rule_id="TAC-SWITCH-BREAK")
            self.emit("LABEL", None, None, l_next_case, rule_id="TAC-LABEL")

        if stmt.default_case is not None:
            default_stmts = (
                stmt.default_case.statements if isinstance(stmt.default_case, Block) else stmt.default_case
            )
            for s in default_stmts:
                self._lower_stmt(s)
            self.emit("JUMP", None, None, l_exit, rule_id="TAC-SWITCH-BREAK")

        self.emit("LABEL", None, None, l_exit, rule_id="TAC-LABEL")
        self._break_stack.pop()

    def _lower_while_stmt(self, stmt: WhileStmt) -> None:
        l_cond = self.new_label("L_while_cond")
        l_exit = self.new_label("L_while_exit")

        self._loop_stack.append((l_exit, l_cond))
        self._break_stack.append(l_exit)

        self.emit("LABEL", None, None, l_cond, rule_id="TAC-LABEL")
        cond_val = self._lower_expr(stmt.condition)
        self.emit("JUMP_IF_FALSE", cond_val, None, l_exit, span=stmt.span, ast_id=stmt.id, rule_id="TAC-WHILE")

        for s in stmt.body.statements:
            self._lower_stmt(s)

        self.emit("JUMP", None, None, l_cond, rule_id="TAC-JUMP")
        self.emit("LABEL", None, None, l_exit, rule_id="TAC-LABEL")

        self._break_stack.pop()
        self._loop_stack.pop()

    def _lower_dowhile_stmt(self, stmt: DoWhileStmt) -> None:
        l_start = self.new_label("L_dowhile_start")
        l_cond = self.new_label("L_dowhile_cond")
        l_exit = self.new_label("L_dowhile_exit")

        self._loop_stack.append((l_exit, l_cond))
        self._break_stack.append(l_exit)

        self.emit("LABEL", None, None, l_start, rule_id="TAC-LABEL")
        for s in stmt.body.statements:
            self._lower_stmt(s)

        self.emit("LABEL", None, None, l_cond, rule_id="TAC-LABEL")
        cond_val = self._lower_expr(stmt.condition)
        self.emit("JUMP_IF", cond_val, None, l_start, span=stmt.span, ast_id=stmt.id, rule_id="TAC-DOWHILE")
        self.emit("LABEL", None, None, l_exit, rule_id="TAC-LABEL")

        self._break_stack.pop()
        self._loop_stack.pop()

    def _lower_for_stmt(self, stmt: ForStmt) -> None:
        l_cond = self.new_label("L_for_cond")
        l_update = self.new_label("L_for_update")
        l_exit = self.new_label("L_for_exit")

        if stmt.init is not None:
            self._lower_stmt(stmt.init)

        self._loop_stack.append((l_exit, l_update))
        self._break_stack.append(l_exit)

        self.emit("LABEL", None, None, l_cond, rule_id="TAC-LABEL")
        if stmt.condition is not None:
            cond_val = self._lower_expr(stmt.condition)
            self.emit("JUMP_IF_FALSE", cond_val, None, l_exit, span=stmt.span, ast_id=stmt.id, rule_id="TAC-FOR-COND")

        for s in stmt.body.statements:
            self._lower_stmt(s)

        self.emit("LABEL", None, None, l_update, rule_id="TAC-LABEL")
        if stmt.update is not None:
            self._lower_stmt(stmt.update)

        self.emit("JUMP", None, None, l_cond, rule_id="TAC-JUMP")
        self.emit("LABEL", None, None, l_exit, rule_id="TAC-LABEL")

        self._break_stack.pop()
        self._loop_stack.pop()

    def _lower_expr(self, expr: Expr) -> TACOperand:
        span = expr.span
        ast_id = expr.id

        if isinstance(expr, LiteralExpr):
            return Constant(value=expr.value, type_name=expr.literal_type)

        if isinstance(expr, VarRefExpr):
            return Variable(name=expr.name)

        if isinstance(expr, UnaryExpr):
            op_val = self._lower_expr(expr.operand)
            t = self.new_temp()
            if expr.op == "-":
                self.emit("NEG", op_val, None, t, span=span, ast_id=ast_id, rule_id="TAC-NEG")
            elif expr.op in ("not", "!"):
                self.emit("NOT", op_val, None, t, span=span, ast_id=ast_id, rule_id="TAC-NOT")
            return t

        if isinstance(expr, (CastExpr, ImplicitCast)):
            op_val = self._lower_expr(expr.expr)
            target_type = expr.target_type if isinstance(expr, CastExpr) else expr.to_type
            t = self.new_temp(target_type)
            self.emit(
                "CAST",
                op_val,
                Constant(target_type, "type"),
                t,
                span=span,
                ast_id=ast_id,
                rule_id="TAC-CAST",
            )
            return t

        if isinstance(expr, ArrayAccessExpr):
            idx_val = self._lower_expr(expr.index)
            t = self.new_temp()
            self.emit(
                "ARRAY_GET",
                Variable(expr.name),
                idx_val,
                t,
                span=span,
                ast_id=ast_id,
                rule_id="TAC-ARRAY-GET",
            )
            return t

        if isinstance(expr, CallExpr):
            arg_ops = [self._lower_expr(arg) for arg in expr.args]
            for arg_op in arg_ops:
                self.emit("PARAM", arg_op, None, None, span=span, ast_id=ast_id, rule_id="TAC-PARAM")
            t = self.new_temp()
            self.emit(
                "CALL",
                Label(expr.callee),
                Constant(len(arg_ops), "int"),
                t,
                span=span,
                ast_id=ast_id,
                rule_id="TAC-CALL",
            )
            return t

        if isinstance(expr, BinaryExpr):
            if expr.op == "and":
                t_res = self.new_temp("bool")
                l_false = self.new_label("L_and_false")
                l_end = self.new_label("L_and_end")
                left_val = self._lower_expr(expr.left)
                self.emit(
                    "JUMP_IF_FALSE",
                    left_val,
                    None,
                    l_false,
                    span=span,
                    ast_id=ast_id,
                    rule_id="TAC-SHORT-CIRCUIT-AND",
                )
                right_val = self._lower_expr(expr.right)
                self.emit(
                    "ASSIGN",
                    right_val,
                    None,
                    t_res,
                    span=span,
                    ast_id=ast_id,
                    rule_id="TAC-SHORT-CIRCUIT-AND",
                )
                self.emit("JUMP", None, None, l_end, rule_id="TAC-JUMP")
                self.emit("LABEL", None, None, l_false, rule_id="TAC-LABEL")
                self.emit(
                    "ASSIGN",
                    Constant(False, "bool"),
                    None,
                    t_res,
                    span=span,
                    ast_id=ast_id,
                    rule_id="TAC-SHORT-CIRCUIT-AND",
                )
                self.emit("LABEL", None, None, l_end, rule_id="TAC-LABEL")
                return t_res

            if expr.op == "or":
                t_res = self.new_temp("bool")
                l_true = self.new_label("L_or_true")
                l_end = self.new_label("L_or_end")
                left_val = self._lower_expr(expr.left)
                self.emit(
                    "JUMP_IF",
                    left_val,
                    None,
                    l_true,
                    span=span,
                    ast_id=ast_id,
                    rule_id="TAC-SHORT-CIRCUIT-OR",
                )
                right_val = self._lower_expr(expr.right)
                self.emit(
                    "ASSIGN",
                    right_val,
                    None,
                    t_res,
                    span=span,
                    ast_id=ast_id,
                    rule_id="TAC-SHORT-CIRCUIT-OR",
                )
                self.emit("JUMP", None, None, l_end, rule_id="TAC-JUMP")
                self.emit("LABEL", None, None, l_true, rule_id="TAC-LABEL")
                self.emit(
                    "ASSIGN",
                    Constant(True, "bool"),
                    None,
                    t_res,
                    span=span,
                    ast_id=ast_id,
                    rule_id="TAC-SHORT-CIRCUIT-OR",
                )
                self.emit("LABEL", None, None, l_end, rule_id="TAC-LABEL")
                return t_res

            # Arithmetic / Relational operators
            left_val = self._lower_expr(expr.left)
            right_val = self._lower_expr(expr.right)
            op_name = OP_MAP.get(expr.op, "RAW_OP")
            t_res = self.new_temp()
            self.emit(op_name, left_val, right_val, t_res, span=span, ast_id=ast_id, rule_id="TAC-BINOP")
            return t_res

        # Fallback constant
        return Constant(0, "int")
