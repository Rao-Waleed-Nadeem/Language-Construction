# 03 — UI/UX Specification (Vela Studio)

> **Status:** Batch 1 draft for group review.
> **Related:** architecture & routes `02_COMPILER_ARCHITECTURE.md` §9 · data shapes `12_API_AND_DATA_CONTRACTS.md` (Batch 4) · the compiler data each page shows is defined in docs 04–11.
> **Golden rule (AP-4):** every number, token, tree, table, instruction and output on every page comes from a backend response. Where a page shows an *educational example* (Grammar Lab presets, SDD presets) it is produced by the backend grammar/SDD engines and carries the “Educational module” badge. No decorative or inert controls: if a control exists it works.

---

## 1. Product concept

*Vela Studio* is a dark, VS Code–like workbench: a left **activity bar** switches between pages, the Playground has editor + console, and each explorer page shows one compiler phase with a synchronized source panel. Moving the mouse over any token, AST node, TAC line, block or target instruction highlights the corresponding source span everywhere (AP-7).

Mapping of the 21 pages requested in the brief to the 12 routes (nothing dropped):

| Requested page | Where it lives |
|---|---|
| 1 Dashboard | `/` Dashboard |
| 2 Compiler Playground / Code Editor | `/playground` |
| 3 Lexer Explorer | `/lexer` |
| 4 Parser | `/parser` |
| 5 Grammar Lab | `/grammar-lab` |
| 6 FIRST/FOLLOW Explorer | `/grammar-lab` tab **Analysis** |
| 7 Parsing Table Generator | `/grammar-lab` tabs **LL(1)** and **LR family** |
| 8 AST Visualizer | `/trees` tab **AST** |
| 9 DAG Visualizer | `/trees` tab **DAG** |
| 10 Semantic Analysis | `/semantic` tab **Checks & types** |
| 11 Symbol Table Explorer | `/semantic` tab **Symbol tables** |
| 12 Intermediate Code Generator | `/ir` tab **Translation** |
| 13 TAC Viewer | `/ir` tab **TAC** |
| 14 Basic Block Explorer | `/ir` tab **Basic blocks** |
| 15 Control Flow Graph | `/ir` tab **CFG** |
| 16 Code Optimization Lab | `/optimizer` |
| 17 Target Code Generator | `/codegen` tab **Target code** |
| 18 Register Allocation Viewer | `/codegen` tab **Registers** |
| 19 Virtual Machine | `/vm` |
| 20 Instruction Execution / Simulation | `/vm` (step player) |
| 21 Documentation / Language Reference | `/reference` |

---

## 2. Visual design system

### 2.1 Theme
Dark by default; a light theme toggle is **out of scope** (documented cut). All colors are CSS variables in `frontend/src/app/theme.css`.

| Token | Value | Use |
|---|---|---|
| `--bg-0` | `#0b0e14` | app background |
| `--bg-1` | `#11151d` | panels |
| `--bg-2` | `#171c27` | raised surfaces, table headers |
| `--border` | `#252c3a` | 1 px borders |
| `--text-0` | `#e6e9ef` | primary text |
| `--text-1` | `#9aa4b5` | secondary text |
| `--accent` | `#5eead4` | primary action, focus ring |
| `--ok` `--warn` `--err` | `#4ade80` `#fbbf24` `#f87171` | status |
| `--sel` | `rgba(94,234,212,.18)` | selection / source highlight |

Phase colors (used in the pipeline bar, badges and graph node borders): Lexer `#60a5fa`, Parser `#a78bfa`, Semantic `#f472b6`, IR `#fb923c`, Optimizer `#facc15`, CodeGen `#34d399`, VM `#22d3ee`.

Typography: UI **Inter** 13–14 px; code, tokens, TAC, instructions **JetBrains Mono** 13 px (both bundled offline). Spacing scale 4/8/12/16/24. Radius 6 px. Icons: lucide. Motion: ≤ 150 ms ease for hover/expand; none for data updates; respect `prefers-reduced-motion`.

### 2.2 Syntax highlighting (editor and every code view)
Colors by token category: keyword `#c792ea`, type keyword `#82aaff`, identifier `#e6e9ef`, number `#f78c6c`, string/char `#c3e88d`, comment `#5c6773` italic, operator `#89ddff`, delimiter `#9aa4b5`. Highlighting uses a Monaco **Monarch** language definition generated at startup from `GET /api/language` (keywords, operators, token regexes) — no hand-maintained duplicate list.

### 2.3 Layout and responsiveness
Target: 1280×720 and larger desktop; usable down to 1024 px wide. Below 1024 px a banner states that the app is designed for desktop; layouts stack vertically (no horizontal page scroll). Panels use resizable splitters (`react-resizable-panels`), sizes persisted in `uiStore` (localStorage with try/catch; works without it).

