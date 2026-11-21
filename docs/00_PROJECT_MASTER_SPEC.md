# 00 — Project Master Specification (Vela Compiler & Vela Studio)

> **Authority:** this is the top-level document. If any other document contradicts it, this one wins; fix the other document.
> **Status:** Batch 1 draft for group review. Batches 2–4 (docs 04–16) are written after the group approves Batch 1.
> **Course:** CS 4031 Compiler Construction — Final Semester Project.

---

## 1. Project in one paragraph

We design an original statically-typed language, **Vela**, and build a complete compiler for it in Python: lexer → recursive-descent parser → AST → semantic analysis → three-address code → basic blocks/CFG → optimizer → target code generator → a custom register-machine virtual machine that really executes the output. Around the compiler we build **Vela Studio**, a dark VS Code–style web app (React + FastAPI) in which every phase’s real output is visualized, plus a **Grammar Lab** that runs the textbook parsing algorithms (FIRST/FOLLOW, LL(1), LR(0), SLR(1), CLR(1), LALR(1), shift-reduce, operator-precedence, left-recursion elimination, left factoring) on any grammar, including Vela’s.

---

## 2. Source of requirements and what it does *not* say

The authoritative source is the course document **“CS 4031 Compiler Construction — Final Semester Project”** (project file `Semester Project.md`). It is a one-page description containing: the project description, the language-design requirements (including the mandatory-constructs table), sample language styles, and Phases 1–7.

**It contains no text about** group size or roles, independent-work rules, permitted use of AI tools, plagiarism policy, deliverables list, submission format, deadlines, grading weights, or the viva format. Either those rules are announced elsewhere (LMS, instructor, other pages) or the extraction is incomplete. **Action for the group (open item OQ-1):** confirm them with the instructor and record the answer in `docs/DECISION_LOG.md` (template in doc 16). Until confirmed, this specification applies the strictest reasonable reading (Section 9): all members understand and can defend every phase; AI assistance is logged; external material is acknowledged.

The traceability matrix below therefore covers every requirement actually present in the document and carries **no invented** requirements. Items we added on our own are marked *(project goal)* so they are never mistaken for assignment text.

---

## 3. Requirement classes

| Class | Meaning | Rule |
|---|---|---|
| **A** | Must be a fully working compiler implementation on the production path | Must run on user programs end-to-end and be tested. |
| **B** | Algorithmic educational demonstration | Must run the **real algorithm on any user-supplied input** (never hard-coded output) and be labelled “Educational module”. |
| **C** | Both: production implementation **and** a visual demonstration | Both must exist and share data where possible. |

No requirement is downgraded: where the assignment asks to “implement”, class is A or C. Where it asks to “study and demonstrate” (LR(0), SLR(1), CLR(1), LALR(1)), class is B with real table construction and real parsing.

---

## 4. Requirement traceability matrix

Columns: **Class** (A/B/C) · **Implementation** (module under `backend/vela/`, see doc 02 §3) · **UI** (page section in doc 03) · **Docs** (specification document that defines it in detail; 04–11 are written in Batches 2–3) · **Verification** (test group in doc 13) · **Pri** (M = mandatory in the assignment text) · **Viva** (explanation topic).

### 4.1 Project-level and language-design requirements

