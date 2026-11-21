# 04 — Lexer Specification (Phase 2)

> Status: written by the implementation agent, needs group review
> Authority: follows `docs/00_PROJECT_MASTER_SPEC.md` and `docs/01_LANGUAGE_SPECIFICATION.md` §2.

---

## 1. Overview and Requirements
The lexical analyzer scans normalized UTF-8 source code into a sequential stream of tokens. It implements:
- Hand-written scanner driven by explicit DFA tables built from regular expressions (P2-01, P2-02, P2-08).
- Two-buffer input scheme with sentinels and configurable buffer size (P2-05).
- Maximal munch (longest match) token recognition with tie-breaking precedence (P2-03, P2-04).
- Fail-soft lexical error recovery collecting all diagnostics (P2-06).
- Generation of detailed DFA state path traces and buffer refill traces for the Vela Studio Lexer Explorer.

---

## 2. Token Specification and Categorization

### 2.1 Keywords (26)
All keywords are reserved, lowercase, and cannot be used as identifiers:
- Declarations: `let`, `func`
- Types: `int`, `float`, `char`, `string`, `bool`
- Literals: `true`, `false`
- Selection: `if`, `else`, `switch`, `case`, `default`
- Loops / jumps: `for`, `while`, `do`, `break`, `continue`, `return`
- I/O: `show`, `read`
- Operators / Conversions: `and`, `or`, `not`, `as`

### 2.2 Operators and Delimiters
- Arithmetic: `+`, `-`, `*`, `/`, `%`
- Relational: `<`, `<=`, `>`, `>=`, `==`, `!=`
- Assignment: `=`, `+=`, `-=`, `*=`, `/=`, `%=`
- Statement Inc/Dec: `++`, `--`
- Delimiters: `(`, `)`, `{`, `}`, `[`, `]`, `;`, `,`, `:`

### 2.3 Literals & Identifiers
- `INT_LIT`: `[0-9]+`, 0 .. 2 147 483 647.
- `FLOAT_LIT`: `[0-9]+\.[0-9]+` (digits mandatory on both sides).
- `CHAR_LIT`: `'([^'\\\n]|\\[ntr0\\'"])'`, code point <= 255.
- `STRING_LIT`: `"([^"\\\n]|\\[ntr0\\'"])*"`.
- `ID`: `[A-Za-z_][A-Za-z0-9_]*`, length <= 64.

---

## 3. Data Structures

### 3.1 Token Data Class
```python
@dataclass(frozen=True)
class Token:
    category: str        # KEYWORD, IDENTIFIER, INT_LITERAL, etc.
    symbol: str          # Grammar terminal: 'let', '<=', 'ID', 'INT_LIT', '$'
    lexeme: str          # Raw text from source
    value: Any           # Evaluated value (int, float, str, bool, or None)
    span: Span           # Start and end SourceLocation
```

### 3.2 Lexical Result
```python
@dataclass
class LexResult:
    tokens: list[Token]
    diagnostics: list[Diagnostic]
    dfa_trace: list[dict]     # Optional step trace through FSM
    buffer_trace: list[dict]  # Optional refill/sentinel events
```

---

## 4. Buffering Algorithm (Two-Buffer with Sentinels)
Two buffers $B_1$ and $B_2$ each of size $N$ (e.g. 4096 bytes) ending with sentinel `EOF` character `\0`.
- Pointers: `lexeme_begin` and `forward`.
- When `forward` reaches the end of buffer $B_1$, it refills $B_2$ and moves to $B_2[0]$.
- When `forward` reaches the end of buffer $B_2$, it refills $B_1$ and moves to $B_1[0]$.
- If a token exceeds $N$, buffer expansion or circular buffering maintains the slice.

---

## 5. Lexical Error Recovery
- `VL-LEX-001` (invalid character): emit diagnostic, skip bad character, continue scanning.
- `VL-LEX-002` (unterminated string): emit diagnostic at opening quote, stop at newline or EOF.
- `VL-LEX-003` (unterminated char): emit diagnostic at opening quote.
- `VL-LEX-004` (empty char): emit diagnostic.
- `VL-LEX-005` (multi-char literal): emit diagnostic.
- `VL-LEX-006` (invalid escape sequence): emit diagnostic at backslash.
- `VL-LEX-007` (unterminated block comment): emit diagnostic at `/*`.
- `VL-LEX-008` (malformed number): emit diagnostic for the full alphanumeric run.
- `VL-LEX-009` (integer out of range): emit diagnostic.
- `VL-LEX-010` (identifier > 64 chars): emit diagnostic.
- `VL-LEX-011` (char code > 255): emit diagnostic.
- `VL-LIM-001` (token count > 50 000): halt lexer immediately.