### 2.4 Accessibility
Keyboard reachable controls, visible focus ring (`--accent`), contrast ≥ 4.5:1 for text, graph nodes also focusable (Enter selects), status never conveyed by color alone (icon + text), `aria-live="polite"` for the status bar and diagnostics counts.

---

## 3. Application shell

```
┌──┬──────────────────────────────────────────────────────────────────────────┐
│  │ Title bar:  Vela Studio · <example/file name>  ● unsaved    [Compile ▶] [Run ▶▶] │
│A │ Pipeline bar:  ① Lexer → ② Parser → ③ Semantic → ④ IR → ⑤ Optimizer → ⑥ CodeGen → ⑦ VM │
│c ├──────────────────────────────────────────────────────────────────────────┤
│t │                                                                          │
│i │                       page content (routes in §5)                        │
│v │                                                                          │
│i │                                                                          │
│t ├──────────────────────────────────────────────────────────────────────────┤
│y │ Status bar: ✓ compiled 42 ms · 0 errors · 1 warning · Ln 12, Col 8 · backend ● connected │
└──┴──────────────────────────────────────────────────────────────────────────┘
```

- **Activity bar** (left, 48 px, icons with tooltips): Dashboard, Playground, Lexer, Parser, Grammar Lab, Semantic, Trees, IR, Optimizer, CodeGen, VM, Reference.
- **Title bar:** example picker (dropdown of `/api/examples`), **Compile** (`Ctrl+Enter`), **Run** (`Ctrl+Shift+Enter`, compiles if needed), **Auto-compile** switch, **Optimization** switch (O0 / O1 = all passes; the individual pass toggles live in the Optimizer page).
- **Pipeline bar** (`PhaseBar`): seven chips with status icon (idle ○, running ◐ spinner, ok ✓, error ✕, skipped –) and counts of diagnostics; clicking a chip navigates to that phase’s page. The bar is always visible.
- **Status bar:** compile time (from the response `timings_ms`), error/warning counts (click opens Problems in the Playground), cursor position, backend connection indicator (polls `/api/health` every 10 s).
- **Global shortcuts:** `Ctrl+Enter` compile, `Ctrl+Shift+Enter` run, `Ctrl+K` command palette (jump to any page or example — a real feature: list of routes and examples), `F8` next problem.

### 3.1 Global states (apply to every page unless a page overrides)

| State | Display |
|---|---|
| **Backend unreachable** (health check fails or fetch rejects) | Full-width red banner “Cannot reach the Vela backend at 127.0.0.1:8000 — start it with `scripts\start.ps1`”, **Retry** button; pages show their empty state. |
| **No compile yet** | Page empty state with a single button **“Compile current program”** and the sentence naming what the page will show. |
| **Compiling** | Skeleton shimmer in content area; Compile button shows spinner and becomes **Cancel** (aborts the request). |
| **Phase skipped due to earlier error** | Banner: “Semantic analysis was skipped because the program has syntax errors” + button **Go to first error** (opens Playground with the cursor on it). Data from earlier phases remains visible. |
| **Stale result** (source edited after the last compile and auto-compile off) | Yellow chip “Out of date — recompile” on the page header; the old data stays visible. |
| **Transport / server error** (5xx, network) | Toast + inline error panel with response text and **Retry**; never a blank page. |
| **Truncated data** (response has `truncated: true`) | Info chip “Showing first N of M …” stating the cap. |

---

## 4. Shared components (`frontend/src/components/`)

| Component | Props (essential) | Behavior |
|---|---|---|
| `SourceView` | `source`, `spans[]`, `activeSpan` | Read-only Monaco with highlight decorations; hover/click on a span emits `uiStore.hoverSpan/pinSpan`. |
| `DiagnosticList` | `diagnostics[]` | Grouped by phase; severity icon, code chip (links to the Reference error catalogue), `line:col`, message, hint. Click jumps to Playground and selects the span. |
| `PhaseBar` | phase statuses | Section 3. |
| `GraphCanvas` | `nodes[]`, `edges[]`, `layout` | React Flow + dagre (top-bottom or left-right); pan, zoom, fit, minimap when > 40 nodes; node click selects and pins its span; **Export PNG** button (real: `html-to-image`). Layout runs in the browser; **content** is backend data. |
| `DataTable` | `columns`, `rows`, `filter?`, `virtualize?` | Sticky header, sortable columns, text filter, copy-as-TSV, row hover emits a span when the row has one. |
| `StepPlayer` | `steps[]`, `render(step)` | ⏮ ◀ ▶ ⏭ play/pause, speed 0.25×–4×, scrub slider, “step N / M”, keyboard ←/→/space. Pure playback over a backend array. |
| `DiffView` | `before`, `after` (arrays of lines + per-line ids) | Side-by-side or unified toggle; removed lines red, added green, unchanged dim; line mapping uses backend-provided ids, not a text-diff guess. |
| `BadgeUsedByCompiler` / `BadgeEducational` | — | Teal “Used by the compiler” / amber “Educational module” chip with tooltip (doc 02 §7). |
| `ExplainPanel` | `topic` | Collapsible “How this works” text, static content stored in `frontend/src/content/*.md` (viva-oriented: what, why, algorithm, complexity). |
| `CopyButton`, `JsonDrawer` | data | **“View raw JSON”** drawer on every page showing the exact backend payload slice (supports transparency and debugging). |
| `EmptyState`, `ErrorPanel`, `Skeleton` | — | Section 3.1. |
| `CommandPalette` | — | `Ctrl+K`. |