| ID | Requirement (faithful to the assignment) | Cls | Implementation | UI | Docs | Verification | Pri | Viva |
|---|---|---|---|---|---|---|---|---|
| PR-01 | Design our own programming language | C | doc 01; `language/spec.py` | §5.12 | 01 | doc review; examples | M | why Vela’s design choices |
| PR-02 | Build a complete compiler for it that translates programs into target instructions | A | `pipeline.py` | §5.2 | 02 | e2e pipeline tests | M | the full data flow |
| PR-03 | Implement all major phases: lexical, syntax, semantic, SDT, ICG, optimization, target code | A | all packages | pipeline bar §3 | 02, 04–11 | e2e, selftest | M | each phase’s role |
| PR-04 | Compiler built *according to our language’s grammar and rules* | A | grammar files loaded and cross-checked (AP-5) | §5.5 | 01, 06 | grammar–lexer consistency test | M | one grammar → all phases |
| LD-01 | Language name | A | “Vela”, `.vela` | title bar | 01 §1 | — | M | naming |
| LD-02 | Keywords and reserved words | C | `language/spec.py`; lexer keyword table | §5.3, §5.12 | 01 §2.4, 04 | lexer tests | M | keyword table |
| LD-03 | Identifiers and naming conventions | C | identifier DFA | §5.3 | 01 §2.3 | lexer tests | M | identifier regex |
| LD-04 | Data types | C | `semantic/types.py` | §5.6 | 01 §4 | type tests | M | type system |
| LD-05 | Arithmetic and logical operators | C | grammar, checker, TAC | §5.5, §5.6 | 01 §6 | expr tests | M | precedence |
| LD-06 | Relational operators | C | same | same | 01 §6 | expr tests | M | typing of comparisons |
| LD-07 | Assignment operators | C | parser, TAC | §5.4 | 01 §7 | stmt tests | M | compound assignment desugaring |
| LD-08 | Conditional structures | C | parser, TAC | §5.4, §5.8 | 01 §7 | control-flow tests | M | if/else translation |
| LD-09 | Looping structures | C | same | same | 01 §7 | loop tests | M | loop translation |
| LD-10 | Switch-case structure | C | same | same | 01 §7 | switch tests | M | no fall-through, jump table vs compare chain |
| LD-11 | Function declaration and calling syntax | C | parser, semantic, ICG, VM | §5.4, §5.8 | 01 §8 | function tests | M | calling convention |
| LD-12 | Array declaration and access syntax | C | same | same | 01 §9 | array tests | M | array addressing |
| LD-13 | Input/output statements | C | `show` / `read` through VM | §5.2, §5.11 | 01 §10 | I/O tests | M | I/O model |
| LD-14 | Comments and delimiters | C | lexer | §5.3 | 01 §2.2, §2.6 | lexer tests | M | comment handling |
| LD-15 | Mandatory: data types int, float, char, string, bool | C | as LD-04 | §5.6 | 01 §4 | type tests | M | — |
| LD-16 | Mandatory: variable declaration, initialization, assignment | C | parser, semantic, TAC | §5.6, §5.8 | 01 §5 | decl tests | M | default values |
| LD-17 | Mandatory: arithmetic `+ - * / %` | C | as LD-05 | — | 01 §6 | arithmetic tests | M | int wrap, division rules |
| LD-18 | Mandatory: relational `> < >= <= == !=` | C | as LD-06 | — | 01 §6 | relational tests | M | — |
| LD-19 | Mandatory: logical AND, OR, NOT | C | `and` `or` `not`, short-circuit TAC | §5.8 | 01 §6.5 | logic tests | M | short-circuit translation |
| LD-20 | Mandatory: IF, IF-ELSE, nested IF | C | as LD-08 | — | 01 §7 | — | M | — |
| LD-21 | Mandatory: SWITCH-CASE, DEFAULT | C | as LD-10 | — | 01 §7 | — | M | — |
| LD-22 | Mandatory: FOR, WHILE, DO-WHILE | C | as LD-09 | — | 01 §7 | — | M | — |
| LD-23 | Mandatory: functions (declaration, parameters, return) | C | as LD-11 | — | 01 §8 | — | M | — |
| LD-24 | Mandatory: arrays (declaration, initialization, indexing) | C | as LD-12 | — | 01 §9 | — | M | — |
| LD-25 | Mandatory: Read/Input and Print/Output | C | as LD-13 | — | 01 §10 | — | M | — |
| LD-26 | Students may define their own syntax per construct | A | design decision recorded | — | 01 §1, §17 | — | M | design rationale |

### 4.2 Phase 1 — Language specification and grammar

