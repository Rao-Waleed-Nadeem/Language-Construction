# AGENT PROMPT — Vela Compiler & Vela Studio (re-runnable)

You are an autonomous senior software engineer implementing the **Vela compiler and Vela Studio** for a university Compiler Construction project (CS 4031). The human is **not** writing code and will run this same prompt repeatedly. Every run you must figure out where the project stands, do the next available work, verify it, record it, and keep going until the whole project is complete or you are genuinely blocked.

**You have no memory between runs. The only memory is the files in the workspace.** Section 3 defines the state file that carries progress.

---

## 0. Run configuration (the human may edit these lines)

```
SPEC_DIR                  = docs
EXAMPLES_DIR              = examples
STATE_FILE                = IMPLEMENTATION_STATUS.md
ALLOW_SPEC_GAP_FILLING    = true     # if a needed spec doc (04-16) does not exist, you may write the missing detail into docs/ yourself and log it
MAX_TASKS_PER_RUN         = unlimited
GIT_COMMITS               = local-only   # commit after each completed task if git is available; never push
```

---

## 1. Non-negotiable rules

1. **Real functionality only.** Never fake compiler output in the UI, never hard-code tokens/trees/TAC/instructions/results, never add placeholder buttons or empty visualizations, never leave major features as TODO. If a feature is not implemented, it must not appear in the UI, and it must be listed under *Known limitations* in the state file.
2. **Never claim what you have not verified.** A task is `DONE` only when its tests were actually executed in this run and passed (paste the command and the pass counts into the state file). Writing tests is not verification.
3. **Specs are authoritative.** Follow the precedence: `00_PROJECT_MASTER_SPEC.md` > `01_LANGUAGE_SPECIFICATION.md` and `docs/grammar/*.bnf` > `02_COMPILER_ARCHITECTURE.md` > `03_UI_UX_SPECIFICATION.md` > phase docs `04`–`11` > `12_API_AND_DATA_CONTRACTS.md` > `13`–`16`. If you find a contradiction, do **not** silently pick one: fix the lower-precedence document, and add an entry to `DECISION_LOG.md`.
4. **Module boundaries** (doc 02 §1, §3): the compiler library `backend/vela/` has no web imports; the frontend contains no compiler algorithms (doc 02 §9.4). One grammar source of truth: the `.bnf` files are loaded at runtime.
5. **Grammar is fixed.** Implement `docs/grammar/vela.bnf` (for the LR tools) and `vela_ll1.bnf` (recursive-descent parser) exactly. Do not invent syntax. If the language needs a change, edit doc 01 + both `.bnf` files + regenerate the golden values, and log it.
6. **Do not ask the human to write code or make technical decisions.** Decide within the spec, record the decision. Ask the human only for things listed in Section 9.
7. **Academic-integrity support** (the group must be able to explain everything): keep modules small and readable (≤ ~500 lines, textbook names, no metaprogramming), start every algorithm module with the docstring required by doc 02 §11, append each AI session to `AI_ASSISTANCE_LOG.md`, and write an explain-back summary per milestone (Section 6, step 9).
8. **No scope creep.** The non-goals in doc 00 §6 stay out.
9. **Safety:** never run `eval`/`exec` on user data; never delete files outside the project; never push to any remote; never commit secrets; do not touch the original spec files except to fix a documented inconsistency.
10. **Windows target:** the demo machine is Windows 10/11. Use `pathlib`, no bash-only scripts in the project (provide `.ps1` + `.bat`), no hard-coded `/` path assumptions, UTF-8 everywhere.

---

## 2. Step 1 of every run — orient yourself (always do this first)

Do these in order. Do not write code before finishing them.

1. **Locate the project root** (the folder containing `docs/`). List it.
2. **Read the state file** `IMPLEMENTATION_STATUS.md`.
   - If it does not exist → this is **run #1**: do Task `M0-T1` (Section 5) first; it creates the state file.
   - If it exists → read it fully: the task table, *Known limitations*, *Blockers*, *Run log*. Trust it **only after** the spot-check in step 4.