---

## 5. Pages

Every page definition has the same fields. **Data** names the response path from doc 12; **API** the endpoints used. All pages use the global states in §3.1 in addition to the page-specific ones listed.

### 5.1 Dashboard — `/`
- **Purpose:** orientation, project status, proof the pipeline works, quick start.
- **Layout:** header (logo, language tagline, backend status) · 3 columns: *Quick start* (example cards) · *Pipeline overview* (clickable 7-stage diagram) · *Self-test* panel. Below: *Assignment coverage* (collapsible list of the 7 phases with links to the pages that demonstrate each).
- **Components:** `ExampleCard` ×10 (title, constructs covered, **Open in Playground** and **Compile & run**), pipeline diagram (SVG, static layout, status colors from `compileStore`), `SelfTestPanel`, `LastRunSummary`.
- **Inputs:** none (buttons only).
- **Outputs:** navigation; self-test results table (`program`, `expected`, `actual`, pass/fail, duration).
- **Interactions:** **Run self-test** calls `/api/selftest` (valid + invalid corpus) and shows a pass/fail bar and a row per program; clicking a row opens it in the Playground.
- **Data:** `/api/examples`, `/api/selftest`, last compile summary from `compileStore`.
- **Empty:** no last run → “No program compiled yet — pick an example.” · **Loading:** card skeletons; self-test progress bar (“12/40 programs”). · **Error:** examples fetch fails → ErrorPanel with Retry; self-test row failure shows diff of expected/actual.
- **Acceptance:** AC-D1 shows all 10 examples loaded from the backend; AC-D2 *Run self-test* reports every bundled program with pass status and total counts that equal the corpus size; AC-D3 clicking an example loads it into the editor; AC-D4 the coverage list links to existing routes only.

### 5.2 Compiler Playground — `/playground`
- **Purpose:** write, compile, run and see errors.
- **Layout:** left 60 % **Editor** · right 40 % tabbed **Output / Problems / Stdin** · bottom strip **PhaseBar summary** (also global).
- **Components:** Monaco editor (Vela Monarch grammar, line numbers, bracket matching, error squiggles from diagnostics, hover shows diagnostic message + hint, minimap off), autocomplete (keywords, types, declared identifiers and function signatures **taken from the last successful semantic result** — if none, keywords only), snippet completions (`for`, `while`, `switch`, `func`, `if/else` templates defined in `frontend/src/features/editor/snippets.ts`), **Output** tab (console: stdout, runtime error in red with code and source line link, exit status, steps, time), **Problems** tab (`DiagnosticList`), **Stdin** tab (multi-line text box; “Used by `read` statements”).
- **Inputs:** source text, stdin text, example picker, optimization switch.
- **Outputs:** console output, diagnostics, status of each phase.
- **Interactions:** Compile / Run buttons; Run executes `/api/run` and shows output; a runtime error highlights its line; **Verify** button calls `/api/verify` and shows “TAC oracle (O0) = TAC oracle (optimized) = VM ✓” or the first mismatch; **Format**: *not provided* (cut). Reset example, Download `.vela`, Open `.vela` (browser file picker).
- **Data:** `compileStore.result.diagnostics`, `compileStore.lastRun`. **API:** `/api/compile`, `/api/run`, `/api/verify`, `/api/examples`, `/api/language`.
- **Empty:** blank editor shows a placeholder program prompt: “Pick an example or start typing.” · **Loading:** run button spinner, console shows “Running…” · **Error:** lexical/syntax/semantic errors appear as squiggles + Problems; runtime errors in Output.
- **Acceptance:** AC-P1 typing an undeclared variable produces a squiggle with the correct code within 1.5 s (auto-compile on); AC-P2 *Run* on `05_functions.vela` prints the exact expected output from doc 01 §15; AC-P3 `read` programs use the Stdin tab; AC-P4 *Verify* passes on all valid examples; AC-P5 autocomplete lists declared variables in scope-agnostic form (all names from the symbol tables) — acceptable limitation, documented.

