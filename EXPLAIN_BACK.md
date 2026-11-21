# Explain-Back Viva Guide

Consolidated architectural summaries and viva preparation material for each completed milestone.

---

## Milestone M0 — Workspace & Common Foundations

### What the modules do
- **`vela.common.source` (`SourceFile`, `SourceLocation`, `Span`)**: Encapsulates raw source code text, normalizes line breaks (`\r\n` and `\r` to `\n`), maintains a line index for binary-search-based $O(\log L)$ mapping from character offsets to 1-based `line:col` coordinates, and provides immutable `Span` objects (start/end) for source traceability.
- **`vela.common.diagnostics` (`Diagnostic`, `DIAGNOSTIC_CODES`)**: Implements the standardized diagnostic data structures and the complete dictionary of 47 error codes specified in doc 01 §12 across lexical, syntax, semantic, and runtime phases. Formats messages in the canonical `line:col: error[CODE]: message` format.
- **`vela.common.limits` (`LIMITS`)**: Enforces explicit architectural thresholds (source length <= 100k chars, tokens <= 50k, nesting depth <= 200, array size <= 10k, VM execution <= 1M instructions, timeout <= 10s) to prevent Denial of Service and stack exhaustion.
- **`vela.common.budget` (`Budget`, `BudgetExceededError`)**: Implements cooperative resource budgeting for long-running compiler algorithms and VM execution loops without using OS-level thread kills.

### Key Algorithms & Data Structures
1. **Line Indexing via Binary Search**: Source text line start offsets are recorded in an array $O(N)$ once during initialization. Any subsequent offset is translated to `(line, column)` in $O(\log L)$ time using binary search, where $L$ is the number of lines.
2. **Cooperative Step Counting**: Critical loops call `budget.tick()` or `budget.check_soft()`, decrementing or incrementing a finite allowance to guarantee termination on malicious or cyclic inputs.

### Viva Questions & Answers
1. **Q: Why does the compiler normalize `\r\n` and `\r` to `\n` before any phase runs?**
   **A:** Windows uses CRLF while Unix uses LF and older Mac systems used CR. Normalizing to single `\n` bytes ensures column and offset arithmetic is identical and portable across operating systems, guaranteeing byte-for-byte deterministic source spans.
2. **Q: How does the compiler satisfy Architectural Principle AP-1 (pure Python library without web imports)?**
   **A:** `backend/vela/` is completely decoupled from FastAPI, Uvicorn, and HTTP concerns. The FastAPI application in `backend/api/` is an external adapter that imports `vela`, but `vela` never imports `api` or `fastapi`. This is tested automatically in `backend/tests/test_smoke.py`.
3. **Q: What is the purpose of cooperative resource budgets instead of killing threads?**
   **A:** Killing threads in Python or WebAssembly runtimes leaves shared memory, locks, and file descriptors in corrupt states. Cooperative budgets check iteration counts at clean yield points, allowing graceful fail-soft termination and reporting informative errors (`VL-RUN-007` or `VL-LIM-001`) with all prior phase results intact.

---

## Milestone M1 — Lexical Analysis (Phase 2)

### What the modules do
- **`vela.language.spec`**: Central repository for all language tables. Defines 26 reserved keywords, 19 operators, 9 delimiters, 8-level precedence table, and token regular expressions. Acts as the single source of truth for the lexer, `/api/language`, and code editor highlighting.
- **`vela.lexer.tokens` (`Token`, `LexResult`)**: Defines standardized token records holding `category`, `symbol`, `lexeme`, evaluated `value`, and source `span`. Packages tokens, diagnostics, DFA step traces, and buffer refill events.
- **`vela.lexer.buffer` (`InputBuffer`)**: Implements the classic Dragon Book two-buffer input scheme with sentinels (`\0`), configurable chunk sizes, `lexeme_begin` / `forward` pointers, retract capabilities, and refill event telemetry.
- **`vela.lexer.fsm` (`DFA`, `DFASimulator`)**: Explicit deterministic finite automata for numbers, identifiers, and multi-character operators with maximal munch (longest match) simulation and step-by-step transition tracking for UI visualization.
- **`vela.lexer.scanner` (`Scanner`)**: Hand-written lexical analyzer. Scans tokens, strips whitespace and comments (`//` and `/*...*/`), disambiguates keywords vs identifiers (e.g. `show` vs `shown`), evaluates literal values, and gathers all lexical errors (`VL-LEX-001...011`, `VL-LIM-001`) without early abortion.

### Key Algorithms & Data Structures
1. **Two-Buffer Scheme with Sentinels**: Input is loaded in alternating chunks into buffers $B_1$ and $B_2$ with sentinel characters at the end. Only two pointer comparisons per character are needed instead of end-of-buffer checks on every character advance.
2. **Maximal Munch (Longest Match)**: In token recognition (e.g., `<` vs `<=`, `+` vs `++` vs `+=`), the DFA simulator continues advancing while transitions exist, remembering the last accepted state. When no further transition is possible, it retracts the buffer pointer to the longest recognized match.
3. **Keyword Disambiguation**: Identifiers recognized by the identifier DFA are checked against a hash set of 26 reserved words in $O(1)$ time. If matched, the token category is classified as `KEYWORD` (or logical `OPERATOR`) and the symbol is set to the lexeme.

### Viva Questions & Answers
1. **Q: Why is input buffering using two buffers and sentinels necessary?**
   **A:** Reading large files character-by-character from disk or string memory is inefficient and makes lookahead/retract operations complex. The two-buffer scheme with sentinels permits seamless lookahead across buffer boundaries and reduces boundary checking to a single sentinel character test per iteration.
2. **Q: How does the lexer resolve the ambiguity between `<` and `<=` or `=` and `==`?**
   **A:** The lexer uses the longest-match (maximal munch) rule implemented in `OperatorDFA`. When seeing `=`, it does not immediately commit; it checks if the next character is `=`. If so, it transitions to state `EQ` (`==`). Only when no further valid transition exists does it accept the longest match.
3. **Q: How are lexical errors recovered from, and why is recovery important?**
   **A:** The scanner uses panic-mode/character-skip recovery: on an invalid character (`VL-LEX-001`), it emits a diagnostic with the exact span, skips the invalid character, and resumes scanning the next token. This ensures all lexical errors in a file are reported in a single compiler run rather than halting on the very first typo.
