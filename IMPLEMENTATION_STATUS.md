# Implementation Status
Last updated: 2026-11-21   Run #: 1

## Task table
| ID | Task | Status | Verified by (command → result) | Date | Notes |
|----|------|--------|--------------------------------|------|-------|
| M0-T1 | Skeleton and tooling | DONE | `powershell -File .\scripts\test.ps1` → 2 passed, ruff clean, tsc clean; `npm run build` → exit 0; pure import OK | 2026-11-21 | Workspace, backend venv, frontend, scripts |
| M0-T2 | Common foundations | DONE | `powershell -File .\scripts\test.ps1` → 8 passed; covers normalization, line/col conversion, all 47 diagnostic codes | 2026-11-21 | SourceFile, Span, Diagnostic, Limits, Budget |
| M1-T1 | Language tables | DONE | `powershell -File .\scripts\test.ps1` → 15 passed; asserts exactly 26 keywords, operators, delimiters, precedence, regexes | 2026-11-21 | spec.py single source of truth |
| M1-T2 | DFA, buffer, scanner | TODO | | | |
| M2-T1 | Model, loader, analysis | TODO | | | |
| M2-T2 | Transformations | TODO | | | |
| M2-T3 | LL(1) tools | TODO | | | |
| M2-T4 | LR family | TODO | | | |
| M3-T1 | AST nodes | TODO | | | |
| M3-T2 | Recursive-descent parser | TODO | | | |
| M4-T1 | Types and symbols | TODO | | | |
| M4-T2 | Checker | TODO | | | |
| M4-T3 | SDD/SDT engine | TODO | | | |
| M4-T4 | Expression DAG | TODO | | | |
| M5-T1 | TAC model and generator | TODO | | | |
| M5-T2 | TAC interpreter (oracle) | TODO | | | |
| M6-T1 | Blocks, CFG, dominators, loops | TODO | | | |
| M6-T2 | Data-flow framework | TODO | | | |
| M6-T3 | Passes | TODO | | | |
| M7-T1 | ISA, cost, selection | TODO | | | |
| M7-T2 | Registers and DAG code generation | TODO | | | |
| M7-T3 | VM | TODO | | | |
| M7-T4 | Pipeline and CLI | TODO | | | |
| M8-T1 | FastAPI | TODO | | | |
| M9-T1 | Shell and shared components | TODO | | | |
| M9-T2 | Playground and Dashboard | TODO | | | |
| M9-T3 | Lexer and Parser pages | TODO | | | |
| M9-T4 | Grammar Lab | TODO | | | |
| M9-T5 | Semantic and Trees pages | TODO | | | |
| M9-T6 | IR and Optimizer pages | TODO | | | |
| M9-T7 | CodeGen and VM pages | TODO | | | |
| M9-T8 | Reference page | TODO | | | |
| M10-T1 | End-to-end suite | TODO | | | |
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

## Known limitations
None yet.

## Blockers
None.

## Run log
- **Run #1 (2026-11-21):**
  - M0-T1: Workspace skeleton and tooling complete.
  - M0-T2: Common foundations complete (`vela.common.source`, `diagnostics`, `limits`, `budget`). 8 unit tests passing. Milestone M0 complete.
  - M1-T1: Language tables complete (`vela.language.spec`). 15 unit tests passing. Next: M1-T2.
