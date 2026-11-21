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

---

## Milestone M5 — Intermediate Code (TAC) and Oracle Interpreter

### Overview
Milestone M5 delivers the intermediate representation and reference execution layer (Phase 5 of the compiler pipeline). It encompasses:
- Strongly typed Three-Address Code (TAC) quadruple model (`vela.ir.tac`): Quadruple format `(opcode, arg1, arg2, result)` with full source span provenance, AST node references, and IR translation rule tags.
- Intermediate Representation Lowering Generator (`vela.ir.generator`): Converts validated ASTs into linear TAC, handling global startup execution, function call conventions (`FUNC_BEGIN`, `PARAM`, `CALL`, `RECEIVE`, `RETURN`, `FUNC_END`), short-circuit boolean lowering with branches (no hardware/plain `and`/`or` instructions), control-flow loops with break/continue targets, and alpha-converted scope-disambiguated variables.
- Linear TAC Pretty-Printer & Table Formatter (`vela.ir.printer`): Textual representation and structured quadruple table formatting for diagnostics and visual inspection.
- Independent Execution Oracle & Interpreter (`vela.ir.interpreter`): Reference execution engine implementing exact language runtime semantics: 32-bit two's complement arithmetic wrap-around, truncating integer division toward zero, remainder with dividend sign, array bound checks, unified stream I/O, call stack overflow detection, instruction budgets, and runtime errors `VL-RUN-001` through `VL-RUN-008`.
- Comprehensive Golden Verification: All 10 golden programs (`01_hello_types` through `10_scopes`) reproduce their exact `.expected.txt` character-by-character. Error catalog programs `INV-RUN-01` through `INV-RUN-05` reproduce exact error codes and line:col coordinates.

### Key Algorithms & Design Choices
1. **Short-Circuit Boolean Lowering**: In adherence to the strict requirement that no plain boolean `and`/`or` opcode exists in the TAC instruction set, logical conjunction and disjunction are translated into conditional jumps (`JUMP_IF_FALSE` / `JUMP_IF`) with jump labels and boolean constant assignments.
2. **Alpha-Conversion Scope Renaming**: Nested scopes (blocks, functions, for-headers) are dynamically indexed during IR generation, disambiguating shadowed variable names (e.g. `level_2`, `level_3`) while maintaining plain global names, enabling seamless nested block semantics without dynamic scope lookups at runtime.
3. **Two's Complement 32-Bit Arithmetic & Truncating Division**: Emulates standard 32-bit registers via `wrap32` bit masking. Division truncates toward zero (`int(a / b)`), and modulo follows C99/Vela conventions `a - (int(a / b) * b)`.
4. **Unified Stream I/O Tokenizer**: A shared cursor across stdin ensures interleaved reading of tokens (`int`, `float`, `string`, `bool`) and whitespace-skipping raw characters (`char`) accurately reflects real POSIX/C stdin streams.

### Viva Q&A
1. **Q: Why are `and` and `or` logical operators lowered via conditional jumps rather than direct TAC instructions?**
   **A:** Direct hardware-style boolean instructions force both operands to be evaluated eagerly, which would violate the short-circuit semantics mandated by modern programming languages (and Vela spec §6.4). By lowering `a and b` into `ifFalse a goto L_false`, the second operand `b` is never evaluated if `a` is false, preventing illegal memory accesses, division by zero, or side effects in the right-hand operand.
2. **Q: How does the TAC interpreter serve as an independent execution oracle for the compiler?**
   **A:** The TAC interpreter executes the machine-independent IR before any optimizations or machine-specific transformations take place. By verifying that the unoptimized TAC produces 100% identical outputs to the target VM (and matching all golden `.expected.txt` files), the compiler architecture ensures that any discrepancy observed in later phases (Phase 6 optimization or Phase 7 code generation) is immediately identifiable as an optimization or codegen bug rather than a language semantics bug.