| ID | Requirement | Cls | Implementation | UI | Docs | Verification | Pri | Viva |
|---|---|---|---|---|---|---|---|---|
| P1-01 | Define syntax and semantics of the language | A | doc 01 + checker/VM semantics | §5.12 | 01 | doc audit | M | semantics of each construct |
| P1-02 | Identify keywords, identifiers, literals, operators | C | `language/spec.py` | §5.3, §5.12 | 01 §2, 04 | lexer tests | M | token classes |
| P1-03 | Specify data types and programming constructs | C | as LD-04…25 | §5.12 | 01 §4–10 | — | M | — |
| P1-04 | Formal grammar productions in BNF | C | `docs/grammar/vela.bnf` loaded by `grammar/loader.py` | §5.5, §5.12 | 01 §13, 06 | grammar tests (golden counts) | M | reading the grammar |
| P1-05 | Operator precedence and associativity | C | grammar levels; table | §5.12, §5.5 | 01 §6.1 | parser tests (precedence/associativity cases) | M | why one nonterminal per level |
| P1-06 | Identify and resolve grammar ambiguities | C | mandatory braces; Grammar Lab ambiguity detection (S/R conflicts) | §5.5 Dangling else | 01 §13.2, 06 | AC-G5; SLR conflict-free test | M | three dangling-else resolutions |
| P1-07 | Classify grammar in the Chomsky hierarchy with justification | C | `grammar/classify.py` + text | §5.5 Analysis | 01 §13.5, 06 | classifier tests | M | Type 2 vs Type 3; why semantics is context-sensitive |
| P1-08 | Design overall compiler architecture, explaining phases and components | A | doc 02 | §5.1 Dashboard | 02 | doc audit | M | architecture diagram |

### 4.3 Phase 2 — Lexical analysis

| ID | Requirement | Cls | Implementation | UI | Docs | Verification | Pri | Viva |
|---|---|---|---|---|---|---|---|---|
| P2-01 | Regular expressions for tokens | C | `language/spec.py` regex table; DFA tables built from it | §5.3 Token specification | 04 | regex-vs-DFA equivalence test | M | regex of each token |
| P2-02 | Finite state machines for token recognition | C | `lexer/fsm.py` (explicit DFAs + simulator used by the scanner) | §5.3 DFA / FSM | 04 | DFA tests; scanner uses the same tables | M | DFA construction, longest match |
| P2-03 | Identify tokens and lexemes | A | `lexer/scanner.py` | §5.3 Tokens | 04 | lexer tests | M | token vs lexeme vs pattern |
| P2-04 | Recognize keywords, identifiers, operators, literals | A | same | same | 04 | lexer tests | M | keyword lookup |
| P2-05 | Implement input buffering | C | `lexer/buffer.py` two-buffer scheme with sentinels, configurable size | §5.3 Input buffer | 04 | buffer-boundary tests (token spanning a refill) | M | lexemeBegin/forward |
| P2-06 | Handle lexical errors | A | scanner recovery, VL-LEX-001…011 | §5.3 Errors | 01 §12, 04 | INV-LEX-01…07 | M | recovery strategy |
| P2-07 | Output keyword (example `DISPLAY`) recognized as reserved token, not identifier | A | `show` → KEYWORD | §5.3 (AC-L3) | 04 | keyword test | M | reserved words |
| P2-08 | Scanner implemented manually or with Lex/Flex (our choice: manual) | A | hand-written | — | 02 §2 | — | M | why manual |

### 4.4 Phase 3 — Syntax analysis

