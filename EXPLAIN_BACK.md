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