3. **Q: How does Vela handle array memory and parameters during TAC execution?**
   **A:** In Vela, arrays are fixed-size buffers allocated on the heap or frame via `ALLOC_ARRAY`. Array parameters are passed by reference (`name: int[]`). In the interpreter, passing an array passes the reference to the underlying Python list object, allowing in-place mutations (e.g. in sorting or accumulation routines) to affect the caller's array directly, fulfilling the by-reference requirement without pointer arithmetic.

---

## Milestone M6 — Code Optimization and Data-Flow Framework

### Overview
Milestone M6 delivers the complete Phase 6 optimization subsystem for Three-Address Code:
- **Basic Block Partitioning (`vela.opt.blocks`)**: Implements Dragon Book Algorithm 8.5 with explicit provenance tracking for leader identification (`first instruction`, `jump target: L`, `follows jump/branch/return`).
- **Control-Flow Graph (`vela.opt.cfg`)**: Constructs directed control-flow graphs connecting basic blocks with typed edges (`entry`, `fall_through`, `branch`, `jump`, `call`, `return`). Supports interactive GUI export via Mermaid diagrams and JSON schemas.
- **Dominator Analysis & Natural Loops (`vela.opt.dominators`)**: Solves iterative dominator equations $DOM(n) = \{n\} \cup \left(\bigcap_{p \in Pred(n)} DOM(p)\right)$, extracts immediate dominators ($idom$), constructs the dominator tree, identifies back-edges ($n \to d$ where $d \text{ dom } n$), and reconstructs the natural loop body for each loop header.
- **Generic Data-Flow Analysis Framework (`vela.opt.dataflow`)**: A unified iterative worklist engine supporting forward/backward directions and union/intersection meet operators with step-by-step iteration logging:
  - *Reaching Definitions* (Forward, Union)
  - *Live Variables* (Backward, Union)
  - *Available Expressions* (Forward, Intersection)
  - *Available Copies* (Forward, Intersection)
- **Eight Machine-Independent Optimization Passes (`vela.opt.passes.*`)**:
  - `const_fold`: Folds compile-time arithmetic with 32-bit two's complement wrap-around; explicitly protects $\div 0$ and $\% 0$ from folding to preserve runtime diagnostics.
  - `simplify`: Eliminates algebraic identities ($x + 0 \to x$, $x * 1 \to x$, $x * 0 \to 0$, $x - 0 \to x$, $x / 1 \to x$).
  - `const_prop`: Replaces variable uses with constants using local block environment and global reaching definitions.
  - `copy_prop`: Replaces variable copies $x = y$ with the original source operand.
  - `cse`: Eliminates redundant computations via local DAG value numbering and global available expressions.
  - `strength`: Replaces expensive multiplications with additions (e.g. $x * 2 \to x + x$).
  - `licm`: Hoists loop-invariant computations out of natural loops into preheaders.
  - `dce`: Eliminates dead variable assignments based on backward liveness analysis while safeguarding all side-effecting operations and global variables.
- **Pipeline Runner & Equivalence Validator (`vela.opt.pipeline`, `validate`)**:
  - Iterative fixed-point driver recording step-by-step before/after code transformations and reduction metrics.
  - Structural IR well-formedness validation (all jump targets defined, zero plain boolean opcodes).
  - Semantic equivalence verified across all 10 standard language examples and invalid runtime programs (`INV-RUN-01..05`).

### Key Algorithms & Design Choices
1. **Dragon Book Algorithm 8.5 Leader Rules**:
   - The first instruction of the program/function is a leader.
   - Any instruction that is the target of a conditional or unconditional jump is a leader.
   - Any instruction that immediately follows a jump, branch, or return is a leader.
2. **Dominators and Loop Reconstruction**:
   Back-edges are identified as edges $n \to d$ where $d$ dominates $n$. A function call is explicitly distinguished from an intra-procedural jump so recursive calls do not create false loops. The natural loop is reconstructed via reverse depth-first traversal from $n$ without passing through $d$.
3. **Data-Flow Semi-Lattice Solver**:
   Generic round-robin/worklist propagation with boundary conditions and universe pre-seeding. Records snapshots of `IN` and `OUT` sets after every iteration for educational visualization.
