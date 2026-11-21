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

---

## Milestone M2 — Grammar Engine & Parsing Theory (Phase 3 Theory)

### What the modules do
- **`vela.grammar.model` (`Production`, `Grammar`)**: Represents productions $A \to \alpha$ and immutable grammar specifications.
- **`vela.grammar.loader` (`BNFLoader`)**: Loads arbitrary context-free grammars from plain BNF text files, handling continuation lines (`|`), comments (`#`), and $\varepsilon$.
- **`vela.grammar.analysis` (`GrammarAnalysis`)**: Implements fixed-point iterative calculations for `nullable`, $FIRST$, and $FOLLOW$ sets, capturing step-by-step derivation history.
- **`vela.grammar.classify` (`classify_grammar`)**: Categorizes grammars according to the Chomsky Hierarchy into Type 2 (Context-Free) or Type 3 (Regular: left/right linear) with explicit justification.
- **`vela.grammar.transform` (`eliminate_left_recursion`, `left_factor`)**: Implements Dragon Book Algorithm 4.19 (indirect and immediate left recursion removal) and Algorithm 4.22 (left factoring) with pedagogical step logs.
- **`vela.grammar.ll1` (`LL1Table`)**: Builds predictive parsing tables $M[A, a]$, identifies FIRST/FIRST and FIRST/FOLLOW conflicts, and executes predictive stack parsing.
- **`vela.grammar.rdgen` (`RecursiveDescentGenerator`)**: Translates LL(1) parsing tables into executable recursive-descent pseudocode for display in the Grammar Lab.
- **`vela.grammar.lr` (`LRBuilder`, `LRTable`)**: Constructs item-set automata and parsing tables for the entire LR family: LR(0), SLR(1), CLR(1), and LALR(1) (via core-merging). Enforces a 5 000-state cap and implements precedence/associativity conflict resolution.
- **`vela.grammar.shift_reduce` (`ShiftReduceParser`)**: Simulates LR shift-reduce parsing, builds concrete parse tree nodes during reductions, and outputs step-by-step stack traces.
- **`vela.grammar.op_precedence` (`OperatorPrecedenceTable`)**: Verifies operator-grammar eligibility, computes $LEADING$ and $TRAILING$ sets, generates precedence relations ($\lessdot, \doteq, \gtrdot$), detects ambiguity conflicts (such as unary vs binary minus), and executes operator-precedence parsing.

### Key Algorithms & Data Structures
1. **LR(1) State Merging by Core for LALR(1)**: Groups CLR(1) states by their LR(0) item cores. For states sharing the same core, item lookaheads are unioned. Reduces state space from 609 to 214 states on Vela's grammar while avoiding parse table bloat.
2. **Fixed-Point Iterative Analysis**: $FIRST$ and $FOLLOW$ sets are computed by repeatedly applying production rules across all symbols until an iteration produces zero changes ($O(P \cdot |V|)$).
3. **Ambiguity Resolution via Precedence**: When shift/reduce conflicts arise in ambiguous expressions ($E \to E + E$), the conflict is resolved by comparing operator precedence levels and associativity (left-associative favors reduce, right-associative favors shift).

### Viva Questions & Answers
1. **Q: Why does the authoritative grammar `vela.bnf` have LR(0) conflicts but 0 SLR(1) conflicts?**
   **A:** LR(0) reduces whenever an item has the dot at the end $[A \to \alpha \cdot]$ regardless of the lookahead token, causing shift/reduce conflicts in any state that also has a valid shift. SLR(1) restricts reduction to only tokens in $FOLLOW(A)$. Because $FOLLOW(A)$ is disjoint from the shift tokens in every state of `vela.bnf`, all 33 LR(0) conflicts disappear in SLR(1).
2. **Q: Why can LALR(1) parsing introduce reduce/reduce conflicts that do not exist in CLR(1)?**
   **A:** Merging two CLR(1) states with identical cores combines their lookaheads. If two different productions $A \to \alpha$ and $B \to \alpha$ had disjoint lookaheads $\{a\}$ and $\{b\}$ in separate states, merging the states can cause both reductions to be valid on the union of lookaheads, creating a reduce/reduce conflict (as demonstrated in `not_lalr_but_clr.bnf`).