| ID | Requirement | Cls | Implementation | UI | Docs | Verification | Pri | Viva |
|---|---|---|---|---|---|---|---|---|
| P3-01 | Parser based on our grammar | A | `parser/recursive_descent.py` over `G′` | §5.4 | 05 | parser tests; all examples parse | M | grammar ↔ code mapping |
| P3-02 | Recursive descent parsing | A | same (production parser) | §5.4 Call trace; §5.5 LL(1) pseudocode | 05, 06 | parser tests | M | procedure per nonterminal |
| P3-03 | LL(1) parsing | B | `grammar/ll1.py` (table + stack parser); proves `G′` is LL(1) | §5.5 LL(1) | 06 | golden: `G′` 0 conflicts; differential test vs RD parser | M | predictive table |
| P3-04 | FIRST and FOLLOW sets | B | `grammar/analysis.py` | §5.5 Analysis | 06 | golden sets (incl. FOLLOW(IfStmt)) | M | fixed-point computation |
| P3-05 | Left-recursion elimination | B | `grammar/transform.py` (immediate + indirect) | §5.5 Transform | 06 | preset `left_recursion_indirect`; `G → G′` check | M | the algorithm |
| P3-06 | Left factoring | B | same | same | 06 | preset `left_factoring`; `G → G′` check | M | the algorithm |
| P3-07 | Ambiguous-grammar resolution incl. dangling else | B | LR conflict detection + precedence/associativity resolution; presets | §5.5 Dangling else | 06 | AC-G5; `expr_ambiguous` | M | prefer shift; matched/unmatched |
| P3-08 | Operator-precedence parsing | B | `grammar/op_precedence.py` | §5.5 Operator precedence | 06 | AC-G8; conflict case (unary minus) | M | precedence relations |
| P3-09 | Bottom-up shift-reduce parsing | B | `grammar/shift_reduce.py` (LR driver + trace) | §5.5 LR family | 06 | AC-G7; cross-check vs RD on examples | M | stack/handle |
| P3-10 | LR(0) parsing and table construction | B | `grammar/lr.py` | §5.5 LR family | 06 | golden: Vela `G` 214 states, conflicts | M | closure/goto |
| P3-11 | SLR(1) parsing and table construction | B | same | same | 06 | golden: 0 conflicts; `not_slr_but_lalr` | M | FOLLOW-based reduce |
| P3-12 | CLR(1) parsing and table construction | B | same | same | 06 | golden: 609 states; `not_lalr_but_clr` | M | LR(1) items, lookaheads |
| P3-13 | LALR(1) parsing and table construction | B | same (merge by core) | same | 06 | golden: 214 states; merge conflicts | M | why merging can create R/R |
| P3-14 | Detect and handle syntax errors | A | `parser/recovery.py` panic mode; VL-SYN-001…003 | §5.4 Errors & recovery | 05 | INV-SYN-01…08 | M | recovery strategy |
| P3-15 | Recognize IF, SWITCH, FOR, WHILE, DO-WHILE, function definitions | A | parser | §5.4 | 05 | per-construct parser tests | M | — |

### 4.5 Phase 4 — Syntax-directed translation and semantic analysis