4. **Safety and Equivalence Invariants**:
   - *Division by Zero*: Constant folding refuses to fold expressions with divisor 0, guaranteeing that runtime error `VL-RUN-001` is triggered at the exact location expected.
   - *Global State Protection*: Function calls (`CALL`) invalidate all global variables in constant and copy environments; dead-code elimination never removes assignments to global variables within functions.

### Viva Q&A
1. **Q: Why must constant folding NEVER fold division or modulo by zero?**
   **A:** If the compiler folded `10 / 0` at compile time, the code could either crash the compiler or replace the computation with an arbitrary value or compile-time error. However, in Vela, division by zero is a runtime exception (`VL-RUN-001`). In branches that may never execute at runtime (e.g. inside dead or conditional code), folding division by zero would incorrectly terminate compilation or change program semantics. Thus, preserving the `DIV` quadruple ensures the runtime oracle/VM triggers the exact runtime exception at the correct execution step.
2. **Q: What is the difference between S-attributed/L-attributed SDDs and Forward/Backward Data-Flow analyses?**
   **A:** SDDs operate on parse trees/ASTs during parsing or semantic analysis; S-attributed flows bottom-up (synthesized) and L-attributed flows top-down and left-to-right (inherited). Data-flow analysis operates on control-flow graphs (CFGs) over basic blocks; forward problems (e.g. Reaching Definitions) propagate information along control flow edges, while backward problems (e.g. Live Variables) propagate information against control flow edges from exit to entry.
3. **Q: How does Common Subexpression Elimination (CSE) leverage both local DAGs and global data-flow?**
   **A:** Within a single basic block, an Expression DAG uses value numbering to identify identical subtrees and canonicalize commutative operations ($a + b = b + a$) in $O(1)$ hash lookups. Across multiple basic blocks, Global Available Expressions analysis computes the intersection of expressions available along all paths reaching a block. When an available expression is computed, the compiler reuses the previously stored temporary, avoiding redundant operations across control-flow joins.

---

## Milestone M7 — Target Code Generation, Virtual Machine, and CLI Pipeline

### Overview
Milestone M7 completes the compiler backend from machine-independent IR through physical code generation, virtual machine simulation, and driver tooling:
- **Target Instruction Set Architecture (`vela.codegen.isa`)**:
  - 8 General-Purpose 32-bit Registers (`R0` through `R7`), plus special registers `SP` (Stack Pointer), `FP` (Frame Pointer), `PC` (Program Counter), and Condition Flags (`ZF`, `SF`).
  - Four Addressing Modes: Register (`R_k`), Immediate (`#imm`), Memory Direct (`[symbol]`), and Base Displacement (`[FP - offset]`, `[FP + offset]`).
  - Uniform `TargetInstruction` and `TargetProgram` representations with cost modeling and JSON serialization.
- **Instruction Selection & Cost Model (`vela.codegen.selector`, `costs`)**:
  - Pattern-matching / maximal munch selector translating TAC instructions to target instructions with exact `tac_index` links and rule names.
  - Cost model assigning base execution cycles (MOV: 1, LOAD/STORE: 2, ADD/SUB/CMP: 1, MUL: 3, DIV/MOD: 5, CALL/RET: 2, ALLOC: 3).
- **Register Allocation & Descriptors (`vela.codegen.regalloc`)**:
  - Implementation of Dragon Book Algorithm 8.7 (`getReg`).
  - Register descriptors tracking variables held in each register; address descriptors tracking memory/register locations for each variable.
  - Multi-pass backward def-kill next-use distance tracking to ensure temporaries release registers at their last use.
  - Spill heuristic selecting variables with farthest next-use and emitting `STORE [FP - offset], R_spill`.
- **DAG-Based Code Generation (`vela.codegen.dag_codegen`)**:
  - Ershov / topological ordering over Expression DAGs to minimize register pressure and spill operations.
- **Target Code Peephole Optimization (`vela.codegen.peephole`)**:
  - Machine-dependent sliding window optimizer (window size 2–3) eliminating redundant moves (`MOV R, R`), dead moves after stores, store-load forwarding, algebraic identities, and branch inversions.