3. **Q: Why does operator-precedence parsing fail when unary and binary minus share the same `-` token?**
   **A:** In operator grammars, relations ($\lessdot, \gtrdot$) are strictly binary relations between pairs of terminals. Binary minus needs lower precedence than multiplication ($+ \lessdot *$), but unary minus needs higher precedence ($* \lessdot -$). When both use `-`, both relations hold simultaneously ($- \lessdot -$ and $- \gtrdot -$), resulting in an unresolvable relation conflict. Vela's Grammar Lab demonstrates this with `vela_expr_operator.bnf`.


---

## Milestone M3 — Parser and AST (Phase 3 Production & Phase 4 AST)

### What the modules do
- **`vela.ast.nodes`**: Comprehensive AST node hierarchy for all Vela constructs: `Program`, `VarDecl`, `FuncDecl`, `Param`, `Block`, statements (`AssignStmt`, `CallStmt`, `IfStmt`, `SwitchStmt`, `CaseClause`, `WhileStmt`, `DoWhileStmt`, `ForStmt`, `ReturnStmt`, `BreakStmt`, `ContinueStmt`, `ShowStmt`, `ReadStmt`), and expressions (`BinaryExpr`, `UnaryExpr`, `CastExpr`, `ImplicitCast`, `LiteralExpr`, `VarRefExpr`, `ArrayAccessExpr`, `CallExpr`). Every node carries a unique integer `id` and a source `Span`.
- **`vela.ast.printer` (`ASTPrinter`)**: Formats AST hierarchies into human-readable S-expressions (Lisp-style) and structured JSON dictionaries for visualization in the Vela Studio Trees page.
- **`vela.parser.parse_tree` (`ParseTreeNode`, `ParseTree`)**: Concrete Syntax Tree (CST) data structures representing exact grammar derivations according to $G'$ (`vela_ll1.bnf`), including nonterminal branches, matched terminal leaves, $\varepsilon$-derivations, and hierarchical spans.
- **`vela.parser.recovery` (`PanicModeRecovery`)**: Provides synchronizing token sets (`STATEMENT_STARTERS`, `DECLARATION_STARTERS`, `STATEMENT_SYNCHRONIZERS`) and recovery routines to safely resynchronize the parser on statement and declaration boundaries without cascading errors or infinite loops.
- **`vela.parser.recursive_descent` (`RecursiveDescentParser`, `parse_source`)**: Hand-written LL(1) recursive descent parser. Emits execution call traces, enforces the nesting depth limit of 200 (`VL-SYN-003`), builds AST and CST simultaneously, and reports exact diagnostics (`VL-SYN-001`, `VL-SYN-002`).

