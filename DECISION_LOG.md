# Decision Log

Record of technical, architectural, and design decisions made during the development of the Vela Compiler and Vela Studio.

| ID | Date | Topic | Decision | Reason / Context | Made by |
|---|---|---|---|---|---|
| DEC-001 | 2026-11-21 | Workspace structure | Adopt standard layout per doc 02 §3 with separated `backend/`, `frontend/`, `scripts/`, `docs/`, `examples/` | Maintain clean separation of concerns and pure Python compiler library | Implementation Agent |
| DEC-002 | 2026-11-21 | Spec Gap Filling | Create `docs/04_LEXER_SPECIFICATION.md` defining token classes, data structures, two-buffer scheme, and error recovery rules | Per agent-prompt.md Section 8 (ALLOW_SPEC_GAP_FILLING = true) | Implementation Agent |
| DEC-003 | 2026-11-21 | Spec Gap Filling | Create `docs/06_GRAMMAR_AND_PARSING_LAB_SPECIFICATION.md` defining grammar engine model, BNF loader, analysis algorithms, and Chomsky classification | Per agent-prompt.md Section 8 (ALLOW_SPEC_GAP_FILLING = true) | Implementation Agent |
| DEC-004 | 2026-11-21 | Spec Gap Filling | Create `docs/08_AST_DAG_SDD_SDT_SPECIFICATION.md` defining AST node hierarchy, S-expression printer, and JSON structure | Per agent-prompt.md Section 8 (ALLOW_SPEC_GAP_FILLING = true) | Implementation Agent |
| DEC-005 | 2026-11-21 | Spec Gap Filling | Create `docs/05_PARSER_SPECIFICATION.md` defining recursive descent parser over LL(1) grammar $G'$, CST nodes, panic-mode recovery, and call tracing | Per agent-prompt.md Section 8 (ALLOW_SPEC_GAP_FILLING = true) | Implementation Agent |
