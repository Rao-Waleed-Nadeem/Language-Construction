# Implementation Status
Last updated: 2026-11-21   Run #: 1

## Task table
| ID | Task | Status | Verified by (command → result) | Date | Notes |
|----|------|--------|--------------------------------|------|-------|
| M0-T1 | Skeleton and tooling | DONE | `powershell -File .\scripts\test.ps1` → 2 passed, ruff clean, tsc clean; `npm run build` → exit 0; pure import OK | 2026-11-21 | Workspace, backend venv, frontend, scripts |
| M0-T2 | Common foundations | DONE | `powershell -File .\scripts\test.ps1` → 8 passed; covers normalization, line/col conversion, all 47 diagnostic codes | 2026-11-21 | SourceFile, Span, Diagnostic, Limits, Budget |
| M1-T1 | Language tables | DONE | `powershell -File .\scripts\test.ps1` → 15 passed; asserts exactly 26 keywords, operators, delimiters, precedence, regexes | 2026-11-21 | spec.py single source of truth |
| M1-T2 | DFA, buffer, scanner | DONE | `powershell -File .\scripts\test.ps1` → 27 passed; verifies all token classes, longest match, buffer refill, INV-LEX-01..07, 10/10 examples | 2026-11-21 | DFA-driven scanner, InputBuffer, maximal munch |
| M2-T1 | Model, loader, analysis | DONE | `powershell -File .\scripts\test.ps1` → 33 passed; loads 13/13 .bnf files, FOLLOW(IfStmt) has no else, AP-5 grammar-lexer consistency | 2026-11-21 | BNFLoader, GrammarAnalysis, ChomskyClassifier |
| M2-T2 | Transformations | DONE | `powershell -File .\scripts\test.ps1` → 36 passed; eliminates indirect/immediate left recursion, left factors common prefixes, generates step logs | 2026-11-21 | Algorithm 4.19 and 4.22 in transform.py |
| M2-T3 | LL(1) tools | DONE | `powershell -File .\scripts\test.ps1` → 42 passed; vela_ll1 0 conflicts, vela.bnf 19 conflicts, presets report conflicts, ll1_expr parses tokens | 2026-11-21 | LL1Table, conflicts, predictive parser, rdgen |
| M2-T4 | LR family | DONE | `powershell -File .\scripts\test.ps1` → 51 passed; reproduces all golden metrics: vela.bnf LR(0)=214, SLR(1)=214/0, LALR(1)=214/0, CLR(1)=609/0; presets verified | 2026-11-21 | LRBuilder, ShiftReduceParser, OperatorPrecedenceTable |
| M3-T1 | AST nodes | DONE | `powershell -File .\scripts\test.ps1` → 55 passed; verifies all AST node types, spans, ImplicitCast, and S-expression/JSON serialization | 2026-11-21 | ASTNode hierarchy, ASTPrinter |
| M3-T2 | Recursive-descent parser | DONE | `powershell -File .\scripts\test.ps1` → 69 passed; verifies all 10 examples, INV-SYN-01..08, nesting limit VL-SYN-003, and differential testing with SLR(1) | 2026-11-21 | RecursiveDescentParser, PanicModeRecovery, CST, differential testing |
| M4-T1 | Types and symbols | DONE | `powershell -File .\scripts\test.ps1` → 76 passed; verifies scopes, shadowing, redeclaration in same scope, use tracking, all-paths return analysis, type conversions & operator typing | 2026-11-21 | types.py, symbols.py, returns.py |
| M4-T2 | Checker | DONE | `powershell -File .\scripts\test.ps1` → 98 passed; verifies INV-SEM-01..19 exact codes/positions, all 10 examples pass cleanly, conversion table, implicit casts | 2026-11-21 | SemanticChecker in checker.py |
| M4-T3 | SDD/SDT engine | DONE | `powershell -File .\scripts\test.ps1` → 104 passed; verifies S-attributed & L-attributed classification, safe evaluator, cycle detection, right-sibling dependency detection, 4 presets | 2026-11-21 | SDDEngine, SafeSDDEvaluator, classifier, presets |
| M4-T4 | Expression DAG | DONE | `powershell -File .\scripts\test.ps1` → 111 passed; verifies value numbering, commutativity normalization, basic block def-kill, node counts, and (a+b)*2 & (a+b)*3 sharing | 2026-11-21 | DAG, DAGBuilder, value numbering, test_dag.py |
| M5-T1 | TAC model and generator | DONE | `powershell -File .\scripts\test.ps1` → 120 passed; verifies golden TAC for all constructs (declarations, arithmetic, if/else, switch, loops, break/continue, calls, arrays, casts, show/read), short-circuit boolean lowering, all jump labels exist, all 10 examples compile | 2026-11-21 | TACProgram, TACGenerator, TACPrinter, test_tac_generator.py |
| M5-T2 | TAC interpreter (oracle) | DONE | `powershell -File .\scripts\test.ps1` → 139 passed; 10/10 examples match *.expected.txt exactly, INV-RUN-01..05 match exact codes/coords, 32-bit wrap, truncating div, I/O limits | 2026-11-21 | TACInterpreter, ExecutionResult, test_interpreter.py |
| M6-T1 | Blocks, CFG, dominators, loops | DONE | `powershell -File .\scripts\test.ps1` → 143 passed; verifies basic blocks partitioning, CFG dot/json export, Lengauer-Tarjan dominator tree, dominance frontiers, and natural loop detection | 2026-11-21 | BasicBlock, CFG, DominatorTree, Loop, test_cfg.py |
| M6-T2 | Data-flow framework | DONE | `powershell -File .\scripts\test.ps1` → 147 passed; verifies generic worklist solver, bit-vector transfer functions for Reaching Definitions, Live Variables, Available Expressions, Available Copies | 2026-11-21 | DataFlowFramework, ReachingDefs, LiveVars, AvailExprs, AvailCopies, test_dataflow.py |
| M6-T3 | Passes | DONE | `powershell -File .\scripts\test.ps1` → 154 passed; verifies constant folding/propagation, copy propagation, dead-code elimination, common subexpression elimination, loop-invariant code motion, fixed-point driver, and TAC validation | 2026-11-21 | passes.*, pipeline, validate, test_opt_passes.py |
| M7-T1 | ISA, cost, selection | DONE | `powershell -File .\scripts\test.ps1` → 158 passed; verifies 8 general registers R0-R7, target instruction set, cost model, maximal munch tree/pattern matching instruction selector | 2026-11-21 | TargetInstruction, TargetProgram, costs, selector, test_selector.py |
| M7-T2 | Registers and DAG code generation | DONE | `powershell -File .\scripts\test.ps1` → 162 passed; verifies Algorithm 8.7 getReg, descriptors, spilling, next-use distance, Ershov DAG codegen, window-3 peephole optimizer | 2026-11-21 | RegisterAllocator, DAGCodeGenerator, peephole, test_regalloc.py |
| M7-T3 | VM | DONE | `powershell -File .\scripts\test.ps1` → 166 passed; verifies CPU registers R0-R7, SP, FP, PC, flags ZF/SF, segmented memory, step/step_back reversibility (5,000 cap), runtime diagnostics VL-RUN-001..008, and exact 10/10 language examples stdout match | 2026-11-21 | VMCPU, VMMemory, VirtualMachine, test_vm.py |
| M7-T4 | Pipeline and CLI | DONE | `powershell -File .\scripts\test.ps1` → 174 passed; verifies phase-gated pipeline compile_source, timings, VM and TAC oracle execution, CLI subcommands (compile, run, verify, selftest), and 50/50 (100%) passing selftest corpus | 2026-11-21 | compile_source, run_program, cli, test_pipeline_cli.py |
| M8-T1 | FastAPI | DONE | `powershell -File .\scripts\test.ps1` → 195 passed; 21 API tests pass; openapi.json and schema.d.ts generated; ruff clean; tsc clean | 2026-11-21 | FastAPI app, compiler/grammar/docs routes, Pydantic schemas, middleware, schema export |
| M9-T1 | Shell and shared components | DONE | `cd frontend; npx tsc --noEmit` → exit 0; `npm run build` → exit 0 (built in 58s) | 2026-11-21 | Theme tokens, typed api client, Zustand stores (compile, ui, lab), layout (ActivityBar, TitleBar, PhaseBar, StatusBar, AppShell), shared components (DataTable, StepPlayer, GraphCanvas, DiffView, SourceView, DiagnosticList, ExplainPanel, JsonDrawer, CommandPalette) |
| M9-T2 | Playground and Dashboard | DONE | `cd frontend; npx tsc --noEmit` → exit 0; `npm run build` → exit 0 (built in 3.98s) | 2026-11-21 | Dashboard (pipeline overview, quickstart cards, 50-program automated selftest runner, syllabus coverage) and Playground (Monaco editor, output console, DiagnosticList problems, stdin, 3-way oracle verification) |
| M9-T3 | Lexer and Parser pages | DONE | `cd frontend; npx tsc --noEmit` → exit 0; `npm run build` → exit 0 (built in 6.64s) | 2026-11-21 | LexerPage (Tokens table with category filter, token specification from /api/language, DFA FSM graph, character-by-character scan trace, two-buffer simulation with configurable buffer size, lexical diagnostics) and ParserPage (interactive Concrete Syntax Tree graph with symbol search, recursive-descent call trace with call stack and lookahead, G' LL(1) grammar view, panic mode syntax error recovery) |
| M9-T4 | Grammar Lab | DONE | `cd frontend; npx tsc --noEmit` → exit 0; `npm run build` → exit 0 (built in 13.52s) | 2026-11-21 | GrammarLabPage with 6 comprehensive tabs: Analysis (FIRST/FOLLOW sets, derivation StepPlayer, Chomsky classifier), Transform (left recursion elimination & left factoring with step logs), LL(1) Table & predictive parse trace with RD generator, LR Family (LR0, SLR1, CLR1, LALR1 with ACTION/GOTO tables & shift-reduce trace), Operator Precedence (leading/trailing, matrix, trace), and Dangling Else guided demo |
| M9-T5 | Semantic and Trees pages | DONE | `cd frontend; npx tsc --noEmit` → exit 0; `npm run build` → exit 0 (built in 7.29s) | 2026-11-21 | SemanticPage (Type checks table, scope symbol tables, scope event log StepPlayer, type conversions/casts, SDD/SDT attribute grammar evaluator) and TreesPage (typed AST graph with type/span toggles, S-expression viewer, basic block expression DAG with value numbering and 36.4% node savings) |
| M9-T6 | IR and Optimizer pages | DONE | `npm --prefix frontend run build` → exit 0 (built in 6.91s); `tsc` clean | 2026-11-21 | IRPage (TAC quadruples DataTable, translation rule provenance, basic blocks cards, Algorithm 8.5 leader derivation StepPlayer, and CFG GraphCanvas with dominator toggle) and OptimizerPage (pass checklist with Local/Global/Loop/Machine badges, DiffView before/after TAC, transformations log, instruction reduction metrics, and tri-way semantic equivalence verification) |
| M9-T7 | CodeGen and VM pages | DONE | `npm --prefix frontend run build` → exit 0 (built in 6.71s); `tsc` clean | 2026-11-21 | CodeGenPage (Target instructions DataTable with tac_index origin alignment, total cost equals sum of instruction costs AC-C2, peephole status, register allocation StepPlayer with R0-R7 descriptors AC-C3, address descriptors, spill/load events AC-C4, Ershov DAG code generation cost comparison AC-C5, and ISA reference flyout) and VMPage (3-column layout: Program disassembly with PC highlight & breakpoints, Machine state with registers R0-R7, SP, FP, PC, ZF/SF flags, stack frame view, and Console with stdout stream, truncation banner AC-V4, faulting instruction alert AC-V3, and exact state reversibility StepBackward AC-V2) |
| M9-T8 | Reference page | DONE | `npm --prefix frontend run build` → exit 0 (built in 6.13s); `tsc` clean | 2026-11-21 | ReferencePage with Table of Contents (Language Tour with live keywords and operator precedence table AC-R1, Formal Grammar & parsing properties table G vs G' doc 01 §13.4, Error Catalogue covering all 47 error codes AC-R2 with sample code and fixes, Examples Library with Open in Playground AC-R3, and Specification Documents viewer via /api/docs/{name}) with global cross-document search AC-R4 (e.g. "dangling") |
| M10-T1 | End-to-end suite | DONE | `powershell -File .\scripts\test.ps1` → 199 pytest passed, ruff clean, 6 vitest passed, tsc clean, production bundle built in 20.36s | 2026-11-21 | test_architecture_rules.py (doc 02 §3 pure Python compiler rule, AP-4 no fake compiler data in pages, doc 01 §12 all 47 error codes, runtime input .bnf loaders), frontend routes & store integration tests, scripts/test.ps1 full verification pipeline |
| M10-T2 | Docs, demo and final audit | TODO | | | |

## Requirement coverage (doc 00 §4)
| Requirement ID | Description | Status | Evidence |
|---|---|---|---|
| LD-02 | Keywords and reserved words (26) | SATISFIED | `test_keywords_count_and_uniqueness` asserts 26 keywords |
| LD-15 | Mandatory data types int, float, char, string, bool | SATISFIED | `test_base_types` asserts all 5 base types |
| LD-17 | Mandatory arithmetic `+ - * / %` | SATISFIED | `test_operators` in `test_language_spec.py` |
| LD-18 | Mandatory relational `> < >= <= == !=` | SATISFIED | `test_operators` in `test_language_spec.py` |
| LD-19 | Mandatory logical AND, OR, NOT | SATISFIED | `test_operators` in `test_language_spec.py` |
| P1-02 | Identify keywords, identifiers, literals, operators | SATISFIED | `vela.language.spec` tables and unit tests |
| P1-05 | Operator precedence and associativity | SATISFIED | `test_precedence_table` 8 levels verified |
| P2-01 | Regular expressions for tokens | SATISFIED | `test_token_regexes` in `test_language_spec.py` |
| LD-03 | Identifiers and naming conventions | SATISFIED | `IdentifierDFA`, 64-char limit check, `test_scanner.py` |
| LD-14 | Comments and delimiters | SATISFIED | Line comments `//`, block comments `/*...*/`, delimiters verified |
| P2-02 | Finite state machines for token recognition | SATISFIED | `fsm.py` explicit DFAs and simulation path traces |
| P2-03 | Identify tokens and lexemes | SATISFIED | `Token` class and `Scanner.scan()` in `tokens.py`/`scanner.py` |
| P2-04 | Recognize keywords, identifiers, operators, literals | SATISFIED | `test_token_classes_and_literals` in `test_scanner.py` |
| P2-05 | Implement input buffering | SATISFIED | `InputBuffer` two-buffer scheme with sentinels and refill trace |
| P2-06 | Handle lexical errors | SATISFIED | `test_inv_lex_01` through `07` assert exact codes/positions |
| P2-07 | Output keyword (show) recognized as reserved token | SATISFIED | `test_keyword_vs_identifier` asserts show=KEYWORD, shown=ID |
| P2-08 | Scanner implemented manually with explicit DFAs | SATISFIED | Hand-written `Scanner` with `NumberDFA`, `IdentifierDFA`, `OperatorDFA` |
| PR-04 | Compiler built according to language grammar and rules | SATISFIED | `test_grammar_lexer_consistency.py` verifies AP-5 terminal equivalence |
| P1-04 | Formal grammar productions in BNF | SATISFIED | `BNFLoader` verifies golden values for `vela.bnf` (121/47/59) and `vela_ll1.bnf` (138/65/59) |
| P1-06 | Identify and resolve grammar ambiguities | SATISFIED | Mandatory braces proven: `FOLLOW(IfStmt)` contains no `else` |
| P1-07 | Classify grammar in Chomsky hierarchy with justification | SATISFIED | `classify_grammar` identifies Type 2 (Context-Free) with detailed reason |
| P3-04 | FIRST and FOLLOW sets | SATISFIED | `GrammarAnalysis` fixed-point computation with step logs |
| P3-05 | Left-recursion elimination | SATISFIED | `eliminate_left_recursion` handles immediate & indirect left recursion with step logs |
| P3-06 | Left factoring | SATISFIED | `left_factor` algorithm extracts common prefixes with step logs |
| P3-03 | LL(1) parsing | SATISFIED | `LL1Table` table construction, conflict detection (G' 0 conflicts, G 19 conflicts), predictive parser |
| P3-07 | Ambiguous-grammar resolution incl. dangling else | SATISFIED | S/R conflict detection and precedence/associativity resolution verified on `expr_ambiguous` |
| P3-08 | Operator-precedence parsing | SATISFIED | `OperatorPrecedenceTable` eligibility check, relations, and parsing verified |
| P3-09 | Bottom-up shift-reduce parsing | SATISFIED | `ShiftReduceParser` driver, trace, and parse tree verified on `slr_expr` |
| P3-10 | LR(0) parsing and table construction | SATISFIED | `LRBuilder.build_lr0()` verifies golden 214 states for `vela.bnf` |
| P3-11 | SLR(1) parsing and table construction | SATISFIED | `LRBuilder.build_slr1()` verifies 214 states and 0 conflicts for `vela.bnf` |
| P3-12 | CLR(1) parsing and table construction | SATISFIED | `LRBuilder.build_clr1()` verifies golden 609 states and 0 conflicts for `vela.bnf` |
| P3-13 | LALR(1) parsing and table construction | SATISFIED | `LRBuilder.build_lalr1()` merges by core, verifying golden 214 states and 0 conflicts for `vela.bnf` |
| P4-01 | Construct ASTs | SATISFIED | Complete `ASTNode` hierarchy in `backend/vela/ast/nodes.py` with id, span, and children |
| P4-10 | Type conversion (coercion vs cast) | SATISFIED | `ImplicitCast` and `CastExpr` AST nodes with type metadata |
| P3-01 | Recursive-descent parser | SATISFIED | `RecursiveDescentParser` implementing G' with CST and call trace in `backend/vela/parser/` |
| P3-02 | Syntactic error recovery | SATISFIED | `PanicModeRecovery` handles INV-SYN-01..08, multiple errors in one pass (INV-SYN-08) |
| P1-01 | Top-down and bottom-up parsing comparison | SATISFIED | Differential testing in `test_parser.py` proves RD and SLR(1) agreement on examples & mutations |
| P4-04 | Symbol table operations | SATISFIED | `SymbolTable`, `Scope`, `Symbol` with offsets, uses, attributes in `vela.semantic.symbols` |
| P4-05 | Scope resolution and shadowing | SATISFIED | Block, function, for-header, case scopes with shadowing detection and event logs |
| P4-06 | Type checking mechanism | SATISFIED | `vela.semantic.types` tables, operator typing, assignment rules, implicit/explicit conversions |
| P4-02 | Semantic error handling | SATISFIED | `SemanticChecker` handles INV-SEM-01..19, array bounds, duplicate labels, missing main |
| P4-03 | Type checking and semantic validation | SATISFIED | Full semantic validation, operator typing (+ overload), void misuse (VL-SEM-023), ImplicitCast |
| P4-07 | Syntax-Directed Definitions (SDD) | SATISFIED | S-attributed and L-attributed classification, dependency graph, topological evaluation, 4 presets |
| P4-08 | Syntax-Directed Translation (SDT) | SATISFIED | SDD/SDT execution engine with cycle detection and safe evaluator |
| P4-09 | Directed Acyclic Graphs (DAGs) for expressions | SATISFIED | Expression DAG with value numbering, commutativity normalization, build trace, node savings |
| P5-01 | Intermediate code generator producing Three-Address Code | SATISFIED | `ir/generator.py`, `tac.py`, `printer.py` generating well-formed quadruples |
| P5-02 | Variable declarations | SATISFIED | Global startup and local variable initializers lowered to `ASSIGN` and `ARRAY_SET` |
| P5-03 | Arithmetic expressions | SATISFIED | `ADD`, `SUB`, `MUL`, `DIV`, `MOD`, `NEG` with temporaries and widening |
| P5-04 | IF-ELSE statements | SATISFIED | Conditional branches (`JUMP_IF_FALSE`, `JUMP`) and labels |
| P5-05 | Nested conditions | SATISFIED | Nested if/else branch lowering and label validation |
| P5-06 | SWITCH-CASE statements | SATISFIED | Compare chain on cases, jumps to bodies, default handling, break to exit |
| P5-07 | FOR loops | SATISFIED | Header initialization, condition check, update label target for continue |
| P5-08 | WHILE loops | SATISFIED | Condition label, conditional jump, exit label, break/continue targets |
| P5-09 | DO-WHILE loops | SATISFIED | Body start label, condition check at bottom, conditional loop jump |
| P5-10 | Function definitions and calls | SATISFIED | `FUNC_BEGIN`, `PARAM`, `CALL`, `RETURN`, `FUNC_END` calling convention |
| P5-11 | Array operations | SATISFIED | `ARRAY_GET` and `ARRAY_SET` index operations |
| P5-12 | (project goal) TAC interpreter as an independent oracle | SATISFIED | `ir/interpreter.py` executing TAC with exact runtime semantics, oracle for all 10 examples and invalid runs |
| P6-01 | Basic block identification | SATISFIED | `opt/blocks.py` with Algorithm 8.5 leader rules and reasons |
| P6-02 | Control-flow graph construction | SATISFIED | `opt/cfg.py`, `dominators.py` with CFG edges, dominator trees, back edges, natural loops |
| P6-03 | DAG-based optimization | SATISFIED | `ast/dag.py` and `opt/passes/cse.py` for local value numbering |
| P6-04 | Constant folding | SATISFIED | `opt/passes/const_fold.py` with 32-bit wrap-around and zero-division safety protection |
| P6-05 | Constant propagation | SATISFIED | `opt/passes/const_prop.py` with local block env and reaching definitions |
| P6-06 | Common-subexpression elimination | SATISFIED | `opt/passes/cse.py` with local expression table and global available expressions |
| P6-07 | Dead-code elimination | SATISFIED | `opt/passes/dce.py` with backward liveness, side-effect and global preservation |
| P6-08 | Copy propagation | SATISFIED | `opt/passes/copy_prop.py` with available copies propagation |
| P6-09 | Loop optimization | SATISFIED | `opt/passes/licm.py` and `strength.py` with natural loop hoisting and multiplication reduction |
| P6-10 | Global optimization: data-flow framework | SATISFIED | `opt/dataflow.py` forward & backward worklist solver, reaching defs, liveness, available exprs/copies, iteration logs |
| P6-11 | Machine-dependent optimization | SATISFIED | `codegen/peephole.py` with sliding window patterns for loads, moves, and jumps |
| P6-12 | Comparison of original vs optimized code | SATISFIED | `opt/pipeline.py` recording before/after diffs, change records, and reduction metrics |
| P6-13 | (project goal) Optimizations preserve behavior | SATISFIED | `opt/validate.py` with well-formedness checks and oracle equivalence on all examples & invalid runs |
| P7-01 | Design a target instruction set | SATISFIED | `codegen/isa.py` with 8 registers (R0-R7), SP, FP, PC, flags, memory displacement |
| P7-02 | Instruction selection | SATISFIED | `codegen/selector.py` mapping TAC quadruples to target instructions with rule provenance |
| P7-03 | Instruction cost calculation | SATISFIED | `codegen/cost.py` with base opcode costs, memory access penalties, and AC-C2 total cost sum |
| P7-04 | Register allocation | SATISFIED | `codegen/regalloc.py` with Algorithm 8.7 getReg, descriptors, spills, AC-C3, AC-C4 |
| P7-05 | Assign registers to temporary variables | SATISFIED | `codegen/regalloc.py` temp_to_location mapping to physical registers or stack slots |
| P7-06 | DAG-based code generation | SATISFIED | `codegen/dag_codegen.py` with Ershov optimal numbering, AC-C5 (DAG cost <= linear cost) |

## Known limitations
None yet.

## Blockers
None.

## Run log
- **Run #1 (2026-11-21):**
  - M0-T1: Workspace skeleton and tooling complete.
  - M0-T2: Common foundations complete (`vela.common.source`, `diagnostics`, `limits`, `budget`). 8 unit tests passing. Milestone M0 complete.
  - M1-T1: Language tables complete (`vela.language.spec`). 15 unit tests passing.
  - M1-T2: Scanner, buffer, DFA simulator complete (`vela.lexer.tokens`, `buffer`, `fsm`, `scanner`). 27 tests passing. Milestone M1 complete.
  - M2-T1: Grammar engine model, loader, analysis, Chomsky classifier complete (`vela.grammar.model`, `loader`, `analysis`, `classify`). 33 tests passing.
  - M2-T2: Transformations complete (`vela.grammar.transform` for immediate & indirect left recursion, left factoring). 36 tests passing.
  - M2-T3: LL(1) tools complete (`vela.grammar.ll1`, `rdgen`). 42 tests passing.
  - M2-T4: LR family and operator precedence complete (`vela.grammar.lr`, `shift_reduce`, `op_precedence`). 51 tests passing. Milestone M2 complete.
  - M3-T1: AST nodes and serialization complete (`vela.ast.nodes`, `printer`). 55 tests passing.
  - M3-T2: Recursive-descent parser complete (`vela.parser.recursive_descent`, `parse_tree`, `recovery`). 69 tests passing. Milestone M3 complete.
  - M4-T1: Types, symbols, scopes, return-path analysis complete (`vela.semantic.types`, `symbols`, `returns`). 76 tests passing.
  - M4-T2: Checker complete (`vela.semantic.checker`). 98 tests passing.
  - M4-T3: SDD/SDT engine complete (`vela.semantic.sdd`). 104 tests passing.
  - M4-T4: Expression DAG complete (`vela.ast.dag`). 111 tests passing. Milestone M4 complete!
  - M5-T1: TAC model and generator complete (`vela.ir.tac`, `generator`, `printer`). 120 tests passing.
  - M5-T2: TAC interpreter oracle complete (`vela.ir.interpreter`). 139 tests passing. Milestone M5 complete!
  - M6-T1: Basic blocks, CFG, dominators, and natural loop detection complete (`vela.opt.blocks`, `cfg`, `dominators`). 143 tests passing.
  - M6-T2: Data-flow analysis framework complete (`vela.opt.dataflow` for reaching definitions, live variables, available expressions, available copies). 147 tests passing.
  - M6-T3: Optimization passes and pipeline complete (`vela.opt.passes.*`, `pipeline`, `validate`). 154 tests passing. Milestone M6 complete!
  - M7-T1: Target ISA, instruction selection, and cost model complete (`vela.codegen.isa`, `cost`, `selector`). 158 tests passing.
  - M7-T2: Register allocation, DAG code generation, and peephole optimization complete (`vela.codegen.regalloc`, `dag_codegen`, `peephole`). 162 tests passing.
  - M7-T3: Virtual Machine simulation and step reversibility complete (`vela.vm.cpu`, `memory`, `machine`). 10/10 language examples match exact stdout, step backward verified, INV-RUN-01..05 runtime errors verified. 166 tests passing.
  - M7-T4: End-to-end compilation pipeline and CLI driver complete (`vela.pipeline`, `vela.cli`). 50/50 test programs in selftest corpus pass at 100%. 174 tests passing. Milestone M7 complete!
  - M8-T1: Complete FastAPI backend, Pydantic schemas, compiler/grammar/docs routes, size-limiting middleware, OpenAPI schema export script (`scripts/export_schema.py`), generated `openapi.json` and strict TypeScript definitions (`frontend/src/api/schema.d.ts`). 21 new API tests passing (195 total tests passing, 0 regressions). Milestone M8 complete!
  - M9-T1: Shell and shared components complete. App shell with ActivityBar (48px left), TitleBar (actions, example picker, O0/O1, auto-compile), PhaseBar (7 chips with status & diagnostic badges), StatusBar (timings, coordinates, 10s health poll), Zustand stores (`compileStore`, `uiStore`, `labStore`), Monaco Monarch language definition, snippets, and complete set of shared components (`DataTable`, `StepPlayer`, `GraphCanvas`, `DiffView`, `DiagnosticList`, `SourceView`, `ExplainPanel`, `JsonDrawer`, `CommandPalette`). `npx tsc --noEmit` and `npm run build` both exit 0 with clean bundle.
  - M9-T2: Playground and Dashboard pages complete. `DashboardPage.tsx` with 7-phase clickable pipeline architecture, 10 example cards with one-click compile/run, automated 50-program self-test suite runner with live pass/fail bar, and syllabus coverage explorer. `PlaygroundPage.tsx` with Monaco editor, file open/save, output console with exit code and step counts, `DiagnosticList` problems tab, stdin stream, and 3-way equivalence verification (`/api/verify`). `tsc --noEmit` and `npm run build` both exit 0 cleanly.
  - M9-T3: Lexer and Parser pages complete. `LexerPage.tsx` with SourceView, Tokens DataTable, token specification tables, DFA state machine visualization, character scan StepPlayer, two-buffer scheme simulation with adjustable buffer size, and lexical diagnostics. `ParserPage.tsx` with SourceView, interactive Concrete Syntax Tree (CST) GraphCanvas with symbol search, recursive-descent call trace StepPlayer with active stack, Grammar G' viewer, and panic-mode error recovery diagnostics. `tsc --noEmit` and `npm run build` both exit 0 cleanly.
  - M9-T4: Grammar Lab page complete. `GrammarLabPage.tsx` with BNF grammar editor, preset loader, and 6 full parsing theory tabs: Analysis (FIRST/FOLLOW sets, fixed-point derivation StepPlayer, Chomsky classifier), Transform (Algorithm 4.19 left-recursion elimination & Algorithm 4.22 left factoring with step-by-step logs), LL(1) Table & predictive parse trace with recursive-descent pseudocode generator, LR Family (LR(0), SLR(1), CLR(1), LALR(1) tables and shift-reduce StepPlayer), Operator Precedence (leading/trailing sets and precedence matrix), and Dangling Else guided 3-preset demo. `tsc --noEmit` and `npm run build` both exit 0 cleanly.
  - M9-T5: Semantic and Trees pages complete. `SemanticPage.tsx` with SourceView, Type checks & rules validator, hierarchical scope symbol tables with lexical level inspection, scope management event log StepPlayer, implicit & explicit cast resolution table, and live SDD/SDT attribute grammar evaluator with S/L attribution classification. `TreesPage.tsx` with interactive typed AST GraphCanvas, inferred type and span toggles, S-expression viewer, and basic block expression DAG with local value numbering, common subexpression sharing, and node savings stat strip. `tsc --noEmit` and `npm run build` both exit 0 cleanly.
  - M9-T6: IR and Optimizer pages complete. `IRPage.tsx` with TAC quadruples DataTable, source span highlighting, translation rule provenance (While, Short-Circuit Booleans, etc.), basic block cards, Algorithm 8.5 leader derivation StepPlayer, and interactive CFG GraphCanvas with back-edges and dominator toggle. `OptimizerPage.tsx` with 8 optimization passes checklist (Local/Global/Loop/Machine badges), DiffView before/after TAC comparison, transformations log with original vs replacement TAC, instruction count reduction metrics, and live tri-way semantic equivalence verification against O0 oracle, O1 oracle, and target VM. `npm --prefix frontend run build` exits 0 cleanly in 6.91s.
  - M9-T7: CodeGen and VM pages complete. `CodeGenPage.tsx` with target instruction table linked to TAC quadruples via `tac_index` (AC-C1), instruction cost sum equaling displayed total (AC-C2), register allocation StepPlayer with physical register descriptors R0–R7 (AC-C3), variable address descriptors, spill/load event indicators (AC-C4 on `regpressure.vela`), Ershov DAG-order cost comparison (AC-C5), and 24-instruction ISA reference flyout. `VMPage.tsx` with 3-column architecture: disassembly program view with active PC indicator and gutter breakpoints, machine state view with R0–R7 (highlighted value changes), control registers (PC, SP, FP), flags (ZF, SF), stack frame slots, and execution console with accumulated stdout, truncation banner (AC-V4), faulting instruction alerts (AC-V3), and step-by-step backward state restoration (AC-V2). `npm --prefix frontend run build` exits 0 cleanly in 6.71s.
  - M9-T8: Reference page complete. `ReferencePage.tsx` with Language Tour & Spec (live keywords and precedence table matching `/api/language` AC-R1), Formal Grammar properties (G vs G' properties table from doc 01 §13.4), exhaustive Error Catalogue covering all 47 codes with reasons, invalid samples and fixes (AC-R2), Examples Library with "Open in Playground" action (AC-R3), and dynamic Specification Documents reader (`/api/docs/{name}`) with cross-cutting text search (AC-R4 finds "dangling"). `npm --prefix frontend run build` exits 0 cleanly in 6.13s. Milestone M9 100% complete!
  - M10-T1: End-to-end verification suite complete. Added `backend/tests/test_architecture_rules.py` asserting doc 02 §3 dependency rules (zero web imports in `backend/vela`), AP-4 compliance (no fake compiler data in `frontend/src/pages`), registration of all 47 diagnostic error codes (doc 01 §12), and runtime `.bnf` loading. Added `frontend/src/tests/routes.test.ts` verifying all 12 concrete studio pages, store initialization, Monarch syntax definition, and code snippets. Integrated into unified `scripts/test.ps1`. All 199 backend tests, ruff lint, 6 vitest tests, and Vite production build pass at 100%. Next: M10-T2 (Docs, demo and final audit).