### Key Algorithms & Data Structures
1. **Precedence Ladder with Iterative Loops**: Left-associative binary operators ($E \to T E'$; $E' \to + T E' \mid \varepsilon$) are parsed using iterative `while` loops instead of recursive method calls. This eliminates stack frame overhead while building properly left-branching AST structures (`BinaryExpr(BinaryExpr(a, +, b), +, c)`).
2. **Simultaneous AST and CST Construction**: As the recursive descent parser descends grammar productions, it maintains a CST parent stack. When terminal tokens are consumed or nonterminals exit, CST nodes are attached and spans aggregated. At the same time, semantic AST nodes are instantiated and returned up the call stack.
3. **Panic-Mode Synchronization**: On encountering unexpected tokens, the parser records a diagnostic (`VL-SYN-001` or `VL-SYN-002`) and skips tokens until reaching a synchronizing token (`;`, `}`, or statement/declaration starter), guaranteeing forward progress and discovering multiple errors in a single run (as verified on `INV-SYN-08`).

### Viva Questions & Answers
1. **Q: Why does Vela use recursive descent for production parsing instead of table-driven LR parsing?**
   **A:** Recursive descent produces superior, human-readable error messages and enables surgical panic-mode recovery tailored to specific statement constructs (e.g. knowing whether a missing token was in an `if` header, a `for` loop, or a variable declaration). It also constructs rich, custom AST nodes directly without requiring complex reduction actions inside table drivers.
2. **Q: How does the parser prevent stack overflow on adversarial inputs like 250 nested parentheses?**
   **A:** The parser tracks `self.nesting_depth` upon entering each nonterminal or expression level. When `nesting_depth > 200`, it immediately emits diagnostic `VL-SYN-003` at the offending token and raises `NestingLimitExceededError`, safely unwinding the stack and returning a fail-soft `ParseResult`.
3. **Q: How was the recursive-descent parser differentially validated against the LR family?**
   **A:** Using differential testing: the token streams of all valid example programs, invalid syntax error programs, and dozens of mutated sentences were fed into both the recursive-descent parser (operating on $G'$) and the SLR(1) shift-reduce table parser (operating on $G$). Both parsers agreed 100% on accept/reject decisions across all test cases.

---

## Milestone M4 — Semantic Analysis, SDD/SDT, and Expression DAG

### Overview
Milestone M4 delivers the semantic verification and intermediate structure layer (Phase 4 of the compiler pipeline). It comprises:
- Strongly typed semantic representation: type system (`vela.semantic.types`), symbol table with hierarchical lexical scopes and shadowing detection (`vela.semantic.symbols`), and structural all-paths return analysis (`vela.semantic.returns`).
- Two-pass semantic checker (`vela.semantic.checker`): Pass 1 registers global function prototypes and variable types; Pass 2 validates types, statements, assignment compatibility, array index constraints, loop controls, conditions, and inserts `ImplicitCast` AST nodes for numeric widening (`int` to `float`).
- Error reporting: Handles all semantic invariant diagnostic codes (`VL-SEM-001` through `VL-SEM-023`) with exact token column and line coordinates matching the specification.
- Syntax-Directed Definition (SDD) and Translation (SDT) engine (`vela.semantic.sdd`): safe AST expression evaluation without `eval`/`exec`, S-attributed vs L-attributed classification, attribute dependency graph construction, cycle detection, topological evaluation, and 4 educational presets (Desk Calculator, Type Declarations, Boolean Short-Circuit Labels, Vela Expression Typing).
- Expression Directed Acyclic Graph (DAG) with value numbering (`vela.ast.dag`): common subexpression sharing across expressions and basic blocks, commutative operator normalization, tree-vs-DAG node count metrics, and step-by-step trace generation.

### Key Algorithms & Design Choices
1. **Two-Pass Type Checking & Widening**: Pass 1 collects top-level signatures, enabling out-of-order forward references and mutual recursion. Pass 2 checks expression types bottom-up, inserting `ImplicitCast` nodes for numeric widening (`int` to `float`).
2. **Structural All-Paths Return Analysis**: Conservatively traverses control-flow AST nodes (`IfStmt`, `SwitchStmt`, `WhileStmt`, `Block`) ensuring every execution branch returns a value matching the function signature.
3. **S/L-Attributed Classification**: Inspects rule production dependencies; verifies that inherited attributes depend strictly on parent inherited attributes or symbols strictly to the left on the RHS (flagging right-sibling dependencies with exact rule attribution).
4. **Value Numbering for DAG Construction**: Canonical signatures for leaves and operators; commutative sorting for `+`, `*`, `==`, `!=`; variable def-kill tracking across assignments in basic blocks.
5. **No `eval`/`exec`**: The SDD engine evaluates rules via an AST-based safe interpreter restricted to arithmetic, comparisons, ternary expressions, and whitelisted helper functions.

### Viva Q&A
1. **Q: How does the compiler distinguish between S-attributed and L-attributed definitions?**
   **A:** An SDD is S-attributed if every attribute is synthesized (computed from children or intrinsic terminal values). An SDD is L-attributed if every inherited attribute $X_i.a$ in production $A \to X_1 \dots X_n$ depends only on inherited attributes of the parent $A$ or attributes of symbols $X_1 \dots X_{i-1}$ appearing strictly to the left of $X_i$. If an attribute depends on a right sibling $X_j$ ($j > i$) or a synthesized attribute of $A$, it violates the L-attributed property.
2. **Q: How does Value Numbering in an Expression DAG enable Common Subexpression Elimination (CSE)?**
   **A:** Value numbering assigns a unique identifier (value number) to each unique computation. When constructing an expression, the compiler checks if a node with the same operator and operand value numbers already exists. If so, it reuses the existing node instead of allocating a new one. In basic blocks, when a variable is reassigned, its mapping is updated to the new value number, naturally killing obsolete definitions while sharing unmutated subexpressions like `(a + b) * 2` and `(a + b) * 3`.
3. **Q: Why is a two-pass semantic checker required rather than a single-pass traversal?**
   **A:** A two-pass checker decouples declaration order from use. Pass 1 collects all global variable and function signatures into the root symbol table. Pass 2 type-checks function bodies and expressions. This allows mutually recursive functions and forward calls (functions called before their definition in the source file) to resolve cleanly with complete type information.
