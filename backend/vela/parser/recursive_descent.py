"""Hand-written Recursive-Descent Parser for Vela based on LL(1) grammar G'.

Per doc 00 §3, doc 01 §12, §13, §16.2, and doc 05:
- Implements one parsing method per nonterminal in docs/grammar/vela_ll1.bnf.
- Uses while-loops for tail nonterminals (*Tail) to avoid unnecessary recursion.
- Builds both an Abstract Syntax Tree (AST) and Concrete Syntax Tree (CST).
- Enforces nesting depth cap (VL-SYN-003 > 200).
- Emits detailed parser call traces for the Vela Studio Parser Explorer.
- Implements panic-mode error recovery for fail-soft syntax checking.
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
    CaseClause,
    CastExpr,
    ContinueStmt,
    DoWhileStmt,
    Expr,
    ForStmt,
    FuncDecl,
    IfStmt,
    LiteralExpr,
    Param,
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
from vela.common.source import SourceFile, Span
from vela.lexer.scanner import Scanner
from vela.lexer.tokens import Token
from vela.parser.parse_tree import ParseTreeNode
from vela.parser.recovery import PanicModeRecovery


class NestingLimitExceededError(Exception):
    """Raised when nesting depth exceeds limit (VL-SYN-003)."""


@dataclass(frozen=True)
class ParserCallStep:
    """Execution step recorded in the parser call trace."""

    nonterminal: str
    action: str  # "enter", "exit", "match", "loop", "error"
    depth: int
    token_index: int
    token_lexeme: str
    token_symbol: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "nonterminal": self.nonterminal,
            "action": self.action,
            "depth": self.depth,
            "token_index": self.token_index,
            "token_lexeme": self.token_lexeme,
            "token_symbol": self.token_symbol,
        }


@dataclass
class ParseResult:
    """Outcome of parsing a source file."""

    ast: Program | None
    cst: ParseTreeNode | None
    diagnostics: list[Diagnostic] = field(default_factory=list)
    call_trace: list[ParserCallStep] = field(default_factory=list)

    @property
    def success(self) -> bool:
        return not any(d.severity == "error" for d in self.diagnostics)

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "ast": self.ast.to_dict() if self.ast else None,
            "cst": self.cst.to_dict() if self.cst else None,
            "diagnostics": [d.to_dict() for d in self.diagnostics],
            "call_trace_length": len(self.call_trace),
        }


class RecursiveDescentParser:
    """Production recursive-descent parser implementing G'."""

    MAX_NESTING_DEPTH: int = 200

    def __init__(self, tokens: list[Token], source: SourceFile) -> None:
        self.tokens: list[Token] = tokens
        self.source: SourceFile = source
        self.pos: int = 0
        self.diagnostics: list[Diagnostic] = []
        self.call_trace: list[ParserCallStep] = []
        self.nesting_depth: int = 0
        self._node_id: int = 0
        self._cst_stack: list[ParseTreeNode] = []

    def _next_id(self) -> int:
        self._node_id += 1
        return self._node_id

    @property
    def current(self) -> Token:
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return self.tokens[-1]

    @property
    def is_eof(self) -> bool:
        return self.current.symbol == "$"

    def _trace(self, nonterminal: str, action: str) -> None:
        if len(self.call_trace) < 10000:
            self.call_trace.append(
                ParserCallStep(
                    nonterminal=nonterminal,
                    action=action,
                    depth=self.nesting_depth,
                    token_index=self.pos,
                    token_lexeme=self.current.lexeme,
                    token_symbol=self.current.symbol,
                )
            )

    def _enter(self, nonterminal: str) -> ParseTreeNode:
        self.nesting_depth += 1
        if self.nesting_depth > self.MAX_NESTING_DEPTH:
            span = self.current.span
            diag = Diagnostic.create("VL-SYN-003", span, "nesting too deep (> 200)")
            self.diagnostics.append(diag)
            raise NestingLimitExceededError("Nesting too deep (> 200)")

        self._trace(nonterminal, "enter")
        cst_node = ParseTreeNode(name=nonterminal, is_terminal=False)
        if self._cst_stack:
            self._cst_stack[-1].add_child(cst_node)
        self._cst_stack.append(cst_node)
        return cst_node

    def _exit(self, nonterminal: str) -> ParseTreeNode:
        self._trace(nonterminal, "exit")
        node = self._cst_stack.pop()
        self.nesting_depth -= 1
        return node

    def advance(self) -> Token:
        tok = self.current
        if not self.is_eof:
            self.pos += 1
        term_node = ParseTreeNode(
            name=tok.symbol,
            is_terminal=True,
            token=tok,
            span=tok.span,
        )
        if self._cst_stack:
            self._cst_stack[-1].add_child(term_node)
        return tok

    def match(self, expected: str, message: str | None = None) -> Token:
        if self.current.symbol == expected:
            return self.advance()

        if self.is_eof:
            code = "VL-SYN-002"
            msg = message or f"unexpected end of file; expected '{expected}'"
        else:
            code = "VL-SYN-001"
            msg = message or f"unexpected token '{self.current.lexeme}'; expected '{expected}'"

        span = self.current.span
        self.diagnostics.append(Diagnostic.create(code, span, msg))
        return Token(
            category=self.current.category,
            symbol=expected,
            lexeme="",
            value=None,
            span=span,
        )

    def error(self, message: str, code: str = "VL-SYN-001", span: Span | None = None) -> None:
        diag_span = span or self.current.span
        self.diagnostics.append(Diagnostic.create(code, diag_span, message))

    # ---- Grammar Methods (G' in docs/grammar/vela_ll1.bnf) ----

    def parse(self) -> ParseResult:
        """Parse token stream and return AST, CST, diagnostics, and call trace."""
        try:
            root_cst = self._enter("Program")
            ast = self.parse_program()
            self._exit("Program")
            return ParseResult(
                ast=ast,
                cst=root_cst,
                diagnostics=self.diagnostics,
                call_trace=self.call_trace,
            )
        except (NestingLimitExceededError, RecursionError):
            if not any(d.code == "VL-SYN-003" for d in self.diagnostics):
                self.error("nesting too deep (> 200)", code="VL-SYN-003")
            return ParseResult(
                ast=None,
                cst=self._cst_stack[0] if self._cst_stack else None,
                diagnostics=self.diagnostics,
                call_trace=self.call_trace,
            )

    def parse_program(self) -> Program:
        """Program -> TopList."""
        items: list[VarDecl | FuncDecl] = []
        start_loc = self.current.span.start

        while not self.is_eof:
            if self.current.symbol == "func":
                items.append(self.parse_func_decl())
            elif self.current.symbol == "let":
                items.append(self.parse_var_decl())
            else:
                self.error(f"expected 'func' or 'let', found '{self.current.lexeme}'")
                PanicModeRecovery.synchronize_declaration(self)

        end_loc = self.current.span.end
        return Program(id=self._next_id(), span=Span(start_loc, end_loc), items=items)

    def parse_func_decl(self) -> FuncDecl:
        """FuncDecl -> func ID ( ParamsOpt ) RetType Block."""
        self._enter("FuncDecl")
        func_tok = self.advance()  # consume 'func'

        if self.current.symbol != "ID":
            self.error(f"expected function name, found '{self.current.lexeme}'")
            name = ""
            name_span = self.current.span
        else:
            name_tok = self.advance()
            name = name_tok.lexeme
            name_span = name_tok.span

        self.match("(")
        params = self.parse_params_opt()
        self.match(")")
        ret_type = self.parse_ret_type()
        body = self.parse_block()

        self._exit("FuncDecl")
        return FuncDecl(
            id=self._next_id(),
            span=Span(func_tok.span.start, body.span.end),
            name=name,
            params=params,
            return_type=ret_type,
            body=body,
            name_span=name_span,
        )

    def parse_params_opt(self) -> list[Param]:
        """ParamsOpt -> Param ParamTail | ε."""
        self._enter("ParamsOpt")
        params: list[Param] = []
        if self.current.symbol != ")":
            params.append(self.parse_param())
            while self.current.symbol == ",":
                self.advance()  # consume ','
                params.append(self.parse_param())
        self._exit("ParamsOpt")
        return params

    def parse_param(self) -> Param:
        """Param -> ID : BaseType ArrayMark."""
        self._enter("Param")
        if self.current.symbol != "ID":
            self.error(f"expected parameter name, found '{self.current.lexeme}'")
            name_tok = self.current
        else:
            name_tok = self.advance()

        self.match(":")
        btype = self.parse_base_type()
        is_array = False
        if self.current.symbol == "[":
            self.advance()
            self.match("]")
            is_array = True

        self._exit("Param")
        return Param(
            id=self._next_id(),
            span=Span(name_tok.span.start, self.current.span.start),
            name=name_tok.lexeme,
            type_name=btype,
            is_array=is_array,
        )

    def parse_ret_type(self) -> str | None:
        """RetType -> : BaseType | ε."""
        if self.current.symbol == ":":
            self._enter("RetType")
            self.advance()
            btype = self.parse_base_type()
            self._exit("RetType")
            return btype
        return None

    def parse_base_type(self) -> str:
        """BaseType -> int | float | char | string | bool."""
        self._enter("BaseType")
        if self.current.symbol in ("int", "float", "char", "string", "bool"):
            btype = self.advance().lexeme
            self._exit("BaseType")
            return btype
        self.error(f"expected type name, found '{self.current.lexeme}'")
        self._exit("BaseType")
        return "int"

    def parse_var_decl(self) -> VarDecl:
        """VarDecl -> let ID : BaseType DeclRest ;"""
        self._enter("VarDecl")
        let_tok = self.advance()  # consume 'let'

        if self.current.symbol != "ID":
            self.error(f"expected variable identifier, found '{self.current.lexeme}'")
            name = ""
            name_span = self.current.span
        else:
            name_tok = self.advance()
            name = name_tok.lexeme
            name_span = name_tok.span

        # INV-SYN-07: expected ':' after the variable name
        if self.current.symbol != ":":
            self.error(f"expected ':' after the variable name, found '{self.current.lexeme}'")
            # If current is '=', skip to ';'
            if self.current.symbol == "=":
                while not self.is_eof and self.current.symbol != ";":
                    self.advance()
                if self.current.symbol == ";":
                    self.advance()
            self._exit("VarDecl")
            return VarDecl(
                id=self._next_id(),
                span=Span(let_tok.span.start, self.current.span.end),
                name=name,
                type_name="int",
                name_span=name_span,
            )
        self.advance()  # consume ':'

        btype = self.parse_base_type()
        array_size: int | None = None
        array_inits: list[Expr] = []
        init: Expr | None = None

        if self.current.symbol == "[":
            self.advance()
            if self.current.symbol != "INT_LIT":
                self.error(f"expected integer literal for array size, found '{self.current.lexeme}'")
                array_size = 0
            else:
                size_tok = self.advance()
                array_size = int(size_tok.value if size_tok.value is not None else size_tok.lexeme)
            self.match("]")

            if self.current.symbol == "=":
                self.advance()
                self.match("{")
                if self.current.symbol != "}":
                    array_inits.append(self.parse_expr())
                    while self.current.symbol == ",":
                        self.advance()
                        array_inits.append(self.parse_expr())
                self.match("}")
        else:
            if self.current.symbol == "=":
                self.advance()
                # INV-SYN-08: let a: int = ;
                if self.current.symbol == ";":
                    self.error("expected an expression, found ';'")
                    init = None
                else:
                    init = self.parse_expr()

        # INV-SYN-01: missing ';' is reported at next token
        if self.current.symbol != ";":
            self.error(f"expected ';', found '{self.current.lexeme}'")
            semi_span = self.current.span
        else:
            semi_tok = self.advance()
            semi_span = semi_tok.span

        self._exit("VarDecl")
        return VarDecl(
            id=self._next_id(),
            span=Span(let_tok.span.start, semi_span.end),
            name=name,
            type_name=btype,
            array_size=array_size,
            init=init,
            array_inits=array_inits,
            name_span=name_span,
        )

    def parse_block(self) -> Block:
        """Block -> { StmtList }."""
        self._enter("Block")
        # INV-SYN-04: expected '{': braces are mandatory
        if self.current.symbol != "{":
            self.error(f"expected '{{': braces are mandatory, found '{self.current.lexeme}'")
            stmt = self.parse_stmt()
            self._exit("Block")
            stmts = [stmt] if stmt else []
            span = stmt.span if stmt else self.current.span
            return Block(id=self._next_id(), span=span, statements=stmts)

        open_brace = self.advance()
        stmts = self.parse_stmt_list()

        # INV-SYN-05: EOF reached before '}'
        if self.current.symbol != "}":
            if self.is_eof:
                self.error("unexpected end of file; expected '}'", code="VL-SYN-002")
            else:
                self.error(f"expected '}}', found '{self.current.lexeme}'")
            close_span = self.current.span
        else:
            close_tok = self.advance()
            close_span = close_tok.span

        self._exit("Block")
        return Block(
            id=self._next_id(),
            span=Span(open_brace.span.start, close_span.end),
            statements=stmts,
        )

    def parse_stmt_list(self) -> list[Stmt]:
        """StmtList -> Stmt StmtList | ε."""
        stmts: list[Stmt] = []
        while not self.is_eof and self.current.symbol not in ("}", "case", "default"):
            s = self.parse_stmt()
            if s is not None:
                stmts.append(s)
        return stmts

    def parse_stmt(self) -> Stmt | None:
        """Stmt -> VarDecl | ID IdStmtTail ; | IfStmt | SwitchStmt | ..."""
        sym = self.current.symbol
        if sym == "let":
            return self.parse_var_decl()
        if sym == "ID":
            return self.parse_id_stmt()
        if sym == "if":
            return self.parse_if_stmt()
        if sym == "switch":
            return self.parse_switch_stmt()
        if sym == "while":
            return self.parse_while_stmt()
        if sym == "do":
            return self.parse_do_while_stmt()
        if sym == "for":
            return self.parse_for_stmt()
        if sym == "return":
            return self.parse_return_stmt()
        if sym == "break":
            return self.parse_break_stmt()
        if sym == "continue":
            return self.parse_continue_stmt()
        if sym == "show":
            return self.parse_show_stmt()
        if sym == "read":
            return self.parse_read_stmt()
        if sym == "{":
            return self.parse_block()
        if sym == ";":
            self.advance()
            return None

        # INV-SYN-03: unexpected statement starter (e.g. 'else' with no 'if')
        self.error(f"unexpected token '{self.current.lexeme}'; expected statement")
        if sym == "else":
            self.advance()
            if self.current.symbol == "{":
                PanicModeRecovery.skip_matched_braces(self)
        else:
            PanicModeRecovery.synchronize_statement(self)
        return None

    def parse_id_stmt(self) -> Stmt | None:
        """IdStmtTail -> ( ArgsOpt ) ; | IndexOpt AssignTail ;"""
        id_tok = self.advance()  # consume ID
        if self.current.symbol == "(":
            # Call statement
            self.advance()
            args = []
            if self.current.symbol != ")":
                args.append(self.parse_expr())
                while self.current.symbol == ",":
                    self.advance()
                    args.append(self.parse_expr())
            close_paren = self.match(")")
            semi = self.match(";")
            call_expr = CallExpr(
                id=self._next_id(),
                span=Span(id_tok.span.start, close_paren.span.end),
                callee=id_tok.lexeme,
                args=args,
                callee_span=id_tok.span,
            )
            return CallStmt(
                id=self._next_id(),
                span=Span(id_tok.span.start, semi.span.end),
                expr=call_expr,
            )

        # Assignment statement
        if self.current.symbol == "[":
            self.advance()
            idx = self.parse_expr()
            close_b = self.match("]")
            target: VarRefExpr | ArrayAccessExpr = ArrayAccessExpr(
                id=self._next_id(),
                span=Span(id_tok.span.start, close_b.span.end),
                name=id_tok.lexeme,
                index=idx,
            )
        else:
            target = VarRefExpr(
                id=self._next_id(),
                span=id_tok.span,
                name=id_tok.lexeme,
            )

        if self.current.symbol in ("++", "--"):
            op = self.advance().symbol
            semi = self.match(";")
            return AssignStmt(
                id=self._next_id(),
                span=Span(id_tok.span.start, semi.span.end),
                target=target,
                op=op,
                value=None,
            )
        if self.current.symbol in ("=", "+=", "-=", "*=", "/=", "%="):
            op = self.advance().symbol
            val = self.parse_expr()
            semi = self.match(";")
            return AssignStmt(
                id=self._next_id(),
                span=Span(id_tok.span.start, semi.span.end),
                target=target,
                op=op,
                value=val,
            )

        self.error(f"expected assignment operator or call after identifier, found '{self.current.lexeme}'")
        PanicModeRecovery.synchronize_statement(self)
        return None

    def parse_if_stmt(self) -> IfStmt:
        """IfStmt -> if ( Expr ) Block ElsePart."""
        self._enter("IfStmt")
        if_tok = self.advance()  # consume 'if'
        self.match("(")
        cond = self.parse_expr()

        # INV-SYN-02: expected ')' but found '{'
        if self.current.symbol != ")":
            self.error(f"expected ')', found '{self.current.lexeme}'")
        else:
            self.advance()

        then_block = self.parse_block()
        else_stmt: Block | IfStmt | None = None

        if self.current.symbol == "else":
            self.advance()
            if self.current.symbol == "if":
                else_stmt = self.parse_if_stmt()
            elif self.current.symbol == "{":
                else_stmt = self.parse_block()
            else:
                self.error(f"expected 'if' or '{{' after 'else', found '{self.current.lexeme}'")

        end_span = else_stmt.span if else_stmt else then_block.span
        self._exit("IfStmt")
        return IfStmt(
            id=self._next_id(),
            span=Span(if_tok.span.start, end_span.end),
            condition=cond,
            then_block=then_block,
            else_stmt=else_stmt,
        )

    def parse_switch_stmt(self) -> SwitchStmt:
        """SwitchStmt -> switch ( Expr ) { CaseList DefaultOpt }."""
        self._enter("SwitchStmt")
        sw_tok = self.advance()  # consume 'switch'
        self.match("(")
        expr = self.parse_expr()
        self.match(")")
        self.match("{")

        cases: list[CaseClause] = []
        while self.current.symbol == "case":
            cases.append(self.parse_case_clause())

        default_case: list[Stmt] | None = None
        if self.current.symbol == "default":
            self.advance()
            self.match(":")
            d_stmts: list[Stmt] = []
            while not self.is_eof and self.current.symbol not in ("}", "case"):
                s = self.parse_stmt()
                if s is not None:
                    d_stmts.append(s)
            default_case = d_stmts

        close_b = self.match("}")
        self._exit("SwitchStmt")
        return SwitchStmt(
            id=self._next_id(),
            span=Span(sw_tok.span.start, close_b.span.end),
            expr=expr,
            cases=cases,
            default_case=default_case,
        )

    def parse_case_clause(self) -> CaseClause:
        """CaseClause -> case CaseLabels : StmtList."""
        self._enter("CaseClause")
        case_tok = self.advance()  # consume 'case'
        labels = []
        label_spans = []
        c_val, c_span = self.parse_case_const()
        labels.append(c_val)
        label_spans.append(c_span)
        while self.current.symbol == ",":
            self.advance()
            c_val, c_span = self.parse_case_const()
            labels.append(c_val)
            label_spans.append(c_span)
        self.match(":")

        stmts: list[Stmt] = []
        while not self.is_eof and self.current.symbol not in ("case", "default", "}"):
            s = self.parse_stmt()
            if s is not None:
                stmts.append(s)

        end_span = stmts[-1].span if stmts else case_tok.span
        self._exit("CaseClause")
        return CaseClause(
            id=self._next_id(),
            span=Span(case_tok.span.start, end_span.end),
            labels=labels,
            body=stmts,
            label_spans=label_spans,
        )

    def parse_case_const(self) -> tuple[int | str, Span]:
        """CaseConst -> INT_LIT | CHAR_LIT | - INT_LIT."""
        if self.current.symbol == "-":
            neg_tok = self.advance()
            lit = self.match("INT_LIT")
            val = int(lit.value if lit.value is not None else lit.lexeme)
            return -val, Span(neg_tok.span.start, lit.span.end)
        if self.current.symbol == "INT_LIT":
            lit = self.advance()
            val = int(lit.value if lit.value is not None else lit.lexeme)
            return val, lit.span
        if self.current.symbol == "CHAR_LIT":
            lit = self.advance()
            ch_val = str(lit.value if lit.value is not None else lit.lexeme[1:-1])
            return ch_val, lit.span

        self.error(f"expected case constant, found '{self.current.lexeme}'")
        return 0, self.current.span

    def parse_while_stmt(self) -> WhileStmt:
        """WhileStmt -> while ( Expr ) Block."""
        self._enter("WhileStmt")
        w_tok = self.advance()
        self.match("(")
        cond = self.parse_expr()
        self.match(")")
        body = self.parse_block()
        self._exit("WhileStmt")
        return WhileStmt(
            id=self._next_id(),
            span=Span(w_tok.span.start, body.span.end),
            condition=cond,
            body=body,
        )

    def parse_do_while_stmt(self) -> DoWhileStmt:
        """DoWhileStmt -> do Block while ( Expr ) ;"""
        self._enter("DoWhileStmt")
        do_tok = self.advance()
        body = self.parse_block()
        self.match("while")
        self.match("(")
        cond = self.parse_expr()
        self.match(")")
        semi = self.match(";")
        self._exit("DoWhileStmt")
        return DoWhileStmt(
            id=self._next_id(),
            span=Span(do_tok.span.start, semi.span.end),
            body=body,
            condition=cond,
        )

    def parse_for_stmt(self) -> ForStmt:
        """ForStmt -> for ( ForInit ; ExprOpt ; ForUpdate ) Block."""
        self._enter("ForStmt")
        for_tok = self.advance()
        self.match("(")

        # ForInit
        init: VarDecl | AssignStmt | None = None
        if self.current.symbol == "let":
            let_tok = self.advance()
            name_tok = self.match("ID")
            self.match(":")
            btype = self.parse_base_type()
            self.match("=")
            init_expr = self.parse_expr()
            init = VarDecl(
                id=self._next_id(),
                span=Span(let_tok.span.start, init_expr.span.end),
                name=name_tok.lexeme,
                type_name=btype,
                init=init_expr,
            )
            self.match(";")
        elif self.current.symbol == "ID":
            init = self.parse_simple_assign()
            self.match(";")
        elif self.current.symbol == ";":
            self.advance()
        else:
            self.error(f"expected initialization in for loop, found '{self.current.lexeme}'")
            PanicModeRecovery.synchronize_statement(self)

        # ExprOpt
        cond = self.parse_expr() if self.current.symbol != ";" else None

        # INV-SYN-06: expected ';' in the for header
        if self.current.symbol != ";":
            self.error(f"expected ';' in for header, found '{self.current.lexeme}'")
        else:
            self.advance()

        # ForUpdate
        update = self.parse_simple_assign() if self.current.symbol != ")" else None
        self.match(")")

        body = self.parse_block()
        self._exit("ForStmt")
        return ForStmt(
            id=self._next_id(),
            span=Span(for_tok.span.start, body.span.end),
            init=init,
            condition=cond,
            update=update,
            body=body,
        )

    def parse_simple_assign(self) -> AssignStmt:
        """SimpleAssign -> ID IndexOpt AssignTail."""
        id_tok = self.match("ID")
        if self.current.symbol == "[":
            self.advance()
            idx = self.parse_expr()
            close_b = self.match("]")
            target: VarRefExpr | ArrayAccessExpr = ArrayAccessExpr(
                id=self._next_id(),
                span=Span(id_tok.span.start, close_b.span.end),
                name=id_tok.lexeme,
                index=idx,
            )
        else:
            target = VarRefExpr(
                id=self._next_id(),
                span=id_tok.span,
                name=id_tok.lexeme,
            )

        if self.current.symbol in ("++", "--"):
            op_tok = self.advance()
            return AssignStmt(
                id=self._next_id(),
                span=Span(id_tok.span.start, op_tok.span.end),
                target=target,
                op=op_tok.symbol,
                value=None,
            )
        if self.current.symbol in ("=", "+=", "-=", "*=", "/=", "%="):
            op_tok = self.advance()
            val = self.parse_expr()
            return AssignStmt(
                id=self._next_id(),
                span=Span(id_tok.span.start, val.span.end),
                target=target,
                op=op_tok.symbol,
                value=val,
            )

        self.error(f"expected assignment operator, found '{self.current.lexeme}'")
        return AssignStmt(
            id=self._next_id(),
            span=id_tok.span,
            target=target,
            op="=",
            value=None,
        )

    def parse_return_stmt(self) -> ReturnStmt:
        """ReturnStmt -> return ExprOpt ;"""
        self._enter("ReturnStmt")
        ret_tok = self.advance()
        val = self.parse_expr() if self.current.symbol != ";" else None
        semi = self.match(";")
        self._exit("ReturnStmt")
        return ReturnStmt(
            id=self._next_id(),
            span=Span(ret_tok.span.start, semi.span.end),
            value=val,
        )

    def parse_break_stmt(self) -> BreakStmt:
        """BreakStmt -> break ;"""
        self._enter("BreakStmt")
        b_tok = self.advance()
        semi = self.match(";")
        self._exit("BreakStmt")
        return BreakStmt(id=self._next_id(), span=Span(b_tok.span.start, semi.span.end), keyword_span=b_tok.span)

    def parse_continue_stmt(self) -> ContinueStmt:
        """ContinueStmt -> continue ;"""
        self._enter("ContinueStmt")
        c_tok = self.advance()
        semi = self.match(";")
        self._exit("ContinueStmt")
        return ContinueStmt(id=self._next_id(), span=Span(c_tok.span.start, semi.span.end), keyword_span=c_tok.span)

    def parse_show_stmt(self) -> ShowStmt:
        """ShowStmt -> show ExprList ;"""
        self._enter("ShowStmt")
        sh_tok = self.advance()
        exprs = [self.parse_expr()]
        while self.current.symbol == ",":
            self.advance()
            exprs.append(self.parse_expr())
        semi = self.match(";")
        self._exit("ShowStmt")
        return ShowStmt(
            id=self._next_id(),
            span=Span(sh_tok.span.start, semi.span.end),
            expressions=exprs,
        )

    def parse_read_stmt(self) -> ReadStmt:
        """ReadStmt -> read ID IndexOpt ;"""
        self._enter("ReadStmt")
        rd_tok = self.advance()
        id_tok = self.match("ID")
        if self.current.symbol == "[":
            self.advance()
            idx = self.parse_expr()
            close_b = self.match("]")
            target: VarRefExpr | ArrayAccessExpr = ArrayAccessExpr(
                id=self._next_id(),
                span=Span(id_tok.span.start, close_b.span.end),
                name=id_tok.lexeme,
                index=idx,
            )
        else:
            target = VarRefExpr(
                id=self._next_id(),
                span=id_tok.span,
                name=id_tok.lexeme,
            )
        semi = self.match(";")
        self._exit("ReadStmt")
        return ReadStmt(
            id=self._next_id(),
            span=Span(rd_tok.span.start, semi.span.end),
            target=target,
        )

    # ---- Expression Precedence Ladder ----

    def parse_expr(self) -> Expr:
        """Expr -> OrExpr."""
        self._enter("Expr")
        res = self.parse_or_expr()
        self._exit("Expr")
        return res

    def parse_or_expr(self) -> Expr:
        """OrExpr -> AndExpr OrTail; OrTail -> or AndExpr OrTail | ε."""
        left = self.parse_and_expr()
        while self.current.symbol == "or":
            op_tok = self.advance()
            right = self.parse_and_expr()
            left = BinaryExpr(
                id=self._next_id(),
                span=Span(left.span.start, right.span.end),
                left=left,
                op=op_tok.symbol,
                right=right,
                op_span=op_tok.span,
            )
        return left

    def parse_and_expr(self) -> Expr:
        """AndExpr -> NotExpr AndTail; AndTail -> and NotExpr AndTail | ε."""
        left = self.parse_not_expr()
        while self.current.symbol == "and":
            op_tok = self.advance()
            right = self.parse_not_expr()
            left = BinaryExpr(
                id=self._next_id(),
                span=Span(left.span.start, right.span.end),
                left=left,
                op=op_tok.symbol,
                right=right,
                op_span=op_tok.span,
            )
        return left

    def parse_not_expr(self) -> Expr:
        """NotExpr -> not NotExpr | EqExpr."""
        if self.current.symbol == "not":
            not_tok = self.advance()
            operand = self.parse_not_expr()
            return UnaryExpr(
                id=self._next_id(),
                span=Span(not_tok.span.start, operand.span.end),
                op="not",
                operand=operand,
            )
        return self.parse_eq_expr()

    def parse_eq_expr(self) -> Expr:
        """EqExpr -> RelExpr EqTail; EqTail -> EqOp RelExpr EqTail | ε."""
        left = self.parse_rel_expr()
        while self.current.symbol in ("==", "!="):
            op_tok = self.advance()
            right = self.parse_rel_expr()
            left = BinaryExpr(
                id=self._next_id(),
                span=Span(left.span.start, right.span.end),
                left=left,
                op=op_tok.symbol,
                right=right,
                op_span=op_tok.span,
            )
        return left

    def parse_rel_expr(self) -> Expr:
        """RelExpr -> AddExpr RelTail; RelTail -> RelOp AddExpr RelTail | ε."""
        left = self.parse_add_expr()
        while self.current.symbol in ("<", "<=", ">", ">="):
            op_tok = self.advance()
            right = self.parse_add_expr()
            left = BinaryExpr(
                id=self._next_id(),
                span=Span(left.span.start, right.span.end),
                left=left,
                op=op_tok.symbol,
                right=right,
                op_span=op_tok.span,
            )
        return left

    def parse_add_expr(self) -> Expr:
        """AddExpr -> MulExpr AddTail; AddTail -> AddOp MulExpr AddTail | ε."""
        left = self.parse_mul_expr()
        while self.current.symbol in ("+", "-"):
            op_tok = self.advance()
            right = self.parse_mul_expr()
            left = BinaryExpr(
                id=self._next_id(),
                span=Span(left.span.start, right.span.end),
                left=left,
                op=op_tok.symbol,
                right=right,
                op_span=op_tok.span,
            )
        return left

    def parse_mul_expr(self) -> Expr:
        """MulExpr -> UnaryExpr MulTail; MulTail -> MulOp UnaryExpr MulTail | ε."""
        left = self.parse_unary_expr()
        while self.current.symbol in ("*", "/", "%"):
            op_tok = self.advance()
            right = self.parse_unary_expr()
            left = BinaryExpr(
                id=self._next_id(),
                span=Span(left.span.start, right.span.end),
                left=left,
                op=op_tok.symbol,
                right=right,
                op_span=op_tok.span,
            )
        return left

    def parse_unary_expr(self) -> Expr:
        """UnaryExpr -> - UnaryExpr | CastExpr."""
        if self.current.symbol == "-":
            neg_tok = self.advance()
            operand = self.parse_unary_expr()
            return UnaryExpr(
                id=self._next_id(),
                span=Span(neg_tok.span.start, operand.span.end),
                op="-",
                operand=operand,
            )
        return self.parse_cast_expr()

    def parse_cast_expr(self) -> Expr:
        """CastExpr -> Primary CastTail; CastTail -> as BaseType CastTail | ε."""
        node = self.parse_primary()
        while self.current.symbol == "as":
            as_tok = self.advance()  # consume 'as'
            btype = self.parse_base_type()
            node = CastExpr(
                id=self._next_id(),
                span=Span(node.span.start, self.current.span.start),
                expr=node,
                target_type=btype,
                as_span=as_tok.span,
            )
        return node

    def parse_primary(self) -> Expr:
        """Primary -> INT_LIT | FLOAT_LIT | CHAR_LIT | STRING_LIT | true | false | ( Expr ) | ID PrimaryTail."""
        sym = self.current.symbol

        if sym in ("INT_LIT", "FLOAT_LIT", "CHAR_LIT", "STRING_LIT"):
            tok = self.advance()
            lit_type = sym.replace("_LIT", "").lower()
            return LiteralExpr(
                id=self._next_id(),
                span=tok.span,
                literal_type=lit_type,
                value=tok.value,
            )
        if sym in ("true", "false"):
            tok = self.advance()
            return LiteralExpr(
                id=self._next_id(),
                span=tok.span,
                literal_type="bool",
                value=(sym == "true"),
            )
        if sym == "(":
            self.advance()  # consume '('
            inner = self.parse_expr()
            self.match(")")
            return inner
        if sym == "ID":
            id_tok = self.advance()
            if self.current.symbol == "(":
                # Function call
                self.advance()
                args: list[Expr] = []
                if self.current.symbol != ")":
                    args.append(self.parse_expr())
                    while self.current.symbol == ",":
                        self.advance()
                        args.append(self.parse_expr())
                close_p = self.match(")")
                return CallExpr(
                    id=self._next_id(),
                    span=Span(id_tok.span.start, close_p.span.end),
                    callee=id_tok.lexeme,
                    args=args,
                    callee_span=id_tok.span,
                )
            if self.current.symbol == "[":
                # Array index
                self.advance()
                idx = self.parse_expr()
                close_b = self.match("]")
                return ArrayAccessExpr(
                    id=self._next_id(),
                    span=Span(id_tok.span.start, close_b.span.end),
                    name=id_tok.lexeme,
                    index=idx,
                )
            return VarRefExpr(
                id=self._next_id(),
                span=id_tok.span,
                name=id_tok.lexeme,
            )

        # Unexpected token
        if self.is_eof:
            self.error("unexpected end of file; expected expression", code="VL-SYN-002")
        else:
            self.error(f"expected expression, found '{self.current.lexeme}'")
        return LiteralExpr(
            id=self._next_id(),
            span=self.current.span,
            literal_type="error",
            value=None,
        )


def parse_source(source_text: str, filename: str = "input.vela") -> ParseResult:
    """Convenience helper to scan and parse source text."""
    source = SourceFile(filename, source_text)
    scanner = Scanner(source)
    lex_res = scanner.scan()
    parser = RecursiveDescentParser(lex_res.tokens, source)
    res = parser.parse()
    # Merge any lexer diagnostics with parser diagnostics
    res.diagnostics = lex_res.diagnostics + res.diagnostics
    return res