### 5.3 Lexer Explorer — `/lexer`
- **Purpose:** show the scanner’s work: tokens, lexemes, regexes, DFAs, buffering, errors (assignment Phase 2).
- **Layout:** top: `SourceView` with token underlines (colored by category) · tabs below: **Tokens**, **Token specification**, **DFA / FSM**, **Scan trace**, **Input buffer**, **Errors**.
- **Components:**
  - *Tokens*: `DataTable` — #, category, symbol, lexeme, value, line:col, length; filter by category; category count chips; hover ↔ source highlight.
  - *Token specification*: table of every token class: name, **regular expression**, example lexemes, notes (keywords listed; `DISPLAY`-style rule: “keyword vs identifier resolved by keyword-table lookup after the identifier DFA accepts”). Data from `/api/language`.
  - *DFA / FSM*: `GraphCanvas` showing the DFA for the selected token class (Identifier/Keyword, Integer/Float, String, Char, Operators, Comments) with states, accepting states (double circle), labelled transitions, and — when a token is selected in the Tokens tab — its **path highlighted**.
  - *Scan trace*: `StepPlayer` over the lexeme’s character-by-character DFA moves (state, char, next state) for the selected token.
  - *Input buffer*: visualization of the two-buffer scheme (buffer 1/2, `lexemeBegin`, `forward`, sentinels, refill events) replaying the real scan for the current source with the **configured buffer size** (default 64 chars, adjustable 16–256 in a number box; triggers a recompile of the lexer phase only via `options.buffer_size`).
  - *Errors*: lexical diagnostics with the recovery action taken.
- **Inputs:** selected token; buffer size.
- **Outputs:** the tables/graphs above.
- **Data:** `result.lexer.{tokens, diagnostics, dfas, buffer_trace, token_traces}`, `/api/language`. **API:** `/api/compile` (with `options.trace=true` for lexer traces), `/api/language`.
- **Empty/Loading/Error:** global. Lexical errors do **not** block this page.
- **Acceptance:** AC-L1 the token count and the lexemes equal the backend token list for every example; AC-L2 selecting token `<=` highlights its DFA path; AC-L3 `show` is displayed with category KEYWORD and `shown` with IDENTIFIER (assignment’s reserved-word rule); AC-L4 each INV-LEX program lists its code at the right position; AC-L5 changing buffer size changes the refill count in the Input-buffer tab.

### 5.4 Parser Explorer — `/parser`
- **Purpose:** show how the production parser (recursive descent over LL(1) grammar `G′`) recognizes the program, and the syntax-error handling (Phase 3).
- **Layout:** left `SourceView` · right tabs: **Parse tree**, **Call trace**, **Grammar `G′`**, **Errors & recovery**.
- **Components:**
  - *Parse tree*: `GraphCanvas` (collapsible subtrees; nodes labelled with grammar symbols; terminals show lexeme); large trees collapse below depth 6 by default; click a node → span pinned; search box for a symbol name.
  - *Call trace*: `StepPlayer` over recursive-descent events (`enter FuncDecl`, `match 'func'`, `exit Block`, `lookahead = ID`, `choose production #n`) with the **current call stack** drawn beside it and the current input position highlighted in the source.
  - *Grammar `G′`*: the 138 productions grouped by nonterminal with the **FIRST/FOLLOW-based predict sets** that the parser uses to choose; each production row shows which parser method implements it (e.g. `parse_if_stmt`).
  - *Errors & recovery*: list of syntax diagnostics; for each, the expected-token set, the recovery events (“skipped tokens … until `;`”) and the resulting resync point.
- **Data:** `result.parser.{parse_tree, trace, diagnostics, recovery}`, `/api/grammar/presets/vela-ll1`. **API:** `/api/compile` (`options.trace=true`).
- **Empty/Error:** a syntax-error program shows the **partial** parse tree with `ERROR` nodes in red.
- **Acceptance:** AC-PA1 parse-tree leaves read left-to-right equal the token lexemes; AC-PA2 INV-SYN-08 shows two errors and the recovery events; AC-PA3 the call trace for `04_loops.vela` ends with `exit Program` and `accept`; AC-PA4 *“Used by the compiler”* badge shown.

### 5.5 Grammar Lab — `/grammar-lab`
- **Purpose:** hands-on demonstrations of all parsing theory the assignment lists, on **any** grammar (default: Vela’s). Every result is computed by `vela.grammar` (`BadgeEducational`, except where the grammar is Vela’s own and the algorithm is a compile-path cross-check — badge text says so).
- **Layout:** left **Grammar editor** (monospace, syntax-highlight for `->`, `|`, `ε`; preset dropdown: *Vela G*, *Vela G′*, and all `docs/grammar/presets/*.bnf` with their title/expected-result comments; start-symbol picker; **Load**, **Save as file**, **Reset**) · right tabs (seven below). Grammar parse errors appear inline under the editor.
- **Tabs and components**