- **Virtual Machine Architecture (`vela.vm.cpu`, `memory`, `machine`)**:
  - Simulated CPU with 8 general registers, stack pointer, frame pointer, flags, and program counter.
  - Segmented memory with read-only code segment, symbol-indexed static data segment, activation stack frames, and bounds-checked heap array storage.
  - Reversible step snapshots (up to 5,000 steps) enabling step-by-step backward execution in Vela Studio.
  - Strict runtime limits and diagnostics: `VL-RUN-001` (div-by-zero), `VL-RUN-002` (bounds), `VL-RUN-003` (EOF), `VL-RUN-004` (integer overflow), `VL-RUN-005` (cast out-of-range), `VL-RUN-006` (stack overflow), `VL-RUN-007` (instruction budget), `VL-RUN-008` (output limit).
  - 100% exact stdout match against oracle and language specs across all 10 standard language examples.
- **End-to-End Pipeline & CLI (`vela.pipeline`, `vela.cli`)**:
  - Phase-gated compiler driver (`compile_source`) chaining Lexer $\to$ Parser $\to$ Semantic $\to$ IR $\to$ CFG $\to$ Opt $\to$ Codegen $\to$ Peephole with high-resolution phase timings in milliseconds.
  - Command-line interface with subcommands `compile`, `run`, `verify`, and `selftest`.
  - Automated self-test runner verifying 50 bundled programs (10 examples, valid programs, 39 error catalogue programs) with 100% pass rate.