| ID | Requirement | Cls | Implementation | UI | Docs | Verification | Pri | Viva |
|---|---|---|---|---|---|---|---|---|
| P4-01 | Construct ASTs | A | `ast/nodes.py`; builder in parser | §5.7 AST | 08 | AST shape tests | M | AST vs parse tree |
| P4-02 | Construct DAGs | C | `ast/dag.py` (value numbering), used by optimizer and codegen | §5.7 DAG | 08, 10, 11 | DAG sharing tests | M | DAG for CSE |
| P4-03 | Syntax-directed definitions (SDD) | B | `semantic/sdd/` generic engine + presets | §5.6 SDD/SDT | 08 | preset golden values | M | attributes, rules |
| P4-04 | Syntax-directed translation schemes (SDT) | B | same | same | 08 | SDT action-order tests | M | actions in productions |
| P4-05 | S-attributed definitions with attribute evaluation | B | engine classification + bottom-up evaluation | same | 08 | AC-S4 | M | synthesized attributes |
| P4-06 | L-attributed definitions with attribute evaluation | B | engine classification + depth-first evaluation | same | 08 | AC-S4, AC-S5 | M | inherited attributes |
| P4-07 | Symbol tables and scope management | A | `semantic/symbols.py` | §5.6 Symbol tables | 07 | scope/shadow tests | M | scope stack |
| P4-08 | Type checking | A | `semantic/checker.py` | §5.6 Checks | 07 | type tests | M | typing rules |
| P4-09 | Type equivalence | C | `types.py` (structural for arrays by element type; name equivalence for base types) | §5.6 Conversions | 07 | equivalence tests | M | name vs structural equivalence |
| P4-10 | Type conversion | C | implicit `int→float` (ImplicitCast node), explicit `as` | §5.6, §5.7 | 01 §6.3, 07 | conversion table tests | M | coercion vs cast |
| P4-11 | Validate function arguments and return types | A | checker, `returns.py` | §5.6 | 07 | INV-SEM-06…11 | M | all-paths-return |
| P4-12 | Detect undeclared and redeclared variables | A | checker | §5.6 | 07 | INV-SEM-01, 02 | M | — |
| P4-13 | Function/operator overloading and polymorphism “where supported” | C | operator overloading of `+` (int/float/string) shown; function overloading **not supported by design** (documented, doc 01 §8) | §5.6 Conversions & overloading | 01, 07 | AC-S3 | M | overloading resolution; why we exclude function overloading |

### 4.6 Phase 5 — Intermediate code generation

| ID | Requirement | Cls | Implementation | UI | Docs | Verification | Pri | Viva |
|---|---|---|---|---|---|---|---|---|
| P5-01 | Intermediate code generator producing Three-Address Code | A | `ir/generator.py`, `tac.py` | §5.8 TAC | 09 | TAC golden tests | M | quadruples |
| P5-02 | Variable declarations | A | same | §5.8 Translation | 09 | TAC tests | M | initialization code |
| P5-03 | Arithmetic expressions | A | same | same | 09 | TAC tests | M | temporaries |
| P5-04 | IF-ELSE statements | A | same | same | 09 | TAC tests | M | labels/jumps |
| P5-05 | Nested conditions | A | same | same | 09 | TAC tests | M | — |
| P5-06 | SWITCH-CASE statements | A | same | same | 09 | TAC tests | M | compare chain |
| P5-07 | FOR loops | A | same | same | 09 | TAC tests; continue → update | M | — |
| P5-08 | WHILE loops | A | same | same | 09 | TAC tests | M | — |
| P5-09 | DO-WHILE loops | A | same | same | 09 | TAC tests | M | — |
| P5-10 | Function definitions and calls | A | same | same | 09 | TAC tests | M | param/call protocol |
| P5-11 | Array operations | A | same | same | 09 | TAC tests | M | index → address |
| P5-12 | *(project goal)* TAC interpreter as an independent oracle | A | `ir/interpreter.py` | §5.2 Verify, §5.9 | 09, 13 | all examples: TAC output = VM output | S | testing strategy |

### 4.7 Phase 6 — Code optimization

