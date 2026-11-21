# Vela Compiler & Vela Studio — Specification Package

This folder is the complete, implementation-ready specification for the CS 4031 Compiler Construction final project: the **Vela** programming language, its compiler, and the **Vela Studio** visualization IDE. It is meant to be given to an AI coding agent (Antigravity) and also to be read, reviewed and defended by the group.

## Status of this package

| Batch | Documents | Status |
|---|---|---|
| 1 | `00` master spec · `01` language · `02` architecture & stack · `03` UI/UX · `grammar/` · `../examples/` | **Written — awaiting group review** |
| 2 | `04` lexer · `05` parser · `06` grammar & parsing lab · `07` semantic analysis | Not yet written |
| 3 | `08` AST/DAG/SDD/SDT · `09` intermediate code · `10` optimization · `11` target code & VM | Not yet written |
| 4 | `12` API & data contracts · `13` testing · `14` roadmap · `15` Antigravity instructions · `16` report/demo/viva | Not yet written |

**Do not start implementation until all four batches exist and the group has approved them.** Documents 04–16 are referenced by Batch 1 but do not exist yet; those references are forward references.

## Reading order

1. `00_PROJECT_MASTER_SPEC.md` — scope, requirement traceability matrix (106 rows), decisions, risks, integrity rules. **Authoritative.**
2. `01_LANGUAGE_SPECIFICATION.md` — the Vela language: syntax, types, semantics, error codes, grammar, example programs.
3. `grammar/vela.bnf`, `grammar/vela_ll1.bnf` — the authoritative grammar files (loaded by the compiler at runtime). `grammar/presets/*.bnf` — Grammar Lab teaching grammars.
4. `02_COMPILER_ARCHITECTURE.md` — technology stack, repository layout, module boundaries, pipeline.
5. `03_UI_UX_SPECIFICATION.md` — every page and component.
6. Later batches follow the order in `00` §11.

## Precedence when documents disagree

`00` > `01` and `grammar/*.bnf` (language facts) > `02` (structure) > `03` (UI) > per-phase docs 04–11 > `12` (exact JSON) > `13`–`16`.
A conflict is a documentation bug: fix the lower-precedence document and note it in `DECISION_LOG.md`.

## How the implementation agent uses the package (summary; full rules in doc 15, later)

1. Read the whole `docs/` folder, `examples/` and `grammar/` before writing code.
2. Follow the milestone order in doc 14; verify each milestone with its tests before continuing.
3. Never fake compiler output in the UI; never mark something implemented that is not.
4. Keep an honest `IMPLEMENTATION_STATUS.md` listing implemented features and known limitations.

## Verified facts in this package

Grammar and example programs were machine-checked with a throw-away script (not part of the deliverable): Vela’s grammar is SLR(1), LALR(1) and CLR(1) conflict-free, its LL(1) form has no conflicts, the two grammars accept/reject identically on 3 000 generated and mutated sentences, and all 10 example programs parse under both grammars. The numbers are recorded in `01_LANGUAGE_SPECIFICATION.md` §13.4 and become automated golden tests. Expected outputs of the examples were derived by hand from the language semantics; they have **not** been produced by a running implementation yet and are verified by the first milestone that can execute them.

## Folder contents

```
docs/
  README.md                         this file
  00_PROJECT_MASTER_SPEC.md
  01_LANGUAGE_SPECIFICATION.md
  02_COMPILER_ARCHITECTURE.md
  03_UI_UX_SPECIFICATION.md
  grammar/vela.bnf  vela_ll1.bnf  presets/*.bnf (11 files)
examples/01…10_*.vela  +  *.expected.txt (hand-derived output)  +  07_io / 08 *.stdin.txt
```