| Tab | Content | API |
|---|---|---|
| **Analysis** (FIRST/FOLLOW Explorer) | Terminals, nonterminals, nullable set, **FIRST** table, **FOLLOW** table; **Show derivation** step player explaining how each set was filled (iteration number, rule applied); grammar classification (Chomsky Type 2/3 with reason); LL(1)/SLR/LALR/CLR membership summary chips; ambiguity hints (e.g. conflicts pointing at dangling else). | `/api/grammar/analyze` |
| **Transform** | Buttons **Eliminate left recursion** (immediate + indirect, ordering shown), **Left factor**, **Both**; step log with before/after for each affected nonterminal; resulting grammar with **Use as input** button; re-analysis chips (“now LL(1): yes/no”). | `/api/grammar/transform` |
| **LL(1)** | Predictive parsing table (rows nonterminals × columns terminals+`$`, cells production numbers; conflict cells red with both candidates); numbered production list; **Parse string** box → `StepPlayer` showing stack, remaining input, action (`expand A → …`, `match`, error) and the growing parse tree; **Recursive-descent pseudocode** button (generates pseudocode from the LL(1) grammar). | `/api/grammar/ll1`, `/api/grammar/rd-pseudocode` |
| **LR family** | Algorithm selector **LR(0) / SLR(1) / LALR(1) / CLR(1)**; **canonical collection** as cards (state number, items with dots, kernel vs closure items; lookaheads for LR(1)/LALR) and as an interactive automaton graph (transitions labelled); **ACTION/GOTO table** (shift `sN`, reduce `rN`, `acc`, conflicts highlighted red with S/R or R/R label); numbered productions; **Compare** panel showing for the current grammar: number of states and conflicts under all four algorithms side by side; **Resolve conflicts** panel: precedence/associativity declarations (`left + -`, `left * /`, `right ^`) and “prefer shift” option, with the resolution log; **Parse string** → shift-reduce trace (`StepPlayer`: state stack, symbol stack, input, action, production used) plus parse tree. LALR view marks which CLR states were merged. | `/api/grammar/lr` |
| **Operator precedence** | Leading/trailing sets, precedence relation matrix (`⋖ ≐ ⋗`, blanks = error, conflicts red), eligibility check (no ε, no adjacent nonterminals) with the exact violated production, **Parse string** with stack/relation trace. Includes the *unary-minus problem* note when a conflict arises (preset `vela_expr_operator`). | `/api/grammar/op-precedence` |
| **Dangling else** | Guided demo with three side-by-side presets: ambiguous grammar (conflict shown in the LR table at state *n* on `e`), matched/unmatched grammar (no conflict), and Vela’s mandatory-brace approach; two different parse trees for `i i a e a` shown for the ambiguous grammar by a **“Show all parse trees”** button (backend enumerates derivations up to a bound). | `/api/grammar/lr`, `/api/grammar/analyze` |

- **Inputs:** grammar text, start symbol, algorithm, input string, precedence declarations.
- **Outputs:** as above; downloadable JSON of every table; **Copy table as Markdown** (real).
- **Data:** `labStore` (last responses). **API:** `/api/grammar/*`.
- **Empty:** default loads preset *Vela G* and shows a hint to press **Analyze**. · **Loading:** per-tab spinner (LR(1) of Vela’s `G` is built in < 1 s; show state count progress if > 1 s). · **Error:** grammar syntax error with line number; `limit_reached` for oversize LR(1) with message “LR(1) construction stopped at 5000 states”; empty start symbol.
- **Acceptance (golden values from doc 01 §13.4):** AC-G1 Vela `G`: LR(0) 214 states with conflicts, SLR(1) 0 conflicts, LALR(1) 214 states, CLR(1) 609 states; AC-G2 `G′` LL(1) table has 0 conflicts; AC-G3 preset `not_slr_but_lalr` shows 1 SLR conflict, LALR 10 states, CLR 14 states and no conflicts for both; AC-G4 preset `not_lalr_but_clr` shows LALR 13 states with 2 conflicts and CLR 14 states with none; AC-G5 preset `dangling_else` shows one S/R conflict on `e` and the resolved version shows none; AC-G6 `FOLLOW(IfStmt)` lacks `else`; AC-G7 for `E → E + T | T …` the shift-reduce trace of `id + id * id` ends with `accept`; AC-G8 `vela_expr_operator` reports no conflicts and parses `id + id * id`; AC-G9 a user grammar typed in the editor is analyzed (not only presets).