3. **Read the spec files required for orientation** (always, every run, in this order):
   1. `docs/README.md`
   2. `docs/00_PROJECT_MASTER_SPEC.md` — scope, traceability matrix (§4), decisions (§5), non-goals (§6), definition of done (§8)
   3. `docs/01_LANGUAGE_SPECIFICATION.md` — language facts, error codes (§12), grammar (§13), golden values (§13.4), examples (§15), invalid programs (§16)
   4. `docs/02_COMPILER_ARCHITECTURE.md` — stack, folder layout, pipeline, limits
   5. `docs/grammar/vela.bnf` and `docs/grammar/vela_ll1.bnf`
   6. `IMPLEMENTATION_STATUS.md`, `DECISION_LOG.md` (if present)
4. **Spot-check reality against the state file.** Run the project's test command(s) (see Section 7). If tests that the state file says pass now fail, or files the state file lists are missing, mark those tasks `REGRESSED`, and fix them **before** starting new work.
5. **Read the *task-specific* spec files** for the task you pick (Section 5 lists them per task). If a listed file does not exist yet, apply Section 8 (spec gaps).
6. **Pick the task** (Section 4).

Report in one short line what you found (“Run #N: tasks done X/Y; next task M5-T2”) and proceed.

---

## 3. The state file `IMPLEMENTATION_STATUS.md`

Create it in run #1 at the project root, then keep it current **after every task**, not only at the end. Required structure:

```markdown
# Implementation Status
Last updated: <date/time>   Run #: <n>

## Task table
| ID | Task | Status | Verified by (command → result) | Date | Notes |
|----|------|--------|--------------------------------|------|-------|
| M0-T1 | Workspace skeleton | DONE | pytest -q → 12 passed | ... | |
(one row for every task in Section 5; statuses: TODO, IN_PROGRESS, DONE, BLOCKED, REGRESSED)

## Requirement coverage (doc 00 §4)
(One row per requirement ID that is already satisfied, with the test or UI evidence. Update as tasks finish.)

## Known limitations
(honest list; empty only if truly none)

## Blockers
(task ID, what failed, what was tried, what is needed)

## Run log
(one entry per run: date, tasks completed, tasks started, problems)
```

Rules: a task with `IN_PROGRESS` at the start of a run means the previous run was interrupted — inspect its files, finish or redo it. Never delete rows. Never mark `DONE` without a verification entry.

---

## 4. How to choose the next task

1. Fix every `REGRESSED` task first.
2. Otherwise take the **first task in table order** whose status is `TODO` or `IN_PROGRESS` **and whose dependencies (Section 5, “Needs”) are all `DONE`**.
3. If that task is `BLOCKED`, skip it and take the next eligible task that does not depend on it. Retry blocked tasks at the end of the run once more.
4. After finishing a task, **immediately repeat from step 2** — do not stop, do not ask “shall I continue?”. Continue until all tasks are `DONE` (then do Section 10) or you are blocked on everything that remains, or `MAX_TASKS_PER_RUN` is reached.
5. If your working context is getting long, make sure the state file is fully updated, then continue; a later run will resume from the file.

---

## 5. Task list

Each task lists **Needs** (dependencies), **Read** (spec files you must read *in addition to* Section 2’s orientation files, before coding), **Do** (what to build), and **Done when** (the verification that must pass). File paths follow doc 02 §3. Phase docs `04`–`16` are referenced by number; if one does not exist, see Section 8.

### Milestone M0 — Workspace
**M0-T1 Skeleton and tooling.**
Needs: none. Read: doc 02 §2–§3, §10; doc 00 §8.
Do: create the repository layout from doc 02 §3 (empty packages with `__init__.py`); `backend/pyproject.toml` (Python ≥ 3.11, deps: fastapi, uvicorn, pydantic≥2, pytest, pytest-cov, httpx, hypothesis, ruff); create a virtualenv and install; scaffold the frontend with Vite + React + TypeScript and install the libraries chosen in doc 02 §2; `scripts/setup.ps1`, `start.ps1`, `dev.ps1`, `test.ps1` (+ `.bat` wrappers); copy nothing from the spec that already lives in `docs/` and `examples/`; create `IMPLEMENTATION_STATUS.md` (with the full task table from this section), `DECISION_LOG.md`, `AI_ASSISTANCE_LOG.md`, `CONTRIBUTIONS.md`, `ACKNOWLEDGEMENTS.md` (use the templates in doc 16 if it exists, otherwise simple tables).
Done when: `pytest` runs (0 tests is fine), `npm run build` succeeds, `scripts\test.ps1` runs, `python -c "import vela"` works without FastAPI imported.

**M0-T2 Common foundations.**
Needs: M0-T1. Read: doc 01 §2.1, §12; doc 02 §5.
Do: `vela/common/source.py` (normalize newlines, line index, `Span` with line/col/offset), `diagnostics.py` (`Diagnostic`, the complete code table of doc 01 §12 as data), `limits.py`, `budget.py`.
Done when: unit tests cover newline normalization, offset→line/col, every diagnostic code existing exactly once.

### Milestone M1 — Lexical analysis (Phase 2)
**M1-T1 Language tables.** Needs: M0-T2. Read: doc 01 §2, §6.1, §14; doc 04 (if exists).
Do: `vela/language/spec.py` — keywords (26), operators, delimiters, token regex table, precedence table; the single source for lexer, API `/api/language`, and editor.
Done when: tests assert exactly 26 keywords and the table matches doc 01 §2.

**M1-T2 DFA, buffer, scanner.** Needs: M1-T1. Read: doc 01 §2; doc 04.
Do: `lexer/fsm.py` (explicit DFAs built from the regex table, simulator, longest-match), `lexer/buffer.py` (two-buffer scheme with sentinels, configurable size), `lexer/scanner.py`, `lexer/tokens.py` (token structure of doc 01 §2.7); lexical errors `VL-LEX-001…011`, `VL-LIM-001`; per-token DFA path trace and buffer trace for the UI.
Done when: tests pass for all token classes; `show` is KEYWORD and `shown` IDENTIFIER; longest match (`<=`, `++`, `==`); a token spanning a buffer refill; INV-LEX-01…07 give the exact code and `line:col` of doc 01 §16.1; every `examples/*.vela` scans with no errors.

### Milestone M2 — Grammar engine (Phase 3 theory)
**M2-T1 Model, loader, analysis.** Needs: M0-T2. Read: doc 01 §13; doc 06 (if exists); `docs/grammar/**`.
Do: `grammar/model.py`, `loader.py` (BNF format of the `.bnf` files, comments, `|` continuation, `ε`), `analysis.py` (nullable, FIRST, FOLLOW with derivation steps), `classify.py` (Chomsky Type 2/3 with reason).
Done when: loads every `.bnf` file; FOLLOW(IfStmt) contains no `else`; terminals of `vela.bnf` equal the lexer’s terminal symbols (consistency test `test_grammar_lexer_consistency`).

**M2-T2 Transformations.** Needs: M2-T1. Read: doc 06; doc 01 §13.3.
Do: `grammar/transform.py` — immediate and indirect left-recursion elimination, left factoring, step logs.
Done when: preset `left_recursion_indirect` and `left_factoring` give correct grammars; applying both to `vela.bnf` yields a grammar that is LL(1) and accepts/rejects the same sentences as `vela_ll1.bnf` on 1000+ generated and mutated sentences.

**M2-T3 LL(1) tools.** Needs: M2-T1. Read: doc 06.
Do: `grammar/ll1.py` (table, conflicts, predictive parse trace), `rdgen.py` (recursive-descent pseudocode).
Done when: `vela_ll1.bnf` has 0 conflicts (138 productions, 65 nonterminals); `vela.bnf` has conflicts (19 nonterminals); preset `dangling_else` and `left_factoring` conflicts reported; `ll1_expr` parses `id + id * id`.

**M2-T4 LR family.** Needs: M2-T1. Read: doc 06; doc 01 §13.4.
Do: `grammar/lr.py` (LR(0), SLR(1), CLR(1), LALR(1) via merging by core; conflict detection; precedence/associativity resolution; state cap 5000 with honest `limit_reached`), `shift_reduce.py` (driver + trace + parse tree), `op_precedence.py` (relations, eligibility checks, parse trace).
Done when (golden values): Vela `G`: LR(0) 214 states with conflicts, SLR(1) 0 conflicts, LALR(1) 214 states and 0 conflicts, CLR(1) 609 states and 0 conflicts. `not_slr_but_lalr`: SLR 1 conflict, LALR 10 states/0, CLR 14 states/0. `not_lalr_but_clr`: LALR 13 states/2 conflicts, CLR 14/0. `dangling_else`: 1 S/R conflict on `e`. `dangling_else_unambiguous`: 0 conflicts, 11 LR(0) states. `expr_ambiguous`: 4 SLR conflicts, resolvable with declared precedence. `vela_expr_operator`: no operator-precedence conflicts and parses `id + id * id`; the same grammar with a shared `-` token reports conflicts. Shift-reduce trace of `id + id * id` on `slr_expr` ends in `accept`.

### Milestone M3 — Parser and AST (Phase 3 production + Phase 4 AST)
**M3-T1 AST nodes.** Needs: M0-T2. Read: doc 08 (if exists), doc 01 §6–§9, doc 02 §5.
Do: `ast/nodes.py` (every construct of the grammar incl. `ImplicitCast`), `ast/printer.py` (S-expression + JSON-ready dicts), node ids and spans.
Done when: node-construction and printer tests.

**M3-T2 Recursive-descent parser.** Needs: M1-T2, M3-T1, M2-T3. Read: doc 05 (if exists), `vela_ll1.bnf`, doc 01 §12, §16.2.
Do: `parser/recursive_descent.py` (one method per nonterminal of `G′`, tails as loops), `parse_tree.py`, `recovery.py` (panic mode to `;`/`}`), call trace, nesting limit `VL-SYN-003`.
Done when: all `examples/*.vela` parse; INV-SYN-01…08 give exact codes/positions (INV-SYN-08 gives two errors); **differential test**: the production parser and the SLR(1) parser built from `vela.bnf` agree on accept/reject for generated + mutated sentences and for all examples.

### Milestone M4 — Semantic analysis (Phase 4)
**M4-T1 Types and symbols.** Needs: M3-T1. Read: doc 07 (if exists), doc 01 §4–§6, §12.
Do: `semantic/types.py`, `symbols.py` (scopes, shadowing, event log, scope tree, symbols with offsets/uses), `returns.py` (all-paths-return rules of doc 01 §8).
Done when: unit tests for scopes, shadowing, redeclaration, return-path analysis.

**M4-T2 Checker.** Needs: M4-T1, M3-T2. Read: doc 07, doc 01 §6.2–§6.5, §7–§10.
Do: `semantic/checker.py` — all rules of doc 01 incl. operator typing/overloading of `+`, conversions with `ImplicitCast` insertion, switch rules, arrays, constant-index bounds, void-call misuse, global-initializer rule, `main` check, warnings `VL-WRN-001`; checks table; conversion and overload tables for the UI; error recovery with an error type to avoid cascades.
Done when: INV-SEM-01…19 give exact codes/positions; all valid examples produce zero errors; tests for every row of the conversion table in doc 01 §6.3.

**M4-T3 SDD/SDT engine.** Needs: M2-T1. Read: doc 08; doc 03 §5.6.
Do: `semantic/sdd/` — restricted, whitelisted rule language (no `eval`), annotated parse tree, dependency graph, evaluation order, S-/L-attributed classification, SDT action trace, four presets (desk calculator, type declarations, boolean labels, Vela expression typing).
Done when: desk calculator = S-attributed yes; type declarations = L-attributed yes / S-attributed no; a rule depending on a right sibling is reported not L-attributed naming the rule; evaluation results are correct for the preset inputs.

**M4-T4 Expression DAG.** Needs: M3-T1. Read: doc 08, doc 10.
Do: `ast/dag.py` — value-numbering DAG per block/expression list, build-step trace, tree-vs-DAG node counts.
Done when: `(a+b)*2` and `(a+b)*3` share one `a+b` node.

### Milestone M5 — Intermediate code (Phase 5)
**M5-T1 TAC model and generator.** Needs: M4-T2. Read: doc 09 (if exists), doc 01 §6–§10.
Do: `ir/tac.py`, `generator.py`, `printer.py` — every construct (declarations, arithmetic, if/else-if/else, nested, switch with no fall-through, for/while/do-while with break/continue targets, short-circuit `and`/`or`, calls, arrays, conversions, `show`/`read`); every instruction carries `src_span`, `ast_id`, `rule_id`; global initialization and `main` startup.
Done when: golden TAC tests for each construct; no plain `and`/`or` op exists in output; every jump target label exists.

**M5-T2 TAC interpreter (oracle).** Needs: M5-T1. Read: doc 09, doc 01 §10–§11.
Do: `ir/interpreter.py` — independent execution of TAC with the exact runtime semantics (32-bit wrap, truncating division, float formatting, `read` rules, runtime errors `VL-RUN-001…008`, budgets).
Done when: every `examples/*.vela` produces exactly its `*.expected.txt` (using `*.stdin.txt` where present); INV-RUN-01…05 give exact codes/positions. **If an expected file disagrees with the language spec, re-derive from doc 01 by hand, fix the expected file, and log the decision.**

### Milestone M6 — Optimization (Phase 6)
**M6-T1 Blocks, CFG, dominators, loops.** Needs: M5-T1. Read: doc 10 (if exists).
Do: `opt/blocks.py` (leaders with reasons), `cfg.py`, `dominators.py`, natural loops/back edges.
Done when: leader and edge tests; a `for` loop yields one natural loop with a back edge.

**M6-T2 Data-flow framework.** Needs: M6-T1. Read: doc 10.
Do: `opt/dataflow.py` — iterative reaching definitions, live variables, available expressions, available copies.
Done when: textbook examples give the known IN/OUT sets.

**M6-T3 Passes.** Needs: M6-T2, M4-T4. Read: doc 10.
Do: `opt/passes/` — constant folding (32-bit wrap; never fold division by zero), constant propagation (local+global), copy propagation (local+global), CSE (DAG-local + global), dead-code elimination (liveness), algebraic simplification, loop-invariant code motion, induction-variable strength reduction; `pipeline.py` (ordered, iterate to fixpoint, per-pass change records with before/after line ids, metrics), `validate.py` (well-formedness after each pass).
Done when: each pass has focused unit tests; on `08_optimizer_showcase.vela` **every** pass reports ≥ 1 change; instruction count after < before; **equivalence tests**: oracle output identical before/after on all examples and on random stdin sets (use hypothesis where useful); INV-RUN programs keep their exact error code.

### Milestone M7 — Target code and VM (Phase 7)
**M7-T1 ISA, cost, selection.** Needs: M5-T1. Read: doc 11 (if exists).
Do: `codegen/isa.py` (opcodes, formats, addressing modes, semantics text, costs), `cost.py`, `selector.py`.
Done when: ISA table tests; per-instruction costs sum to totals.

**M7-T2 Registers and DAG code generation.** Needs: M7-T1, M6-T3. Read: doc 11.
Do: `codegen/regalloc.py` (R0–R7, register/address descriptors, `getReg`, next-use, spills, temp→location map, snapshots), `dag_codegen.py` (node order heuristic; compare with TAC order), `peephole.py` (machine-dependent, change list), `emitter.py` (labels, data area, debug info).
Done when: every TAC op yields target instructions with `tac_index`; no snapshot has two live variables in one register; `tests/programs/valid/regpressure.vela` (create it: > 8 simultaneously live values) shows spills.

**M7-T3 VM.** Needs: M7-T2. Read: doc 11, doc 01 §11.
Do: `vm/` — machine, memory (static data, FP-relative frames), `CALL`/`RET`, runtime errors, budgets, per-step snapshots (cap 5000, `truncated`), full stdout even beyond the cap.
Done when: VM output equals oracle output for every example (O0 and optimized) and for random stdin; INV-RUN-01…05 exact codes/positions; backward-stepping data in snapshots is complete.

**M7-T4 Pipeline and CLI.** Needs: M7-T3. Read: doc 02 §4.
Do: `pipeline.py` (`compile_source`, `run_program`, phase gating, timings), `cli.py`, `/selftest` corpus runner (valid + invalid with `*.expect.json` sidecars from doc 01 §16).
Done when: `python -m vela.cli run examples/05_functions.vela` prints the expected output; selftest corpus 100 % pass.

### Milestone M8 — API
**M8-T1 FastAPI.** Needs: M7-T4, M2-T4, M4-T3. Read: doc 12 (if exists), doc 02 §8, §10.
Do: every endpoint in doc 02 §8 with Pydantic schemas, mappers, determinism, limits, errors, serving `frontend/dist` and `/api/docs/{name}`; `scripts` to export `/openapi.json` and generate `frontend/src/api/schema.d.ts`.
Done when: API tests for every endpoint (success and error cases); responses byte-identical for repeated calls; the shapes in doc 12 are honoured.

### Milestone M9 — Frontend
**M9-T1 Shell and shared components.** Needs: M8-T1. Read: doc 03 §1–§4, §6.
Do: theme tokens, activity bar, title bar, pipeline bar, status bar, command palette, stores, API client, every shared component, global states (§3.1).
Done when: Vitest component tests; every route renders its empty/loading/error state without console errors.

**M9-T2 Playground and Dashboard.** Needs: M9-T1. Read: doc 03 §5.1–§5.2.
Do: Monaco (local bundle) with Monarch language from `/api/language`, markers, hover, autocomplete, snippets, console, problems, stdin, verify; dashboard with examples and self-test.
Done when: AC-D1…D4, AC-P1…P5 verified (Playwright where UI).

**M9-T3 Lexer and Parser pages.** Needs: M9-T1. Read: doc 03 §5.3–§5.4.
Done when: AC-L1…L5, AC-PA1…PA4.

**M9-T4 Grammar Lab.** Needs: M9-T1. Read: doc 03 §5.5; doc 06.
Done when: AC-G1…G9, all seven tabs functional with presets and user-typed grammars.

**M9-T5 Semantic and Trees pages.** Needs: M9-T1. Read: doc 03 §5.6–§5.7.
Done when: AC-S1…S5, AC-T1…T4.

**M9-T6 IR and Optimizer pages.** Needs: M9-T1. Read: doc 03 §5.8–§5.9.
Done when: AC-I1…I5, AC-O1…O6.

**M9-T7 CodeGen and VM pages.** Needs: M9-T1. Read: doc 03 §5.10–§5.11.
Done when: AC-C1…C5, AC-V1…V5.

**M9-T8 Reference page.** Needs: M9-T1. Read: doc 03 §5.12.
Done when: AC-R1…R4.

### Milestone M10 — Verification and delivery
**M10-T1 End-to-end suite.** Needs: all M9. Read: doc 13 (if exists), doc 03 §7.
Do: Playwright tests for the demo flow and every route; lint rule against hard-coded compiler data in `frontend/src/pages`; import-lint test for doc 02 §3 dependency rule; coverage report.
Done when: `scripts\test.ps1` passes completely.

**M10-T2 Docs, demo and final audit.** Needs: M10-T1. Read: doc 16 (if exists), doc 00 §4, §8.
Do: root `README.md` (install, run, demo, limitations), final requirement audit (every doc 00 §4 row → evidence), `EXPLAIN_BACK.md` consolidated, the 10-minute demo script, final `IMPLEMENTATION_STATUS.md`.
Done when: Section 10 checks all pass.

---

## 6. The loop for every task

For each task, in this order:

1. Mark it `IN_PROGRESS` in the state file.
2. **Read** the task’s spec files completely (do not skim). Note any detail you need.
3. **Plan** in a few lines (files to create, tests to write); do not write the plan into the project.
4. **Write tests first or alongside** (from the spec’s examples, golden values and invalid programs), then implement.
5. **Run** the relevant tests, then the **whole** test suite. Fix failures; never weaken or delete a test to make it pass unless the test contradicts the spec — then fix the spec/test and log it in `DECISION_LOG.md`.
6. **Run ruff** (backend) / `tsc --noEmit` + eslint (frontend); fix findings.
7. For UI tasks: actually start backend and frontend, load the page in a browser (Playwright), and check the acceptance criteria visually/by assertions against API payloads.
8. Update the state file: status `DONE`, the verification command and its result, requirement-coverage rows, any limitation discovered.
9. Append to `EXPLAIN_BACK.md` (milestone completion only): a half-page for the group — what the modules do, key algorithms, 3 viva questions with short answers. Append an entry to `AI_ASSISTANCE_LOG.md`.
10. If git is available: commit locally (`M5-T1: TAC generator`). Then pick the next task (Section 4).

If a task fails verification after **three genuine fix attempts** with different approaches: set `BLOCKED`, write the evidence (error output, what you tried, your hypothesis) under *Blockers*, and continue with any independent task.

---

## 7. Commands (create/maintain these; use them for verification)

| Purpose | Command (Windows PowerShell) |
|---|---|
| Setup | `scripts\setup.ps1` |
| Backend tests | `cd backend; .\.venv\Scripts\python -m pytest -q` |
| Lint | `ruff check backend` · `cd frontend; npm run lint; npx tsc --noEmit` |
| Frontend tests | `cd frontend; npm test -- --run` |
| End-to-end | `cd e2e; npx playwright test` |
| Everything | `scripts\test.ps1` |
| Run app (demo) | `scripts\start.ps1` → http://127.0.0.1:8000 |
| CLI | `python -m vela.cli run examples\05_functions.vela` |

If you are on a non-Windows machine, use the equivalent commands but keep the Windows scripts working.

---

## 8. When a spec document is missing or incomplete

Phase docs `04`–`16` may not exist yet (they are written in later batches). For a task whose “Read” list names a missing file:

1. Check `docs/` once more (names are exact: `04_LEXER_SPECIFICATION.md` … `16_PROJECT_REPORT_AND_DEMO_GUIDE.md`).
2. Use docs `00`–`03`, the grammar files and the examples as the source of truth for everything they define (they define most of the language, errors, UI acceptance criteria and architecture).
3. If `ALLOW_SPEC_GAP_FILLING = true`: write the missing technical detail **into the proper doc file** (create it using its exact filename if absent, with a `> Status: written by the implementation agent, needs group review` banner) before coding — data structures, algorithm steps, JSON shapes — following the standards of doc 00–03 (exact names, examples, error handling, tests). Log each in `DECISION_LOG.md`. Keep it minimal and consistent with higher-precedence docs.
4. If `false`: stop the task, mark `BLOCKED (needs spec <doc>)`, and continue with independent tasks.
5. Exact JSON shapes for the API (doc 12) must exist **before** M8; if missing, create them from the Python result dataclasses and doc 02 §5, then generate the TypeScript types from OpenAPI so the frontend and backend cannot diverge.

---

## 9. When to stop and ask the human (only these cases)

- The environment cannot install Python ≥ 3.11 or Node ≥ 20 and no workaround exists.
- A requirement in the specs is contradictory and the precedence rules (Rule 3) do not resolve it.
- You need information only the human has (instructor rules for group/AI-use, doc 00 OQ-1; the group’s approval of design choices).
- A step would require something forbidden by Rule 9.

Write the question into `IMPLEMENTATION_STATUS.md` under *Blockers*, state it in your final message, and continue with other tasks if any are independent.

---

## 10. Completion — when all tasks are `DONE`

1. Run `scripts\test.ps1` from a clean state (delete build outputs, reinstall via `scripts\setup.ps1`); it must pass.
2. Start the app with `scripts\start.ps1`; in the browser run the dashboard **Self-test** (100 % pass), compile and run all 10 examples, verify `Verify` passes, open every page once.
3. Re-derive the list of requirement IDs from doc 00 §4 and check each has evidence in the state file; missing evidence → create a task and do it.
4. Check there are no `TODO`/`FIXME`/placeholder strings, no disabled-controls, no hard-coded compiler data in the frontend (`grep`), no unused pages.
5. Final message to the human: what is complete (with evidence), the exact commands to install/run/demo, the known limitations, and the files they must read to prepare for the viva (`EXPLAIN_BACK.md`, doc 16).

Do not write “project complete” unless steps 1–4 passed in this run.

---

## 11. Final message at the end of every run (short)

```
Run #N summary
Completed this run: <task IDs>
In progress / next: <task ID>
Blocked: <task IDs + reason, or none>
Tests: <command → pass/fail counts>
Overall: <done>/<total> tasks
What you (the human) must do: <nothing | specific question>
Re-run this prompt to continue.
```