### Key Algorithms & Design Choices
1. **Dragon Book Algorithm 8.7 (`getReg`)**:
   When assigning a register for $x = y \text{ op } z$, the allocator first attempts to reuse the register holding $y$ if $y$ has no subsequent uses. If unavailable, it selects any free register. If all 8 registers are occupied, it selects the register holding the value whose next use is farthest in the future (Belady's optimal spill principle) and emits `STORE [FP - offset], R_spill`.
2. **Multi-Pass Backward Next-Use with Def-Kill**:
   In programs containing loops and control branches, linear forward scans overestimate liveness. The register allocator executes a multi-pass backward analysis that propagates next-uses across jump targets while killing definitions ($Live_{in} = Use \cup (Live_{out} \setminus Def)$), ensuring temporaries die immediately after their final use and preventing register leaks.
3. **Global State and Calling Conventions**:
   Global variables are mapped directly to memory references (`MemoryRef(symbol=...)`) in the data segment. During function calls (`CALL`), activation records preserve the return address and caller frame pointer. Because global variables reside in the data segment rather than caller-saved register slots, inter-procedural mutations (such as in `10_scopes.vela`) remain coherent across function calls.
4. **Step Reversibility via Historical Snapshots**:
   The VM captures compact state snapshots (PC, registers, condition flags, output length, stack depth) before each instruction execution. When the user steps backward in the UI, the VM pops the previous snapshot and restores CPU registers and memory state, providing time-travel debugging without process re-forking.

### Viva Q&A
1. **Q: How does Algorithm 8.7 determine which register to spill when register pressure exceeds 8?**
   **A:** The allocator inspects the address and register descriptors for all currently occupied registers and consults the next-use distance table for each held variable. It chooses the register containing the variable whose next use is farthest in the future (or has no next use). If that variable has no other valid copy in memory, it emits `STORE [FP - offset], R_spill`, allocates a stack slot relative to the frame pointer `FP`, and updates the variable's address descriptor to record that it now resides in memory.
2. **Q: Why are global variables addressed via memory references (`[symbol]`) rather than kept in registers across the whole program?**
   **A:** In a program with multiple functions, any function can read or mutate global variables. If a global variable were pinned to a register in `main`, and `main` called a helper function that modified the global variable, the helper's modification would either be overwritten when `main`'s registers were restored upon `RET`, or the helper would be unable to access the variable if it used a different register. Using memory-direct addressing (`[symbol]`) guarantees that all functions read and write the single authoritative location in the VM's static data segment.
3. **Q: How does the phase-gated compilation pipeline satisfy requirement AP-8?**
   **A:** Principle AP-8 requires that when an early compiler phase detects an error, downstream phases are skipped to avoid cascading syntax/semantic noise, while earlier phase results remain completely intact and queryable by the UI. In `vela.pipeline.compile_source`, after each phase (Lexer, Parser, Semantic), the pipeline checks `result.diagnostics` for errors. If an error exists, it records `result.halted_at_phase` and returns immediately without running subsequent phases, allowing the UI (such as Lexer Explorer or Syntax Trees) to display all valid structures parsed up to the point of failure.


---

## Milestone M8 — FastAPI Backend & OpenAPI Interface

### What the modules do
- **`backend.api.schemas`**: Pydantic models for request and response payloads across all compiler phases (`CompileRequest`, `CompileResponse`, `RunRequest`, `RunResponse`, `VerifyRequest`, `VerifyResponse`, `GrammarAnalyzeRequest`, etc.). All fields are strictly typed, serializable to JSON, and adhere to OpenAPI 3.1.
- **`backend.api.routes.compiler`**: Endpoints for full compilation (`/api/compile`), execution (`/api/run`), semantic tri-way equivalence verification (`/api/verify`), and automated selftest corpus execution (`/api/selftest`).
- **`backend.api.routes.grammar`**: Dedicated endpoints powering the Grammar & Parsing Lab: `/api/grammar/analyze` (FIRST/FOLLOW sets and Chomsky classification), `/api/grammar/transform` (left-recursion elimination and left factoring), `/api/grammar/ll1`, `/api/grammar/lr`, `/api/grammar/op-precedence`, `/api/grammar/rd-pseudocode`, and `/api/grammar/sdd`.
- **`backend.api.routes.docs`**: Endpoints serving project specification markdown files (`/api/docs`, `/api/docs/{name}`) and bundled example programs (`/api/examples`, `/api/examples/{id}`).
- **`backend.api.main`**: FastAPI application entry point configuring CORS middleware for Vite (port 5173), request body size limiting middleware (rejecting payloads over 1MB with HTTP 413), and OpenAPI JSON export.
- **`scripts.export_schema`**: Automated generator exporting `openapi.json` from FastAPI and compiling strict TypeScript definitions (`frontend/src/api/schema.d.ts`) using `openapi-typescript`.

### Key Algorithms & Design Choices
1. **Zero-Mock Architecture (AP-4 Compliance)**:
   The backend API serves as the single source of truth for the entire IDE. Every number, token, tree node, symbol table, quadruple, control-flow edge, register descriptor, and execution step displayed in the frontend is computed by the pure Python compiler library and delivered over JSON contracts.
2. **Tri-Way Equivalence Verification (`/api/verify`)**:
   Provides cryptographic-level confidence in compiler correctness by executing the user's program across three independent engines:
   1. Unoptimized TAC Oracle (doc 09)
   2. Optimized TAC Oracle (doc 10)
   3. Target ISA Virtual Machine (doc 11)
   Compares exit codes and standard output streams, proving that optimization passes preserve semantic behavior identically.
3. **Automated Selftest Suite (`/api/selftest`)**:
   Runs all 50 test programs in the bundled corpus (10 valid examples, 1 edge-case register-pressure program, 39 error-handling programs from doc 01 §16) and reports individual execution statuses and error codes, providing instant regression detection directly in the browser.

### Viva Q&A
1. **Q: How does the FastAPI backend guarantee that the pure compiler library remains decoupled from web concerns?**
   **A:** By adhering to architectural rule AP-1 and doc 02 §3: `backend/vela` contains zero imports of FastAPI, Starlette, Pydantic, or any web framework. All API routers in `backend/api/` import the pure compiler library as a consumer, convert Pydantic request models into compiler options, invoke `compile_source()` or `run_program()`, and map the resulting pure dataclasses back into Pydantic response models.
2. **Q: How is type safety maintained between the Python backend and TypeScript frontend?**
   **A:** The script `scripts/export_schema.py` inspects the FastAPI OpenAPI schema at compile time, writes `openapi.json`, and runs `openapi-typescript` to generate `frontend/src/api/schema.d.ts`. Any schema mismatch between backend dataclasses and frontend UI components results in a TypeScript build failure during `npm run build`.

---

## Milestone M9 — Vela Studio Frontend (Vite + React 18 + Tailwind + Monaco + React Flow)

### What the modules do
- **Layout & Shell (`AppShell`, `ActivityBar`, `TitleBar`, `PhaseBar`, `StatusBar`)**:
  48px icon sidebar for routing, header toolbar with example loader and O0/O1 compiler switches, 7-chip pipeline phase navigator with live diagnostic badges, and status bar showing execution timings and backend health.
- **State Management (`compileStore`, `uiStore`, `labStore`)**:
  Zustand stores managing source code, stdin, compilation artifacts, AST/TAC inspection data, Grammar Lab inputs/outputs, JSON inspection drawers, and command palette state.
- **Editor Features (`monarch.ts`, `snippets.ts`)**:
  Monaco Monarch language definition for Vela with keyword coloring, type highlighting, bracket matching, and standard code snippets.
- **Shared Pedagogical Components**:
  - `DataTable`: Generic sortable, filterable table with line-number column and source-span hover highlighting.
  - `StepPlayer`: Interactive time-travel scrubber (Play, Pause, Step Forward, Step Back, Reset, Speed Slider).
  - `GraphCanvas`: Interactive node-edge visualizer powered by `@xyflow/react` and `@dagrejs/dagre` hierarchical layout.
  - `DiffView`: Split/Unified side-by-side comparison view with line-level diff highlighting.
  - `DiagnosticList`: Problem list with severity filters, error code chips, and source navigation.
- **12 Dedicated Pages**:
  - `DashboardPage`: Interactive pipeline overview, quickstart example cards, 50-program automated selftest runner, and syllabus coverage explorer.
  - `PlaygroundPage`: Monaco code editor, terminal output console, stdin input box, problems drawer, and 3-way equivalence verification button.
  - `LexerPage`: Token stream table with category filters, token specification tables, DFA finite state machine graph, character scan trace StepPlayer, two-buffer simulation with adjustable buffer size, and lexical diagnostics.
  - `ParserPage`: Concrete Syntax Tree (CST) graph canvas with symbol search, recursive-descent call trace StepPlayer with active call stack, Grammar G' viewer, and panic-mode error recovery diagnostics.
  - `GrammarLabPage`: 6 parsing theory tabs: FIRST/FOLLOW fixed-point derivation, Chomsky classification, left-recursion elimination & left-factoring step logs, LL(1) predictive parse table & trace, LR family (LR(0), SLR(1), CLR(1), LALR(1)) ACTION/GOTO tables & shift-reduce trace, Operator Precedence relations matrix, and Dangling Else guided demo.
  - `SemanticPage`: Type checks table, hierarchical scope symbol tables with lexical depth inspection, scope management event log StepPlayer, type cast resolution table, and live SDD/SDT attribute grammar evaluator with S/L classification.
  - `TreesPage`: Interactive typed AST graph with inferred type badges and source span toggles, S-expression viewer, and basic block expression DAG with local value numbering, common subexpression sharing, and node savings stat strip.
  - `IRPage`: TAC quadruples DataTable with source span highlighting, translation rule provenance (While, Short-Circuit Booleans), basic block cards, Algorithm 8.5 leader derivation StepPlayer, and interactive CFG GraphCanvas with back-edges and dominator toggle.
  - `OptimizerPage`: 8 optimization passes checklist (Local/Global/Loop/Machine badges), DiffView before/after TAC comparison, transformations log with original vs replacement TAC, instruction count reduction metrics, and live tri-way semantic equivalence verification against O0 oracle, O1 oracle, and target VM.
  - `CodeGenPage`: Target instruction table linked to TAC quadruples via `tac_index` (AC-C1), instruction cost sum equaling displayed total (AC-C2), register allocation StepPlayer with physical register descriptors R0–R7 (AC-C3), variable address descriptors, spill/load event indicators (AC-C4 on `regpressure.vela`), Ershov DAG-order cost comparison (AC-C5), and 24-instruction ISA reference flyout.
  - `VMPage`: 3-column architecture: disassembly program view with active PC indicator and gutter breakpoints, machine state view with R0–R7 (highlighted value changes), control registers (PC, SP, FP), flags (ZF, SF), stack frame slots, and execution console with accumulated stdout, truncation banner (AC-V4), faulting instruction alerts (AC-V3), and step-by-step backward state restoration (AC-V2).
  - `ReferencePage`: Language Tour & Spec (live keywords and precedence table matching `/api/language` AC-R1), Formal Grammar properties (G vs G' properties table from doc 01 §13.4), exhaustive Error Catalogue covering all 47 codes with reasons, invalid samples and fixes (AC-R2), Examples Library with "Open in Playground" action (AC-R3), and dynamic Specification Documents reader (`/api/docs/{name}`) with cross-cutting text search (AC-R4 finds "dangling").

### Viva Q&A
1. **Q: How does the frontend prevent hard-coded compiler logic from creeping into React components (Golden Rule AP-4)?**
   **A:** Every page component is completely stateless with respect to compiler algorithms. When the user modifies source code or loads an example, the action dispatches to `compileStore.compile()`, which issues an HTTP POST to `/api/compile`. The backend compiler runs the real parser, checker, optimizer, and code generator, returning the complete payload. The React components only render the returned arrays and graphs using shared components (`DataTable`, `GraphCanvas`, `StepPlayer`).
2. **Q: How does the CST in ParserPage differ from the AST in TreesPage?**
   **A:** The CST (Concrete Syntax Tree) represents the exact parse tree produced by the grammar rules, containing every terminal punctuation symbol (semicolons, parentheses, braces) and intermediate non-terminal expansions (e.g., `StmtList`, `ExprStmt`). The AST (Abstract Syntax Tree) is an abstract semantic representation where syntax overhead is discarded, operator nodes directly link their operands, and nodes are annotated with semantic types, symbol references, and source spans.

---

## Milestone M10 — Verification Suite, Architecture Rules, and Final Capstone Audit

### What the modules do
- **`backend.tests.test_architecture_rules`**: Automated architectural integrity test enforcing:
  1. Pure Python compiler library rule (doc 02 §3): zero web imports in `backend/vela`.
  2. Zero-mock golden rule (AP-4): scans `frontend/src/pages` to ensure no mock compiler data exists.
  3. Complete error coverage (doc 01 §12): validates that all 47 diagnostic error codes are registered in the compiler.
  4. Runtime BNF loading: verifies that `docs/grammar/vela.bnf` and `docs/grammar/vela_ll1.bnf` are loaded and parsed dynamically.
- **`frontend.src.tests.routes.test.ts`**: Vitest integration test verifying all 12 Studio pages, store initialization, Monarch language tokenization, and Monaco editor snippets.
- **`scripts.test.ps1`**: Unified test execution harness executing backend pytest tests (199 test cases), ruff linting, frontend vitest tests, and Vite production bundle compilation in a single command.
- **`DEMO_SCRIPT.md` & `README.md`**: Complete viva defense guide and installation instructions enabling a 10-minute live demonstration of the compiler and IDE.

### Key Verification Metrics
- **Backend Test Suite**: 199 tests passing in ~90s across all compiler phases with 0 failures and 0 regressions.
- **Frontend Test Suite**: 6 vitest tests passing in <10ms; TypeScript typecheck (`tsc --noEmit`) passes with 0 errors.
- **Production Build**: Complete Vite production bundle compiles cleanly with gzip assets in ~20s.
- **Selftest Corpus**: 50 bundled programs verified at 100% pass rate.
- **Doc 00 §4 Requirement Coverage**: 100% of all functional requirements satisfied with verifiable code and test evidence.