| ID | Requirement | Cls | Implementation | UI | Docs | Verification | Pri | Viva |
|---|---|---|---|---|---|---|---|---|
| P6-01 | Basic block identification | C | `opt/blocks.py` (leaders algorithm) | §5.8 Basic blocks | 10 | leader tests | M | leader rules |
| P6-02 | Control-flow graph construction | C | `opt/cfg.py` (+ dominators, loops) | §5.8 CFG | 10 | CFG edge tests | M | edges, back edges |
| P6-03 | DAG-based optimization | C | `ast/dag.py` used in local optimization pass | §5.7, §5.9 | 10 | DAG tests | M | value numbering |
| P6-04 | Constant folding | C | `passes/const_fold.py` | §5.9 | 10 | opt tests (incl. wrap, no folding of ÷0) | M | safety |
| P6-05 | Constant propagation | C | `passes/const_prop.py` (local + global) | §5.9 | 10 | opt tests | M | reaching definitions |
| P6-06 | Common-subexpression elimination | C | `passes/cse.py` (DAG-local + global available expressions) | §5.7, §5.9 | 10 | opt tests | M | available expressions |
| P6-07 | Dead-code elimination | C | `passes/dce.py` (liveness) | §5.9 | 10 | opt tests | M | live variables |
| P6-08 | Copy propagation | C | `passes/copy_prop.py` | §5.9 | 10 | opt tests | M | available copies |
| P6-09 | Loop optimization | C | `passes/licm.py`, `strength.py` (natural loops, dominators) | §5.9, §5.8 CFG | 10 | opt tests on `08` | M | LICM conditions |
| P6-10 | Global optimization | C | data-flow framework `opt/dataflow.py` (reaching defs, liveness, available exprs/copies) | §5.9 | 10 | opt tests | M | iterative data-flow |
| P6-11 | Machine-dependent optimization | C | `codegen/peephole.py` + register-aware choices | §5.9, §5.10 | 10, 11 | peephole tests | M | peephole patterns |
| P6-12 | Clear comparison of original vs optimized code and explanation of each technique’s improvement | A | before/after with change records and metrics | §5.9 | 10 | AC-O1, AC-O5 | M | explaining each pass |
| P6-13 | *(project goal)* optimizations preserve behavior | A | validator + oracle equivalence | §5.9 | 10, 13 | AC-O3, AC-O4 | S | correctness argument |

### 4.8 Phase 7 — Target code generation

| ID | Requirement | Cls | Implementation | UI | Docs | Verification | Pri | Viva |
|---|---|---|---|---|---|---|---|---|
| P7-01 | Design a target instruction set | A | `codegen/isa.py` | §5.10 ISA drawer | 11 | ISA tests | M | formats, addressing modes |
| P7-02 | Instruction selection | A | `codegen/selector.py` | §5.10 Target code | 11 | selection tests | M | templates |
| P7-03 | Instruction cost calculation | A | `codegen/cost.py` | §5.10 | 11 | AC-C2 | M | cost model |
| P7-04 | Register allocation | A | `codegen/regalloc.py` (`getReg`, spills) | §5.10 Registers | 11 | AC-C3, AC-C4 | M | descriptors, spill choice |
| P7-05 | Assign registers to temporary variables | A | same | same | 11 | allocation tests | M | temp → location map |
| P7-06 | DAG-based code generation | A | `codegen/dag_codegen.py` | §5.10 DAG codegen | 11 | AC-C5 | M | node ordering |
| P7-07 | Show translation to executable or simulated target instructions | A | `vm/` executes generated program | §5.11 | 11 | AC-V1…V5; e2e outputs | M | execution model |

**Coverage count:** 4 project-level + 26 language-design + 8 Phase 1 + 8 Phase 2 + 15 Phase 3 + 13 Phase 4 + 12 Phase 5 + 13 Phase 6 + 7 Phase 7 = **106 rows** (2 of them *(project goal)*: P5-12 and P6-13). The Batch 4 audit re-derives this list from the assignment text and re-checks every row against the final documents.

---

## 5. Decisions made for ambiguous points

