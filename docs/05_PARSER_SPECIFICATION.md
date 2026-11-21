# 05 — Parser Specification (Phase 3)

> Status: written by the implementation agent, needs group review
> Authority: follows `docs/00_PROJECT_MASTER_SPEC.md`, `docs/01_LANGUAGE_SPECIFICATION.md` §13, §16.2, and `docs/grammar/vela_ll1.bnf`.

---

## 1. Overview and Requirements
The syntactic analyzer (parser) processes the stream of tokens produced by the lexer and constructs both:
1. An Abstract Syntax Tree (AST) rooted in `Program` (conforming to `docs/08_AST_DAG_SDD_SDT_SPECIFICATION.md` and `vela.ast.nodes`).
2. A Concrete Parse Tree (CST) representing the exact derivation according to the LL(1) grammar $G'$ (`docs/grammar/vela_ll1.bnf`).
3. An execution trace of recursive descent function calls and derivations for the Vela Studio Parser Explorer.

Key requirements:
- **Hand-written recursive descent** (P3-01): One parsing function per nonterminal of grammar $G'$, with tail nonterminals implemented as loops for efficiency.
- **Fail-soft error recovery** (P3-02): Panic-mode error recovery synchronizing on statement and declaration boundaries (`;`, `}`). Multiple errors are reported in a single pass without cascading nonsense.
- **Nesting limit enforcement** (VL-SYN-003): Maximum recursion/nesting depth of 200 to prevent stack exhaustion on adversarial inputs.
- **Exact diagnostic matching**:
  - `VL-SYN-001`: Unexpected token (naming expected tokens / constructs).
  - `VL-SYN-002`: Unexpected end of file (at the EOF position).
  - `VL-SYN-003`: Nesting too deep (> 200).
- **Differential verification**: The recursive-descent parser must agree with the SLR(1) / LR table driver on all valid programs and syntax error detection.

---

## 2. Grammar $G'$ Mapping

Every nonterminal in `vela_ll1.bnf` corresponds to a parser method:
- Top-level: `parse_program()`, `parse_top_item()`, `parse_func_decl()`, `parse_var_decl()`.
- Types: `parse_base_type()`.
- Statements: `parse_block()`, `parse_stmt()`, `parse_if()`, `parse_switch()`, `parse_while()`, `parse_do_while()`, `parse_for()`, `parse_show()`, `parse_read()`, `parse_return()`.
- Expressions (precedence ladder): `parse_expr()` -> `parse_or_expr()` -> `parse_and_expr()` -> `parse_not_expr()` -> `parse_eq_expr()` -> `parse_rel_expr()` -> `parse_add_expr()` -> `parse_mul_expr()` -> `parse_unary_expr()` -> `parse_cast_expr()` -> `parse_primary()`.

For tail nonterminals (`OrTail`, `AndTail`, `EqTail`, `RelTail`, `AddTail`, `MulTail`, `CastTail`, `ExprTail`, `StmtList`), the parser uses iterative `while` loops instead of recursion, avoiding unnecessary stack frames while maintaining identical language recognition.

---

## 3. Data Structures

### 3.1 Concrete Parse Tree (`ParseTreeNode`)
```python
@dataclass
class ParseTreeNode:
    name: str # Nonterminal or terminal name (e.g. "Program", "VarDecl", "let", "ID")
    is_terminal: bool
    token: Token | None = None
    children: list["ParseTreeNode"] = field(default_factory=list)
    span: Span | None = None
```

### 3.2 Parser Call Trace (`ParserCallStep`)
```python
@dataclass(frozen=True)
class ParserCallStep:
    nonterminal: str
    action: str # "enter", "match", "loop", "exit", "recover"
    depth: int
    token_index: int
    token_lexeme: str
    token_type: str
```

### 3.3 Parse Result (`ParseResult`)
```python
@dataclass
class ParseResult:
    ast: Program | None
    cst: ParseTreeNode | None
    diagnostics: list[Diagnostic]
    call_trace: list[ParserCallStep]
    success: bool
```

---

## 4. Error Recovery (Panic Mode)

When an unexpected token is encountered:
1. Report diagnostic `VL-SYN-001` or `VL-SYN-002`.
2. Enter panic-mode recovery in the innermost synchronizing boundary:
   - For statement recovery: skip tokens until a synchronizer (`;` or `}`) or EOF is reached.
   - For declaration recovery: skip tokens until `;`, `}`, or a declaration keyword (`let`, `func`) is reached.
3. If synchronizer is `;`, consume it and resume parsing the next statement/item.
4. If synchronizer is `}`, do not consume it (allow block closure to handle it) and resume.

---

## 5. Verification
- Verify against all 10 standard test programs `examples/*.vela`.
- Verify against all invalid syntax test cases `INV-SYN-01` through `INV-SYN-08`.
- Differential test comparing RD parser outcomes against SLR(1) parser outcomes across a test suite.