### 5.6 Semantic Analysis — `/semantic`
- **Purpose:** type checking, symbol tables, scopes, conversions, overloading, and the SDD/SDT demonstrations (Phase 4).
- **Tabs:** **Checks & types**, **Symbol tables**, **Conversions & overloading**, **SDD / SDT**.
- **Components**
  - *Checks & types*: source on the left with each expression’s inferred type shown on hover; table of checks performed (rule, node, result ✓/✕, message) grouped by rule family: declarations, assignment, operators, conditions, calls, returns, arrays, switch, jumps; diagnostics list.
  - *Symbol tables*: **scope tree** (`GraphCanvas` or indented tree) with a table of symbols for the selected scope (name, kind var/param/func, type, scope level, declared at, size/offset, uses count); **event log** `StepPlayer` (“enter scope #2”, “insert `i: int`”, “lookup `i` → found in scope #2”, “shadow `level`”, “exit scope”) so scope management is visible; a toggle shows the table **as it was at a chosen source line**.
  - *Conversions & overloading*: table of every implicit cast inserted (`int→float` at line:col) and explicit `as` casts; table of `+` resolutions: operand types → chosen operation (`int add`, `float add`, `string concat`) — the operator-overloading/polymorphism demonstration; **type equivalence** panel listing compared type pairs with verdicts and the rule (“name equivalence for base types; array params by element type”).
  - *SDD / SDT*: preset selector (**Desk calculator (S-attributed)**, **Type declarations (L-attributed, inherited type)**, **Boolean expression labels**, **Vela expression typing**), editable rule table (production → semantic rules, restricted rule language in doc 08), input string, **Evaluate**; output: annotated parse tree (each node with its attribute values), **dependency graph** (attribute→attribute edges), **evaluation order**, and verdict chips **S-attributed: yes/no**, **L-attributed: yes/no** with the violating rule if no; SDT view shows the same translation as a scheme with action positions and a trace of actions executing during a bottom-up/top-down parse.
- **Data:** `result.semantic.*`, `/api/sdd/evaluate`. **API:** `/api/compile`, `/api/sdd/evaluate`.
- **Empty/Error:** semantic skipped on syntax errors; SDD rule syntax errors reported inline.
- **Acceptance:** AC-S1 INV-SEM-01…19 each show the right code at the right position in Checks; AC-S2 `10_scopes.vela` shows 4 scopes for `main` with the three `level` shadows and the log events in order; AC-S3 `09_strings_and_casts.vela` shows `+` resolved as `string concat`; AC-S4 the *Desk calculator* preset reports S-attributed = yes, and *Type declarations* reports L-attributed = yes, S-attributed = no; AC-S5 a user rule making an attribute depend on a right sibling is reported not L-attributed with that rule named.

### 5.7 AST and DAG Visualizer — `/trees`
- **Purpose:** show the abstract syntax tree and the expression DAGs (Phase 4).
- **Tabs and components**
  - **AST**: `GraphCanvas` of the typed AST (node label = kind, key attribute e.g. `BinaryOp +`, `type: int`, implicit-cast nodes drawn dashed); toggle **Show types**, **Show spans**, **Collapse function bodies**; node inspector side panel (kind, fields, span, children ids); **Compare with parse tree**: a toggle that shows the parse tree beside the AST with lines connecting corresponding nodes (to explain AST vs concrete syntax); text view **S-expression** with copy.
  - **DAG**: pick a function and a basic block (or “each expression statement”); `GraphCanvas` of the **expression DAG** (value numbering: shared subexpressions drawn once, with in-edges showing sharing; each node lists the variables/temporaries attached); a **Build steps** `StepPlayer` shows each TAC instruction being added (“new node #4 `+`”, “reuse node #4 (common subexpression)”); a stat strip: nodes with tree-form vs DAG-form node counts.
- **Data:** `result.parser.ast`, `result.semantic.typed_ast`, `result.optimizer.dags[function][block]` (the same DAGs the optimizer and code generator use). **API:** `/api/compile`.
- **Acceptance:** AC-T1 the AST of `a + b * c` has `+` at the root with `*` as right child; AC-T2 the DAG of `(a+b)*2` and `(a+b)*3` (08_optimizer_showcase, block with both) shares one `a+b` node and the stat strip shows tree nodes > DAG nodes; AC-T3 selecting an AST node highlights its exact source span; AC-T4 implicit casts appear as dashed `ImplicitCast` nodes in `01_hello_types.vela` (`answer + ratio`).

### 5.8 Intermediate Code — `/ir`
- **Purpose:** three-address code, how each construct is translated, basic blocks and the control-flow graph (Phases 5–6a).
- **Tabs and components**
  - **TAC**: function picker; `DataTable` of instructions (index, label, op text like `t3 = t1 + t2`, source line link); labels shown as separate rows; jump targets are clickable (scroll to label); **Stats** (instruction count, temporaries, labels, per-op counts); toggle **Original / Optimized** (Optimized after Optimizer).
  - **Translation**: pick any source statement (by clicking in the source panel or from a list) → shows the **translation rule applied** (rule name, e.g. “`while` loop”, the rule’s TAC template with placeholders) next to the actual TAC it produced, with matching colors for each template part. Rule catalogue is the backend’s static rule table (doc 09) used by the generator — each emitted instruction carries `rule_id`.
  - **Basic blocks**: block list as cards (id, leader reason: “first instruction”, “jump target”, “follows a jump”; instruction range; successors/predecessors); **Leaders** step player (“instruction 7 is a leader because it is the target of `goto L2`”).
  - **CFG**: `GraphCanvas` (blocks as boxes containing their TAC; edges labelled `true`/`false`/`fallthrough`/`goto`; entry and exit nodes; back-edges dashed; loop membership shading when loops were found); **dominator tree** toggle and **natural loops** list (header, members, back edge).
- **Data:** `result.ir.functions[*].code`, `result.optimizer.functions[*].{blocks, edges, dominators, loops}` (computed for the **unoptimized** TAC and for the optimized TAC). **API:** `/api/compile`.
- **Acceptance:** AC-I1 each construct in the assignment (declaration, arithmetic, if-else, nested if, switch, for, while, do-while, function def/call, array read/write) has a translation shown for `examples/*.vela`; AC-I2 a `for` loop CFG shows a back edge and one natural loop; AC-I3 every jump target label exists in the TAC; AC-I4 block count shown equals the number of leaders computed by the backend; AC-I5 `and`/`or` produce jump code, never a plain `and` instruction.

### 5.9 Code Optimization Lab — `/optimizer`
- **Purpose:** show each optimization, what it changed, and prove it preserved behavior (Phase 6).
- **Layout:** left column **Pass list** (checkboxes with order, each with a one-line description and badge “Local / Global / Loop / Machine”); right: **Before / After** `DiffView` for the selected function and pass (or **All passes** cumulative); below: **Change log**, **Metrics**, **Equivalence check**.
- **Passes (all real, doc 10):** Constant folding · Constant propagation (local+global) · Copy propagation (local+global) · Common-subexpression elimination (DAG/local + global available-expressions) · Dead-code elimination (local + global liveness) · Algebraic simplification · Loop-invariant code motion · Strength reduction (induction variables) · Peephole (machine-dependent; shown under CodeGen but toggled here) .
- **Components:** per-pass **change records** (“line 12: `t4 = 2*3` → `t4 = 6` — constant folding”; each record has before/after line ids for `DiffView`); **Metrics table** (instructions before/after, temporaries, estimated instruction cost from the cost model, loop-body instruction count, per pass and total); **Step through** `StepPlayer` that applies the recorded changes one at a time; **Iteration view** (the pipeline repeats until no change; shows each round); **Equivalence check** button → `/api/verify` shows outputs of: unoptimized TAC oracle, optimized TAC oracle, VM — plus the equality result; **Explanation** per pass (`ExplainPanel`: technique, algorithm, when safe, the example from this program).
- **Inputs:** pass toggles; function selector; stdin used for equivalence check.
- **Data:** `result.optimizer.{passes, stats, program}`; `/api/verify`. **API:** `/api/compile` (`options.passes=[…]`), `/api/verify`.
- **Empty:** a program where nothing changes shows “No optimization opportunities found” plus the list of passes that ran.
- **Acceptance:** AC-O1 on `08_optimizer_showcase.vela` every pass in the list reports at least one change; AC-O2 disabling a pass removes its changes (recompile) and the diff updates; AC-O3 the equivalence check passes for all valid examples, with several stdin sets for `07_io` and `08`; AC-O4 INV-RUN-01…05 produce the same error code with and without optimization; AC-O5 the after-TAC instruction count ≤ before for every example, and strictly less for `08`; AC-O6 no placeholder passes are listed.

### 5.10 Target Code and Register Allocation — `/codegen`
- **Purpose:** show instruction selection, costs, register allocation, DAG-based code generation (Phase 7).
- **Tabs and components**
  - **Target code**: function picker; two-column view: **optimized TAC** (left) and **target instructions** (right) aligned by `tac_index` (hover links both); each instruction row shows opcode, operands, **cost**, and the **selection rule** applied (“`t = a + b`, a in R1, b in memory → `ADD R1, b` cost 2”); totals per block and per function; **Peephole** toggle with its change list; **Instruction-set reference** drawer (opcode table with formats, costs and semantics — from `/api/language`-like `isa` object in the compile response).
  - **Registers**: for a selected basic block, a `StepPlayer` over **register and address descriptors** after each TAC instruction (table: R0–R7 contents, variables’ locations: register / memory / both), **spill** and **load** events highlighted, the `getReg` decision with its reason (“free register”, “farthest next use”, “spill Rk”); a **live/next-use** table for the block; **temporary → location mapping** (`t3 → R2`, `t9 → [FP-12]`); allocation summary (spills, max registers used).
  - **DAG codegen**: the block’s DAG with the **chosen node evaluation order** (numbered) and the instructions emitted per node; toggle **DAG order vs straight TAC order** to compare instruction counts/cost (both computed by the backend).
- **Data:** `result.codegen.{program, costs, allocation, dags, peephole}`. **API:** `/api/compile`.
- **Acceptance:** AC-C1 each TAC op in the generated program has at least one target instruction linked by `tac_index`; AC-C2 sum of per-instruction costs equals the displayed total; AC-C3 register snapshots never show two live variables in one register; AC-C4 a function with more than 8 simultaneously live values shows spills (provided in test program `tests/programs/valid/regpressure.vela`); AC-C5 DAG-order cost ≤ TAC-order cost is shown truthfully (whatever the backend computed — the page never alters it).

### 5.11 Virtual Machine and Execution Console — `/vm`
- **Purpose:** execute the generated target program and let the user watch it (Phase 7 “executable or simulated”).
- **Layout:** top: control bar (**Run**, **Step**, **Back**, **Run to end**, speed, scrub slider, **Reset**; stdin box) · three columns: **Program** (instruction list, current `PC` row highlighted, breakpoints by clicking the gutter — breakpoints are stored in the UI and *applied during playback of the recorded trace*) · **Machine state** (registers R0–R7, SP, FP, PC, flags; **stack** frames with variable names via debug info; **static memory** with changed cells highlighted; **call stack**) · **Console** (stdout so far, input consumed).
- **Mechanism:** `/api/run` returns the full snapshot trace (cap 5 000 steps, then `truncated`). The UI plays it back; it never executes instructions itself. If the program runs longer than the cap, the console still shows the **complete** final output (executed by the backend) and a banner explains that the step-by-step view covers the first 5 000 steps.
- **Components:** `StepPlayer`, register grid (changed registers flash for one step), stack view (frame boundaries, locals with names/types), instruction detail card (opcode semantics text from the ISA table and the operands’ values before/after), **Execution summary** (status, steps, total cost executed, max stack depth, output length), **Runtime error panel** (code, message, source line link, PC, instruction).
- **Data:** `lastRun.{status, stdout, error, steps, summary, snapshots}`. **API:** `/api/run`.
- **Acceptance:** AC-V1 stdout equals the expected output for all valid examples (doc 01 §15); AC-V2 stepping backward restores previous register values exactly; AC-V3 each INV-RUN program ends in the specified code and the faulting instruction is highlighted; AC-V4 Run-to-end on a program over 5 000 steps still shows full stdout and the truncation banner; AC-V5 stdin from the Playground is reused here.

### 5.12 Language Reference and Documentation — `/reference`
- **Purpose:** Vela’s language manual and the project documentation, reading from the same source as the compiler.
- **Layout:** left sidebar table of contents · right content · top search box (client-side text search over the loaded documents — a legitimate UI function).
- **Sections:** *Language tour* (generated from `/api/language`: keywords, types, operators with precedence table, literals, scope rules); *Grammar* (the BNF with syntax coloring, `G` and `G′`, and the verified-properties table from doc 01 §13.4); *Error catalogue* (every code with meaning, an invalid example and the fix; each diagnostic code chip elsewhere links here); *Examples* (all valid programs with **Open in Playground**); *Architecture* and *Specification documents* (renders `docs/*.md` via `/api/docs/{name}`); *Viva guide* (doc 16, when present).
- **Acceptance:** AC-R1 the keyword and operator tables equal `/api/language` exactly; AC-R2 every error code defined in doc 01 §12 appears once; AC-R3 each example link opens the right program; AC-R4 search finds a known term (“dangling”) across documents.

---

## 6. Cross-page interaction rules

1. **Single source selection:** hovering a span in any view sets `hoverSpan`; every `SourceView` and any row/node with that span (or containing it) gets a highlight; pinning (click) persists until Esc.
2. **Compile-once semantics:** pages never trigger compiles except via the global controls (and Lexer buffer-size, Optimizer pass toggles, which call `/api/compile` with changed options and update the global result).
3. **Deep links:** `/lexer?token=12`, `/ir?fn=main&block=3`, `/optimizer?pass=cse`, `/grammar-lab?preset=dangling_else&tab=lr` select state from the URL so a viva demo can be bookmarked.
4. **Consistent identifiers:** a TAC instruction index, block id, target instruction index shown on one page is the same on all others.
5. **Raw JSON drawer** is available on every page and shows the real payload; this is the answer to “is this fabricated?”

## 7. UI-level acceptance summary
- Every route in doc 02 §9.2 renders with all three states (empty, loading, error) without console errors (Playwright test iterates routes).
- No control without a handler; no static fake data in `frontend/src` except the content in `frontend/src/content/*.md` and the snippets list (checked by a lint rule forbidding hard-coded token/TAC/instruction arrays in `pages/`).
- A 10-minute demo script (doc 16) can be executed using only the UI.