| # | Ambiguity | Decision | Reason |
|---|---|---|---|
| D-01 | “Implement parser” plus “demonstrate LR(0)/SLR/CLR/LALR” | One production parser (recursive descent over LL(1) `G′`); a generic grammar engine implements all other techniques on any grammar, cross-checked against the production parser | Avoids five duplicated production parsers while keeping every algorithm real (doc 02 §7) |
| D-02 | Does the compiler need to *use* YACC-style LR? | No; assignment allows hand-written. The SLR(1) table of Vela’s `G` is used in tests as a second recognizer | Defensible and testable |
| D-03 | “Function/operator overloading and polymorphism where supported” | Support operator overloading of `+` (numeric/string) and implicit widening; **no** function overloading | Keeps checker small; requirement conditional on language support; documented |
| D-04 | Is DAG a data structure or an optimization? | Both: expression DAG per basic block via value numbering; used for CSE and for code generation order | Covers P4-02, P6-03, P7-06 with one structure |
| D-05 | “Global optimization” | Iterative data-flow analyses over the CFG (reaching definitions, live variables, available expressions/copies) driving global const/copy propagation, CSE, DCE | Textbook-standard and testable |
| D-06 | “Machine-dependent optimization” | Peephole optimization on target code plus instruction-cost-aware selection | Standard definition |
| D-07 | “Executable or simulated target” | A custom VM (instruction-by-instruction interpreter of the generated instructions) | Allowed by the assignment; guarantees real execution |
| D-08 | Static typing and no `void` type | Functions without a return type are void; usable only as statements | Simple and C-familiar |
| D-09 | Light theme | Not provided | Cut for scope |
| D-10 | Scanner generator or manual | Manual scanner driven by explicit DFAs | The assignment asks for regexes, FSMs and buffering to be shown |

---

## 6. Scope and explicit non-goals

In scope: everything in Section 4. Out of scope (stated so nobody builds them): classes/objects, pointers, dynamic memory, generics, modules/imports, file I/O, function overloading, light theme, user accounts, persistence of programs on the server, running on anything but localhost, generating real x86/ARM machine code, garbage collection, string indexing/length, arrays as first-class values.

---

## 7. Technical risks and mitigations

| ID | Risk | Likelihood / impact | Mitigation |
|---|---|---|---|
| R-01 | Project too large for the time available | High / High | Milestone order puts a thin end-to-end path first (lexer → parser → semantic → TAC → VM-less TAC interpreter), then deepens; Grammar Lab and optimizer passes are independently shippable. Must-have vs should-have is the matrix priority. |
| R-02 | Grammar and lexer/parser drift apart | Medium / High | AP-5: grammar loaded at runtime; consistency tests; golden values (doc 01 §13.4). |
| R-03 | Optimizer breaks semantics | Medium / High | Per-pass validator; oracle comparison on every example and with random stdin; conservative memory/call handling. |
| R-04 | LR(1) state explosion on user grammars | Low / Medium | 5 000-state cap with honest `limit_reached` result. Vela’s own CLR(1) has 609 states (measured). |
| R-05 | Register allocation + DAG codegen bugs | Medium / High | Simple local `getReg` algorithm; values live in memory across blocks; differential tests TAC oracle vs VM. |
| R-06 | UI ends up showing invented data | Low / High | AP-4 lint rules, raw JSON drawer, Playwright tests asserting displayed values against API payloads. |
| R-07 | AI-generated code the group cannot explain | High / High | Section 9 workflow: explain-back reviews, module docstrings, size limits, AI log. |
| R-08 | Windows setup friction | Medium / Medium | Single `setup.ps1`/`start.ps1`; one-port demo mode; no Docker; documented prerequisites (Python ≥ 3.11, Node ≥ 20). |
| R-09 | Language design not liked by the instructor | Low / Medium | Open decisions list (doc 01 §17) reviewed before implementation. |
| R-10 | Assignment rules (group/AI/viva) unknown | Medium / High | OQ-1 below; strict defaults. |

---

## 8. Definition of done (project level)

1. All rows of Section 4 with priority M are demonstrably satisfied in the UI and by automated tests.
2. `scripts\test.ps1` passes: backend unit/integration tests, frontend tests, Playwright end-to-end.
3. `/api/selftest` reports every bundled valid and invalid program as passing.
4. All 10 valid examples produce their documented output through (a) the TAC oracle at O0, (b) the TAC oracle optimized, (c) the VM.
5. The 10-minute demo script (doc 16) works from a clean checkout on Windows 10/11 in ≤ 10 minutes of setup.
6. README lists exactly what is implemented and every known limitation (no claims beyond reality).
7. Every group member has completed the explain-back review of every phase (Section 9).

---

## 9. Academic integrity, group participation and viva (assumption set until OQ-1 is answered)

**Principles.** The language design, the grammar decisions and the explanation of every algorithm are the group’s own work and must be explainable by every member. AI assistance is used as an implementation tool and is **disclosed**.

**Workflow rules (binding on the implementation plan, doc 14/15):**
1. **Design review gate:** the group reads and approves docs 00–03 (this batch) and records approvals and changes in `DECISION_LOG.md` before implementation. Each member records at least one design decision they made or changed.
2. **AI assistance log:** every AI-agent session that produces code or documents is entered in `AI_ASSISTANCE_LOG.md` (date, tool, prompt summary, files affected, who reviewed). Templates in doc 16.
3. **Contribution tracking:** `CONTRIBUTIONS.md` records per member the modules they reviewed, tested, extended and presented.
4. **Explain-back review per milestone:** after each milestone, a group member (rotating) explains the new modules to the others using the module docstrings and the viva questions; unexplained code is simplified or rewritten.
5. **External material:** libraries and any copied algorithm descriptions (textbook, lecture notes, articles) are acknowledged in `ACKNOWLEDGEMENTS.md`; no code is copied from other student projects.
6. **Defensibility limits:** doc 02 §11 (module size, plain names, docstrings).
7. **Viva guide:** doc 16 gives, per phase: what/why/how, key algorithms, data structures, example in/out, common questions and “explain your design decision” questions.

If the instructor’s rules differ (e.g. stricter limits on AI use), they override this section and the roadmap is adjusted (OQ-1).

---

## 10. Open questions for the group

| ID | Question | Needed before |
|---|---|---|
| OQ-1 | Group size/roles, AI-use policy, plagiarism rules, deliverables, submission format, deadlines, viva format — not in the assignment text we have | Milestone 0 |
| OQ-2 | Approve language name *Vela* and the syntax choices listed in doc 01 §17 | Batch 2 |
| OQ-3 | Approve the cut list in Section 6 (notably: no function overloading, no light theme) | Batch 2 |
| OQ-4 | Confirm Windows 10/11 with Python ≥ 3.11 and Node ≥ 20 can be installed on the demo machine | Milestone 1 |
| OQ-5 | Is a written report required, and in what format? (doc 16 will contain a report skeleton either way) | Batch 4 |

---

## 11. Document map and dependencies

| Doc | Title | Batch | Depends on |
|---|---|---|---|
| 00 | Master spec (this) | 1 | — |
| 01 | Language specification | 1 | 00 |
| 02 | Compiler architecture & stack | 1 | 00, 01 |
| 03 | UI/UX specification | 1 | 00, 02 |
| 04 | Lexer | 2 | 01 |
| 05 | Parser | 2 | 01, 04 |
| 06 | Grammar & parsing lab | 2 | 01, 05 |
| 07 | Semantic analysis | 2 | 01, 05 |
| 08 | AST, DAG, SDD/SDT | 3 | 05, 07 |
| 09 | Intermediate code generation | 3 | 07, 08 |
| 10 | Code optimization | 3 | 09 |
| 11 | Target code & VM | 3 | 09, 10 |
| 12 | API & data contracts | 4 | 02–11 |
| 13 | Testing & acceptance | 4 | all |
| 14 | Implementation roadmap | 4 | all |
| 15 | Antigravity instructions | 4 | all |
| 16 | Report, demo & viva guide | 4 | all |

Also in the package: `docs/grammar/*` (runtime inputs), `examples/*.vela` (golden programs), `docs/README.md`.

## 12. Glossary of decisions that must not change without updating all documents
Language name; the 26 keywords; the five types; operator precedence table (doc 01 §6.1); grammar `G`/`G′` (`docs/grammar/`); error-code scheme `VL-<PHASE>-<nnn>`; TAC quadruple form; Vela VM with R0–R7; stack FP-relative frames; API prefix `/api`; one-port demo mode.
